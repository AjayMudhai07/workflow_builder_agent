"""
Test script for the IRA Workflow Builder Orchestrator.

This script tests the complete end-to-end workflow:
1. Planner Agent gathering requirements through interview
2. Business Logic Plan generation
3. Coder Agent generating and executing production code
4. State persistence and error handling
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ira_builder.orchestrator import (
    create_orchestrator,
    WorkflowPhase
)
from ira_builder.utils.logger import setup_logging, get_logger
from ira_builder.agents.planner import PlannerResponseType

# Setup logging
setup_logging(log_level="INFO", pretty_print=True)
logger = get_logger(__name__)


# =============================================================================
# TEST CONFIGURATION
# =============================================================================

# Simple test workflow
TEST_WORKFLOW_NAME = "Simple_Test_Workflow"
TEST_WORKFLOW_DESCRIPTION = "Load FBL3N CSV, convert dates, and save all records to output"
TEST_CSV_FILES = ["tests/fixtures/sample_csvs/FBL3N.csv"]
TEST_OUTPUT_FILENAME = "orchestrator_test_result.csv"

# Pre-defined answers for Planner questions (for automated testing)
# These will be used to answer Planner's questions automatically
AUTOMATED_ANSWERS = [
    "A",  # Usually answer to first question about workflow approach
    "A",  # Usually answer to second question
    "A",  # Usually answer to third question
    "A",  # Usually answer to output structure question
    "A",  # Usually answer to final review question (generate plan)
]


# =============================================================================
# TEST ORCHESTRATOR WITH AUTOMATED RESPONSES
# =============================================================================

async def test_orchestrator_automated():
    """
    Test orchestrator with automated responses.

    This simulates a complete workflow execution with pre-defined answers.
    """
    print("\n" + "=" * 80)
    print("IRA WORKFLOW BUILDER - ORCHESTRATOR TEST (AUTOMATED)")
    print("=" * 80)
    print()

    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ ERROR: OPENAI_API_KEY not found in .env file")
        return False

    print(f"✓ Found API key: {api_key[:20]}...")
    print()

    # Verify test CSV exists
    csv_file = TEST_CSV_FILES[0]
    if not Path(csv_file).exists():
        print(f"❌ ERROR: Test CSV not found: {csv_file}")
        return False

    print(f"✓ Test CSV found: {csv_file}")
    print()

    # Create orchestrator
    print("Creating Orchestrator...")
    try:
        orchestrator = create_orchestrator(
            workflow_name=TEST_WORKFLOW_NAME,
            workflow_description=TEST_WORKFLOW_DESCRIPTION,
            csv_filepaths=TEST_CSV_FILES,
            output_filename=TEST_OUTPUT_FILENAME,
            model="gpt-4o",  # or "o4-mini" if that's your model
            max_planner_questions=10,
            max_coder_iterations=3,
            code_execution_timeout=120,
            on_phase_change=lambda phase: print(f"📍 Phase changed to: {phase.value}"),
            on_planner_response=lambda resp, resp_type: print(f"💬 Planner responded ({resp_type.value})")
        )
        print("✓ Orchestrator created")
        print()
    except Exception as e:
        print(f"❌ Failed to create Orchestrator: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    # Start workflow (Planner initialization)
    print("-" * 80)
    print("PHASE 1: PLANNING - Starting Planner Agent")
    print("-" * 80)
    print()

    try:
        start_result = await orchestrator.start()

        if start_result['status'] != 'success':
            print(f"❌ Failed to start workflow: {start_result.get('error')}")
            return False

        print("✓ Workflow started successfully")
        print()
        print("First Response from Planner:")
        print("-" * 80)
        print(start_result['response'])
        print("-" * 80)
        print()

    except Exception as e:
        print(f"❌ Exception during workflow start: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    # Answer Planner's questions automatically
    answer_index = 0
    max_iterations = 15  # Safety limit

    for iteration in range(max_iterations):
        print(f"\n{'='*80}")
        print(f"ITERATION {iteration + 1}")
        print(f"{'='*80}\n")

        # Check current phase
        current_phase = orchestrator.state.phase

        if current_phase == WorkflowPhase.PLAN_REVIEW:
            print("✓ Business Logic Plan generated!")
            print()
            print("Business Logic Plan:")
            print("-" * 80)
            print(orchestrator.state.business_logic_plan[:500] + "...")
            print("-" * 80)
            print()
            break

        elif current_phase == WorkflowPhase.PLANNING:
            # Provide automated answer
            if answer_index < len(AUTOMATED_ANSWERS):
                user_answer = AUTOMATED_ANSWERS[answer_index]
                answer_index += 1
            else:
                # Default to Option A if we run out of predefined answers
                user_answer = "A"

            print(f"Providing answer: {user_answer}")
            print()

            try:
                result = await orchestrator.process_user_input(user_answer)

                if result['status'] != 'success':
                    print(f"❌ Error processing input: {result.get('error')}")
                    return False

                print("Planner Response:")
                print("-" * 80)
                print(result['response'][:500])
                if len(result['response']) > 500:
                    print("... (response truncated)")
                print("-" * 80)
                print()

                print(f"Questions asked: {result['questions_asked']}")
                print(f"Response type: {result['response_type']}")
                print()

            except Exception as e:
                print(f"❌ Exception processing user input: {str(e)}")
                import traceback
                traceback.print_exc()
                return False

        else:
            print(f"❌ Unexpected phase: {current_phase.value}")
            return False

    # Check if we got to plan review phase
    if orchestrator.state.phase != WorkflowPhase.PLAN_REVIEW:
        print("❌ Failed to reach PLAN_REVIEW phase")
        return False

    # Approve plan and start code generation
    print("\n" + "=" * 80)
    print("PHASE 2: CODING - Approving Plan and Starting Code Generation")
    print("=" * 80)
    print()

    try:
        print("Approving plan and starting code generation...")
        print("This will:")
        print("  1. Initialize Coder Agent")
        print("  2. Generate Python pandas code with IRA preprocessing")
        print("  3. Validate syntax")
        print("  4. Execute the code")
        print("  5. Validate output")
        print("  6. Retry if errors (up to 3 times)")
        print()
        print("Please wait...\n")

        result = await orchestrator.approve_plan_and_generate_code()

        print("\n" + "=" * 80)
        print("RESULT")
        print("=" * 80)
        print()

        if result['status'] == 'success':
            print("✅ SUCCESS - Complete workflow executed successfully!")
            print()
            print(f"Phase: {result['phase']}")
            print(f"Iterations: {result['iterations']}")
            print(f"Output File: {result['output_path']}")
            print(f"Code File: {result['code_filepath']}")
            print(f"Execution Time: {result['execution_time']:.2f} seconds")
            print()

            # Show code preview
            print("-" * 80)
            print("Generated Code (first 30 lines):")
            print("-" * 80)
            code_lines = result['code'].split('\n')
            for i, line in enumerate(code_lines[:30], 1):
                print(f"{i:3d} | {line}")
            if len(code_lines) > 30:
                print(f"... ({len(code_lines) - 30} more lines)")
            print()

            # Show output preview
            if result.get('output_preview'):
                print("-" * 80)
                print("Output Preview:")
                print("-" * 80)
                print(result['output_preview'])
                print()

            # Show workflow summary
            print("-" * 80)
            print("Workflow Summary:")
            print("-" * 80)
            summary = orchestrator.get_workflow_summary()
            print(f"Workflow: {summary['workflow_name']}")
            print(f"Started: {summary['started_at']}")
            print(f"Completed: {summary['completed_at']}")
            print(f"Successful: {summary['is_successful']}")
            print(f"Planner Questions: {summary['planner_summary']['questions_asked']}")
            print(f"Coder Iterations: {summary['coder_summary']['iterations']}")
            print()

            return True

        else:
            print("❌ FAILED - Code generation failed")
            print()
            print(f"Error: {result.get('error')}")
            print(f"Iterations: {result.get('iterations', 0)}")
            print()

            if result.get('last_code'):
                print("-" * 80)
                print("Last Generated Code (first 30 lines):")
                print("-" * 80)
                code_lines = result['last_code'].split('\n')
                for i, line in enumerate(code_lines[:30], 1):
                    print(f"{i:3d} | {line}")
                print()

            return False

    except Exception as e:
        print(f"❌ Exception during code generation: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


# =============================================================================
# TEST ORCHESTRATOR WITH INTERACTIVE MODE
# =============================================================================

async def test_orchestrator_interactive():
    """
    Test orchestrator with interactive user input.

    This allows manual testing of the workflow.
    """
    print("\n" + "=" * 80)
    print("IRA WORKFLOW BUILDER - ORCHESTRATOR TEST (INTERACTIVE)")
    print("=" * 80)
    print()

    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ ERROR: OPENAI_API_KEY not found in .env file")
        return False

    print(f"✓ Found API key: {api_key[:20]}...")
    print()

    # Get workflow details from user
    workflow_name = input("Workflow Name (or press Enter for default): ").strip()
    if not workflow_name:
        workflow_name = TEST_WORKFLOW_NAME

    workflow_description = input("Workflow Description (or press Enter for default): ").strip()
    if not workflow_description:
        workflow_description = TEST_WORKFLOW_DESCRIPTION

    # Verify test CSV exists
    csv_file = TEST_CSV_FILES[0]
    if not Path(csv_file).exists():
        print(f"❌ ERROR: Test CSV not found: {csv_file}")
        return False

    print(f"✓ Using CSV: {csv_file}")
    print()

    # Create orchestrator
    print("Creating Orchestrator...")
    orchestrator = create_orchestrator(
        workflow_name=workflow_name,
        workflow_description=workflow_description,
        csv_filepaths=TEST_CSV_FILES,
        output_filename=TEST_OUTPUT_FILENAME,
        model="gpt-4o",
    )
    print("✓ Orchestrator created")
    print()

    # Start workflow
    print("-" * 80)
    print("Starting Planner Agent...")
    print("-" * 80)
    print()

    start_result = await orchestrator.start()

    if start_result['status'] != 'success':
        print(f"❌ Failed to start: {start_result.get('error')}")
        return False

    print(start_result['response'])
    print()

    # Interactive Q&A loop
    while orchestrator.state.phase == WorkflowPhase.PLANNING:
        user_input = input("\nYour answer: ").strip()

        if not user_input:
            continue

        result = await orchestrator.process_user_input(user_input)

        if result['status'] != 'success':
            print(f"❌ Error: {result.get('error')}")
            continue

        print()
        print(result['response'])
        print()

        if result['response_type'] == PlannerResponseType.BUSINESS_LOGIC_PLAN.value:
            print("\n✓ Business Logic Plan generated!")
            break

    # Plan review
    if orchestrator.is_plan_ready():
        print("\n" + "=" * 80)
        print("Business Logic Plan is ready!")
        print("=" * 80)
        print()

        approve = input("Approve plan and generate code? (yes/no): ").strip().lower()

        if approve == 'yes' or approve == 'y':
            print("\nGenerating code...")
            result = await orchestrator.approve_plan_and_generate_code()

            if result['status'] == 'success':
                print("\n✅ SUCCESS!")
                print(f"Output: {result['output_path']}")
                print(f"Code: {result['code_filepath']}")
                return True
            else:
                print(f"\n❌ FAILED: {result.get('error')}")
                return False

    return False


# =============================================================================
# MAIN
# =============================================================================

async def main():
    """Main entry point."""
    print("\n" + "=" * 80)
    print("IRA WORKFLOW BUILDER ORCHESTRATOR TEST")
    print("=" * 80)
    print()

    print("Test Modes:")
    print("  1. Automated (uses pre-defined answers)")
    print("  2. Interactive (manual input)")
    print()

    mode = input("Select mode (1 or 2, default=1): ").strip()

    if mode == "2":
        success = await test_orchestrator_interactive()
    else:
        success = await test_orchestrator_automated()

    print("\n" + "=" * 80)
    if success:
        print("✅ TEST PASSED")
    else:
        print("❌ TEST FAILED")
    print("=" * 80)
    print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\nTest failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
