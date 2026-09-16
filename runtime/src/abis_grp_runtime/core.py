"""Runtime core — minimal orchestration pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from abis_grp_runtime.authorization import AuthorizationDisposition, AuthorizationInput, evaluate_authorization
from abis_grp_runtime.connector import BusinessConnectorPort, FixtureConnector, NullConnector
from abis_grp_runtime.context import RuntimeRequestContext
from abis_grp_runtime.control_plane import control_plane_allows
from abis_grp_runtime.evidence import FoundationTrace
from abis_grp_runtime.execution import ExecutionClass, ExecutionDisposition, resolve_execution_disposition
from abis_grp_runtime.native_result import NativeResultEnvelope
from abis_grp_runtime.outcome import NullOutcomeInterpreter, OutcomeInterpretationDisposition, OutcomeInterpreterPort
from abis_grp_runtime.semantic import SemanticBoundaryInput


@dataclass(frozen=True)
class RuntimePipelineResult:
    """Pipeline result — operational dispositions, not normative ABIS Outcome."""

    context: RuntimeRequestContext
    authorization: AuthorizationDisposition
    execution: ExecutionDisposition
    control_plane_pass: bool
    native_result: NativeResultEnvelope | None
    outcome_disposition: OutcomeInterpretationDisposition | None
    trace: FoundationTrace
    halted: bool
    halt_reason: str | None = None


class RuntimeCore:
    """
    Minimal orchestration pipeline:

    request → context → authorization → semantic envelope → execution disposition
    → connector boundary → native result → outcome interpreter boundary → evidence trace
    """

    def __init__(
        self,
        *,
        connector: BusinessConnectorPort | None = None,
        outcome_interpreter: OutcomeInterpreterPort | None = None,
    ) -> None:
        self._connector = connector or NullConnector()
        self._outcome_interpreter = outcome_interpreter or NullOutcomeInterpreter()

    def _select_connector(self, execution_class: ExecutionClass) -> BusinessConnectorPort:
        if execution_class is ExecutionClass.FIXTURE:
            return FixtureConnector()
        if execution_class is ExecutionClass.CONTROLLED_SIMULATOR:
            return self._connector
        return NullConnector()

    def process(
        self,
        context: RuntimeRequestContext,
        semantic_input: SemanticBoundaryInput,
        authorization_input: AuthorizationInput,
        operation: str = "check_availability",
        operation_context: Mapping[str, Any] | None = None,
    ) -> RuntimePipelineResult:
        trace = FoundationTrace(
            correlation_id=context.correlation_id,
            request_id=context.request_id,
        )
        trace.record("context", "ACCEPTED", agent_id=context.agent_id)

        authorization = evaluate_authorization(authorization_input)
        trace.record("authorization", authorization.state.value, reason=authorization.reason)
        if not authorization.allowed:
            return RuntimePipelineResult(
                context=context,
                authorization=authorization,
                execution=resolve_execution_disposition(context.execution_class),
                control_plane_pass=False,
                native_result=None,
                outcome_disposition=None,
                trace=trace,
                halted=True,
                halt_reason=authorization.reason,
            )

        trace.record("semantic_boundary", "ACCEPTED", interaction_id=semantic_input.interaction.interaction_ref.object_id)

        execution = resolve_execution_disposition(context.execution_class)
        trace.record("execution_disposition", execution.policy.value, execution_class=execution.execution_class.value)
        if not execution.allowed:
            return RuntimePipelineResult(
                context=context,
                authorization=authorization,
                execution=execution,
                control_plane_pass=False,
                native_result=None,
                outcome_disposition=None,
                trace=trace,
                halted=True,
                halt_reason=execution.reason,
            )

        cp_ok, cp_reason = control_plane_allows(context.execution_class)
        trace.record("control_plane", "PASS" if cp_ok else "DENY", reason=cp_reason)
        if not cp_ok:
            return RuntimePipelineResult(
                context=context,
                authorization=authorization,
                execution=execution,
                control_plane_pass=False,
                native_result=None,
                outcome_disposition=None,
                trace=trace,
                halted=True,
                halt_reason=cp_reason,
            )

        connector = self._select_connector(context.execution_class)
        trace.record("connector_attempt", "START", connector_id=connector.connector_id, operation=operation)

        op_ctx = dict(operation_context or {})
        try:
            native_result = connector.execute(operation, op_ctx)
        except Exception as exc:  # pragma: no cover - defensive boundary
            trace.record("connector_attempt", "DENY", reason=str(exc))
            return RuntimePipelineResult(
                context=context,
                authorization=authorization,
                execution=execution,
                control_plane_pass=True,
                native_result=None,
                outcome_disposition=None,
                trace=trace,
                halted=True,
                halt_reason=str(exc),
            )
        if native_result.technical_status == "TRANSPORT_FAILED" and (
            native_result.payload or {}
        ).get("error") == "unsupported_operation":
            trace.record("connector_attempt", "DENY", reason=f"unsupported operation: {operation}")
            return RuntimePipelineResult(
                context=context,
                authorization=authorization,
                execution=execution,
                control_plane_pass=True,
                native_result=None,
                outcome_disposition=None,
                trace=trace,
                halted=True,
                halt_reason=f"unsupported operation: {operation}",
            )
        trace.record(
            "native_result",
            native_result.technical_status,
            external_status=native_result.external_status,
            source=native_result.source,
        )

        outcome = self._outcome_interpreter.interpret(semantic_input, native_result)
        trace.record("outcome_interpreter", outcome.disposition, reason=outcome.reason)

        return RuntimePipelineResult(
            context=context,
            authorization=authorization,
            execution=execution,
            control_plane_pass=True,
            native_result=native_result,
            outcome_disposition=outcome,
            trace=trace,
            halted=False,
        )
