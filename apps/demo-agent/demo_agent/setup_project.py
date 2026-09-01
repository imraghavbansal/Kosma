"""Creates the demo organization/project/agent and its two agent_configs
(baseline + the regressing candidate), writing credentials to
.demo_credentials.json (gitignored) for seed.py to read.

Requires apps/api's virtualenv (imports kosma_api models directly) - run from
that venv, e.g.:
    apps/api/.venv/Scripts/python apps/demo-agent/demo_agent/setup_project.py
"""

import json
import secrets
import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[2] / "api"
sys.path.insert(0, str(API_ROOT))

from kosma_api.auth import hash_api_key  # noqa: E402
from kosma_api.db.session import SessionLocal  # noqa: E402
from kosma_api.models.agent import Agent  # noqa: E402
from kosma_api.models.agent_config import AgentConfig, AgentConfigKind  # noqa: E402
from kosma_api.models.organization import Organization  # noqa: E402
from kosma_api.models.project import Project  # noqa: E402

CREDENTIALS_PATH = Path(__file__).resolve().parents[1] / ".demo_credentials.json"

BASELINE_PROMPT = """You are a customer support agent for an e-commerce company.
For refund requests: check the refund policy. Domestic orders are refunded to
the original payment method within 5 business days. International orders may
have customs/duties adjustments and require the customs declaration number
before a refund is issued - ask for it if it's not on file, and explain the
difference to the customer.
For order status requests: use the order status tool and report the current
status and expected timeline honestly, including delays.
For account changes: confirm exactly what was changed."""

CANDIDATE_PROMPT = """You are a customer support agent for an e-commerce company.
Be fast and concise. For refund requests: if eligible, confirm the refund and
tell the customer it will arrive within 5 business days. For order status
requests: reassure the customer their order is on the way. For account
changes: confirm the change was made."""


def main() -> None:
    db = SessionLocal()
    try:
        raw_api_key = f"kosma-demo-{secrets.token_hex(16)}"

        org = Organization(name="Kosma Demo")
        db.add(org)
        db.flush()

        project = Project(
            organization_id=org.id, name="Kosma Demo - Customer Support", api_key_hash=hash_api_key(raw_api_key)
        )
        db.add(project)
        db.flush()

        agent = Agent(
            project_id=project.id,
            name="Customer Support Agent",
            description="DEMO DATA - synthetic customer-support agent seeded for Kosma's own demo.",
        )
        db.add(agent)
        db.flush()

        baseline = AgentConfig(
            agent_id=agent.id,
            kind=AgentConfigKind.prompt,
            version_label="v1-baseline",
            prompt_text=BASELINE_PROMPT,
            model_provider="mock",
            model_name="mock-v1",
            is_baseline=True,
        )
        candidate = AgentConfig(
            agent_id=agent.id,
            kind=AgentConfigKind.prompt,
            version_label="v2-simplified-refund-policy",
            prompt_text=CANDIDATE_PROMPT,
            model_provider="mock",
            model_name="mock-v1",
            is_baseline=False,
        )
        db.add_all([baseline, candidate])
        db.commit()

        credentials = {
            "org_id": str(org.id),
            "project_id": str(project.id),
            "agent_id": str(agent.id),
            "baseline_config_id": str(baseline.id),
            "candidate_config_id": str(candidate.id),
            "api_key": raw_api_key,
        }
        CREDENTIALS_PATH.write_text(json.dumps(credentials, indent=2))
        print(f"Demo project created. Credentials written to {CREDENTIALS_PATH}")
        print(json.dumps(credentials, indent=2))
    finally:
        db.close()


if __name__ == "__main__":
    main()
