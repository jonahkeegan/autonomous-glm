"""
Propose command for CLI.

Provides the `glm propose` command to view and manage design system proposals.
"""

import click
from rich.console import Console

from ..errors import (
    ProposalNotFoundError,
    InvalidArgumentsError,
)
from ..formatters import (
    format_proposals_table,
    format_proposal_detail,
    output_json,
    print_info,
    print_success,
)
from ..progress import spinner_progress


console = Console()


@click.command()
@click.argument("proposal_id", required=False)
@click.option(
    "--diff",
    "-d",
    is_flag=True,
    help="Show before/after diff for proposals.",
)
@click.option(
    "--status",
    "-s",
    type=click.Choice(["pending", "approved", "rejected", "implemented"]),
    help="Filter proposals by status.",
)
@click.option(
    "--json",
    "output_json_flag",
    is_flag=True,
    help="Output results in JSON format.",
)
@click.option(
    "--approve",
    is_flag=True,
    help="Approve a pending proposal (requires PROPOSAL_ID).",
)
@click.option(
    "--reject",
    is_flag=True,
    help="Reject a pending proposal (requires PROPOSAL_ID).",
)
@click.pass_context
def propose(
    ctx: click.Context,
    proposal_id: str | None,
    diff: bool,
    status: str | None,
    output_json_flag: bool,
    approve: bool,
    reject: bool,
) -> None:
    """View and manage design system proposals.
    
    PROPOSAL_ID is the identifier of a specific proposal to view.
    
    Examples:
        glm propose                    List all proposals
        glm propose proposal_abc123    View a specific proposal
        glm propose --status pending   List pending proposals
        glm propose proposal_abc123 --diff
        glm propose proposal_abc123 --approve
        glm propose proposal_abc123 --reject
    """
    # Get global options from context
    global_json = ctx.obj.get("output_json", False)
    use_json = output_json_flag or global_json
    
    # Handle status changes
    if approve or reject:
        if proposal_id is None:
            raise InvalidArgumentsError(
                "PROPOSAL_ID is required for --approve or --reject",
                details="Specify the proposal ID to approve or reject.",
            )
        
        new_status = "approved" if approve else "rejected"
        _update_proposal_status(proposal_id, new_status)
        print_success(f"Proposal {proposal_id} {new_status}")
        return
    
    # List or view proposals
    if proposal_id:
        _show_proposal(proposal_id, show_diff=diff, use_json=use_json)
    else:
        _list_proposals(status=status, use_json=use_json)


def _list_proposals(status: str | None, use_json: bool) -> None:
    """List all proposals, optionally filtered by status.
    
    Args:
        status: Optional status filter
        use_json: Whether to output as JSON
    """
    from src.db.crud import list_proposals
    
    with spinner_progress("Fetching proposals..."):
        proposals = list_proposals(status=status, limit=100)
    
    # Convert to list of dicts
    proposals_data = []
    for p in proposals:
        if hasattr(p, "model_dump"):
            data = p.model_dump()
        elif hasattr(p, "__dict__"):
            data = p.__dict__
        else:
            data = dict(p)
        
        proposals_data.append({
            "id": data.get("id", "unknown"),
            "change_type": data.get("change_type", "-"),
            "target": data.get("target", data.get("token_name", "-")),
            "status": data.get("status", "pending"),
            "priority": data.get("priority", "-"),
        })
    
    if use_json:
        output_json(proposals_data)
    else:
        if proposals_data:
            table = format_proposals_table(proposals_data)
            console.print(table)
        else:
            status_msg = f" with status '{status}'" if status else ""
            print_info(f"No proposals found{status_msg}")


def _show_proposal(proposal_id: str, show_diff: bool, use_json: bool) -> None:
    """Show details of a specific proposal.
    
    Args:
        proposal_id: Proposal identifier
        show_diff: Whether to show before/after diff
        use_json: Whether to output as JSON
    """
    from src.db.crud import get_proposal
    
    with spinner_progress(f"Fetching proposal {proposal_id}..."):
        proposal = get_proposal(proposal_id)
        
        if proposal is None:
            raise ProposalNotFoundError(proposal_id)
        
        # Convert to dict
        if hasattr(proposal, "model_dump"):
            data = proposal.model_dump()
        elif hasattr(proposal, "__dict__"):
            data = proposal.__dict__
        else:
            data = dict(proposal)
    
    if use_json:
        output_json(data)
    else:
        # If diff requested, try to get before/after values
        if show_diff:
            data.setdefault("before", data.get("current_value", "-"))
            data.setdefault("after", data.get("proposed_value", "-"))
        
        panel = format_proposal_detail(data)
        console.print(panel)


def _update_proposal_status(proposal_id: str, new_status: str) -> None:
    """Update the status of a proposal.
    
    Args:
        proposal_id: Proposal identifier
        new_status: New status value
    """
    from src.db.crud import get_proposal, update_proposal
    
    # Verify proposal exists
    proposal = get_proposal(proposal_id)
    if proposal is None:
        raise ProposalNotFoundError(proposal_id)
    
    # Update status
    update_proposal(proposal_id, {"status": new_status})