#!/usr/bin/env python3
"""Validate the complete set of release jars before publishing anywhere."""

import json
import re
import sys
import zipfile
from pathlib import Path


def main() -> None:
    release_dir = Path(sys.argv[1])
    root = Path(__file__).resolve().parents[1]
    versions = (root / "supported-versions.txt").read_text().splitlines()
    jars = list(release_dir.glob("*.jar"))
    if len(jars) != len(versions):
        raise SystemExit(f"Expected {len(versions)} jars, found {len(jars)}")

    for minecraft in versions:
        props = dict(
            line.split("=", 1)
            for line in (root / "versions" / minecraft / "gradle.properties").read_text().splitlines()
            if "=" in line and not line.startswith("#")
        )
        prefix = f"custom-splash-{minecraft}-{props['mod_version']}+mc{minecraft}."
        matches = [jar for jar in jars if jar.name.startswith(prefix)]
        if len(matches) != 1:
            raise SystemExit(f"Expected one jar for Minecraft {minecraft}, found {len(matches)}")

        jar = matches[0]
        with zipfile.ZipFile(jar) as archive:
            try:
                metadata = json.loads(archive.read("fabric.mod.json"))
                registry = archive.read("dev/arrbrants/customsplash/SplashRegistry.class")
                archive.read("dev/arrbrants/customsplash/mixin/SplashManagerMixin.class")
                archive.read("dev/arrbrants/customsplash/SplashConfig.class")
                archive.read("dev/arrbrants/customsplash/SplashEntry.class")
                archive.read("dev/arrbrants/customsplash/SplashContext.class")
            except KeyError as error:
                raise SystemExit(f"{jar.name}: missing {error}") from error
        if metadata["depends"]["minecraft"] != f"={minecraft}":
            raise SystemExit(f"{jar.name}: incorrect Minecraft dependency")
        if not re.fullmatch(rf"{re.escape(prefix)}[0-9a-f]{{8}}\.jar", jar.name):
            raise SystemExit(f"{jar.name}: missing 8-character commit hash")
        if metadata["version"] != jar.name[len(f"custom-splash-{minecraft}-") : -4]:
            raise SystemExit(f"{jar.name}: metadata version does not match jar filename")
        if int.from_bytes(registry[6:8], "big") > int(props["java_version"]) + 44:
            raise SystemExit(f"{jar.name}: Java class version exceeds configured target")
        print(f"OK {minecraft}: {jar.name}")


if __name__ == "__main__":
    main()
