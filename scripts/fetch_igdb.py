#!/usr/bin/env python3
"""Fetch game data from IGDB (Twitch) API and write to cache/igdb_cache.json.

Two-pass approach:
1. Search and fetch game details (name, rating, genres, cover, etc.)
2. Batch-resolve age rating IDs to get ESRB/PEGI ratings and content descriptors
"""

import json
import os
import re
import sys
import time
from datetime import datetime, timezone

import requests

SCRIPT_DIR = os.path.dirname(__file__)
SCANNED_FILE = os.path.join(SCRIPT_DIR, "scanned_games.json")
CACHE_FILE = os.path.join(SCRIPT_DIR, "cache", "igdb_cache.json")
IGDB_OVERRIDES_FILE = os.path.join(SCRIPT_DIR, "igdb_overrides.json")

IGDB_BASE = "https://api.igdb.com/v4"
TWITCH_TOKEN_URL = "https://id.twitch.tv/oauth2/token"

# IGDB organization IDs
ORG_ESRB = 1
ORG_PEGI = 2

# IGDB ESRB rating_category values -> our format
IGDB_ESRB_MAP = {
    1: {"rating": "RP", "min_age": None, "family_friendly": None, "kid_safe": None},
    2: {"rating": "EC", "min_age": 3, "family_friendly": True, "kid_safe": True},
    3: {"rating": "E", "min_age": 6, "family_friendly": True, "kid_safe": True},
    4: {"rating": "E10", "min_age": 10, "family_friendly": True, "kid_safe": True},
    5: {"rating": "T", "min_age": 13, "family_friendly": True, "kid_safe": False},
    6: {"rating": "M", "min_age": 17, "family_friendly": False, "kid_safe": False},
    7: {"rating": "AO", "min_age": 18, "family_friendly": False, "kid_safe": False},
}

# IGDB PEGI rating_category -> min age
IGDB_PEGI_MAP = {
    8: 3, 9: 7, 10: 12, 11: 16, 12: 18,
}


