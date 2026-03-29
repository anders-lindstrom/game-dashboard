---
name: fix-igdb-matches
description: Analyze and fix IGDB game matches - find unmatched/uncertain games, search IGDB using multiple strategies, and update overrides
user_invocable: true
---

# Fix IGDB Game Matches

You are analyzing the game dashboard's IGDB data quality and fixing any bad or missing matches.

## Context

- Project: `C:\Games\game-dashboard`
- IGDB cache: `scripts/cache/igdb_cache.json`
- IGDB ID overrides: `scripts/igdb_overrides.json` (game_id -> IGDB numeric ID)
- Name overrides: `scripts/overrides.json` (folder_name -> display name)
- Scanned games: `scripts/scanned_games.json`
- Twitch credentials: `scripts/.env` (TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET)
- Final output: `public/data/games.json`

## Steps

### 1. Identify problems

Read `scripts/cache/igdb_cache.json` and find:
- Games with `"source_id": null` (no match at all)
- Games with `"match_confidence": "uncertain"` (weak match)
- Games where `source_name` looks wrong compared to the game's actual name

Report a summary of all issues found.

### 2. Search IGDB with multiple strategies

For each problematic game, search IGDB using the Twitch API with multiple strategies. First get a token:

```python
import requests
env = {}
with open('C:/Games/game-dashboard/scripts/.env') as f:
    for line in f:
        if '=' in line:
            k, v = line.strip().split('=', 1)
            env[k] = v
resp = requests.post('https://id.twitch.tv/oauth2/token', params={
    'client_id': env['TWITCH_CLIENT_ID'],
    'client_secret': env['TWITCH_CLIENT_SECRET'],
    'grant_type': 'client_credentials',
})
token = resp.json()['access_token']
headers = {'Client-ID': env['TWITCH_CLIENT_ID'], 'Authorization': f'Bearer {token}'}
```

Then for each game, try these search strategies in order until a good match is found:

1. **Exact name search**: `search "Game Name"; fields name,id,genres.name,summary; limit 5;`
2. **Partial name** (drop subtitles): search with just the main title before any colon/dash
3. **Key words**: pick the most distinctive 1-2 words and search those
4. **Where clause**: `fields name,id; where name ~ *"keyword"*; limit 10;` (fuzzy match)
5. **Use your knowledge**: You know what these games are. If the folder is "BlackMythWukong", you know it's "Black Myth: Wukong". Use your knowledge of gaming to determine the correct game and search for it accordingly.

The IGDB API endpoint is: `POST https://api.igdb.com/v4/games`
- Send the query as the request body (plain text, not JSON)
- Fields must be comma-separated on a single line (no newlines in the fields list)
- Do NOT use `where category = 0` - it breaks results

### 3. Verify matches

For each candidate match:
- Check the game description/summary makes sense for the game we're looking for
- Check genres are plausible
- Check release date is reasonable
- Prefer the base game over DLC, deluxe editions, or platform-specific variants (like Apple Arcade "+" versions)
- If a game has both a regular and "Deluxe/Complete/GOTY" edition, prefer the regular one

### 4. Apply fixes

For confirmed matches, update these files:

**`scripts/igdb_overrides.json`** - Add entries mapping game_id to IGDB numeric ID:
```json
{
    "game-id-slug": 12345
}
```

**`scripts/overrides.json`** - If the folder name doesn't normalize well, add a name mapping:
```json
{
    "FolderName": "Correct Game Title"
}
```

### 5. Re-fetch and rebuild

After updating overrides, run:
```bash
cd C:\Games\game-dashboard

# Clear fixed entries from cache
python -c "
import json
fixed_ids = ['game-id-1', 'game-id-2']  # IDs you fixed
with open('scripts/cache/igdb_cache.json', encoding='utf-8') as f:
    cache = json.load(f)
for gid in fixed_ids:
    if gid in cache: del cache[gid]
with open('scripts/cache/igdb_cache.json', 'w', encoding='utf-8') as f:
    json.dump(cache, f, indent=2, ensure_ascii=False)
"

# Re-scan (in case name overrides changed), re-fetch, merge
python scripts/scan_games.py
python scripts/fetch_igdb.py
python scripts/merge_sources.py
```

### 6. Report results

Show a summary:
- How many games were fixed
- Any remaining unmatched games
- Final data quality stats (run the stats check below)

```bash
python -c "
import json
with open('public/data/games.json', encoding='utf-8') as f:
    games = json.load(f)
from collections import Counter
esrb = Counter(g.get('esrb_rating') or 'Unrated' for g in games)
print(f'Total: {len(games)}')
print(f'IGDB data:   {sum(1 for g in games if g.get(\"sources\",{}).get(\"igdb\"))}')
print(f'ESRB rated:  {sum(1 for g in games if g.get(\"esrb_rating\"))}')
print(f'Cover art:   {sum(1 for g in games if g.get(\"background_image\"))}')
print(f'ESRB breakdown: {dict(esrb)}')
print(f'Uncertain:   {sum(1 for g in games if g.get(\"match_quality\")==\"uncertain\")}')
print(f'No data:     {sum(1 for g in games if not g.get(\"sources\"))}')
"
```
