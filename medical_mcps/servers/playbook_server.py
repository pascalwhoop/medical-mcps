#!/usr/bin/env python3
"""
Drug Repurposing Playbook MCP Server

Exposes playbooks and playbook execution tools via MCP.
Playbooks provide structured strategies for navigating biomedical data trails.
"""

import logging
from typing import Optional

from mcp.server.fastmcp import FastMCP
from ..med_mcp_server import unified_mcp, tool as medmcps_tool

from ..playbooks.definitions import (
    PLAYBOOKS,
    get_playbook,
    list_playbooks,
    get_playbook_steps,
    Playbook,
    PlaybookStep,
)

logger = logging.getLogger(__name__)

# Create FastMCP server for Playbooks
playbook_mcp = FastMCP(
    "drug-repurposing-playbooks",
    stateless_http=True,
    json_response=True,
)


@medmcps_tool(name="playbook_list_all", servers=[playbook_mcp, unified_mcp])
async def list_all_playbooks() -> dict:
    """List all available drug repurposing playbooks.

    Returns:
        JSON with list of playbook IDs, names, descriptions, and starting points
    """
    logger.info("Tool invoked: list_all_playbooks()")
    try:
        playbook_list = []
        for playbook_id in list_playbooks():
            playbook = get_playbook(playbook_id)
            if playbook:
                playbook_list.append({
                    "playbook_id": playbook["playbook_id"],
                    "name": playbook["name"],
                    "description": playbook["description"],
                    "starting_point": playbook["starting_point"],
                    "first_principles_framework": playbook.get("first_principles_framework"),
                })
        
        return {
            "playbooks": playbook_list,
            "count": len(playbook_list),
        }
    except Exception as e:
        logger.error(f"Tool failed: list_all_playbooks() - {e}", exc_info=True)
        return {"error": f"Error listing playbooks: {str(e)}"}


@medmcps_tool(name="playbook_get_details", servers=[playbook_mcp, unified_mcp])
async def get_playbook_details(playbook_id: str) -> dict:
    """Get detailed information about a specific playbook.

    Args:
        playbook_id: ID of the playbook (e.g., 'drug_centric', 'disease_centric', 'pathway_centric')

    Returns:
        JSON with complete playbook definition including all steps, tools, and criteria
    """
    logger.info(f"Tool invoked: get_playbook_details(playbook_id='{playbook_id}')")
    try:
        playbook = get_playbook(playbook_id)
        if not playbook:
            return {
                "error": f"Playbook '{playbook_id}' not found",
                "available_playbooks": list_playbooks(),
            }
        
        # Convert to JSON-serializable format
        result = {
            "playbook_id": playbook["playbook_id"],
            "name": playbook["name"],
            "description": playbook["description"],
            "starting_point": playbook["starting_point"],
            "first_principles_framework": playbook.get("first_principles_framework"),
            "steps": [
                {
                    "step_id": step["step_id"],
                    "step_type": step["step_type"].value if hasattr(step["step_type"], "value") else str(step["step_type"]),
                    "description": step["description"],
                    "tool_suggestions": step["tool_suggestions"],
                    "criteria": step.get("criteria"),
                    "outputs": step["outputs"],
                }
                for step in playbook["steps"]
            ],
            "expected_outputs": playbook["expected_outputs"],
            "convergence_criteria": playbook.get("convergence_criteria"),
        }
        
        return result
    except Exception as e:
        logger.error(f"Tool failed: get_playbook_details(playbook_id='{playbook_id}') - {e}", exc_info=True)
        return {"error": f"Error getting playbook details: {str(e)}"}


@medmcps_tool(name="playbook_get_steps", servers=[playbook_mcp, unified_mcp])
async def get_playbook_steps_tool(playbook_id: str) -> dict:
    """Get the steps for a specific playbook.

    Args:
        playbook_id: ID of the playbook

    Returns:
        JSON with list of steps, each including step_id, type, description, tool suggestions, and criteria
    """
    logger.info(f"Tool invoked: get_playbook_steps(playbook_id='{playbook_id}')")
    try:
        steps = get_playbook_steps(playbook_id)
        if steps is None:
            return {
                "error": f"Playbook '{playbook_id}' not found",
                "available_playbooks": list_playbooks(),
            }
        
        return {
            "playbook_id": playbook_id,
            "steps": [
                {
                    "step_id": step["step_id"],
                    "step_type": step["step_type"].value if hasattr(step["step_type"], "value") else str(step["step_type"]),
                    "description": step["description"],
                    "tool_suggestions": step["tool_suggestions"],
                    "criteria": step.get("criteria"),
                    "outputs": step["outputs"],
                }
                for step in steps
            ],
            "step_count": len(steps),
        }
    except Exception as e:
        logger.error(f"Tool failed: get_playbook_steps(playbook_id='{playbook_id}') - {e}", exc_info=True)
        return {"error": f"Error getting playbook steps: {str(e)}"}


