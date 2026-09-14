"""JSON file persistence for reservations and idempotency records."""

from __future__ import annotations

import json
import threading
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Optional


class JsonFileStore:
    """Thread-safe JSON store. Default path: <data_dir>/state.json."""

    def __init__(self, data_dir: str | Path) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.state_path = self.data_dir / "state.json"
        self._lock = threading.RLock()
        if not self.state_path.exists():
            self._write({"reservations": {}, "idempotency": {}})

    def _read(self) -> Dict[str, Any]:
        with self.state_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, state: Dict[str, Any]) -> None:
        tmp = self.state_path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, sort_keys=True)
            f.write("\n")
        tmp.replace(self.state_path)

    def put_reservation(self, reservation_id: str, record: Dict[str, Any]) -> None:
        with self._lock:
            state = self._read()
            state.setdefault("reservations", {})[reservation_id] = deepcopy(record)
            self._write(state)

    def get_reservation(self, reservation_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            state = self._read()
            rec = state.get("reservations", {}).get(reservation_id)
            return deepcopy(rec) if rec is not None else None

    def update_reservation(self, reservation_id: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self._lock:
            state = self._read()
            rec = state.get("reservations", {}).get(reservation_id)
            if rec is None:
                return None
            rec = deepcopy(rec)
            rec.update(fields)
            state["reservations"][reservation_id] = rec
            self._write(state)
            return deepcopy(rec)

    def put_idempotency(self, key: str, request_fingerprint: str, reservation_id: str, result: Dict[str, Any]) -> None:
        with self._lock:
            state = self._read()
            state.setdefault("idempotency", {})[key] = {
                "request_fingerprint": request_fingerprint,
                "reservation_id": reservation_id,
                "result": deepcopy(result),
            }
            self._write(state)

    def get_idempotency(self, key: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            state = self._read()
            rec = state.get("idempotency", {}).get(key)
            return deepcopy(rec) if rec is not None else None
