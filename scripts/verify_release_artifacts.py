#!/usr/bin/env python3
"""Validate the complete set of release jars before publishing anywhere.

Every loader keeps its own version list, so a jar is identified by the loader
directory it lives in plus its Minecraft version.
"""

import json
import re
import sys
import zipfile
from pathlib import Path

LOADERS = ("fabric", "forge", "neoforge")

CLASSES = [
    "SplashRegistry",
    "SplashConfig",
    "SplashEntry",
    "SplashContext",
    "SplashColors",
    "SplashResourcePack",
]

PLATFORM_CLASS = {
    "fabric": "SplashFabricPlatform",
    "forge": "SplashForgePlatform",
    "neoforge": "SplashForgePlatform",
}


def metadata_name(loader: str) -> str:
    if loader == "neoforge":
        return "META-INF/neoforge.mods.toml"
    if loader == "forge":
        return "META-INF/mods.toml"
    return "fabric.mod.json"


def jar_name_pattern(loader: str) -> re.Pattern:
    """Match one jar name for a loader and capture its version and hash."""
    if loader == "fabric":
        return re.compile(
            r"custom-splash-(?P<mc>[0-9.]+)-(?P<version>[^/]+)(?P<hash>\.[0-9a-f]{8})?\.jar"
        )
    return re.compile(
        rf"custom-splash-(?P<mc>[0-9.]+)-{loader}-(?P<version>[^/]+)"
        rf"(?P<hash>\.[0-9a-f]{{8}})?\.jar"
    )


def main() -> None:
    release_dir = Path(sys.argv[1])
    root = Path(__file__).resolve().parents[1]
    jars = list(release_dir.glob("*.jar"))

    expected = []
    for loader in LOADERS:
        list_file = root / f"supported-{loader}-versions.txt"
        if not list_file.exists():
            continue
        for minecraft in list_file.read_text().splitlines():
            if minecraft and not minecraft.startswith("#"):
                expected.append((loader, minecraft))

    if len(jars) != len(expected):
        raise SystemExit(f"Expected {len(expected)} jars, found {len(jars)}")

    matched = set()
    for loader, minecraft in expected:
        props = dict(
            line.split("=", 1)
            for line in (root / loader / minecraft / "gradle.properties").read_text().splitlines()
            if "=" in line and not line.startswith("#")
        )
        mod_version = props["mod_version"]
        pattern = jar_name_pattern(loader)
        matches = [jar for jar in jars if pattern.fullmatch(jar.name) and pattern.fullmatch(jar.name).group("mc") == minecraft]
        if len(matches) != 1:
            raise SystemExit(
                f"Expected one jar for Minecraft {minecraft} on {loader}, found {len(matches)}"
            )

        jar = matches[0]
        matched.add(jar.name)
        version = pattern.fullmatch(jar.name).group("version")
        with zipfile.ZipFile(jar) as archive:
            try:
                metadata = json.loads(archive.read(metadata_name(loader)))
                archive.read("dev/arrbrants/customsplash/SplashRegistry.class")
                archive.read("dev/arrbrants/customsplash/mixin/SplashManagerMixin.class")
                for class_name in CLASSES + [PLATFORM_CLASS[loader]]:
                    archive.read(f"dev/arrbrants/customsplash/{class_name}.class")
            except KeyError as error:
                raise SystemExit(f"{jar.name}: missing {error}") from error

            if loader == "fabric":
                if metadata["depends"]["minecraft"] != f"={minecraft}":
                    raise SystemExit(f"{jar.name}: incorrect Minecraft dependency")
                if metadata["version"] != version:
                    raise SystemExit(f"{jar.name}: metadata version does not match jar filename")
            else:
                mods = metadata.get("mods")
                if not mods or mods[0].get("version") != version:
                    raise SystemExit(f"{jar.name}: metadata version does not match jar filename")
                minecraft_dependency = next(
                    (d for d in metadata.get("dependencies") or [] if d.get("modId") == "minecraft"),
                    None,
                )
                if minecraft_dependency is None or minecraft_dependency.get(
                    "versionRange"
                ) != f"[{minecraft}]":
                    raise SystemExit(f"{jar.name}: incorrect Minecraft dependency")
            if not version.startswith(f"{mod_version}+mc{minecraft}"):
                raise SystemExit(f"{jar.name}: unexpected version prefix")
        print(f"OK {loader} {minecraft}: {jar.name}")

    unexpected = [jar.name for jar in jars if jar.name not in matched]
    if unexpected:
        raise SystemExit(f"Unexpected jars in release: {unexpected}")


if __name__ == "__main__":
    main()
