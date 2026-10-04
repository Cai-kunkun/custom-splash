#!/usr/bin/env python3
"""Validate the complete set of release jars before publishing anywhere.

Every build target produces exactly one jar. Fabric jars carry a
``fabric.mod.json`` at the archive root, Forge jars carry
``META-INF/mods.toml`` and NeoForge jars carry
``META-INF/neoforge.mods.toml``; the loader is inferred from which of the
three is present, so the families can share this validation pass.
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


def load_targets(root: Path) -> list[tuple[str, str]]:
    """Return (project, loader) pairs for every release target."""
    fabric = [
        (version, "fabric")
        for version in (root / "supported-versions.txt").read_text().splitlines()
    ]
    forge = [
        (f"{version}-forge", "forge")
        for version in (root / "supported-forge-versions.txt").read_text().splitlines()
    ]
    neoforge = [
        (f"{version}-neoforge", "neoforge")
        for version in (root / "supported-neoforge-versions.txt").read_text().splitlines()
    ]
    return fabric + forge + neoforge


def target_prefix(root: Path, project: str, loader: str) -> str:
    props = read_properties(root, project)
    mod_version = props["mod_version"]
    minecraft = props["minecraft_version"]
    if loader == "forge":
        return f"custom-splash-{minecraft}-forge-{mod_version}+forge-mc{minecraft}."
    if loader == "neoforge":
        return f"custom-splash-{minecraft}-neoforge-{mod_version}+neoforge-mc{minecraft}."
    return f"custom-splash-{minecraft}-{mod_version}+mc{minecraft}."


def check_fabric_metadata(jar_name: str, metadata: dict, minecraft: str, expected_version: str) -> list[str]:
    errors = []
    if metadata["depends"]["minecraft"] != f"={minecraft}":
        errors.append(f"{jar_name}: incorrect Minecraft dependency")
    if metadata["version"] != expected_version:
        errors.append(
            f"{jar_name}: metadata version {metadata['version']!r} does not match {expected_version!r}"
        )
    return errors


def check_mod_metadata(jar_name: str, text: str, expected_version: str) -> list[str]:
    errors = []
    if 'modId="custom-splash"' not in text:
        errors.append(f"{jar_name}: missing custom-splash modId in the mod metadata")
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
    jars = list(release_dir.glob("*.jar"))
    if len(jars) != len(targets):
        raise SystemExit(f"Expected {len(targets)} jars, found {len(jars)}")

    for project, loader in targets:
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
                    jar.name, metadata, props["minecraft_version"], expected_version
                )
            elif loader == "neoforge":
                text = archive.read("META-INF/neoforge.mods.toml").decode("utf-8")
                errors = check_mod_metadata(jar.name, text, expected_version)
            else:
                text = archive.read("META-INF/mods.toml").decode("utf-8")
                errors = check_mod_metadata(jar.name, text, expected_version)
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
