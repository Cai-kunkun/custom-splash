#!/usr/bin/env python3
"""Publish every built jar to Modrinth as one alpha version per loader.

Each jar identifies itself through its metadata, so a Fabric jar is published
with the "fabric" loader while Forge and NeoForge jars use their own loader.
The version number keeps the Minecraft version and, for loaders that publish it,
the loader name, so each file gets a unique Modrinth version.
"""

import json
import os
import re
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

METADATA = {
    "fabric": "fabric.mod.json",
    "forge": "META-INF/mods.toml",
    "neoforge": "META-INF/neoforge.mods.toml",
}

PATTERNS = {
    "fabric": re.compile(r"^custom-splash-(?P<mc>[0-9.]+)-(?P<version>[^/]+)$"),
    "forge": re.compile(r"^custom-splash-(?P<mc>[0-9.]+)-forge-(?P<version>[^/]+)$"),
    "neoforge": re.compile(r"^custom-splash-(?P<mc>[0-9.]+)-neoforge-(?P<version>[^/]+)$"),
}


def detect_loader(jar: Path) -> str:
    with zipfile.ZipFile(jar) as archive:
        names = archive.namelist()
    for loader, entry in METADATA.items():
        if entry in names:
            return loader
    raise SystemExit(f"{jar.name}: no mod metadata found")


def read_metadata(jar: Path, loader: str):
    with zipfile.ZipFile(jar) as archive:
        return json.loads(archive.read(METADATA[loader]))


def request(method: str, url: str, token: str, data: bytes | None = None, content_type: str | None = None) -> bytes:
    headers = {"Authorization": token, "User-Agent": "custom-splash/release-script"}
    if content_type is not None:
        headers["Content-Type"] = content_type
    request = urllib.request.Request(url, headers=headers, method=method, data=data)
    with urllib.request.urlopen(request) as response:
        return response.read()


def publish(jar: Path, loader: str, token: str, project_id: str) -> None:
    metadata = read_metadata(jar, loader)
    if loader == "fabric":
        version = metadata["version"]
        game_versions = [metadata["depends"]["minecraft"].lstrip("=")]
    else:
        mod = metadata["mods"][0]
        version = mod["version"]
        game_versions = [
            dependency["versionRange"].strip("[]")
            for dependency in metadata.get("dependencies", [])
            if dependency.get("modId") == "minecraft"
        ]

    boundary = "----modrinth-release"
    body = bytearray()
    for name, value in (
        ("project_id", project_id),
        ("version_number", version),
        ("version_title", version),
        ("version_type", "alpha"),
        ("changelog", ""),
        ("loaders", json.dumps([loader])),
        ("game_versions", json.dumps(game_versions)),
        ("featured", "false"),
        ("file_parts", json.dumps(["file"])),
        ("primary_file", "file"),
    ):
        body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n".encode()
    body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{jar.name}\"\r\n".encode()
    body += b"Content-Type: application/java-archive\r\n\r\n"
    body += jar.read_bytes()
    body += f"\r\n--{boundary}--\r\n".encode()
    request(
        "POST",
        "https://api.modrinth.com/v3/version",
        token,
        data=bytes(body),
        content_type=f"multipart/form-data; boundary={boundary}",
    )
    print(f"published {jar.name} for {'/'.join(game_versions)} on {loader} as {version}")


def main() -> None:
    release_dir = Path(sys.argv[1])
    token = os.environ.get("MODRINTH_TOKEN", "")
    project_id = os.environ.get("MODRINTH_ID", "")
    if not token or not project_id:
        print("Modrinth token or project id not configured, skipping")
        return

    existing = json.loads(
        request("GET", f"https://api.modrinth.com/v3/project/{project_id}/version", token)
    )
    known = {entry["version_number"] for entry in existing}
    for jar in sorted(release_dir.glob("*.jar")):
        loader = detect_loader(jar)
        version = read_metadata(jar, loader)["version"]
        if version in known:
            print(f"skipping existing Modrinth version {version}")
            continue
        publish(jar, loader, token, project_id)


if __name__ == "__main__":
    main()
