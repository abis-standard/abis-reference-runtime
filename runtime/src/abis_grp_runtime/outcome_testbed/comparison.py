"""Deterministic expected vs observed comparison engine."""

from __future__ import annotations

from typing import Any, Mapping

from abis_grp_runtime.outcome_testbed.models import ComparisonResult, EvaluationTrace, ExpectedState
from abis_grp_runtime.outcome_testbed.observed import extract_observed_state, native_result_snapshot
from abis_grp_runtime.outcome_testbed.patterns import (
    EVALUATION_MATCH,
    EVALUATION_MISMATCH,
    PATTERN_BUSINESS_REJECTED,
    PATTERN_CONSTRAINT_MISMATCH,
    PATTERN_DUPLICATE_IDEMPOTENT,
    PATTERN_EXACT_MATCH,
    PATTERN_NO_AVAILABILITY,
    PATTERN_PARTIAL_RESULT,
    PATTERN_PENDING,
    PATTERN_TECHNICAL_ERROR,
    PATTERN_TECHNICAL_SUCCESS_BUSINESS_MISMATCH,
    PATTERN_TIMEOUT,
    SEMANTIC_AUTHORITY,
)


def _compare_fields(
    expected: ExpectedState,
    observed: Mapping[str, Any],
) -> tuple[tuple[str, ...], tuple[str, ...], dict[str, Any], dict[str, Any]]:
    matched: list[str] = []
    mismatched: list[str] = []
    expected_values: dict[str, Any] = {}
    observed_values: dict[str, Any] = {}

    for field_name in expected.comparable_fields():
        exp_val = expected.value(field_name)
        obs_val = observed.get(field_name) if hasattr(observed, "get") else getattr(observed, field_name, None)
        expected_values[field_name] = exp_val
        observed_values[field_name] = obs_val
        if exp_val == obs_val:
            matched.append(field_name)
        else:
            mismatched.append(field_name)

    return tuple(matched), tuple(mismatched), expected_values, observed_values


def _result(
    *,
    evaluation: str,
    pattern: str,
    matched: tuple[str, ...],
    mismatched: tuple[str, ...],
    expected_values: dict[str, Any],
    observed_values: dict[str, Any],
    technical_disposition: str,
    native_status: str | None,
    correlation_id: str,
) -> ComparisonResult:
    return ComparisonResult(
        evaluation=evaluation,
        pattern=pattern,
        matched_fields=matched,
        mismatched_fields=mismatched,
        expected_values=expected_values,
        observed_values=observed_values,
        technical_disposition=technical_disposition,
        native_status=native_status,
        correlation_id=correlation_id,
        semantic_authority=SEMANTIC_AUTHORITY,
    )


