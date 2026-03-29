#!/usr/bin/env python3
"""Merge RAWG and IGDB caches with scanned game data into final games.json.

Priority logic:
- Metacritic score: RAWG (they're the Metacritic aggregator)
- ESRB / age ratings: prefer IGDB (more structured), fallback to RAWG
- Content descriptors: IGDB only (RAWG doesn't have these)
- Cover image: prefer RAWG (higher quality), fallback to IGDB
- Description: prefer longer description from either source
- Genres: merge from both, deduplicate
- User rating: include both (RAWG 0-5 scale, IGDB 0-100 scale)
- Release date: prefer IGDB (more reliable), fallback to RAWG
- Platforms: merge from both, deduplicate
- Tags/themes: merge from both
- Developer/publisher: IGDB only
"""

import json
import os
import sys
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(__file__)
SCANNED_FILE = os.path.join(SCRIPT_DIR, "scanned_games.json")
RAWG_CACHE = os.path.join(SCRIPT_DIR, "cache", "rawg_cache.json")
IGDB_CACHE = os.path.join(SCRIPT_DIR, "cache", "igdb_cache.json")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "..", "public", "data", "games.json")


def load_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {} if path.endswith("_cache.json") else []


def merge_game(game, rawg, igdb):
    """Merge scanned game data with RAWG and IGDB cache entries."""
    has_rawg = rawg and rawg.get("source_id") is not None
    has_igdb = igdb and igdb.get("source_id") is not None

    # --- Metacritic: RAWG is the authority ---
    metacritic = rawg.get("metacritic") if has_rawg else None

    # --- ESRB / age rating: prefer IGDB, fallback to RAWG ---
    esrb_rating = None
    min_age = None
    family_friendly = None
    kid_safe = None

    if has_igdb and igdb.get("esrb_rating"):
        esrb_rating = igdb["esrb_rating"]
        min_age = igdb.get("min_age")
        family_friendly = igdb.get("family_friendly")
        kid_safe = igdb.get("kid_safe")
    elif has_rawg and rawg.get("esrb_rating"):
        esrb_rating = rawg["esrb_rating"]
        min_age = rawg.get("min_age")
        family_friendly = rawg.get("family_friendly")
        kid_safe = rawg.get("kid_safe")

    # --- Content descriptors: IGDB only ---
    content_descriptors = igdb.get("content_descriptors", []) if has_igdb else []

    # --- PEGI: IGDB only ---
    pegi_age = igdb.get("pegi_age") if has_igdb else None

    # --- Cover image: prefer RAWG (bigger/better), fallback to IGDB ---
    background_image = None
    if has_rawg and rawg.get("background_image"):
        background_image = rawg["background_image"]
    elif has_igdb and igdb.get("cover_url"):
        background_image = igdb["cover_url"]

    # --- Description: prefer longer ---
    rawg_desc = rawg.get("description", "") if has_rawg else ""
    igdb_desc = igdb.get("description", "") if has_igdb else ""
    description = rawg_desc if len(rawg_desc) >= len(igdb_desc) else igdb_desc

    # --- Release date: prefer IGDB, fallback to RAWG ---
    released = None
    if has_igdb and igdb.get("released"):
        released = igdb["released"]
    elif has_rawg and rawg.get("released"):
        released = rawg["released"]

    # --- Genres: merge and deduplicate ---
    genres = list(dict.fromkeys(
        (rawg.get("genres", []) if has_rawg else []) +
        (igdb.get("genres", []) if has_igdb else [])
    ))

    # --- Platforms: merge and deduplicate ---
    platforms = list(dict.fromkeys(
        (rawg.get("platforms", []) if has_rawg else []) +
        (igdb.get("platforms", []) if has_igdb else [])
    ))

    # --- Tags + themes: merge ---
    tags = list(dict.fromkeys(
        (rawg.get("tags", []) if has_rawg else []) +
        (igdb.get("themes", []) if has_igdb else [])
    ))

    # --- Ratings from both sources ---
    rawg_rating = rawg.get("user_rating") if has_rawg else None
    rawg_ratings_count = rawg.get("ratings_count", 0) if has_rawg else 0
    igdb_rating = igdb.get("igdb_rating") if has_igdb else None
    igdb_rating_count = igdb.get("igdb_rating_count", 0) if has_igdb else 0
    aggregated_rating = igdb.get("aggregated_rating") if has_igdb else None

    # --- Developer / publisher: IGDB only ---
    developers = igdb.get("developers", []) if has_igdb else []
    publishers = igdb.get("publishers", []) if has_igdb else []

    # --- Source provenance tracking ---
    sources = {}
    if has_rawg:
        sources["rawg"] = {
            "id": rawg["source_id"],
            "name": rawg.get("source_name", ""),
            "match_confidence": rawg.get("match_confidence", "unknown"),
            "fetched_at": rawg.get("fetched_at", ""),
        }
    if has_igdb:
        sources["igdb"] = {
            "id": igdb["source_id"],
            "name": igdb.get("source_name", ""),
            "match_confidence": igdb.get("match_confidence", "unknown"),
            "fetched_at": igdb.get("fetched_at", ""),
        }

    # Determine overall match quality
    rawg_conf = rawg.get("match_confidence", "none") if has_rawg else "none"
    igdb_conf = igdb.get("match_confidence", "none") if has_igdb else "none"
    if rawg_conf == "confident" or igdb_conf == "confident":
        overall_match = "confident"
    elif rawg_conf == "uncertain" or igdb_conf == "uncertain":
        overall_match = "uncertain"
    else:
        overall_match = "none"

    return {
        # Core identity (from scan)
        "id": game["id"],
        "name": game["name"],
        "folder_name": game["folder_name"],
        "paths": game["paths"],
        "in_sunshine": game["in_sunshine"],
        # Merged data
        "metacritic": metacritic,
        "esrb_rating": esrb_rating,
        "min_age": min_age,
        "family_friendly": family_friendly,
        "kid_safe": kid_safe,
        "content_descriptors": content_descriptors,
        "pegi_age": pegi_age,
        "background_image": background_image,
        "description": description,
        "released": released,
        "genres": genres,
        "platforms": platforms,
        "tags": tags,
        "developers": developers,
        "publishers": publishers,
        # Ratings from each source
        "rawg_rating": rawg_rating,
        "rawg_ratings_count": rawg_ratings_count,
        "igdb_rating": igdb_rating,
        "igdb_rating_count": igdb_rating_count,
        "aggregated_rating": aggregated_rating,
        # Provenance
        "sources": sources,
        "match_quality": overall_match,
        "merged_at": datetime.now(timezone.utc).isoformat(),
    }


