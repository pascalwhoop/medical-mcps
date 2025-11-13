"""
Drug Repurposing Playbooks

Structured strategies for navigating biomedical data to discover drug repurposing opportunities.
Each playbook represents a different "data trail" or navigation strategy.
"""

from .definitions import (
    PLAYBOOKS,
    get_playbook,
    get_playbook_steps,
    list_playbooks,
)

__all__ = [
    "PLAYBOOKS",
    "get_playbook",
    "list_playbooks",
    "get_playbook_steps",
]
