"""M-18F — structured resource-observation evidence (synthetic fixtures only)."""

from __future__ import annotations

import unittest
from typing import Any
from uuid import uuid4

from abis_grp_runtime.authorization import AuthorizationInput
from abis_grp_runtime.connector import BusinessConnectorPort
from abis_grp_runtime.context import RuntimeRequestContext
from abis_grp_runtime.core import RuntimeCore
from abis_grp_runtime.evidence import (
    OBSERVATION_CAUSE_UNKNOWN,
    OBSERVATION_RESULT_NOT_OBSERVED,
    OBSERVATION_RESULT_OBSERVED,
    OBSERVATION_SOURCE_ACTION_RESPONSE,
    OBSERVATION_SOURCE_LATER_READ,
    STRUCTURED_RESOURCE_OBSERVATION_DETAIL_KEY,
    FoundationTrace,
    StructuredResourceObservation,
    validate_structured_resource_observation,
)
from abis_grp_runtime.execution import ExecutionClass
from abis_grp_runtime.gateway.observe import execute_observe
from abis_grp_runtime.native_result import NativeResultEnvelope
from abis_grp_runtime.semantic import InteractionEnvelope, SemanticBoundaryInput, SemanticReference


class _PayloadConnector(BusinessConnectorPort):
    connector_id = "payload-test"

    def __init__(self, envelope: NativeResultEnvelope) -> None:
        self._envelope = envelope

    def execute(self, operation: str, operation_context: dict[str, Any]) -> NativeResultEnvelope:
        return self._envelope


def _minimal_semantic() -> SemanticBoundaryInput:
    cid = str(uuid4())
    return SemanticBoundaryInput(
        participant_ref=SemanticReference("implementation_participant", f"p-{cid}"),
        intent_ref=SemanticReference("implementation_intent", f"i-{cid}"),
        interaction=InteractionEnvelope(
            interaction_ref=SemanticReference("implementation_interaction", f"x-{cid}"),
            capability_ref=SemanticReference("implementation_capability", f"c-{cid}"),
            decision_ref=SemanticReference("implementation_decision", f"d-{cid}"),
        ),
    )


def _minimal_context() -> RuntimeRequestContext:
    return RuntimeRequestContext.create(
        agent_id="m18f-agent",
        execution_class=ExecutionClass.CONTROLLED_SIMULATOR,
    )