def get_credentials():
    client_id = os.environ.get("TWITCH_CLIENT_ID", "")
    client_secret = os.environ.get("TWITCH_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        env_file = os.path.join(SCRIPT_DIR, ".env")
        if os.path.exists(env_file):
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("TWITCH_CLIENT_ID="):
                        client_id = line.split("=", 1)[1].strip().strip('"').strip("'")
                    elif line.startswith("TWITCH_CLIENT_SECRET="):
                        client_secret = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not client_id or not client_secret:
        print("ERROR: Set TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET in env or scripts/.env")
        sys.exit(1)
    return client_id, client_secret


def get_access_token(client_id, client_secret):
    resp = requests.post(TWITCH_TOKEN_URL, params={
        "client_id": client_id, "client_secret": client_secret,
        "grant_type": "client_credentials",
    }, timeout=15)
    resp.raise_for_status()
    return resp.json()["access_token"]


def igdb_request(endpoint, body, client_id, token):
    headers = {"Client-ID": client_id, "Authorization": f"Bearer {token}"}
    resp = requests.post(f"{IGDB_BASE}/{endpoint}", data=body, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.json()


def search_game(name, client_id, token):
    search_name = re.sub(r"[:\-']", " ", name)
    # Remove commas in numbers (40,000 -> 40000) but replace other commas with space
    search_name = re.sub(r"(\d),(\d)", r"\1\2", search_name)
    search_name = search_name.replace(",", " ")
    search_name = re.sub(r"\s+", " ", search_name).strip()
    fields = ",".join([
        "name", "slug", "summary", "rating", "rating_count",
        "aggregated_rating", "aggregated_rating_count",
        "total_rating", "total_rating_count", "first_release_date",
        "genres.name", "platforms.name", "themes.name", "cover.url",
        "age_ratings",
        "involved_companies.company.name",
        "involved_companies.developer", "involved_companies.publisher",
    ])
    body = f'search "{search_name}"; fields {fields}; limit 5;'
    try:
        return igdb_request("games", body, client_id, token)
    except requests.RequestException as e:
        print(f"    Search error for '{name}': {e}")
        return []


def fetch_game_by_id(igdb_id, client_id, token):
    """Fetch a single game by its IGDB ID."""
    fields = ",".join([
        "name", "slug", "summary", "rating", "rating_count",
        "aggregated_rating", "aggregated_rating_count",
        "total_rating", "total_rating_count", "first_release_date",
        "genres.name", "platforms.name", "themes.name", "cover.url",
        "age_ratings",
        "involved_companies.company.name",
        "involved_companies.developer", "involved_companies.publisher",
    ])
    body = f"fields {fields}; where id = {igdb_id}; limit 1;"
    try:
        results = igdb_request("games", body, client_id, token)
        return results[0] if results else None
    except requests.RequestException as e:
        print(f"    Fetch error for IGDB ID {igdb_id}: {e}")
        return None


def load_igdb_overrides():
    if os.path.exists(IGDB_OVERRIDES_FILE):
        with open(IGDB_OVERRIDES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def match_score(query, candidate):
    # Exact match (case-insensitive) gets highest score
    if query.lower().strip() == candidate.lower().strip():
        return 1.0
    q_tokens = set(re.findall(r"\w+", query.lower()))
    c_tokens = set(re.findall(r"\w+", candidate.lower()))
    if not q_tokens:
        return 0
    overlap = q_tokens & c_tokens
    score = len(overlap) / max(len(q_tokens), len(c_tokens))
    # Penalize candidates that have extra tokens (e.g. "Dredge+" vs "Dredge")
    extra = len(c_tokens - q_tokens)
    if extra > 0:
        score *= (1 - 0.05 * extra)
    return score


def resolve_age_ratings(age_rating_ids, client_id, token):
    """Batch-fetch age ratings by IDs from the age_ratings endpoint."""
    if not age_rating_ids:
        return {}

    results = {}
    # IGDB allows up to 500 IDs per request, batch in chunks of 100
    id_list = list(age_rating_ids)
    for i in range(0, len(id_list), 100):
        chunk = id_list[i:i+100]
        ids_str = ",".join(str(x) for x in chunk)
        body = f"fields organization,rating_category,rating_content_descriptions,synopsis; where id = ({ids_str}); limit 500;"
        try:
            data = igdb_request("age_ratings", body, client_id, token)
            for ar in data:
                results[ar["id"]] = ar
            time.sleep(0.3)
        except requests.RequestException as e:
            print(f"    Age rating batch error: {e}")

    return results


def process_age_ratings(game_age_rating_ids, resolved_ratings):
    """Extract ESRB/PEGI info from resolved age rating data."""
    esrb_info = {"rating": None, "min_age": None, "family_friendly": None, "kid_safe": None}
    pegi_age = None
    synopsis = None

    for ar_id in game_age_rating_ids:
        ar = resolved_ratings.get(ar_id, {})
        org = ar.get("organization")
        rc = ar.get("rating_category")

        if org == ORG_ESRB and rc in IGDB_ESRB_MAP:
            esrb_info = IGDB_ESRB_MAP[rc]
            if ar.get("synopsis"):
                synopsis = ar["synopsis"]
        elif org == ORG_PEGI and rc in IGDB_PEGI_MAP:
            pegi_age = IGDB_PEGI_MAP[rc]
            if not synopsis and ar.get("synopsis"):
                synopsis = ar["synopsis"]

    # Extract content descriptors from synopsis if available
    content_descriptors = []
    if synopsis:
        # Truncate long synopses
        if len(synopsis) > 200:
            synopsis = synopsis[:197] + "..."

    return {
        **esrb_info,
        "pegi_age": pegi_age,
        "content_descriptors": content_descriptors,
        "age_synopsis": synopsis,
    }


def extract_data(game_data, age_info):
    """Extract fields from IGDB response into our cache format."""
    cover_url = None
    if game_data.get("cover", {}).get("url"):
        cover_url = "https:" + game_data["cover"]["url"].replace("t_thumb", "t_cover_big")

    released = None
    if game_data.get("first_release_date"):
        released = datetime.fromtimestamp(
            game_data["first_release_date"], tz=timezone.utc
        ).strftime("%Y-%m-%d")

    summary = game_data.get("summary", "")
    if len(summary) > 300:
        summary = summary[:297] + "..."

    genres = [g["name"] for g in game_data.get("genres", [])]
    themes = [t["name"] for t in game_data.get("themes", [])]
    platforms = [p["name"] for p in game_data.get("platforms", [])]

    developers = []
    publishers = []
    for ic in game_data.get("involved_companies", []):
        company_name = ic.get("company", {}).get("name")
        if company_name:
            if ic.get("developer"):
                developers.append(company_name)
            if ic.get("publisher"):
                publishers.append(company_name)

    return {
        "source": "igdb",
        "source_id": game_data["id"],
        "source_name": game_data.get("name", ""),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "igdb_rating": round(game_data["rating"], 1) if game_data.get("rating") else None,
        "igdb_rating_count": game_data.get("rating_count", 0),
        "aggregated_rating": round(game_data["aggregated_rating"], 1) if game_data.get("aggregated_rating") else None,
        "aggregated_rating_count": game_data.get("aggregated_rating_count", 0),
        "total_rating": round(game_data["total_rating"], 1) if game_data.get("total_rating") else None,
        "esrb_rating": age_info["rating"],
        "min_age": age_info["min_age"],
        "family_friendly": age_info["family_friendly"],
        "kid_safe": age_info["kid_safe"],
        "pegi_age": age_info.get("pegi_age"),
        "content_descriptors": age_info.get("content_descriptors", []),
        "age_synopsis": age_info.get("age_synopsis"),
        "genres": genres,
        "themes": themes,
        "released": released,
        "cover_url": cover_url,
        "description": summary,
        "platforms": platforms,
        "developers": developers,
        "publishers": publishers,
        "age_rating_ids": game_data.get("age_ratings", []),
    }


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def main():
    force = "--force" in sys.argv

    if not os.path.exists(SCANNED_FILE):
        print("ERROR: Run scan_games.py first")
        sys.exit(1)

    client_id, client_secret = get_credentials()
    print("IGDB: Authenticating with Twitch...")
    try:
        token = get_access_token(client_id, client_secret)
    except requests.RequestException as e:
        print(f"ERROR: Failed to get Twitch token: {e}")
        sys.exit(1)
    print("  Authenticated successfully")

    with open(SCANNED_FILE, "r", encoding="utf-8") as f:
        scanned = json.load(f)

    cache = load_cache()
    igdb_overrides = load_igdb_overrides()
    fetched = 0
    skipped = 0
    uncertain = []
    all_age_rating_ids = set()
    games_needing_age_ratings = {}  # game_id -> list of age_rating_ids

    # === Pass 1: Search and fetch game details ===
    print(f"IGDB Pass 1: Searching {len(scanned)} games...")

    for i, game in enumerate(scanned):
        game_id = game["id"]

        if not force and game_id in cache and cache[game_id].get("source_id"):
            # Collect age rating IDs from cached entries too
            ar_ids = cache[game_id].get("age_rating_ids", [])
            if ar_ids and not cache[game_id].get("esrb_rating"):
                all_age_rating_ids.update(ar_ids)
                games_needing_age_ratings[game_id] = ar_ids
            skipped += 1
            continue

        name = game["name"]
        print(f"  [{i+1}/{len(scanned)}] {name}")

        # Check for IGDB ID override
        if game_id in igdb_overrides:
            override_id = igdb_overrides[game_id]
            print(f"    Using IGDB override ID: {override_id}")
            best = fetch_game_by_id(override_id, client_id, token)
            if best:
                confidence = "confident"
                best_score = 1.0
            else:
                print(f"    Override ID {override_id} not found")
                cache[game_id] = {
                    "source": "igdb", "source_id": None,
                    "match_confidence": "none",
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                }
                time.sleep(0.3)
                continue
        else:
            results = search_game(name, client_id, token)
            if not results:
                print(f"    No results")
                cache[game_id] = {
                    "source": "igdb", "source_id": None,
                    "match_confidence": "none",
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                }
                uncertain.append(f"  NO MATCH: {name} (folder: {game['folder_name']})")
                time.sleep(0.3)
                continue

            best = None
            best_score = 0
            for r in results:
                score = match_score(name, r.get("name", ""))
                if score > best_score:
                    best_score = score
                    best = r

            if best is None:
                best = results[0]
                best_score = 0

            confidence = "confident" if best_score >= 0.5 else "uncertain"

        # Store with placeholder age info (will be resolved in pass 2)
        ar_ids = best.get("age_ratings", [])
        placeholder_age = {"rating": None, "min_age": None, "family_friendly": None, "kid_safe": None}
        entry = extract_data(best, placeholder_age)
        entry["match_confidence"] = confidence
        cache[game_id] = entry
        fetched += 1

        if ar_ids:
            all_age_rating_ids.update(ar_ids)
            games_needing_age_ratings[game_id] = ar_ids

        if confidence == "uncertain":
            uncertain.append(f"  UNCERTAIN: {name} -> {best.get('name', '?')} (score={best_score:.2f})")

        time.sleep(0.3)
        if fetched % 10 == 0:
            save_cache(cache)
            print(f"    ({fetched} fetched, saving checkpoint...)")

    save_cache(cache)
    print(f"\nPass 1 done: {fetched} fetched, {skipped} cached")

    # === Pass 2: Batch-resolve age ratings ===
    if all_age_rating_ids:
        print(f"\nIGDB Pass 2: Resolving {len(all_age_rating_ids)} age ratings...")
        resolved = resolve_age_ratings(all_age_rating_ids, client_id, token)
        print(f"  Resolved {len(resolved)} age rating entries")

        age_count = 0
        for game_id, ar_ids in games_needing_age_ratings.items():
            if game_id in cache:
                age_info = process_age_ratings(ar_ids, resolved)
                cache[game_id]["esrb_rating"] = age_info["rating"]
                cache[game_id]["min_age"] = age_info["min_age"]
                cache[game_id]["family_friendly"] = age_info["family_friendly"]
                cache[game_id]["kid_safe"] = age_info["kid_safe"]
                cache[game_id]["pegi_age"] = age_info.get("pegi_age")
                cache[game_id]["content_descriptors"] = age_info.get("content_descriptors", [])
                cache[game_id]["age_synopsis"] = age_info.get("age_synopsis")
                if age_info["rating"]:
                    age_count += 1

        save_cache(cache)
        print(f"  {age_count} games now have ESRB ratings")
    else:
        print("\nNo age ratings to resolve")

    print(f"\nIGDB done! {fetched} fetched, {skipped} cached")
    if uncertain:
        print(f"\n{len(uncertain)} games need review:")
        for line in uncertain:
            print(line)


if __name__ == "__main__":
    main()
