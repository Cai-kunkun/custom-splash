#!/usr/bin/env python3
"""Write the Modrinth version payload for one jar.

Modrinth takes the version metadata as a JSON form field, and a changelog is
multi-line Markdown. Building that inline in the workflow meant hand-escaping
every quote and newline inside a shell string, so the payload is written here
instead and posted with ``-F data=@file;type=application/json``.

The changelog comes from the ``## <version>`` section of CHANGELOG.md. A jar's
version carries a build suffix (``2.0.0+mc1.20``) while the changelog is keyed by
the release (``2.0.0``), so the suffix is dropped before looking it up.

Usage:
    modrinth_payload.py OUTPUT PROJECT_ID VERSION LOADER GAME_VERSIONS_JSON
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHANGELOG = ROOT / "CHANGELOG.md"
FALLBACK = "See the repository's CHANGELOG.md for what changed in this release."


def changelog_for(release: str) -> str:
    """The changelog section for a release, or a fallback when it has none."""
    if not CHANGELOG.is_file():
        return FALLBACK
    heading = re.compile(r"^##\s+\[?" + re.escape(release) + r"\]?\s*$")
    lines = CHANGELOG.read_text(encoding="utf-8").splitlines()
    body = None
    for index, line in enumerate(lines):
        if heading.match(line):
            body = []
            for following in lines[index + 1:]:
                if following.startswith("## "):
                    break
                body.append(following)
            break
    if body is None:
        return FALLBACK
    text = "\n".join(body).strip()
    return text or FALLBACK


def main() -> None:
    if len(sys.argv) != 6:
        raise SystemExit(__doc__.strip())
    output, project_id, version, loader, game_versions = sys.argv[1:]
    release = version.split("+", 1)[0]
    changelog = changelog_for(release)
    payload = {
        "project_id": project_id,
        "version_number": version,
        "version_title": version,
        "version_type": "release",
        "changelog": changelog,
        "dependencies": [],
        "game_versions": json.loads(game_versions),
        "loaders": [loader],
        "environment": "client_or_server",
        "featured": False,
        "file_parts": ["file"],
        "primary_file": "file",
    }
    Path(output).write_text(json.dumps(payload), encoding="utf-8")
    source = "CHANGELOG.md" if changelog != FALLBACK else "fallback"
    print(f"payload for {version} ({loader}, {len(payload['game_versions'])} game "
          f"versions, changelog from {source}, {len(changelog)} chars)")


if __name__ == "__main__":
    main()
