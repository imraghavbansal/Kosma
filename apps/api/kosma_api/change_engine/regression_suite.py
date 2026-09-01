"""Turns the worst regressions an impact report found into regression_tests -
concrete input/expected-condition pairs an engineer can point a real test
runner at later (execution itself is V2, see docs/development-plan.md - V1
generates the test spec, matching PRODUCT-SPEC.md's V1 scope)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from kosma_api.models.impact_evidence import ImpactEvidence
from kosma_api.models.regression_test import RegressionTest
from kosma_api.models.trace import Trace

MAX_TESTS_PER_REPORT = 10


def generate_from_impact_report(db: Session, *, impact_report_id, project_id) -> list[RegressionTest]:
    regressed_evidence = db.scalars(
        select(ImpactEvidence).where(
            ImpactEvidence.impact_report_id == impact_report_id, ImpactEvidence.note == "regressed"
        )
    ).all()

    tests: list[RegressionTest] = []
    for evidence in regressed_evidence[:MAX_TESTS_PER_REPORT]:
        baseline_trace = db.get(Trace, evidence.baseline_trace_id)
        replay_trace = db.get(Trace, evidence.replay_trace_id)
        if baseline_trace is None:
            continue

        context_snapshot = {
            "workflow": baseline_trace.workflow_tag,
            "segment_tags": baseline_trace.segment_tags,
            "baseline_trace_id": str(baseline_trace.id),
            "replay_trace_id": str(replay_trace.id) if replay_trace else None,
        }
        test = RegressionTest(
            project_id=project_id,
            impact_report_id=impact_report_id,
            source_trace_id=baseline_trace.id,
            input_text=baseline_trace.input_text,
            context_snapshot=context_snapshot,
            expected_condition=(
                f"Must succeed on {baseline_trace.workflow_tag} "
                f"({evidence.segment}) the way the baseline config did - "
                f"this input succeeded under baseline and failed under the "
                f"candidate config during replay."
            ),
            baseline_output=None,
        )
        db.add(test)
        tests.append(test)

    db.commit()
    for test in tests:
        db.refresh(test)
    return tests
