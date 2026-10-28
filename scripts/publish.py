"""Mirrors unpublished releases to this repository's GitHub Releases and rebuilds index.json.

Runs on pushes to main. For each release in plugin.json that is not in the
plugin's published.json, the file is taken from `upload` (then removed from
the tree) or downloaded from `source`, checked, and attached to a GitHub
Release tagged <id>-v<version>. Published versions are never re-mirrored.

Requires the gh CLI with GH_TOKEN and GITHUB_REPOSITORY set.

Usage: python scripts/publish.py
"""

import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import build_index
from storelib import (ROOT, StoreError, asset_name, check_plugin, fetch_release, inspect_release, load_json,
                      load_published, plugin_dirs, release_tag, write_json)


def gh(*args):
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout


def existing_assets(repo, tag):
    try:
        return {asset["name"] for asset in json.loads(gh("release", "view", tag, "--repo", repo, "--json", "assets"))["assets"]}
    except subprocess.CalledProcessError:
        return None


def mirror(repo, plugin, entry, data):
    tag = release_tag(plugin["id"], entry["version"])
    name = asset_name(plugin["id"], entry["version"])
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / name
        path.write_bytes(data)
        assets = existing_assets(repo, tag)
        if assets is None:
            notes = Path(tmp) / "notes.md"
            notes.write_text(entry.get("changelog") or f"{plugin['name']} {entry['version']}", encoding="utf-8")
            gh("release", "create", tag, str(path), "--repo", repo, "--title", f"{plugin['name']} {entry['version']}",
               "--notes-file", str(notes), "--latest=false")
        elif name not in assets:
            gh("release", "upload", tag, str(path), "--repo", repo)
    return f"https://github.com/{repo}/releases/download/{tag}/{name}"


def main():
    repo = os.environ["GITHUB_REPOSITORY"]
    repository = load_json(ROOT / "repository.json")
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    count = 0
    for plugin_dir in plugin_dirs():
        plugin = check_plugin(plugin_dir, repository)
        published = load_published(plugin_dir)
        for entry in plugin["releases"]:
            if entry["version"] in published:
                continue
            data = fetch_release(plugin_dir, entry)
            record = inspect_release(plugin["id"], entry, data)
            record["url"] = mirror(repo, plugin, entry, data)
            record["origin"] = entry.get("source")
            record["publishedAt"] = now
            published[entry["version"]] = record
            write_json(plugin_dir / "published.json", dict(sorted(published.items())))
            if "upload" in entry:
                (plugin_dir / entry["upload"]).unlink()
            count += 1
            print(f"published: {plugin['id']} {entry['version']} -> {record['url']}")
    build_index.main()
    print(f"{count} release(s) published")


if __name__ == "__main__":
    try:
        main()
    except (StoreError, subprocess.CalledProcessError) as e:
        detail = getattr(e, "stderr", "") or ""
        print(f"error: {e} {detail}".strip(), file=sys.stderr)
        sys.exit(1)
