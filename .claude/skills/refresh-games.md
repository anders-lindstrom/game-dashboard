---
name: refresh-games
description: Scan for new games across all drives, fetch IGDB data for new entries, merge sources, and rebuild the dashboard
user_invocable: true
---

# Refresh Game Library

Scan all game drives for new/removed games, fetch data from IGDB (and RAWG if configured), merge everything, and rebuild.

## Steps

### 1. Scan game directories

```bash
cd C:\Games\game-dashboard
python scripts/scan_games.py
```

This scans C:\Games, D:\Games, E:\Games, F:\Games and produces `scripts/scanned_games.json`.

Review the output - note how many games were found and if the count changed from before.

### 2. Check for new games needing name overrides

```bash
python -c "
import json
with open('scripts/scanned_games.json', encoding='utf-8') as f:
    scanned = json.load(f)
with open('scripts/cache/igdb_cache.json', encoding='utf-8') as f:
    cache = json.load(f)
new_games = [g for g in scanned if g['id'] not in cache]
if new_games:
    print(f'{len(new_games)} new games found:')
    for g in new_games:
        print(f'  {g[\"folder_name\"]:50s} -> {g[\"name\"]}')
else:
    print('No new games found')
"
```

For any new games with mangled folder names, add entries to `scripts/overrides.json` before fetching. Use your knowledge of gaming to determine the correct title.

### 3. Fetch from IGDB

```bash
python scripts/fetch_igdb.py
```

This is incremental - only fetches data for games not already in the cache.

If any new games show as "NO MATCH" or "UNCERTAIN", use the `/fix-igdb-matches` skill to resolve them.

### 4. Fetch from RAWG (if configured)

Only if `RAWG_API_KEY` is set in `scripts/.env`:

```bash
python scripts/fetch_rawg.py
```

### 5. Merge sources and rebuild

```bash
python scripts/merge_sources.py
npm run build
```

### 6. Report

Show what changed:
- New games added
- Games removed (if any drives are disconnected, note this but don't panic)
- Data quality stats
- Any games needing attention (uncertain matches, missing data)

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
print(f'Sunshine:    {sum(1 for g in games if g.get(\"in_sunshine\"))}')
print(f'ESRB: {dict(esrb)}')
uncertain = [g[\"name\"] for g in games if g.get(\"match_quality\")==\"uncertain\"]
nodata = [g[\"name\"] for g in games if not g.get(\"sources\")]
if uncertain: print(f'Uncertain matches: {\", \".join(uncertain)}')
if nodata: print(f'No data: {\", \".join(nodata)}')
"
```

### 7. Deploy (optional)

If the user asks to deploy:

```bash
bash scripts/deploy.sh [beelink-hostname] [/opt/game-dashboard]
```

Or just copy the data file:

```bash
scp public/data/games.json beelink:/opt/game-dashboard/public/data/
```
