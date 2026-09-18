#!/usr/bin/env python3
"""M229D-006 — Release manifest / allowlist validation."""
from __future__ import annotations

import fnmatch
import sys
from pathlib import Path


def load_allowed(path: Path) -> list[str]:
    allowed: list[str] = []
    in_block = False
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("allowed_paths:"):
            in_block = True
            continue
        if in_block:
            if s.startswith("- "):
                allowed.append(s[2:].strip())
            elif s and not s.startswith("#") and ":" in s:
                break
    return allowed


def allowed_file(rel: str, patterns: list[str]) -> bool:
    rel = rel.replace("\\", "/")
    for pattern in patterns:
        pattern = pattern.replace("\\", "/")
        if fnmatch.fnmatch(rel, pattern):
            return True
        if pattern.endswith("/**"):
            prefix = pattern[:-3]
            if rel == prefix or rel.startswith(prefix + "/"):
                return True
    return False


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    allowlist = root / "public-release-allowlist.yml"
    if not allowlist.exists():
        print("M229D-006 REVIEW_REQUIRED: allowlist unavailable", file=sys.stderr)
        return 3

    patterns = load_allowed(allowlist)
    unknown: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if rel.startswith(".git/"):
            continue
        if "__pycache__" in rel.split("/"):
            continue
        if rel.endswith(".pyc"):
            continue
        if not allowed_file(rel, patterns):
            unknown.append(rel)

    if unknown:
        print("M229D-006 BLOCK: Release manifest policy violation.", file=sys.stderr)
        print(f"Unexpected file count: {len(unknown)}", file=sys.stderr)
        return 1

    print("M229D-006 PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
