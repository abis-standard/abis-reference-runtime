"""Reference Runtime Pointer validation tests."""

from __future__ import annotations

import json
import unittest

from tests._bootstrap import ensure_paths

ensure_paths()

from abis_grp_runtime.discovery.pointer import (  # noqa: E402
    FORBIDDEN_POINTER_TERMS,
    POINTER_KIND,
    POINTER_VERSION,
    PointerValidationError,
    build_reference_runtime_pointer,
    extract_runtime_base_url,
    validate_pointer,
    validate_runtime_base_url,
)


class TestRuntimePointer(unittest.TestCase):
    def test_valid_pointer(self) -> None:
        pointer = build_reference_runtime_pointer("http://127.0.0.1:9080/")
        self.assertEqual(pointer["pointer_kind"], POINTER_KIND)
        self.assertEqual(pointer["pointer_version"], POINTER_VERSION)
        self.assertEqual(pointer["runtime"]["base_url"], "http://127.0.0.1:9080")

    def test_wrong_pointer_kind(self) -> None:
        with self.assertRaises(PointerValidationError):
            validate_pointer({"pointer_kind": "wrong", "pointer_version": 1, "runtime": {"base_url": "http://127.0.0.1:1"}})

    def test_unsupported_pointer_version(self) -> None:
        pointer = build_reference_runtime_pointer("http://127.0.0.1:9080")
        pointer["pointer_version"] = 99
        with self.assertRaises(PointerValidationError):
            validate_pointer(pointer)

    def test_missing_runtime_url(self) -> None:
        with self.assertRaises(PointerValidationError):
            validate_pointer({"pointer_kind": POINTER_KIND, "pointer_version": POINTER_VERSION, "runtime": {}})

    def test_malformed_json_object(self) -> None:
        with self.assertRaises(PointerValidationError):
            validate_pointer("not-json")

    def test_unsafe_runtime_url_userinfo(self) -> None:
        with self.assertRaises(PointerValidationError):
            validate_runtime_base_url("http://user:pass@127.0.0.1:9080")

    def test_unsafe_runtime_url_scheme(self) -> None:
        with self.assertRaises(PointerValidationError):
            validate_runtime_base_url("file:///tmp/runtime")

    def test_extract_runtime_base_url(self) -> None:
        pointer = build_reference_runtime_pointer("https://127.0.0.1:9443/demo")
        self.assertEqual(extract_runtime_base_url(pointer), "https://127.0.0.1:9443/demo")

    def test_semantic_firewall_pointer(self) -> None:
        pointer = build_reference_runtime_pointer("http://127.0.0.1:9080")
        serialized = json.dumps(pointer)
        for term in FORBIDDEN_POINTER_TERMS:
            self.assertNotIn(term, serialized, msg=f"forbidden term present: {term}")


if __name__ == "__main__":
    unittest.main()
