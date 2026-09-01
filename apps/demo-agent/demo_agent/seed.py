"""Generates the seeded historical corpus: real executions of the demo agent
(baseline + candidate config), submitted through the actual SDK -> ingestion API
-> Postgres path, then backdated so they look like real history rather than all
having the same timestamp.

Backdating is a deliberate, documented exception to "the ingestion API doesn't
accept a client-supplied timestamp": every trace's content (query, retrieved
docs, tool result, generated answer, success/failure) is a real execution of the
deterministic mock agent - nothing about the trace's substance is fabricated,
only its created_at is adjusted after the fact so the corpus reads as history
instead of one burst of activity. This corpus is clearly DEMO DATA throughout
the product (see PRODUCT-SPEC.md); it is not presented as production traffic.

Usage (with the API running locally):
    apps/api/.venv/Scripts/python apps/demo-agent/demo_agent/seed.py
"""

import json
import random
import sys
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

DEMO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DEMO_ROOT))
API_ROOT = Path(__file__).resolve().parents[2] / "api"
sys.path.insert(0, str(API_ROOT))

from kosma.client import KosmaClient  # noqa: E402

from demo_agent import agent, setup_project  # noqa: E402
from demo_agent.agent import REGIONS, WORKFLOWS  # noqa: E402
from demo_agent.mock_provider import REGION_WEIGHTS, WORKFLOW_WEIGHTS  # noqa: E402

CREDENTIALS_PATH = DEMO_ROOT / ".demo_credentials.json"

BASELINE_TRACE_COUNT = 1400
BASELINE_DAY_RANGE = (5, 60)  # "older" history, days ago

CANDIDATE_TRACE_COUNT = 300
CANDIDATE_DAY_RANGE = (0, 5)  # recent canary rollout, days ago

SEED = 20260901  # fixed seed - the corpus is reproducible, not different every run


def _load_or_create_credentials() -> dict:
    if CREDENTIALS_PATH.exists():
        return json.loads(CREDENTIALS_PATH.read_text())
    setup_project.main()
    return json.loads(CREDENTIALS_PATH.read_text())


def _weighted_choice(rng: random.Random, weights: dict) -> str:
    return rng.choices(list(weights.keys()), weights=list(weights.values()), k=1)[0]


def _generate_batch(
    *,
    count: int,
    day_range: tuple[int, int],
    is_candidate: bool,
    credentials: dict,
    client: "KosmaClient",
    rng: random.Random,
) -> list[tuple[str, datetime]]:
    """Runs `count` agent executions, returns [(trace_ref, backdated_timestamp)]."""
    config_id = credentials["candidate_config_id"] if is_candidate else credentials["baseline_config_id"]
    results = []
    for i in range(count):
        workflow = _weighted_choice(rng, WORKFLOW_WEIGHTS)
        region = _weighted_choice(rng, REGION_WEIGHTS)

        trace_ref = agent.run_once(
            workflow=workflow,
            region=region,
            agent_id=credentials["agent_id"],
            agent_config_id=config_id,
            is_candidate=is_candidate,
            client=client,
            rng=rng,
        )

        days_ago = rng.uniform(*day_range)
        jitter = timedelta(hours=rng.uniform(0, 23), minutes=rng.uniform(0, 59))
        timestamp = datetime.now(timezone.utc) - timedelta(days=days_ago) - jitter
        results.append((trace_ref, timestamp))

        if (i + 1) % 100 == 0:
            print(f"  {'candidate' if is_candidate else 'baseline'}: {i + 1}/{count}")

    return results


def _backdate_timestamps(pairs: list[tuple[str, datetime]]) -> None:
    import psycopg

    from kosma_api.config import get_settings

    settings = get_settings()
    dsn = settings.database_url.replace("postgresql+psycopg://", "postgresql://")
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.executemany(
                "UPDATE traces SET created_at = %s WHERE trace_ref = %s",
                [(ts, ref) for ref, ts in pairs],
            )
        conn.commit()


def _print_summary(credentials: dict) -> None:
    import psycopg

    from kosma_api.config import get_settings

    settings = get_settings()
    dsn = settings.database_url.replace("postgresql+psycopg://", "postgresql://")
    with psycopg.connect(dsn) as conn:
        rows = conn.execute(
            """
            SELECT ac.version_label, t.workflow_tag, t.segment_tags->>'region',
                   count(*), avg(case when t.success then 1.0 else 0.0 end)
            FROM traces t JOIN agent_configs ac ON ac.id = t.agent_config_id
            WHERE t.agent_id = %s
            GROUP BY ac.version_label, t.workflow_tag, t.segment_tags->>'region'
            ORDER BY 1, 2, 3
            """,
            (credentials["agent_id"],),
        ).fetchall()

    print("\nSeeded corpus summary (config | workflow | region | count | success rate):")
    for version_label, workflow, region, count, success_rate in rows:
        print(f"  {version_label:30s} {workflow:15s} {region:15s} {count:5d}  {success_rate:.0%}")


def _clear_existing_traces(agent_id: str) -> None:
    """Makes reruns safe: a prior run that crashed partway through (or a
    deliberate reseed) shouldn't leave stray traces mixed in with a fresh batch."""
    import psycopg

    from kosma_api.config import get_settings

    settings = get_settings()
    dsn = settings.database_url.replace("postgresql+psycopg://", "postgresql://")
    with psycopg.connect(dsn, autocommit=True) as conn:
        deleted = conn.execute("DELETE FROM traces WHERE agent_id = %s", (agent_id,)).rowcount
    if deleted:
        print(f"Cleared {deleted} traces from a previous run.")


def main() -> None:
    credentials = _load_or_create_credentials()
    _clear_existing_traces(credentials["agent_id"])
    client = KosmaClient(api_key=credentials["api_key"])
    rng = random.Random(SEED)

    start = time.time()
    print(f"Generating {BASELINE_TRACE_COUNT} baseline traces...")
    baseline_pairs = _generate_batch(
        count=BASELINE_TRACE_COUNT,
        day_range=BASELINE_DAY_RANGE,
        is_candidate=False,
        credentials=credentials,
        client=client,
        rng=rng,
    )

    print(f"Generating {CANDIDATE_TRACE_COUNT} candidate (canary) traces...")
    candidate_pairs = _generate_batch(
        count=CANDIDATE_TRACE_COUNT,
        day_range=CANDIDATE_DAY_RANGE,
        is_candidate=True,
        credentials=credentials,
        client=client,
        rng=rng,
    )

    print("Backdating timestamps...")
    _backdate_timestamps(baseline_pairs + candidate_pairs)

    elapsed = time.time() - start
    print(f"Done in {elapsed:.1f}s.")
    _print_summary(credentials)


if __name__ == "__main__":
    main()
