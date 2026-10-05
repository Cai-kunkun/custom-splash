#!/usr/bin/env python3
"""Resolve the SRG name every Forge line's mixin has to look for.

A Forge jar below 1.20.5 ships a mixin refmap, so the whole line has to resolve
``SplashManager#getSplash`` to one SRG name. Two places know that name: the
refmap baked into a built jar (CI prints it in the ``report mixin refmap
targets`` step) and the ``mcp_config`` mappings. This reads the mappings, which
needs no build, and reports the name for the oldest and newest release of every
line in ``forge-targets.txt`` so a line can be extended with evidence.

From 1.20.5 on there is no refmap at all, so those lines are reported as exempt.

Needs network access to piston-meta.mojang.com and maven.minecraftforge.net.
Exit status is non-zero when a line's ends disagree.
"""

import json
import re
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from generate_common_sources import FORGE_TARGETS_FILE, read_targets  # noqa: E402

CACHE = ROOT / "build" / "mapcache"
UA = {"User-Agent": "customsplash-forge-line-check"}
SPLASH_MANAGER = "net.minecraft.client.resources.SplashManager"
SPLASH_RENDERER = "net.minecraft.client.gui.components.SplashRenderer"
# The mod stops generating a refmap at this release, so later lines need no check.
REFMAP_STOPS_AT = (1, 20, 5)


def key(version: str) -> tuple:
    return tuple(int(part) for part in version.split("."))


def fetch(url: str, name: str) -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    dest = CACHE / name
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    request = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(request, timeout=240) as response:
        dest.write_bytes(response.read())
    return dest


def mojang_mappings(version: str) -> Path:
    manifest = fetch(
        "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json",
        "version_manifest_v2.json",
    )
    entries = json.loads(manifest.read_text())["versions"]
    url = next(entry["url"] for entry in entries if entry["id"] == version)
    meta = json.loads(fetch(url, f"{version}.json").read_text())
    return fetch(meta["downloads"]["client_mappings"]["url"], f"{version}-client_mappings.txt")


def mcp_config(version: str) -> Path:
    url = (
        "https://maven.minecraftforge.net/de/oceanlabs/mcp/mcp_config/"
        f"{version}/mcp_config-{version}.zip"
    )
    return fetch(url, f"mcp_config-{version}.zip")


def class_block(path: Path, named: str):
    """The obfuscated name of a class plus its member lines.

    Mojang's mapping files carry ``#`` comment lines at column zero, so skip those
    instead of treating them as the start of the next class.
    """
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for index, line in enumerate(lines):
        if line.startswith("#"):
            continue
        match = re.match(r"^(\S+) -> (\S+):$", line)
        if match and match.group(1) == named:
            members = []
            for following in lines[index + 1:]:
                if following.startswith("#"):
                    continue
                if following and not following[0].isspace():
                    break
                if following.strip():
                    members.append(following.strip())
            return match.group(2), members
    return None, []


def srg_name(version: str):
    """The SRG name getSplash resolves to, or None when it cannot be found."""
    obf, members = class_block(mojang_mappings(version), SPLASH_MANAGER)
    get_obf = None
    for member in members:
        if " getSplash(" in member:
            get_obf = re.search(r"-> (\S+)$", member).group(1)
    if obf is None or get_obf is None:
        return None

    renderer, _ = class_block(mojang_mappings(version), SPLASH_RENDERER)
    # 1.20 is where SplashRenderer arrives; before that the splash is a String.
    descriptor = f"()L{renderer};" if renderer else "()Ljava/lang/String;"

    text = zipfile.ZipFile(mcp_config(version)).read("config/joined.tsrg").decode("utf-8", "replace")
    current = None
    for line in text.splitlines():
        if line.startswith("tsrg2"):
            continue
        if not line.startswith("\t"):
            parts = line.split()
            current = parts[0] if parts else None
        elif current == obf:
            parts = line.strip().split()
            if len(parts) >= 3 and parts[0] == get_obf and parts[1] == descriptor:
                return parts[2]
    return None


def main() -> None:
    failures = 0
    print(f"{'line':<16} {'release':<9} {'splash target':<16} note")
    for project, _compile, covered in read_targets(FORGE_TARGETS_FILE):
        if key(covered[0]) >= REFMAP_STOPS_AT:
            print(f"{project:<16} {'-':<9} {'-':<16} no refmap from "
                  f"{'.'.join(map(str, REFMAP_STOPS_AT))}; literal names")
            continue
        resolved = []
        for release in (covered[0], covered[-1]):
            name = srg_name(release)
            resolved.append(name)
            print(f"{project:<16} {release:<9} {name or 'UNRESOLVED':<16} ")
        if None in resolved or resolved[0] != resolved[-1]:
            failures += 1
            print(f"{project:<16} {'':<9} {'':<16} MISMATCH: the line cannot share one jar")
    if failures:
        raise SystemExit(f"{failures} Forge line(s) do not resolve to a single SRG name")
    print("\nEvery Forge line resolves to one SRG name at both ends.")


if __name__ == "__main__":
    main()
