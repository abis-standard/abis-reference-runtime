"""Test service factory — registry-backed GrokE2EService."""

from __future__ import annotations

from abis_grp_runtime.e2e.service import GrokE2EService
from abis_grp_runtime.registry.factory import build_reference_registry
from css.engine import CommerceEngine
from crs.engine import ReservationEngine


def make_test_service(data_dir: str) -> GrokE2EService:
    crs_engine = ReservationEngine(data_dir=data_dir)
    css_engine = CommerceEngine()
    registry = build_reference_registry(crs_engine, css_engine)
    return GrokE2EService(registry)
