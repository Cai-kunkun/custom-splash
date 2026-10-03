#!/usr/bin/env python3
"""Publish MODRINTH.md as the Modrinth project page description.

Only the description and body are touched; every other project field on
Modrinth keeps whatever the dashboard says. Run from the repository root with
MODRINTH_TOKEN and MODRINTH_ID set, which is how CI invokes it.
"""

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = "https://api.modrinth.com/v2/project"
# The page shows one short sentence next to the title; the markdown file starts
# with the mod name followed by a one line summary, so lift that line for it.
SUMMARY_SOURCE = ROOT / "MODRINTH.md"
BODY_SOURCE = ROOT / "MODRINTH.md"


def summary(markdown: str) -> str:
    """Return the first paragraph after the title as the short description."""
    blocks = markdown.split("\n\n")
    for block in blocks[1:]:
        text = block.strip()
        if text and not text.startswith("#") and not text.startswith("|") and not text.startswith("```"):
            # Keep only the opening sentence: Modrinth wants a short summary.
            sentence = text.split(". ")[0].split("!")[0]
            sentence = " ".join(sentence.split())
            if not sentence.endswith("."):
                sentence = sentence + "."
            return sentence
    return "A Fabric mod that customises the Minecraft title screen splash text."


def main() -> None:
    token = os.environ.get("MODRINTH_TOKEN", "").strip()
    project = os.environ.get("MODRINTH_ID", "").strip()
    if not token or not project:
        print("MODRINTH_TOKEN or MODRINTH_ID not set, skipping")
        return 0

    markdown = BODY_SOURCE.read_text(encoding="utf-8")
    payload = json.dumps({"body": markdown, "description": summary(markdown)}).encode("utf-8")

    request = urllib.request.Request(
        f"{API}/{project}",
        data=payload,
        method="PATCH",
        headers={
            "Authorization": token,
            "Content-Type": "application/json",
            "User-Agent": "arrbrants/custom-splash/1.2.0 (CI version sync)",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            print(f"Modrinth description updated ({response.status})")
            return 0
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", "replace")
        print(f"Modrinth description update failed: {error.code} {body}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
