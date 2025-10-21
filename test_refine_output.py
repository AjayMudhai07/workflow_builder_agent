#!/usr/bin/env python3
"""
Test script to verify the refine-output endpoint works correctly.
This script will:
1. Find a workflow in output_review phase
2. Test the refine-output endpoint with sample feedback
"""

import requests
import json
import sys

API_BASE = "http://localhost:8000/api/v1"

def get_workflows():
    """Get all workflows."""
    response = requests.get(f"{API_BASE}/workflows")
    response.raise_for_status()
    return response.json()["workflows"]

def get_workflow_status(workflow_id):
    """Get workflow status."""
    response = requests.get(f"{API_BASE}/workflows/{workflow_id}")
    response.raise_for_status()
    return response.json()

def test_refine_output(workflow_id, feedback):
    """Test the refine-output endpoint."""
    print(f"\n{'='*80}")
    print(f"Testing refine-output endpoint for workflow: {workflow_id}")
    print(f"{'='*80}")

    # Get workflow status before
    status_before = get_workflow_status(workflow_id)
    print(f"\n✓ Workflow phase: {status_before['phase']}")
    print(f"✓ Output file: {status_before.get('output_file_path', 'N/A')}")
    print(f"✓ Refinement iterations: {status_before.get('output_refinement_iterations', 0)}")

    if status_before['phase'] != 'output_review':
        print(f"\n⚠ Warning: Workflow is not in output_review phase, skipping test")
        return False

    # Test refine-output endpoint
    print(f"\n📝 Sending refinement request with feedback: {feedback[:50]}...")

    try:
        response = requests.post(
            f"{API_BASE}/workflows/{workflow_id}/refine-output",
            json={"feedback": feedback},
            timeout=180  # 3 minutes timeout for AI to generate and execute code
        )

        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ SUCCESS! Refinement completed")
            print(f"✓ Status: {result['status']}")
            print(f"✓ Phase: {result['phase']}")
            print(f"✓ Refinement iteration: {result.get('refinement_iteration', 'N/A')}")
            print(f"✓ New output path: {result.get('output_path', 'N/A')}")

            if result.get('code'):
                print(f"✓ Generated code length: {len(result['code'])} characters")

            return True
        else:
            print(f"\n❌ FAILED with status {response.status_code}")
            try:
                error_detail = response.json()
                print(f"Error: {error_detail}")
            except:
                print(f"Error: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print(f"\n⏱ TIMEOUT: Request took longer than 3 minutes")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False

def main():
    """Main test function."""
    print("=" * 80)
    print("REFINE OUTPUT ENDPOINT TEST")
    print("=" * 80)

    # Get all workflows
    print("\n📋 Fetching workflows...")
    workflows = get_workflows()
    print(f"✓ Found {len(workflows)} total workflows")

    # Find workflows in output_review phase
    output_review_workflows = [
        w for w in workflows
        if w['phase'] == 'output_review'
    ]

    if not output_review_workflows:
        print("\n⚠ No workflows found in output_review phase")
        print("Please complete a workflow to the output_review phase first")
        return 1

    print(f"✓ Found {len(output_review_workflows)} workflow(s) in output_review phase")

    # Test the first one
    workflow = output_review_workflows[0]
    print(f"\n📊 Testing workflow: {workflow['name']}")
    print(f"   ID: {workflow['workflow_id']}")
    print(f"   Phase: {workflow['phase']}")

    # Sample feedback for testing
    feedback = "Please add a summary row at the end showing the total count of exceptions."

    success = test_refine_output(workflow['workflow_id'], feedback)

    if success:
        print(f"\n{'='*80}")
        print("✅ TEST PASSED: Refine-output endpoint is working correctly!")
        print(f"{'='*80}")
        return 0
    else:
        print(f"\n{'='*80}")
        print("❌ TEST FAILED: Refine-output endpoint has issues")
        print(f"{'='*80}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