class StructuredResourceObservationEvidenceTest(unittest.TestCase):
    def test_legacy_trace_without_observation_unchanged(self) -> None:
        trace = FoundationTrace(correlation_id="c1", request_id="r1")
        trace.record("context", "ACCEPTED")
        serialized = trace.to_dict()
        self.assertEqual(len(serialized["events"]), 1)
        self.assertNotIn(STRUCTURED_RESOURCE_OBSERVATION_DETAIL_KEY, serialized["events"][0]["detail"])

    def test_action_time_observation_via_native_payload(self) -> None:
        observation_spec = {
            "subject_ref": "evidence-local-order-001",
            "observation_source": OBSERVATION_SOURCE_ACTION_RESPONSE,
            "observation_result": OBSERVATION_RESULT_OBSERVED,
            "observed_provider_state": "confirmed",
            "sequence_index": 1,
        }
        envelope = NativeResultEnvelope(
            technical_status="TRANSPORT_OK",
            external_status="CONFIRMED",
            external_identifier="evidence-local-order-001",
            source="synthetic",
            payload={STRUCTURED_RESOURCE_OBSERVATION_DETAIL_KEY: observation_spec},
        )
        core = RuntimeCore(connector=_PayloadConnector(envelope))
        result = core.process(
            _minimal_context(),
            _minimal_semantic(),
            AuthorizationInput(permission_token="ALLOW"),
            operation="reserve",
        )
        observations = result.trace.structured_resource_observations()
        self.assertEqual(len(observations), 1)
        self.assertEqual(observations[0].observation_result, OBSERVATION_RESULT_OBSERVED)
        self.assertEqual(result.outcome_disposition.disposition, "NOT_EVALUATED")

    def test_multiple_ordered_observations_do_not_overwrite(self) -> None:
        trace = FoundationTrace(correlation_id="duffel-shaped", request_id="r-duffel")
        subject = "evidence-local-order-duffel-01"
        entries = [
            StructuredResourceObservation(
                subject_ref=subject,
                observation_source=OBSERVATION_SOURCE_ACTION_RESPONSE,
                observation_result=OBSERVATION_RESULT_OBSERVED,
                observed_provider_state="created",
                sequence_index=1,
            ),
            StructuredResourceObservation(
                subject_ref=subject,
                observation_source=OBSERVATION_SOURCE_ACTION_RESPONSE,
                observation_result=OBSERVATION_RESULT_OBSERVED,
                observed_provider_state="cancellation_quoted",
                sequence_index=2,
            ),
            StructuredResourceObservation(
                subject_ref=subject,
                observation_source=OBSERVATION_SOURCE_LATER_READ,
                observation_result=OBSERVATION_RESULT_OBSERVED,
                observed_provider_state="cancelled",
                sequence_index=3,
            ),
        ]
        for entry in entries:
            trace.record_structured_resource_observation(entry)
        observations = trace.structured_resource_observations()
        self.assertEqual(len(observations), 3)
        self.assertEqual([o.sequence_index for o in observations], [1, 2, 3])
        self.assertEqual(observations[0].observed_provider_state, "created")
        self.assertEqual(observations[2].observed_provider_state, "cancelled")

    def test_negative_observation_without_causal_inference(self) -> None:
        err = validate_structured_resource_observation(
            {
                "subject_ref": "sq-order-01",
                "observation_source": OBSERVATION_SOURCE_LATER_READ,
                "observation_result": OBSERVATION_RESULT_NOT_OBSERVED,
                "observation_cause": "DELETED",
            }
        )
        self.assertIsNotNone(err)
        trace = FoundationTrace(correlation_id="square-shaped", request_id="r-square")
        subject = "evidence-local-order-square-01"
        trace.record_structured_resource_observation(
            StructuredResourceObservation(
                subject_ref=subject,
                observation_source=OBSERVATION_SOURCE_ACTION_RESPONSE,
                observation_result=OBSERVATION_RESULT_OBSERVED,
                observed_provider_state="DRAFT",
                sequence_index=1,
            )
        )
        for seq in (2, 3):
            trace.record_structured_resource_observation(
                StructuredResourceObservation(
                    subject_ref=subject,
                    observation_source=OBSERVATION_SOURCE_LATER_READ,
                    observation_result=OBSERVATION_RESULT_NOT_OBSERVED,
                    observation_cause=OBSERVATION_CAUSE_UNKNOWN,
                    sequence_index=seq,
                    local_processing_note="sanitizer_failed_after_read_2" if seq == 3 else None,
                )
            )
        observations = trace.structured_resource_observations()
        self.assertEqual(len(observations), 3)
        self.assertEqual(observations[1].observation_result, OBSERVATION_RESULT_NOT_OBSERVED)
        self.assertEqual(observations[1].observation_cause, OBSERVATION_CAUSE_UNKNOWN)
        self.assertNotIn("DELETED", observations[1].to_detail_dict().values())

    def test_resourceless_interaction_no_observation_events(self) -> None:
        envelope = NativeResultEnvelope(
            technical_status="FIXTURE_OK",
            external_status="AVAILABLE",
            source="fixture",
            payload={"operation": "check_availability", "fixture": True},
        )
        core = RuntimeCore(connector=_PayloadConnector(envelope))
        result = core.process(
            _minimal_context(),
            _minimal_semantic(),
            AuthorizationInput(permission_token="ALLOW"),
            operation="check_availability",
        )
        self.assertEqual(result.trace.structured_resource_observations(), [])

    def test_observe_emits_structured_observation(self) -> None:
        class _Adapter:
            business_system_identifier = "restaurant-sim"
            business_system_classification = "CONTROLLED_SIMULATOR"

            def get_connector(self) -> _PayloadConnector:
                return _PayloadConnector(
                    NativeResultEnvelope(
                        technical_status="TRANSPORT_OK",
                        external_status="PENDING",
                        external_identifier="ext-observe-001",
                        source="restaurant-simulator",
                        payload={
                            "crs_native_result": {
                                "transport_ok": True,
                                "status": "PENDING",
                                "reservation_id": "ext-observe-001",
                            }
                        },
                    )
                )

        class _Registry:
            def get_adapter(self, vertical: str, capability: str) -> _Adapter:
                return _Adapter()

        class _Service:
            registry = _Registry()

        response = execute_observe(
            _Service(),
            normalized={
                "vertical": "restaurant",
                "correlation_id": "corr-observe-m18f",
                "external_identifier": "ext-observe-001",
            },
            authorization_token="ALLOW",
        )
        trace = response.trace_reference
        events = [e for e in trace["events"] if e["phase"] == "resource_observation"]
        self.assertEqual(len(events), 1)
        blob = events[0]["detail"][STRUCTURED_RESOURCE_OBSERVATION_DETAIL_KEY]
        self.assertEqual(blob["observation_result"], OBSERVATION_RESULT_OBSERVED)
        self.assertEqual(response.outcome_disposition["disposition"], "NOT_EVALUATED")


if __name__ == "__main__":
    unittest.main()
