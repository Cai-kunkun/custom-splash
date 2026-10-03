#!/usr/bin/env python3
"""Download the Yarn mappings used by the pre-1.14.4 version projects.

Mojang only publishes official client mappings from 1.14.4 onwards, so the
earliest supported versions have to build against Fabric's Yarn mappings
instead.

The published Yarn v2 archives for 1.14-1.14.2 are malformed: their header
declares ``intermediary named`` while the column data is ordered ``named
intermediary``, which makes TinyRemapper reject the file as containing
duplicate mappings. This script downloads them, rewrites the columns so the
data matches the declared header, and writes the result to
``versions/<version>/mappings/yarn.tiny``.

Run it whenever a Yarn build needs to be bumped:

    python3 scripts/update_yarn_mappings.py            # every Yarn version
    python3 scripts/update_yarn_mappings.py 1.14       # a single version
"""

import io
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://maven.fabricmc.net/net/fabricmc/yarn"

# Minecraft version -> Yarn build. Only versions without Mojang mappings (1.14,
# 1.14.1 and 1.14.2) need the corrected tiny file, because 1.14.3's published
# archive is already well formed.
YARN_BUILDS = {
    "1.14": "1.14+build.21",
    "1.14.1": "1.14.1+build.10",
    "1.14.2": "1.14.2+build.7",
}


def download_tiny(yarn_version: str) -> str:
    """Fetch mappings.tiny out of the published Yarn v2 jar."""
    encoded = yarn_version.replace("+", "%2B")
    url = f"{BASE_URL}/{encoded}/yarn-{encoded}-v2.jar"
    with urllib.request.urlopen(url, timeout=60) as response:
        payload = response.read()
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        return archive.read("mappings/mappings.tiny").decode("utf-8")


def needs_column_fix(text: str) -> bool:
    """True when the declared namespaces do not match the column data."""
    lines = text.splitlines()
    # tiny <format> <minor> <namespace> [<namespace> ...]
    header = lines[0].split("\t")
    if header[:3] != ["tiny", "2", "0"] or len(header) < 5:
        raise SystemExit(f"unexpected tiny header: {lines[0]!r}")
    namespaces = header[3:]
    if namespaces != ["intermediary", "named"]:
        raise SystemExit(f"unexpected namespaces: {namespaces}")
    intermediary_first = 0
    named_first = 0
    for line in lines[1:]:
        parts = line.split("\t")
        if parts[0] != "c" or len(parts) < 3:
            continue
        if parts[1].startswith("net/minecraft/class_"):
            intermediary_first += 1
        elif parts[2].startswith("net/minecraft/class_"):
            named_first += 1
    return named_first > intermediary_first


def fix_columns(text: str) -> str:
    """Swap the two namespace columns so they match the declared header.

    Class lines start with ``c`` and carry three tab separated fields. Field
    and method lines start with an empty field followed by their kind and hold
    a descriptor before the two namespace values. Parameter lines start with
    ``p`` and carry a single namespace value, comments start with ``#``; both
    are left untouched.
    """
    output = []
    for line in text.splitlines():
        parts = line.split("\t")
        if line.startswith("c\t"):
            # parts: c, intermediary, named
            parts[1], parts[2] = parts[2], parts[1]
        elif line.startswith("\t") and len(parts) >= 5:
            # parts: '', <kind>, <descriptor>, intermediary, named
            parts[-2], parts[-1] = parts[-1], parts[-2]
        output.append("\t".join(parts))
    return "\n".join(output) + "\n"


def main() -> None:
    requested = sys.argv[1:] or list(YARN_BUILDS)
    for version in requested:
        if version not in YARN_BUILDS:
            raise SystemExit(f"unknown Yarn version: {version}")
        yarn = YARN_BUILDS[version]
        print(f"{version}: downloading yarn {yarn}")
        text = download_tiny(yarn)
        broken = needs_column_fix(text)
        if broken:
            print(f"{version}: fixing reversed intermediary/named columns")
            text = fix_columns(text)
        else:
            print(f"{version}: published archive is already well formed")
        destination = ROOT / "versions" / version / "mappings" / "yarn.tiny"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text, encoding="utf-8")
        print(f"{version}: wrote {destination}")


if __name__ == "__main__":
    main()
