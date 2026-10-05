#!/usr/bin/env python3
"""Validate the complete set of release jars before publishing anywhere.

Every build target produces exactly one jar. Fabric jars carry a
``fabric.mod.json`` at the archive root, Forge jars carry
``META-INF/mods.toml`` and NeoForge jars carry
``META-INF/neoforge.mods.toml``; the loader is inferred from which of the
three is present, so the families can share this validation pass.

Fabric targets are defined by fabric-targets.txt, where one jar covers a range
of Minecraft releases, so its ``minecraft`` dependency is checked against the
range rather than a single version.
"""

import re
import sys
import zipfile
from pathlib import Path

# Classes shared by every loader, plus the loader-specific platform class.
SHARED_CLASSES = (
    "dev/arrbrants/customsplash/SplashRegistry.class",
    "dev/arrbrants/customsplash/SplashConfig.class",
    "dev/arrbrants/customsplash/SplashEntry.class",
    "dev/arrbrants/customsplash/SplashContext.class",
    "dev/arrbrants/customsplash/SplashColors.class",
    "dev/arrbrants/customsplash/SplashColor.class",
    "dev/arrbrants/customsplash/SplashResourcePack.class",
    "dev/arrbrants/customsplash/SplashPlatform.class",
    "dev/arrbrants/customsplash/mixin/SplashManagerMixin.class",
)

PLATFORM_CLASS = {
    "fabric": "dev/arrbrants/customsplash/FabricSplashPlatform.class",
    "forge": "dev/arrbrants/customsplash/ForgeSplashPlatform.class",
    "neoforge": "dev/arrbrants/customsplash/NeoForgeSplashPlatform.class",
}


def read_properties(root: Path, project: str) -> dict[str, str]:
    lines = (root / "versions" / project / "gradle.properties").read_text().splitlines()
    return dict(
        line.split("=", 1)
        for line in lines
        if "=" in line and not line.startswith("#")
    )


TARGET_FILES = {
    "fabric": "fabric-targets.txt",
    "forge": "forge-targets.txt",
    "neoforge": "neoforge-targets.txt",
}


def read_targets(root: Path, loader: str) -> dict[str, list[str]]:
    """Project -> the Minecraft releases its single jar covers."""
    targets: dict[str, list[str]] = {}
    for line in (root / TARGET_FILES[loader]).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 3:
            raise SystemExit(f"Malformed target line in {TARGET_FILES[loader]}: {line}")
        targets[parts[0]] = parts[2:]
    return targets


def load_targets(root: Path) -> list[tuple[str, str]]:
    """Return (project, loader) pairs for every release target."""
    return [
        (project, loader)
        for loader in ("fabric", "forge", "neoforge")
        for project in read_targets(root, loader)
    ]


def target_prefix(root: Path, project: str, loader: str) -> str:
    props = read_properties(root, project)
    mod_version = props["mod_version"]
    minecraft = props["minecraft_version"]
    if loader == "forge":
        return f"custom-splash-{minecraft}-forge-{mod_version}+forge-mc{minecraft}."
    if loader == "neoforge":
        return f"custom-splash-{minecraft}-neoforge-{mod_version}+neoforge-mc{minecraft}."
    return f"custom-splash-{minecraft}-{mod_version}+mc{minecraft}."


def check_fabric_metadata(jar_name: str, metadata: dict, covered: list[str], expected_version: str) -> list[str]:
    errors = []
    expected = f">={covered[0]} <={covered[-1]}"
    if metadata["depends"]["minecraft"] != expected:
        errors.append(
            f"{jar_name}: Minecraft dependency {metadata['depends']['minecraft']!r} "
            f"does not match {expected!r}"
        )
    if metadata["version"] != expected_version:
        errors.append(
            f"{jar_name}: metadata version {metadata['version']!r} does not match {expected_version!r}"
        )
    return errors


def mc_marker(covered: list[str]) -> str:
    """The Maven version range start a Forge or NeoForge jar has to declare."""
    return f'versionRange="[{covered[0]},'


def check_mod_metadata(jar_name: str, text: str, expected_version: str, marker: str) -> list[str]:
    errors = []
    if 'modId="custom-splash"' not in text:
        errors.append(f"{jar_name}: missing custom-splash modId in the mod metadata")
    if marker not in text:
        errors.append(f"{jar_name}: Minecraft range does not start at {marker}")
    match = re.search(r'^version="([^"]*)"$', text, flags=re.MULTILINE)
    if not match:
        errors.append(f"{jar_name}: missing version entry in the mod metadata")
    elif match.group(1) != expected_version:
        errors.append(
            f"{jar_name}: mod metadata version {match.group(1)!r} does not match {expected_version!r}"
        )
    return errors


def main() -> None:
    release_dir = Path(sys.argv[1])
    root = Path(__file__).resolve().parents[1]
    targets = load_targets(root)
    covered_by_target = {
        loader: read_targets(root, loader) for loader in ("fabric", "forge", "neoforge")
    }
    jars = list(release_dir.glob("*.jar"))
    if len(jars) != len(targets):
        raise SystemExit(f"Expected {len(targets)} jars, found {len(jars)}")

    for project, loader in targets:
        covered = covered_by_target[loader][project]
        prefix = target_prefix(root, project, loader)
        matches = [jar for jar in jars if jar.name.startswith(prefix)]
        if len(matches) != 1:
            raise SystemExit(f"Expected one jar for {project}, found {len(matches)}")

        jar = matches[0]
        if not re.fullmatch(rf"{re.escape(prefix)}[0-9a-f]{{8}}\.jar", jar.name):
            raise SystemExit(f"{jar.name}: missing 8-character commit hash")

        props = read_properties(root, project)
        commit = jar.name[len(prefix) : -len(".jar")]
        if loader == "forge":
            expected_version = f"{props['mod_version']}+forge-mc{props['minecraft_version']}.{commit}"
        elif loader == "neoforge":
            expected_version = f"{props['mod_version']}+neoforge-mc{props['minecraft_version']}.{commit}"
        else:
            expected_version = f"{props['mod_version']}+mc{props['minecraft_version']}.{commit}"

        with zipfile.ZipFile(jar) as archive:
            names = set(archive.namelist())
            for class_name in SHARED_CLASSES + (PLATFORM_CLASS[loader],):
                if class_name not in names:
                    raise SystemExit(f"{jar.name}: missing {class_name}")

            if loader == "fabric":
                import json

                metadata = json.loads(archive.read("fabric.mod.json"))
                errors = check_fabric_metadata(
                    jar.name, metadata, covered, expected_version
                )
            elif loader == "neoforge":
                text = archive.read("META-INF/neoforge.mods.toml").decode("utf-8")
                errors = check_mod_metadata(
                    jar.name, text, expected_version, mc_marker(covered)
                )
            else:
                text = archive.read("META-INF/mods.toml").decode("utf-8")
                errors = check_mod_metadata(
                    jar.name, text, expected_version, mc_marker(covered)
                )
            for error in errors:
                raise SystemExit(error)

        java_level = int(props["java_version"])
        # Sanity-check the shared classes were compiled for a supported Java level.
        registry_class = next(
            name for name in SHARED_CLASSES if name.endswith("/SplashRegistry.class")
        )
        with zipfile.ZipFile(jar) as archive:
            major = int.from_bytes(archive.read(registry_class)[6:8], "big")
            if major > java_level + 44:
                raise SystemExit(
                    f"{jar.name}: Java class version exceeds configured target"
                )

        print(f"OK {project} ({loader}): {jar.name}")


if __name__ == "__main__":
    main()
