"""Builds index.json from repository.json, plugin.json and published.json.

Only releases already recorded in published.json (mirrored by CI) are listed,
so this script never needs the plugin files themselves.

Usage: python scripts/build_index.py [--check]
  --check  validate and print the result without writing index.json
"""

import json
import sys
from datetime import datetime, timezone

from storelib import ROOT, StoreError, check_plugin, load_json, load_published, plugin_dirs, version_key, write_json

SCHEMA_VERSION = 1


def build_plugin(plugin_dir, repository):
    source = check_plugin(plugin_dir, repository)
    published = load_published(plugin_dir)
    releases = []
    for entry in source["releases"]:
        record = published.get(entry["version"])
        if record is None:
            continue
        releases.append({
            "version": entry["version"],
            "apiVersion": record["apiVersion"],
            "releasedAt": entry["releasedAt"],
            "changelog": entry.get("changelog", ""),
            "url": record["url"],
            "size": record["size"],
            "sha256": record["sha256"],
            "dependency": record["dependency"],
            "nativeLibrary": record["nativeLibrary"],
        })
    if not releases:
        return None
    releases.sort(key=lambda release: version_key(release["version"]), reverse=True)

    verified = set(repository.get("verifiedAuthors", []))
    readme = plugin_dir / "README.md"
    icon = plugin_dir / "icon.png"
    return {
        "id": source["id"],
        "name": source["name"],
        "summary": source["summary"],
        "description": readme.read_text(encoding="utf-8").strip() if readme.is_file() else "",
        "authors": [
            {"name": author["name"], "url": author.get("url"), "verified": author["name"] in verified}
            for author in source["authors"]
        ],
        "category": source["category"],
        "tags": source.get("tags", []),
        "icon": icon.relative_to(ROOT).as_posix() if icon.is_file() else None,
        "screenshots": [
            {"image": (plugin_dir / shot["file"]).relative_to(ROOT).as_posix(), "caption": shot.get("caption", "")}
            for shot in source.get("screenshots", [])
        ],
        "license": source.get("license"),
        "source": source.get("source"),
        "publishedAt": source["publishedAt"],
        "releases": releases,
    }


def build():
    repository = load_json(ROOT / "repository.json")
    plugins = [plugin for plugin in (build_plugin(path, repository) for path in plugin_dirs()) if plugin]
    ids = {plugin["id"] for plugin in plugins}
    featured = [feature for feature in repository.get("featured", []) if feature["plugin"] in ids]
    return {
        "schemaVersion": SCHEMA_VERSION,
        "name": repository["name"],
        "description": repository.get("description"),
        "categories": repository["categories"],
        "featured": featured,
        "plugins": plugins,
    }


def main(check=False):
    index = build()
    path = ROOT / "index.json"
    previous = load_json(path) if path.is_file() else {}
    generated_at = previous.pop("generatedAt", None)
    if previous == index and generated_at:
        print(f"index.json: unchanged, {len(index['plugins'])} plugins")
        return
    if check:
        print(f"index.json: would list {len(index['plugins'])} plugins")
        return
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    ordered = {key: index[key] for key in ("schemaVersion", "name", "description")}
    ordered["generatedAt"] = stamp
    ordered.update((key, index[key]) for key in ("categories", "featured", "plugins"))
    write_json(path, ordered)
    print(f"index.json: {len(index['plugins'])} plugins")


if __name__ == "__main__":
    try:
        main(check="--check" in sys.argv[1:])
    except StoreError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
