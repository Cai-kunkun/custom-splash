#!/usr/bin/env python3
"""Check the metadata every target declares: its mod id and its release line.

Each target builds one jar and declares the mod id and the Minecraft range it
supports, so three things have to hold at once:

* the mod id satisfies the strictest loader rule. NeoForge requires
  ``^(?=.{2,64}$)[a-z][a-z0-9_]*(\\.[a-z][a-z0-9_]*)*$`` and Forge from 1.17 turns
  the id into a Java module name, so an id with a hyphen makes the jar fail to
  load on both -- which is how ``custom-splash`` shipped broken for years;
* every release in ``supported-*-versions.txt`` is claimed by at least one jar,
  otherwise an upload supports nothing;
* the range a jar declares matches the line its targets file gives it, otherwise
  the jar promises releases it was not built for. A jar that declares a release
  belonging to a later line is a failure, because the later line exists precisely
  because something changed: the Forge 1.20-1.20.4 jar resolves getSplash through
  a refmap, and a range reaching 1.21 offered it on 1.20.6, where Forge resolves
  official names and the injection could not find its target.

Reads only the generated projects, so it needs no build and no network.
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from generate_common_sources import (FABRIC_TARGETS_FILE, FORGE_TARGETS_FILE,  # noqa: E402
                                     NEOFORGE_TARGETS_FILE, read_targets)

LOADERS = (
    ("fabric", FABRIC_TARGETS_FILE, "supported-versions.txt"),
    ("forge", FORGE_TARGETS_FILE, "supported-forge-versions.txt"),
    ("neoforge", NEOFORGE_TARGETS_FILE, "supported-neoforge-versions.txt"),
)

# Taken from the message NeoForge prints when it rejects a mod file.
MOD_ID_PATTERN = re.compile(r"^(?=.{2,64}$)[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*$")


def key(version: str) -> tuple:
    return tuple(int(part) for part in version.split("."))


def declared_mod_id(loader: str, project: str):
    """The mod id a project declares for itself."""
    resources = ROOT / "versions" / project / "src" / "main" / "resources"
    if loader == "fabric":
        return json.loads((resources / "fabric.mod.json").read_text())["id"]
    name = "neoforge.mods.toml" if loader == "neoforge" else "mods.toml"
    text = (resources / "META-INF" / name).read_text()
    block = text.split("[[mods]]")[1] if "[[mods]]" in text else text
    match = re.search(r'modId="([^"]+)"', block)
    return match.group(1) if match else None


def declared(loader: str, project: str):
    """The Minecraft range a project declares: (low, high, high_is_inclusive)."""
    resources = ROOT / "versions" / project / "src" / "main" / "resources"
    if loader == "fabric":
        metadata = json.loads((resources / "fabric.mod.json").read_text())
        match = re.fullmatch(r">=(\S+) <=(\S+)", metadata["depends"]["minecraft"])
        if not match:
            return None
        return key(match.group(1)), key(match.group(2)), True
    name = "neoforge.mods.toml" if loader == "neoforge" else "mods.toml"
    text = (resources / "META-INF" / name).read_text()
    for block in text.split("[[dependencies.customsplash]]")[1:]:
        if 'modId="minecraft"' not in block:
            continue
        match = re.search(r'versionRange="\[([^,]+),([^)]+)\)"', block)
        if match:
            # A Maven range excludes its upper bound.
            return key(match.group(1)), key(match.group(2)), False
    return None


def covers(span, release: str) -> bool:
    low, high, inclusive = span
    value = key(release)
    return low <= value and (value <= high if inclusive else value < high)


def main() -> None:
    failures = 0
    for loader, targets_file, versions_file in LOADERS:
        supported = [line.strip() for line in (ROOT / versions_file).read_text().splitlines()
                     if line.strip() and not line.startswith("#")]
        spans = {}
        for project, _compile, covered in read_targets(targets_file):
            span = declared(loader, project)
            if span is None:
                print(f"{loader}: could not read the declared range of {project}")
                failures += 1
                continue
            spans[project] = span
            mod_id = declared_mod_id(loader, project)
            if not mod_id or not MOD_ID_PATTERN.match(mod_id):
                print(f"{loader}/{project}: mod id {mod_id!r} would be rejected by the strictest "
                      f"loader; NeoForge requires {MOD_ID_PATTERN.pattern}")
                failures += 1
            # A jar has to claim every release its own line says it covers.
            missing = [release for release in covered if not covers(span, release)]
            if missing:
                print(f"{loader}/{project}: its jar does not declare {missing}")
                failures += 1
            extra = [release for release in supported
                     if covers(span, release) and release not in covered]
            if extra:
                print(f"{loader}/{project}: its jar also declares {extra}, which belong to "
                      f"a later line")
                failures += 1

        # Coverage comes from what the jars actually declare, not from the lines.
        claims = defaultdict(list)
        for project, span in spans.items():
            for release in supported:
                if covers(span, release):
                    claims[release].append(project)
        unclaimed = [release for release in supported if not claims[release]]
        overlaps = {release: names for release, names in claims.items() if len(names) > 1}
        print(f"{loader}: {len(supported)} releases, {len(spans)} targets, "
              f"{len(unclaimed)} unclaimed, {len(overlaps)} overlapping")
        for release in unclaimed:
            print(f"  {release} is not claimed by any jar")
            failures += 1
        for release, names in sorted(overlaps.items(), key=lambda item: key(item[0])):
            print(f"  {release} is claimed by {', '.join(names)}")

    if failures:
        raise SystemExit(f"\n{failures} metadata problem(s)")
    print("\nEvery mod id passes the strictest loader rule, every supported release is claimed "
          "by exactly one jar, and no jar declares a release from another line.")


if __name__ == "__main__":
    main()