def main():
    if not os.path.exists(SCANNED_FILE):
        print("ERROR: Run scan_games.py first")
        sys.exit(1)

    scanned = load_json(SCANNED_FILE)
    rawg_cache = load_json(RAWG_CACHE)
    igdb_cache = load_json(IGDB_CACHE)

    print(f"Merging: {len(scanned)} games, "
          f"{len(rawg_cache)} RAWG entries, "
          f"{len(igdb_cache)} IGDB entries")

    results = []
    stats = {"both": 0, "rawg_only": 0, "igdb_only": 0, "neither": 0, "uncertain": 0}

    for game in scanned:
        gid = game["id"]
        rawg = rawg_cache.get(gid, {})
        igdb = igdb_cache.get(gid, {})

        has_rawg = rawg.get("source_id") is not None
        has_igdb = igdb.get("source_id") is not None

        if has_rawg and has_igdb:
            stats["both"] += 1
        elif has_rawg:
            stats["rawg_only"] += 1
        elif has_igdb:
            stats["igdb_only"] += 1
        else:
            stats["neither"] += 1

        merged = merge_game(game, rawg, igdb)
        results.append(merged)

        if merged["match_quality"] == "uncertain":
            stats["uncertain"] += 1

    results.sort(key=lambda g: g["name"].lower())

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nMerge complete! {len(results)} games written to {OUTPUT_FILE}")
    print(f"  Both sources:  {stats['both']}")
    print(f"  RAWG only:     {stats['rawg_only']}")
    print(f"  IGDB only:     {stats['igdb_only']}")
    print(f"  No data:       {stats['neither']}")
    print(f"  Uncertain:     {stats['uncertain']}")

    if stats["neither"] > 0:
        print("\nGames with no data from either source:")
        for game in results:
            if not game["sources"]:
                print(f"  {game['name']} (folder: {game['folder_name']})")


if __name__ == "__main__":
    main()