class OutcomeResultPatternTestbed:
    """
    Private Outcome Result Pattern Testbed (M-204).

    Derives evaluation from expected vs observed state and Native Result signals.
    Does not treat Simulator scenario labels as semantic authority.
    """

    def evaluate(
        self,
        expected: ExpectedState,
        native_result: Mapping[str, Any],
        *,
        correlation_id: str = "testbed",
    ) -> tuple[ComparisonResult, EvaluationTrace]:
        native = dict(native_result)
        observed = extract_observed_state(native)
        transport_ok = bool(native.get("transport_ok"))
        error = native.get("error")
        status = native.get("status")
        technical = "TRANSPORT_OK" if transport_ok else "TRANSPORT_FAILED"

        trace = EvaluationTrace(
            correlation_id=correlation_id,
            expected_state=expected,
            native_result_reference=native_result_snapshot(native),
        )

        if native.get("idempotent_replay"):
            result = _result(
                evaluation=EVALUATION_MATCH,
                pattern=PATTERN_DUPLICATE_IDEMPOTENT,
                matched=(),
                mismatched=(),
                expected_values={},
                observed_values={},
                technical_disposition=technical,
                native_status=status,
                correlation_id=correlation_id,
            )
            trace.compared_fields = ()
            trace.evaluation_disposition = result.evaluation
            trace.pattern = result.pattern
            return result, trace

        if not transport_ok:
            pattern = PATTERN_TIMEOUT if error == "TIMEOUT" else PATTERN_TECHNICAL_ERROR
            result = _result(
                evaluation=pattern,
                pattern=pattern,
                matched=(),
                mismatched=(),
                expected_values={},
                observed_values={},
                technical_disposition=technical,
                native_status=status,
                correlation_id=correlation_id,
            )
            trace.evaluation_disposition = result.evaluation
            trace.pattern = result.pattern
            return result, trace

        if error == "NO_AVAILABILITY":
            result = _result(
                evaluation=PATTERN_NO_AVAILABILITY,
                pattern=PATTERN_NO_AVAILABILITY,
                matched=(),
                mismatched=(),
                expected_values={},
                observed_values={},
                technical_disposition=technical,
                native_status=status,
                correlation_id=correlation_id,
            )
            trace.evaluation_disposition = result.evaluation
            trace.pattern = result.pattern
            return result, trace

        if error == "CONSTRAINT_MISMATCH":
            result = _result(
                evaluation=PATTERN_CONSTRAINT_MISMATCH,
                pattern=PATTERN_CONSTRAINT_MISMATCH,
                matched=(),
                mismatched=(),
                expected_values={},
                observed_values={},
                technical_disposition=technical,
                native_status=status,
                correlation_id=correlation_id,
            )
            trace.evaluation_disposition = result.evaluation
            trace.pattern = result.pattern
            return result, trace

        if error == "BUSINESS_REJECTED":
            result = _result(
                evaluation=PATTERN_BUSINESS_REJECTED,
                pattern=PATTERN_BUSINESS_REJECTED,
                matched=(),
                mismatched=(),
                expected_values={},
                observed_values={},
                technical_disposition=technical,
                native_status=status,
                correlation_id=correlation_id,
            )
            trace.evaluation_disposition = result.evaluation
            trace.pattern = result.pattern
            return result, trace

        if status == "PENDING":
            result = _result(
                evaluation=PATTERN_PENDING,
                pattern=PATTERN_PENDING,
                matched=(),
                mismatched=(),
                expected_values={},
                observed_values={},
                technical_disposition=technical,
                native_status=status,
                correlation_id=correlation_id,
            )
            trace.evaluation_disposition = result.evaluation
            trace.pattern = result.pattern
            return result, trace

        if observed.partial:
            matched, mismatched, exp_vals, obs_vals = _compare_fields(expected, observed)
            trace.compared_fields = expected.comparable_fields()
            trace.matched_fields = matched
            trace.mismatched_fields = mismatched
            result = _result(
                evaluation=PATTERN_PARTIAL_RESULT,
                pattern=PATTERN_PARTIAL_RESULT,
                matched=matched,
                mismatched=mismatched,
                expected_values=exp_vals,
                observed_values=obs_vals,
                technical_disposition=technical,
                native_status=status,
                correlation_id=correlation_id,
            )
            trace.evaluation_disposition = result.evaluation
            trace.pattern = result.pattern
            return result, trace

        matched, mismatched, exp_vals, obs_vals = _compare_fields(expected, observed)
        trace.compared_fields = expected.comparable_fields()
        trace.matched_fields = matched
        trace.mismatched_fields = mismatched

        if not mismatched:
            result = _result(
                evaluation=EVALUATION_MATCH,
                pattern=PATTERN_EXACT_MATCH,
                matched=matched,
                mismatched=mismatched,
                expected_values=exp_vals,
                observed_values=obs_vals,
                technical_disposition=technical,
                native_status=status,
                correlation_id=correlation_id,
            )
        elif transport_ok and status == "CONFIRMED":
            result = _result(
                evaluation=EVALUATION_MISMATCH,
                pattern=PATTERN_TECHNICAL_SUCCESS_BUSINESS_MISMATCH,
                matched=matched,
                mismatched=mismatched,
                expected_values=exp_vals,
                observed_values=obs_vals,
                technical_disposition=technical,
                native_status=status,
                correlation_id=correlation_id,
            )
        else:
            result = _result(
                evaluation=EVALUATION_MISMATCH,
                pattern=EVALUATION_MISMATCH,
                matched=matched,
                mismatched=mismatched,
                expected_values=exp_vals,
                observed_values=obs_vals,
                technical_disposition=technical,
                native_status=status,
                correlation_id=correlation_id,
            )

        trace.evaluation_disposition = result.evaluation
        trace.pattern = result.pattern
        return result, trace
