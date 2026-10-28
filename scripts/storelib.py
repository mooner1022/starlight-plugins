"""Shared helpers for the repository scripts. Standard library only."""

import hashlib
import io
import json
import re
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGINS = ROOT / "plugins"

MAX_FILE_SIZE = 50 * 1024 * 1024
SOURCE_HOSTS = {"github.com", "raw.githubusercontent.com"}
VERSION = re.compile(r"^\d+\.\d+\.\d+$")
DEPENDENCY = re.compile(r"^[A-Za-z0-9_.\-]+(@\d+\.\d+\.\d+)?\??$")
REQUIRED_FIELDS = ("id", "name", "summary", "authors", "category", "publishedAt", "releases")


class StoreError(Exception):
    pass


def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise StoreError(f"{path.relative_to(ROOT)}: invalid JSON ({e})")


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def version_key(version):
    if not VERSION.match(version):
        raise StoreError(f"invalid version {version!r}, expected MAJOR.MINOR.PATCH")
    return tuple(int(part) for part in version.split("."))


def plugin_dirs():
    return sorted(path for path in PLUGINS.iterdir() if (path / "plugin.json").is_file())


def load_published(plugin_dir):
    path = plugin_dir / "published.json"
    return load_json(path) if path.is_file() else {}


def release_tag(plugin_id, version):
    return f"{plugin_id}-v{version}"


def asset_name(plugin_id, version):
    return f"{plugin_id}-{version}.slp"


def check_plugin(plugin_dir, repository):
    """Validates plugin.json and returns it. Does not look at release files."""
    source = load_json(plugin_dir / "plugin.json")
    where = f"plugins/{plugin_dir.name}"
    missing = [field for field in REQUIRED_FIELDS if field not in source]
    if missing:
        raise StoreError(f"{where}/plugin.json: missing {', '.join(missing)}")
    if source["id"] != plugin_dir.name:
        raise StoreError(f"{where}: directory name must match id {source['id']!r}")
    if source["category"] not in {category["id"] for category in repository["categories"]}:
        raise StoreError(f"{where}: unknown category {source['category']!r}")
    if not source["releases"]:
        raise StoreError(f"{where}: no releases")

    versions = set()
    for entry in source["releases"]:
        version = entry.get("version")
        if version is None:
            raise StoreError(f"{where}: every release needs a version")
        version_key(version)
        if version in versions:
            raise StoreError(f"{where}: duplicate release {version}")
        versions.add(version)
        if "releasedAt" not in entry:
            raise StoreError(f"{where}: release {version} needs releasedAt")

    for shot in source.get("screenshots", []):
        if not (plugin_dir / shot["file"]).is_file():
            raise StoreError(f"{where}: missing screenshot {shot['file']}")
    return source


def fetch_release(plugin_dir, entry):
    """Returns the bytes of an unpublished release from its upload file or source URL."""
    where = f"plugins/{plugin_dir.name} {entry['version']}"
    has_upload, has_source = "upload" in entry, "source" in entry
    if has_upload == has_source:
        raise StoreError(f"{where}: set exactly one of upload or source")

    if has_upload:
        path = (plugin_dir / entry["upload"]).resolve()
        if plugin_dir.resolve() not in path.parents:
            raise StoreError(f"{where}: upload must be inside the plugin directory")
        if not path.is_file():
            raise StoreError(f"{where}: missing upload {entry['upload']}")
        if path.stat().st_size > MAX_FILE_SIZE:
            raise StoreError(f"{where}: file is larger than {MAX_FILE_SIZE // (1024 * 1024)} MB")
        return path.read_bytes()

    url = urllib.parse.urlparse(entry["source"])
    if url.scheme != "https" or url.hostname not in SOURCE_HOSTS:
        raise StoreError(f"{where}: source must be an https URL on {', '.join(sorted(SOURCE_HOSTS))}")
    request = urllib.request.Request(entry["source"], headers={"User-Agent": "starlight-plugins-ci"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = response.read(MAX_FILE_SIZE + 1)
    except OSError as e:
        raise StoreError(f"{where}: cannot download {entry['source']} ({e})")
    if len(data) > MAX_FILE_SIZE:
        raise StoreError(f"{where}: file is larger than {MAX_FILE_SIZE // (1024 * 1024)} MB")
    return data


def inspect_release(plugin_id, entry, data):
    """Checks the manifest inside a release file and returns its index metadata."""
    where = f"plugins/{plugin_id} {entry['version']}"
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            manifest = json.loads(archive.read("assets/starlight.json"))
    except (zipfile.BadZipFile, KeyError, json.JSONDecodeError) as e:
        raise StoreError(f"{where}: cannot read assets/starlight.json ({e})")

    if manifest.get("id") != plugin_id:
        raise StoreError(f"{where}: manifest id is {manifest.get('id')!r}")
    if manifest.get("version") != entry["version"]:
        raise StoreError(f"{where}: manifest version is {manifest.get('version')!r}, plugin.json says {entry['version']!r}")
    api_version = manifest.get("api_version", "")
    if not VERSION.match(api_version):
        raise StoreError(f"{where}: invalid api_version {api_version!r}")
    dependency = manifest.get("dependency", [])
    for item in dependency:
        if not DEPENDENCY.match(item):
            raise StoreError(f"{where}: invalid dependency {item!r}")

    return {
        "apiVersion": api_version,
        "dependency": dependency,
        "nativeLibrary": bool(manifest.get("uses_native_lib", False)),
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }
