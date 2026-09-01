"""Dev utility: creates one organization/project/agent/agent_config and prints a
usable API key + IDs. Not part of the product surface - Phase 3+ will replace this
with real project/agent management in the dashboard. Usage:

    python scripts/create_dev_project.py
"""

import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kosma_api.auth import hash_api_key
from kosma_api.db.session import SessionLocal
from kosma_api.models.agent import Agent
from kosma_api.models.agent_config import AgentConfig, AgentConfigKind
from kosma_api.models.organization import Organization
from kosma_api.models.project import Project


def main() -> None:
    db = SessionLocal()
    try:
        raw_api_key = f"kosma-dev-{secrets.token_hex(16)}"

        org = Organization(name="Dev Organization")
        db.add(org)
        db.flush()

        project = Project(organization_id=org.id, name="Dev Project", api_key_hash=hash_api_key(raw_api_key))
        db.add(project)
        db.flush()

        agent = Agent(project_id=project.id, name="Customer Support Agent")
        db.add(agent)
        db.flush()

        config = AgentConfig(
            agent_id=agent.id,
            kind=AgentConfigKind.model,
            version_label="baseline",
            model_provider="mock",
            model_name="mock-v1",
            is_baseline=True,
        )
        db.add(config)
        db.commit()

        print("Created dev project:")
        print(f"  KOSMA_API_KEY={raw_api_key}")
        print(f"  agent_id={agent.id}")
        print(f"  agent_config_id={config.id}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
