#!/usr/bin/env python3
"""ABIS disclosure content-tree hash — canonical algorithm v1 (M-229F.1).

Domain-separated deterministic hash of publishable repository content.
Excludes the approval artifact from the reviewed content identity.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path

DOMAIN = "ABIS-DISCLOSURE-CONTENT-V1"
EXCLUDED_PATHS = frozenset(
    {
        ".abis/disclosure-approval.json",
    }
)


def canonical_path(rel: str) -> str | None:
    rel = rel.replace("\\", "/").strip()
    if rel.startswith("./"):
        rel = rel[2:]
    if not rel or rel.startswith("/"):
        return None
    parts: list[str] = []
    for part in rel.split("/"):
        if not part or part == ".":
            continue
        if part == "..":
            return None
        parts.append(part)
    return "/".join(parts)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def is_excluded(path: str) -> bool:
    return path in EXCLUDED_PATHS


def list_paths_from_index(repo: Path) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(repo), "ls-files", "-z"],
        capture_output=True,
        check=True,
    )
    paths: list[str] = []
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        path = canonical_path(raw.decode("utf-8", errors="surrogateescape"))
        if path and not is_excluded(path):
            paths.append(path)
    return sorted(set(paths))


def list_paths_from_head(repo: Path) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(repo), "ls-tree", "-r", "--name-only", "-z", "HEAD"],
        capture_output=True,
        check=True,
    )
    paths: list[str] = []
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        path = canonical_path(raw.decode("utf-8", errors="surrogateescape"))
        if path and not is_excluded(path):
            paths.append(path)
    return sorted(set(paths))


def read_index_blob(repo: Path, path: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repo), "show", f":{path}"],
        capture_output=True,
        check=True,
    )
    return result.stdout


def read_head_blob(repo: Path, path: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repo), "show", f"HEAD:{path}"],
        capture_output=True,
        check=True,
    )
    return result.stdout


def compute_content_tree_hash(repo: Path, source: str) -> str:
    if source == "index":
        paths = list_paths_from_index(repo)
        blobs = {path: read_index_blob(repo, path) for path in paths}
    elif source == "head":
        paths = list_paths_from_head(repo)
        blobs = {path: read_head_blob(repo, path) for path in paths}
    else:
        raise ValueError(f"unsupported source: {source}")

    records: list[str] = []
    for path in sorted(blobs):
        digest = sha256_bytes(blobs[path])
        records.append(f"{path}\n{digest}\n")

    payload = f"{DOMAIN}\n" + "".join(records)
    return sha256_bytes(payload.encode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute ABIS disclosure content-tree hash")
    parser.add_argument("repo", type=Path, help="Repository root")
    parser.add_argument(
        "--source",
        choices=["index", "head"],
        default="head",
        help="index = git index (staged); head = committed HEAD tree",
    )
    args = parser.parse_args()

    repo = args.repo.resolve()
    if not (repo / ".git").exists():
        print("error: not a git repository", file=sys.stderr)
        return 2

    try:
        digest = compute_content_tree_hash(repo, args.source)
    except subprocess.CalledProcessError as exc:
        print("error: git content enumeration failed", file=sys.stderr)
        return 2

    print(digest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
