"""Validates every plugin and the release files that are not published yet.

Runs on pull requests. Nothing is uploaded or written.

Usage: python scripts/validate.py
"""

import sys

import build_index
from storelib import ROOT, StoreError, check_plugin, fetch_release, inspect_release, load_json, load_published, plugin_dirs


def main():
    repository = load_json(ROOT / "repository.json")
    errors = []
    pending = 0
    for plugin_dir in plugin_dirs():
        try:
            source = check_plugin(plugin_dir, repository)
            published = load_published(plugin_dir)
            for entry in source["releases"]:
                if entry["version"] in published:
                    continue
                inspect_release(source["id"], entry, fetch_release(plugin_dir, entry))
                pending += 1
                print(f"ok: {source['id']} {entry['version']} (will be published)")
        except StoreError as e:
            errors.append(str(e))

    if not errors:
        try:
            build_index.main(check=True)
        except StoreError as e:
            errors.append(str(e))

    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if errors:
        sys.exit(1)
    print(f"valid: {pending} release(s) waiting to be published")


if __name__ == "__main__":
    main()
