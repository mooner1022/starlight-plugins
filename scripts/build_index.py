"""Builds index.json from repository.json and plugins/<id>/plugin.json.

Release metadata (version, PluginCore API, dependencies, native library use)
is read from assets/starlight.json inside each .slp file, and the file size
and SHA-256 are computed from the file itself, so they always match what the
app downloads.

Usage: python scripts/build_index.py
"""

import hashlib
import json
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGINS = ROOT / "plugins"
SCHEMA_VERSION = 1


class BuildError(Exception):
    pass


def fail(message):
    raise BuildError(message)


def version_key(version):
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)", version)
    if not match:
        fail(f"invalid version: {version}")
    return tuple(int(part) for part in match.groups())


def read_manifest(slp):
    try:
        with zipfile.ZipFile(slp) as archive:
            return json.loads(archive.read("assets/starlight.json"))
    except (zipfile.BadZipFile, KeyError, json.JSONDecodeError) as e:
        fail(f"{slp.relative_to(ROOT)}: cannot read assets/starlight.json ({e})")


def sha256_of(path):
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative(path):
    return path.relative_to(ROOT).as_posix()


def build_release(plugin_id, plugin_dir, entry):
    slp = plugin_dir / entry["file"]
    if not slp.is_file():
        fail(f"{plugin_id}: missing release file {entry['file']}")
    manifest = read_manifest(slp)
    if manifest.get("id") != plugin_id:
        fail(f"{relative(slp)}: id is {manifest.get('id')!r}, expected {plugin_id!r}")
    return {
        "version": manifest["version"],
        "apiVersion": manifest["api_version"],
        "releasedAt": entry["releasedAt"],
        "changelog": entry.get("changelog", ""),
        "file": relative(slp),
        "size": slp.stat().st_size,
        "sha256": sha256_of(slp),
        "dependency": manifest.get("dependency", []),
        "nativeLibrary": manifest.get("uses_native_lib", False),
    }, manifest


def build_plugin(plugin_dir, repository):
    source = json.loads((plugin_dir / "plugin.json").read_text(encoding="utf-8"))
    plugin_id = source["id"]
    if plugin_dir.name != plugin_id:
        fail(f"plugins/{plugin_dir.name}: directory name must match id {plugin_id!r}")

    categories = {category["id"] for category in repository["categories"]}
    if source["category"] not in categories:
        fail(f"{plugin_id}: unknown category {source['category']!r}")

    built = [build_release(plugin_id, plugin_dir, entry) for entry in source["releases"]]
    if not built:
        fail(f"{plugin_id}: no releases")
    built.sort(key=lambda pair: version_key(pair[0]["version"]), reverse=True)
    versions = [release["version"] for release, _ in built]
    if len(set(versions)) != len(versions):
        fail(f"{plugin_id}: duplicate release versions")
    latest_manifest = built[0][1]

    verified = set(repository.get("verifiedAuthors", []))
    readme = plugin_dir / "README.md"
    icon = plugin_dir / "icon.png"

    screenshots = []
    for shot in source.get("screenshots", []):
        image = plugin_dir / shot["file"]
        if not image.is_file():
            fail(f"{plugin_id}: missing screenshot {shot['file']}")
        screenshots.append({"image": relative(image), "caption": shot.get("caption", "")})

    return {
        "id": plugin_id,
        "name": source.get("name") or latest_manifest["name"],
        "summary": source["summary"],
        "description": readme.read_text(encoding="utf-8").strip() if readme.is_file() else "",
        "authors": [
            {"name": author["name"], "url": author.get("url"), "verified": author["name"] in verified}
            for author in source["authors"]
        ],
        "category": source["category"],
        "tags": source.get("tags", []),
        "icon": relative(icon) if icon.is_file() else None,
        "screenshots": screenshots,
        "license": source.get("license"),
        "source": source.get("source"),
        "publishedAt": source["publishedAt"],
        "releases": [release for release, _ in built],
    }


def main():
    repository = json.loads((ROOT / "repository.json").read_text(encoding="utf-8"))
    plugins = [
        build_plugin(plugin_dir, repository)
        for plugin_dir in sorted(PLUGINS.iterdir())
        if (plugin_dir / "plugin.json").is_file()
    ]

    ids = {plugin["id"] for plugin in plugins}
    for feature in repository.get("featured", []):
        if feature["plugin"] not in ids:
            fail(f"featured plugin {feature['plugin']!r} does not exist")

    index = {
        "schemaVersion": SCHEMA_VERSION,
        "name": repository["name"],
        "description": repository.get("description"),
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "categories": repository["categories"],
        "featured": repository.get("featured", []),
        "plugins": plugins,
    }
    (ROOT / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"index.json: {len(plugins)} plugins")


if __name__ == "__main__":
    try:
        main()
    except BuildError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
