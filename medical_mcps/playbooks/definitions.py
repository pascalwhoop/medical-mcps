"""
Playbook Definitions

Each playbook defines a systematic strategy for drug repurposing discovery.
Playbooks can be executed independently or in parallel to triangulate on promising candidates.

Playbooks are loaded from YAML files in this directory (one file per playbook).
"""

from enum import Enum
from pathlib import Path
from typing import Optional, TypedDict

import yaml


class PlaybookStepType(str, Enum):
    """Types of steps in a playbook"""

    QUERY = "query"  # Query an API or database
    ANALYZE = "analyze"  # Analyze results
    FILTER = "filter"  # Filter results based on criteria
    HYPOTHESIZE = "hypothesize"  # Generate mechanistic hypotheses
    VALIDATE = "validate"  # Validate against evidence
    SYNTHESIZE = "synthesize"  # Synthesize findings


class PlaybookStep(TypedDict):
    """A single step in a playbook"""

    step_id: str
    step_type: PlaybookStepType
    description: str
    tool_suggestions: list[str]  # Suggested MCP tools to use
    criteria: Optional[dict]  # Filtering or evaluation criteria
    outputs: list[str]  # What this step produces


class Playbook(TypedDict):
    """A complete playbook definition"""

    playbook_id: str
    name: str
    description: str
    starting_point: str  # What you start with (drug, disease, target, pathway, etc.)
    first_principles_framework: Optional[str]  # Academic framework this follows
    steps: list[PlaybookStep]
    expected_outputs: list[str]
    convergence_criteria: Optional[dict]  # When to consider this playbook successful


# ============================================================================
# LOAD PLAYBOOKS FROM YAML FILES
# ============================================================================


def _load_playbooks() -> dict[str, Playbook]:
    """Load all playbooks from YAML files in this directory"""
    playbooks_dir = Path(__file__).parent
    playbooks: dict[str, Playbook] = {}

    # Find all YAML files (excluding __init__.py, definitions.py, py.typed)
    yaml_files = sorted(playbooks_dir.glob("*.yaml"))

    for yaml_file in yaml_files:
        with open(yaml_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Convert step_type strings to PlaybookStepType enum
        for step in data.get("steps", []):
            step_type_str = step.get("step_type", "")
            try:
                step["step_type"] = PlaybookStepType(step_type_str)
            except ValueError:
                raise ValueError(
                    f"Invalid step_type '{step_type_str}' in {yaml_file}. "
                    f"Must be one of: {[e.value for e in PlaybookStepType]}"
                )

        playbook_id = data.get("playbook_id")
        if not playbook_id:
            raise ValueError(f"Missing playbook_id in {yaml_file}")

        playbooks[playbook_id] = data  # type: ignore

    return playbooks


PLAYBOOKS: dict[str, Playbook] = _load_playbooks()


def get_playbook(playbook_id: str) -> Optional[Playbook]:
    """Get a playbook by ID"""
    return PLAYBOOKS.get(playbook_id)


def list_playbooks() -> list[str]:
    """List all available playbook IDs"""
    return list(PLAYBOOKS.keys())


def get_playbook_steps(playbook_id: str) -> Optional[list[PlaybookStep]]:
    """Get steps for a playbook"""
    playbook = get_playbook(playbook_id)
    return playbook["steps"] if playbook else None
