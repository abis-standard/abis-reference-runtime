"""Test path bootstrap — reference package only (no Vault source imports)."""

from __future__ import annotations

import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SRC = PACKAGE_ROOT / "runtime" / "src"
CRS_SRC = PACKAGE_ROOT / "reference-business" / "controlled-reservation-simulator" / "src"


def ensure_paths() -> None:
    for path in (str(RUNTIME_SRC), str(CRS_SRC)):
        if path not in sys.path:
            sys.path.insert(0, path)
