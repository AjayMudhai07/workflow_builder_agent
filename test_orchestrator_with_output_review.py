"""
End-to-End Test for IRA Workflow Builder Orchestrator with Output Review

This script tests the complete workflow including:
1. Planner Agent - Requirements gathering
2. Business Logic Plan generation and approval
3. Coder Agent - Code generation and execution
4. Output Review - User feedback and refinement
5. Final approval and workflow completion
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

TEST_WORKFLOW_NAME = "Sales_Summary_Test"
TEST_WORKFLOW_DESCRIPTION = "Load FBL3N CSV, group by vendor, calculate totals, and save results"
TEST_CSV_FILES = ["tests/fixtures/sample_csvs/FBL3N.csv"]
TEST_OUTPUT_FILENAME = "sales_summary_output.csv"

# Pre-defined answers for Planner (automated mode)
PLANNER_AUTOMATED_ANSWERS = [
    "A",  # First question
    "A",  # Second question
    "A",  # Third question
    "A",  # Output structure question
    "A",  # Generate plan
]

# Refinement feedback for output review
OUTPUT_REFINEMENT_FEEDBACK = """
I noticed the output needs some improvements:
1. Add a new column called 'average_amount' that shows the average transaction amount per vendor
2. Sort the results by total amount in descending order (highest first)
3. Add a column showing the percentage each vendor contributes to the total
"""

# Second refinement (if needed)
SECOND_REFINEMENT_FEEDBACK = """
Great! Now please also:
1. Add a 'transaction_count' column showing the number of transactions per vendor
2. Filter to only show vendors with total amount > 100
"""


# =============================================================================
# AUTOMATED TEST FUNCTION
# =============================================================================

async def test_orchestrator_with_output_review():
    """
    Test complete orchestrator workflow with output review and refinement.
    """
    print("\n" + "=" * 80)
    print("IRA ORCHESTRATOR - END-TO-END TEST WITH OUTPUT REVIEW")
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

    # ==========================================================================
    # CREATE ORCHESTRATOR
    # ==========================================================================
    print("Creating Orchestrator...")
    try:
        orchestrator = create_orchestrator(
            workflow_name=TEST_WORKFLOW_NAME,
            workflow_description=TEST_WORKFLOW_DESCRIPTION,
            csv_filepaths=TEST_CSV_FILES,
            output_filename=TEST_OUTPUT_FILENAME,
            model="gpt-4o",
            max_planner_questions=10,
            max_coder_iterations=3,
            code_execution_timeout=120,
            on_phase_change=lambda phase: print(f"\n📍 Phase changed to: {phase.value}\n"),
        )
        print("✓ Orchestrator created")
        print()
    except Exception as e:
        print(f"❌ Failed to create Orchestrator: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    # ==========================================================================
    # PHASE 1: PLANNING
    # ==========================================================================
    print("\n" + "=" * 80)
    print("PHASE 1: PLANNING - Gathering Requirements")
    print("=" * 80)
    print()

    try:
        start_result = await orchestrator.start()

        if start_result['status'] != 'success':
            print(f"❌ Failed to start workflow: {start_result.get('error')}")
            return False

        print("✓ Workflow started successfully")
        print()
        print("Planner's First Question:")
        print("-" * 80)
        print(start_result['response'][:500])
        if len(start_result['response']) > 500:
            print("... (truncated)")
        print("-" * 80)
        print()

    except Exception as e:
        print(f"❌ Exception during workflow start: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    # Answer Planner's questions automatically
    answer_index = 0
    max_planning_iterations = 15

    for iteration in range(max_planning_iterations):
        if orchestrator.state.phase == WorkflowPhase.PLAN_REVIEW:
            print("✓ Business Logic Plan generated!")
            break

        if orchestrator.state.phase == WorkflowPhase.PLANNING:
            # Provide automated answer
            if answer_index < len(PLANNER_AUTOMATED_ANSWERS):
                user_answer = PLANNER_AUTOMATED_ANSWERS[answer_index]
                answer_index += 1
            else:
                user_answer = "A"  # Default to Option A

            print(f"Iteration {iteration + 1}: Answering '{user_answer}'")

            try:
                result = await orchestrator.process_user_input(user_answer)

                if result['status'] != 'success':
                    print(f"❌ Error processing input: {result.get('error')}")
                    return False

                print(f"  ✓ Questions asked: {result['questions_asked']}")
                print(f"  ✓ Response type: {result['response_type']}")
                print()

            except Exception as e:
                print(f"❌ Exception processing input: {str(e)}")
                import traceback
                traceback.print_exc()
                return False

    # ==========================================================================
    # PHASE 2: PLAN REVIEW
    # ==========================================================================
    if orchestrator.state.phase != WorkflowPhase.PLAN_REVIEW:
        print("❌ Failed to reach PLAN_REVIEW phase")
        return False

    print("\n" + "=" * 80)
    print("PHASE 2: PLAN REVIEW")
    print("=" * 80)
    print()

    print("Business Logic Plan (preview):")
    print("-" * 80)
    print(orchestrator.state.business_logic_plan[:600])
    print("... (truncated)")
    print("-" * 80)
    print()

    print("✓ Approving Business Logic Plan...")
    print()

    # ==========================================================================
    # PHASE 3: CODE GENERATION
    # ==========================================================================
    print("\n" + "=" * 80)
    print("PHASE 3: CODE GENERATION & EXECUTION")
    print("=" * 80)
    print()

    try:
        result = await orchestrator.approve_plan_and_generate_code()

        if result['status'] != 'success':
            print(f"❌ Code generation failed: {result.get('error')}")
            return False

        print("✅ Code generated and executed successfully!")
        print()
        print(f"✓ Phase: {result['phase']}")
        print(f"✓ Iterations: {result['iterations']}")
        print(f"✓ Output path: {result['output_path']}")
        print(f"✓ Code saved to: {result['code_filepath']}")
        print()

        # Show output preview
        if result.get('output_preview'):
            print("📊 Output Preview:")
            print("-" * 80)
            print(result['output_preview'])
            print("-" * 80)
            print()

        # Show output summary
        if result.get('output_summary'):
            summary = result['output_summary']
            print("📈 Output Summary:")
            print(f"  - Rows: {summary.get('row_count', 'N/A'):,}")
            print(f"  - Columns: {summary.get('column_count', 'N/A')}")
            print(f"  - Column Names: {', '.join(summary.get('columns', []))}")
            print()

    except Exception as e:
        print(f"❌ Exception during code generation: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    # ==========================================================================
    # PHASE 4: OUTPUT REVIEW (Initial)
    # ==========================================================================
    if orchestrator.state.phase != WorkflowPhase.OUTPUT_REVIEW:
        print(f"❌ Expected OUTPUT_REVIEW phase, got: {orchestrator.state.phase.value}")
        return False

    print("\n" + "=" * 80)
    print("PHASE 4: OUTPUT REVIEW - Initial Review")
    print("=" * 80)
    print()

    print("✓ Output is ready for review!")
    print()
    print("Simulating user feedback for refinement...")
    print()
    print("User Feedback:")
    print("-" * 80)
    print(OUTPUT_REFINEMENT_FEEDBACK)
    print("-" * 80)
    print()

    # ==========================================================================
    # REFINEMENT 1
    # ==========================================================================
    print("\n" + "=" * 80)
    print("REFINEMENT #1 - Applying User Feedback")
    print("=" * 80)
    print()

    try:
        refine_result = await orchestrator.refine_output(OUTPUT_REFINEMENT_FEEDBACK)

        if refine_result['status'] != 'success':
            print(f"❌ Refinement failed: {refine_result.get('error')}")
            return False

        print("✅ Output refined successfully!")
        print()
        print(f"✓ Refinement iteration: {refine_result['refinement_iteration']}")
        print(f"✓ Output path: {refine_result['output_path']}")
        print(f"✓ Updated code saved to: {refine_result['code_filepath']}")
        print()

        # Show updated output preview
        if refine_result.get('output_preview'):
            print("📊 Updated Output Preview:")
            print("-" * 80)
            print(refine_result['output_preview'])
            print("-" * 80)
            print()

        # Show updated summary
        if refine_result.get('output_summary'):
            summary = refine_result['output_summary']
            print("📈 Updated Output Summary:")
            print(f"  - Rows: {summary.get('row_count', 'N/A'):,}")
            print(f"  - Columns: {summary.get('column_count', 'N/A')}")
            print(f"  - Column Names: {', '.join(summary.get('columns', []))}")
            print()

    except Exception as e:
        print(f"❌ Exception during refinement: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    # ==========================================================================
    # REFINEMENT 2 (Optional - demonstrate multiple refinements)
    # ==========================================================================
    print("\n" + "=" * 80)
    print("REFINEMENT #2 - Additional Changes (Optional)")
    print("=" * 80)
    print()

    print("Simulating additional user feedback...")
    print()
    print("User Feedback:")
    print("-" * 80)
    print(SECOND_REFINEMENT_FEEDBACK)
    print("-" * 80)
    print()

    try:
        refine_result_2 = await orchestrator.refine_output(SECOND_REFINEMENT_FEEDBACK)

        if refine_result_2['status'] != 'success':
            print(f"⚠️  Second refinement failed: {refine_result_2.get('error')}")
            print("Continuing with first refinement result...")
        else:
            print("✅ Second refinement successful!")
            print()
            print(f"✓ Refinement iteration: {refine_result_2['refinement_iteration']}")
            print(f"✓ Output path: {refine_result_2['output_path']}")
            print()

            # Show updated output preview
            if refine_result_2.get('output_preview'):
                print("📊 Final Output Preview:")
                print("-" * 80)
                print(refine_result_2['output_preview'])
                print("-" * 80)
                print()

    except Exception as e:
        print(f"⚠️  Exception during second refinement: {str(e)}")
        print("Continuing with first refinement result...")

    # ==========================================================================
    # PHASE 5: FINAL APPROVAL & COMPLETION
    # ==========================================================================
    print("\n" + "=" * 80)
    print("PHASE 5: FINAL APPROVAL & COMPLETION")
    print("=" * 80)
    print()

    print("User approves the output...")
    print()

    try:
        final_result = await orchestrator.approve_output_and_complete()

        if final_result['status'] != 'success':
            print(f"❌ Failed to complete workflow: {final_result.get('error')}")
            return False

        print("✅ WORKFLOW COMPLETED SUCCESSFULLY!")
        print()
        print(f"✓ Phase: {final_result['phase']}")
        print(f"✓ Execution time: {final_result['execution_time']:.2f} seconds")
        print(f"✓ Output path: {final_result['output_path']}")
        print(f"✓ Is successful: {final_result['is_successful']}")
        print()

    except Exception as e:
        print(f"❌ Exception during workflow completion: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    # ==========================================================================
    # WORKFLOW SUMMARY
    # ==========================================================================
    print("\n" + "=" * 80)
    print("WORKFLOW SUMMARY")
    print("=" * 80)
    print()

    summary = orchestrator.get_workflow_summary()

    print(f"Workflow Name: {summary['workflow_name']}")
    print(f"Phase: {summary['phase']}")
    print(f"Started: {summary['started_at']}")
    print(f"Completed: {summary['completed_at']}")
    print(f"Successful: {summary['is_successful']}")
    print()

    print("Planner Summary:")
    print(f"  - Questions asked: {summary['planner_summary']['questions_asked']}")
    print(f"  - Plan approved: {summary['planner_summary']['plan_approved']}")
    print()

    print("Coder Summary:")
    print(f"  - Code iterations: {summary['coder_summary']['iterations']}")
    print(f"  - Output path: {summary['coder_summary']['output_path']}")
    print()

    print("Output Review Summary:")
    print(f"  - Output approved: {summary['output_review_summary']['output_approved']}")
    print(f"  - Refinement iterations: {summary['output_review_summary']['refinement_iterations']}")
    print(f"  - Feedback entries: {len(summary['output_review_summary']['feedback_history'])}")
    print()

    # Show refinement history
    if summary['output_review_summary']['feedback_history']:
        print("Refinement History:")
        for entry in summary['output_review_summary']['feedback_history']:
            print(f"  [{entry['iteration']}] {entry['timestamp']}")
            print(f"      Feedback: {entry['feedback'][:100]}...")
            print()

    return True


# =============================================================================
# INTERACTIVE MODE (Optional)
# =============================================================================

async def test_orchestrator_interactive():
    """
    Interactive test mode where user provides real input.
    """
    print("\n" + "=" * 80)
    print("IRA ORCHESTRATOR - INTERACTIVE TEST WITH OUTPUT REVIEW")
    print("=" * 80)
    print()

    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ ERROR: OPENAI_API_KEY not found in .env file")
        return False

    print(f"✓ Found API key: {api_key[:20]}...")
    print()

    # Get workflow details
    workflow_name = input("Workflow Name (or press Enter for default): ").strip()
    if not workflow_name:
        workflow_name = TEST_WORKFLOW_NAME

    workflow_description = input("Workflow Description (or press Enter for default): ").strip()
    if not workflow_description:
        workflow_description = TEST_WORKFLOW_DESCRIPTION

    # Verify CSV
    csv_file = TEST_CSV_FILES[0]
    if not Path(csv_file).exists():
        print(f"❌ ERROR: Test CSV not found: {csv_file}")
        return False

    print(f"✓ Using CSV: {csv_file}")
    print()

    # Create orchestrator
    orchestrator = create_orchestrator(
        workflow_name=workflow_name,
        workflow_description=workflow_description,
        csv_filepaths=TEST_CSV_FILES,
        output_filename=TEST_OUTPUT_FILENAME,
        model="gpt-4o",
    )

    # Planning phase
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

    # Interactive Q&A
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
            break

    # Plan review
    if orchestrator.is_plan_ready():
        print("\n" + "="*80)
        print("Business Logic Plan Ready!")
        print("="*80)
        print()

        approve = input("Approve plan and generate code? (yes/no): ").strip().lower()

        if approve == 'yes' or approve == 'y':
            # Code generation
            result = await orchestrator.approve_plan_and_generate_code()

            if result['status'] == 'success':
                print(f"\n✅ Code generated successfully!")
                print(f"Output: {result['output_path']}")
                print()

                # Output preview
                if result.get('output_preview'):
                    print("Output Preview:")
                    print(result['output_preview'])
                    print()

                # Output review
                while orchestrator.is_output_ready():
                    print("\n" + "="*80)
                    print("What would you like to do?")
                    print("  1. Approve and complete")
                    print("  2. Request changes")
                    print("="*80)

                    choice = input("\nYour choice (1/2): ").strip()

                    if choice == "1":
                        # Approve
                        final_result = await orchestrator.approve_output_and_complete()
                        if final_result['status'] == 'success':
                            print(f"\n✅ WORKFLOW COMPLETED!")
                            print(f"Execution time: {final_result['execution_time']:.2f}s")
                            return True

                    elif choice == "2":
                        # Refine
                        feedback = input("\nDescribe what you'd like to change: ").strip()
                        if feedback:
                            refine_result = await orchestrator.refine_output(feedback)

                            if refine_result['status'] == 'success':
                                print(f"\n✅ Output refined!")
                                if refine_result.get('output_preview'):
                                    print("\nUpdated Output Preview:")
                                    print(refine_result['output_preview'])
                            else:
                                print(f"\n❌ Refinement failed: {refine_result.get('error')}")
            else:
                print(f"\n❌ FAILED: {result.get('error')}")
                return False

    return True


# =============================================================================
# MAIN
# =============================================================================

async def main():
    """Main entry point."""
    print("\n" + "=" * 80)
    print("IRA ORCHESTRATOR - END-TO-END TEST")
    print("=" * 80)
    print()

    print("Test Modes:")
    print("  1. Automated (pre-defined answers with output review)")
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
