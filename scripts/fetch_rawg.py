#!/usr/bin/env python3
"""Fetch game data from RAWG API and write to cache/rawg_cache.json."""

import json
import os
import re
import sys
import time
from datetime import datetime, timezone

import requests

SCRIPT_DIR = os.path.dirname(__file__)
SCANNED_FILE = os.path.join(SCRIPT_DIR, "scanned_games.json")
CACHE_FILE = os.path.join(SCRIPT_DIR, "cache", "rawg_cache.json")
RAWG_BASE = "https://api.rawg.io/api"

ESRB_AGE_MAP = {
    "Everyone": {"rating": "E", "min_age": 6, "family_friendly": True, "kid_safe": True},
    "Everyone 10+": {"rating": "E10", "min_age": 10, "family_friendly": True, "kid_safe": True},
    "Teen": {"rating": "T", "min_age": 13, "family_friendly": True, "kid_safe": False},
    "Mature": {"rating": "M", "min_age": 17, "family_friendly": False, "kid_safe": False},
    "Adults Only": {"rating": "AO", "min_age": 18, "family_friendly": False, "kid_safe": False},
}


def get_api_key():
    key = os.environ.get("RAWG_API_KEY", "")
    if not key:
        env_file = os.path.join(SCRIPT_DIR, ".env")
        if os.path.exists(env_file):
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("RAWG_API_KEY="):
                        key = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not key:
        print("ERROR: Set RAWG_API_KEY environment variable or add to scripts/.env")
        sys.exit(1)
    return key


def match_score(query, candidate):
    """Simple token-overlap matching score."""
    q_tokens = set(re.findall(r"\w+", query.lower()))
    c_tokens = set(re.findall(r"\w+", candidate.lower()))
    if not q_tokens:
        return 0
    overlap = q_tokens & c_tokens
    return len(overlap) / max(len(q_tokens), len(c_tokens))


def search_game(name, api_key):
    """Search RAWG for a game by name."""
    search_name = re.sub(r"[:\-,]", " ", name)
    search_name = re.sub(r"\s+", " ", search_name).strip()

    params = {"key": api_key, "search": search_name, "page_size": 5, "search_precise": True}
    try:
        resp = requests.get(f"{RAWG_BASE}/games", params=params, timeout=15)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if not results:
            params.pop("search_precise")
            resp = requests.get(f"{RAWG_BASE}/games", params=params, timeout=15)
            resp.raise_for_status()
            results = resp.json().get("results", [])
        return results
    except requests.RequestException as e:
        print(f"    Search error for '{name}': {e}")
        return []


def fetch_game_details(game_id, api_key):
    """Fetch full game details from RAWG."""
    try:
        resp = requests.get(f"{RAWG_BASE}/games/{game_id}", params={"key": api_key}, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        print(f"    Details error for ID {game_id}: {e}")
        return None


def extract_data(search_result, details):
    """Extract fields from RAWG response into our cache format."""
    src = details or search_result
    esrb = (details or {}).get("esrb_rating")
    esrb_name = esrb.get("name") if esrb else None
    age_info = ESRB_AGE_MAP.get(esrb_name, {
        "rating": None, "min_age": None, "family_friendly": None, "kid_safe": None,
    })

    genres = [g["name"] for g in src.get("genres", [])]
    platforms = [p["platform"]["name"] for p in src.get("platforms", []) if p.get("platform", {}).get("name")]
    tags = [t["name"] for t in (details or {}).get("tags", [])[:10] if t.get("language") == "eng"]

    description = ""
    if details and details.get("description_raw"):
        desc = details["description_raw"]
        description = desc[:297] + "..." if len(desc) > 300 else desc

    return {
        "source": "rawg",
        "source_id": search_result["id"],
        "source_name": search_result.get("name", ""),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "metacritic": src.get("metacritic"),
        "user_rating": src.get("rating"),
        "ratings_count": src.get("ratings_count", 0),
        "esrb_rating": age_info["rating"],
        "esrb_name": esrb_name,
        "min_age": age_info["min_age"],
        "family_friendly": age_info["family_friendly"],
        "kid_safe": age_info["kid_safe"],
        "genres": genres,
        "released": src.get("released"),
        "background_image": src.get("background_image"),
        "description": description,
        "platforms": platforms,
        "tags": tags,
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
    api_key = get_api_key()

    if not os.path.exists(SCANNED_FILE):
        print("ERROR: Run scan_games.py first to generate scanned_games.json")
        sys.exit(1)

    with open(SCANNED_FILE, "r", encoding="utf-8") as f:
        scanned = json.load(f)

    cache = load_cache()
    fetched = 0
    skipped = 0
    uncertain = []

    print(f"RAWG: Processing {len(scanned)} games...")

    for i, game in enumerate(scanned):
        game_id = game["id"]

        # Skip if cached (unless --force)
        if not force and game_id in cache and cache[game_id].get("source_id"):
            skipped += 1
            continue

        name = game["name"]
        print(f"  [{i+1}/{len(scanned)}] {name}")

        results = search_game(name, api_key)
        if not results:
            print(f"    No results")
            cache[game_id] = {
                "source": "rawg",
                "source_id": None,
                "match_confidence": "none",
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }
            uncertain.append(f"  NO MATCH: {name} (folder: {game['folder_name']})")
            time.sleep(0.25)
            continue

        # Pick best match
        best = None
        best_score = 0
        for r in results:
            score = match_score(name, r.get("name", ""))
            if score > best_score:
                best_score = score
                best = r

        confidence = "confident" if best_score >= 0.5 else "uncertain"

        details = fetch_game_details(best["id"], api_key)
        time.sleep(0.25)

        entry = extract_data(best, details)
        entry["match_confidence"] = confidence
        cache[game_id] = entry
        fetched += 1

        if confidence == "uncertain":
            uncertain.append(f"  UNCERTAIN: {name} -> {best.get('name', '?')} (score={best_score:.2f})")

        if fetched % 10 == 0:
            save_cache(cache)  # Periodic save
            print(f"    ({fetched} fetched, saving checkpoint...)")

    save_cache(cache)
    print(f"\nRAWG done! {fetched} fetched, {skipped} cached")

    if uncertain:
        print(f"\n{len(uncertain)} games need review:")
        for line in uncertain:
            print(line)
        print("\nAdd corrections to scripts/overrides.json and re-run.")


if __name__ == "__main__":
    main()
