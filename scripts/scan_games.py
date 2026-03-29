#!/usr/bin/env python3
"""Scan game directories across multiple drives and produce a normalized game list."""

import json
import os
import re
import sys
from pathlib import Path

GAME_DIRS = [
    r"C:\Games",
    r"D:\Games",
    r"E:\Games",
    r"F:\Games",
]

SKIP_ENTRIES = {
    "_older", "switch", "GameSave", "game-dashboard",
    "migrate_saves.sh", "sunshine_apps_updated.json", "steam_emu.ini",
    ".claude", ".git", ".vscode",
}

SUNSHINE_CONFIG = r"C:\Program Files\Sunshine\config\apps.json"
OVERRIDES_FILE = os.path.join(os.path.dirname(__file__), "overrides.json")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "scanned_games.json")


def load_overrides():
    if os.path.exists(OVERRIDES_FILE):
        with open(OVERRIDES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def load_sunshine_games():
    """Load Sunshine app names and their command paths."""
    sunshine_games = {}
    if os.path.exists(SUNSHINE_CONFIG):
        with open(SUNSHINE_CONFIG, "r", encoding="utf-8") as f:
            data = json.load(f)
        for app in data.get("apps", []):
            name = app.get("name", "")
            cmd = app.get("cmd", "")
            if name and name not in ("Desktop", "Steam Big Picture"):
                sunshine_games[name.lower()] = cmd
    return sunshine_games


def normalize_name(folder_name, overrides):
    """Normalize a folder name to a game title."""
    if folder_name in overrides:
        return overrides[folder_name]

    name = folder_name

    # Replace dots with spaces
    name = name.replace(".", " ")

    # Strip REPACK/scene group tags
    name = re.sub(r"\s*[-_]?\s*(?:REPACK|KaOs|CODEX|PLAZA|GOG|FLT|DODI).*$", "", name, flags=re.IGNORECASE)

    # Strip version patterns: v1.2.3, v1.0.01a, (2025)
    name = re.sub(r"\s+v\d+[\d.a-zA-Z]*\s*$", "", name)
    name = re.sub(r"\s*\(\d{4}\)\s*$", "", name)

    # CamelCase splitting: insert space before uppercase after lowercase
    name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
    # Also before a digit sequence followed by uppercase
    name = re.sub(r"(\d)([A-Z][a-z])", r"\1 \2", name)

    # Clean up
    name = re.sub(r"\s+", " ", name).strip()

    return name


def make_id(name):
    """Create a URL-friendly ID from a game name."""
    slug = name.lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug).strip("-")
    return slug


def check_sunshine(normalized_name, game_path, sunshine_games):
    """Check if a game is in the Sunshine config."""
    name_lower = normalized_name.lower()
    # Direct name match
    if name_lower in sunshine_games:
        return True
    # Check if the game path appears in any Sunshine command
    path_normalized = game_path.replace("/", "\\").lower()
    for cmd in sunshine_games.values():
        if path_normalized in cmd.lower():
            return True
    return False


def scan_all_drives():
    overrides = load_overrides()
    sunshine_games = load_sunshine_games()
    games_by_id = {}

    for game_dir in GAME_DIRS:
        if not os.path.isdir(game_dir):
            print(f"  Skipping {game_dir} (not found)")
            continue

        drive = game_dir[0].upper()
        print(f"  Scanning {game_dir}...")

        for entry in os.listdir(game_dir):
            full_path = os.path.join(game_dir, entry)
            if not os.path.isdir(full_path):
                continue
            if entry in SKIP_ENTRIES:
                continue

            normalized = normalize_name(entry, overrides)
            game_id = make_id(normalized)

            in_sunshine = check_sunshine(normalized, full_path, sunshine_games)

            if game_id in games_by_id:
                # Deduplicate: add path to existing entry
                existing_paths = [p["path"] for p in games_by_id[game_id]["paths"]]
                if full_path not in existing_paths:
                    games_by_id[game_id]["paths"].append({
                        "drive": drive,
                        "path": full_path,
                    })
                if in_sunshine:
                    games_by_id[game_id]["in_sunshine"] = True
            else:
                games_by_id[game_id] = {
                    "id": game_id,
                    "folder_name": entry,
                    "name": normalized,
                    "paths": [{"drive": drive, "path": full_path}],
                    "in_sunshine": in_sunshine,
                }

    games = sorted(games_by_id.values(), key=lambda g: g["name"].lower())
    print(f"\n  Found {len(games)} unique games")

    sunshine_count = sum(1 for g in games if g["in_sunshine"])
    print(f"  {sunshine_count} games flagged as Sunshine-configured")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(games, f, indent=2, ensure_ascii=False)

    print(f"  Written to {OUTPUT_FILE}")
    return games


if __name__ == "__main__":
    print("Scanning game directories...")
    games = scan_all_drives()
