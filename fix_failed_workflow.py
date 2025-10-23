#!/usr/bin/env python3
"""
Recovery script to fix failed workflows.

This script resets workflows stuck in 'failed' phase back to 'plan_review'
so users can click "Approve Plan" again to retry code generation.

Usage:
    python fix_failed_workflow.py <workflow_id>
    python fix_failed_workflow.py --all

Examples:
    python fix_failed_workflow.py 2e945647-eb60-4109-b3a3-c4a6d878300c
    python fix_failed_workflow.py --all  # Fix all failed workflows
"""

import json
import sys
from pathlib import Path
from typing import List


def fix_workflow(workflow_id: str) -> bool:
    """
    Fix a single workflow by resetting it from 'failed' to 'plan_review' phase.

    Args:
        workflow_id: The workflow ID to fix

    Returns:
        True if fixed successfully, False otherwise
    """
    state_file = Path(f"storage/workflows/{workflow_id}_state.json")

    if not state_file.exists():
        print(f"❌ Workflow state file not found: {state_file}")
        return False

    try:
        # Read the state
        with open(state_file, 'r') as f:
            state = json.load(f)

        current_phase = state.get('phase', 'unknown')

        if current_phase != 'failed':
            print(f"⚠️  Workflow {workflow_id} is in '{current_phase}' phase (not 'failed')")
            print(f"   No changes needed.")
            return False

        # Reset to plan_review phase
        state['phase'] = 'plan_review'

        # Clear error message if exists
        if 'error_message' in state:
            state['error_message'] = None

        # Reset code generation attempts counter
        if 'code_generation_attempts' in state:
            state['code_generation_attempts'] = 0

        # Write back
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)

        print(f"✅ Fixed workflow {workflow_id}")
        print(f"   Phase changed: failed → plan_review")
        print(f"   User can now click 'Approve Plan' to retry code generation")

        return True

    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON in {state_file}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error fixing workflow {workflow_id}: {e}")
        return False


def find_all_failed_workflows() -> List[str]:
    """
    Find all workflows currently in 'failed' phase.

    Returns:
        List of workflow IDs that are in failed state
    """
    storage_dir = Path("storage/workflows")

    if not storage_dir.exists():
        print(f"❌ Storage directory not found: {storage_dir}")
        return []

    failed_workflows = []

    for state_file in storage_dir.glob("*_state.json"):
        try:
            with open(state_file, 'r') as f:
                state = json.load(f)

            if state.get('phase') == 'failed':
                # Extract workflow ID from filename
                workflow_id = state_file.stem.replace('_state', '')
                failed_workflows.append(workflow_id)

        except Exception as e:
            print(f"⚠️  Error reading {state_file}: {e}")
            continue

    return failed_workflows


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    arg = sys.argv[1]

    if arg == "--all":
        print("Finding all failed workflows...")
        failed_workflows = find_all_failed_workflows()

        if not failed_workflows:
            print("✅ No failed workflows found!")
            return

        print(f"\nFound {len(failed_workflows)} failed workflow(s):\n")

        for workflow_id in failed_workflows:
            fix_workflow(workflow_id)
            print()

        print(f"✅ Fixed {len(failed_workflows)} workflow(s)")

    else:
        # Single workflow ID provided
        workflow_id = arg
        success = fix_workflow(workflow_id)

        if success:
            print("\n✅ Workflow recovery complete!")
            print("   User can now:")
            print("   1. Refresh the page")
            print("   2. Click 'Approve Plan' to retry code generation")
            print("   3. Or click 'Request Changes' to modify the plan first")
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