@medmcps_tool(name="playbook_execute_step", servers=[playbook_mcp, unified_mcp])
async def execute_playbook_step(
    playbook_id: str,
    step_id: str,
    inputs: dict,
    tool_results: Optional[dict] = None,
) -> dict:
    """Execute a single step of a playbook.

    This tool provides guidance on how to execute a playbook step, including:
    - Which MCP tools to use
    - What criteria to apply
    - What outputs to produce

    Args:
        playbook_id: ID of the playbook
        step_id: ID of the step to execute
        inputs: Input data for this step (e.g., {'drug_name': 'ocrelizumab'})
        tool_results: Optional results from previous tool calls (for chaining steps)

    Returns:
        JSON with execution guidance, tool suggestions, and expected outputs
    """
    logger.info(f"Tool invoked: execute_playbook_step(playbook_id='{playbook_id}', step_id='{step_id}')")
    try:
        playbook = get_playbook(playbook_id)
        if not playbook:
            return {
                "error": f"Playbook '{playbook_id}' not found",
                "available_playbooks": list_playbooks(),
            }
        
        # Find the step
        step = None
        for s in playbook["steps"]:
            if s["step_id"] == step_id:
                step = s
                break
        
        if not step:
            return {
                "error": f"Step '{step_id}' not found in playbook '{playbook_id}'",
                "available_steps": [s["step_id"] for s in playbook["steps"]],
            }
        
        # Build execution guidance
        guidance = {
            "playbook_id": playbook_id,
            "step_id": step_id,
            "step_type": step["step_type"].value if hasattr(step["step_type"], "value") else str(step["step_type"]),
            "description": step["description"],
            "inputs_received": inputs,
            "tool_suggestions": step["tool_suggestions"],
            "criteria": step.get("criteria"),
            "expected_outputs": step["outputs"],
            "execution_notes": _get_execution_notes(step, playbook),
        }
        
        return guidance
    except Exception as e:
        logger.error(
            f"Tool failed: execute_playbook_step(playbook_id='{playbook_id}', step_id='{step_id}') - {e}",
            exc_info=True,
        )
        return {"error": f"Error executing playbook step: {str(e)}"}


@medmcps_tool(name="playbook_compare_strategies", servers=[playbook_mcp, unified_mcp])
async def compare_playbook_strategies(
    starting_point: Optional[str] = None,
    disease: Optional[str] = None,
) -> dict:
    """Compare different playbook strategies to identify which ones are most suitable.

    Args:
        starting_point: What you're starting with ('drug', 'disease', 'target', 'pathway', etc.)
        disease: Optional disease name to filter relevant playbooks

    Returns:
        JSON comparing playbooks, their approaches, and recommendations
    """
    logger.info(f"Tool invoked: compare_playbook_strategies(starting_point='{starting_point}', disease='{disease}')")
    try:
        all_playbooks = []
        for playbook_id in list_playbooks():
            playbook = get_playbook(playbook_id)
            if playbook:
                # Filter by starting point if provided
                if starting_point and playbook["starting_point"] != starting_point:
                    continue
                
                all_playbooks.append({
                    "playbook_id": playbook["playbook_id"],
                    "name": playbook["name"],
                    "starting_point": playbook["starting_point"],
                    "description": playbook["description"],
                    "first_principles_framework": playbook.get("first_principles_framework"),
                    "step_count": len(playbook["steps"]),
                })
        
        # Generate recommendations
        recommendations = []
        if starting_point:
            recommendations.append(
                f"Found {len(all_playbooks)} playbook(s) starting from '{starting_point}'"
            )
        else:
            recommendations.append(
                "Consider running multiple playbooks in parallel to triangulate on promising candidates"
            )
        
        if disease:
            recommendations.append(
                f"For disease '{disease}', consider: disease_centric, pathway_centric, and genetic_centric playbooks"
            )
        
        return {
            "playbooks": all_playbooks,
            "count": len(all_playbooks),
            "recommendations": recommendations,
            "convergence_strategy": (
                "Run multiple playbooks independently and compare results. "
                "Candidates identified by multiple playbooks have higher confidence."
            ),
        }
    except Exception as e:
        logger.error(f"Tool failed: compare_playbook_strategies() - {e}", exc_info=True)
        return {"error": f"Error comparing playbook strategies: {str(e)}"}


def _get_execution_notes(step: PlaybookStep, playbook: Playbook) -> str:
    """Generate execution notes for a playbook step"""
    notes = []
    
    step_type = step["step_type"]
    if hasattr(step_type, "value"):
        step_type_str = step_type.value
    else:
        step_type_str = str(step_type)
    
    if step_type_str == "query":
        notes.append("Use the suggested tools to query APIs and gather data.")
        notes.append("Be thorough - gather all relevant information, not just primary mechanisms.")
    elif step_type_str == "analyze":
        notes.append("Analyze the gathered data according to the criteria.")
        notes.append("Look for patterns, connections, and unexpected relationships.")
    elif step_type_str == "filter":
        notes.append("Apply filtering criteria strictly but be conservative.")
        notes.append("When uncertain, prefer inclusion over exclusion.")
    elif step_type_str == "hypothesize":
        notes.append("Generate testable mechanistic hypotheses.")
        notes.append("Connect drug mechanisms to disease pathophysiology.")
        notes.append("Consider both primary and secondary effects.")
    elif step_type_str == "validate":
        notes.append("Check evidence from multiple sources: literature, trials, databases.")
        notes.append("Look for both supporting and contradicting evidence.")
    elif step_type_str == "synthesize":
        notes.append("Synthesize findings from all previous steps.")
        notes.append("Create a coherent narrative connecting drug to disease.")
    
    # Add playbook-specific notes
    if playbook["playbook_id"] == "drug_centric":
        notes.append("CRITICAL: Review ALL activities from ChEMBL, not just primary mechanism.")
        notes.append("Secondary/off-target effects are often repurposing opportunities.")
    elif playbook["playbook_id"] == "disease_centric":
        notes.append("Focus on understanding disease pathophysiology first.")
        notes.append("Prioritize pathways with GWAS validation.")
    elif playbook["playbook_id"] == "pathway_centric":
        notes.append("Consider pathway network effects, not just individual targets.")
        notes.append("Evaluate pathway restoration, not just target binding.")
    
    return " ".join(notes)

