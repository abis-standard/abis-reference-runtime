"""Runtime foundation tests — stdlib unittest only."""

from __future__ import annotations

import inspect
import unittest

from tests._bootstrap import ensure_paths

ensure_paths()

from abis_grp_runtime.authorization import AuthorizationInput  # noqa: E402
from abis_grp_runtime.connector import BusinessConnectorPort, NullConnector  # noqa: E402
from abis_grp_runtime.context import RuntimeRequestContext  # noqa: E402
from abis_grp_runtime.control_plane import control_plane_allows  # noqa: E402
from abis_grp_runtime.core import RuntimeCore  # noqa: E402
from abis_grp_runtime.execution import ExecutionClass, resolve_execution_disposition  # noqa: E402
from abis_grp_runtime.native_result import NativeResultEnvelope  # noqa: E402
from abis_grp_runtime.semantic import InteractionEnvelope, SemanticBoundaryInput, SemanticReference  # noqa: E402


def _semantic_input() -> SemanticBoundaryInput:
    return SemanticBoundaryInput(
        participant_ref=SemanticReference("participant", "part-001"),
        intent_ref=SemanticReference("intent", "intent-001"),
        interaction=InteractionEnvelope(
            interaction_ref=SemanticReference("interaction", "int-001"),
            capability_ref=SemanticReference("capability", "cap-001"),
            decision_ref=SemanticReference("decision", "dec-001"),
        ),
    )


def _authorized() -> AuthorizationInput:
    return AuthorizationInput(permission_token="ALLOW")


class TestExecutionContract(unittest.TestCase):
    def test_controlled_simulator_allowed(self) -> None:
        disp = resolve_execution_disposition(ExecutionClass.CONTROLLED_SIMULATOR)
        self.assertTrue(disp.allowed)

    def test_real_external_denied(self) -> None:
        disp = resolve_execution_disposition(ExecutionClass.REAL_EXTERNAL)
        self.assertFalse(disp.allowed)

    def test_unknown_fail_closed(self) -> None:
        disp = resolve_execution_disposition(ExecutionClass.UNKNOWN)
        self.assertFalse(disp.allowed)
        ok, _ = control_plane_allows(ExecutionClass.UNKNOWN)
        self.assertFalse(ok)


class TestNativeResultOutcomeSeparation(unittest.TestCase):
    def test_fixture_confirmed_still_not_outcome(self) -> None:
        core = RuntimeCore()
        ctx = RuntimeRequestContext.create(agent_id="agent-1", execution_class=ExecutionClass.FIXTURE)
        result = core.process(ctx, _semantic_input(), _authorized(), operation="reserve")
        self.assertIsNotNone(result.native_result)
        self.assertEqual(result.native_result.external_status, "CONFIRMED")
        self.assertEqual(result.outcome_disposition.disposition, "NOT_EVALUATED")


class TestConnectorInterface(unittest.TestCase):
    def test_connector_has_no_domain_specific_methods(self) -> None:
        methods = {
            name
            for name, _ in inspect.getmembers(BusinessConnectorPort, predicate=inspect.isfunction)
            if not name.startswith("_")
        }
        self.assertEqual(methods, {"cancel", "check_availability", "modify", "reserve"})


class TestRuntimePipeline(unittest.TestCase):
    def test_real_external_halted(self) -> None:
        core = RuntimeCore()
        ctx = RuntimeRequestContext.create(agent_id="agent-1", execution_class=ExecutionClass.REAL_EXTERNAL)
        result = core.process(ctx, _semantic_input(), _authorized())
        self.assertTrue(result.halted)

    def test_evidence_trace_records_lifecycle(self) -> None:
        core = RuntimeCore()
        ctx = RuntimeRequestContext.create(agent_id="agent-1", execution_class=ExecutionClass.NULL)
        result = core.process(ctx, _semantic_input(), _authorized())
        phases = result.trace.phases()
        self.assertIn("authorization", phases)
        self.assertIn("outcome_interpreter", phases)


if __name__ == "__main__":
    unittest.main()
