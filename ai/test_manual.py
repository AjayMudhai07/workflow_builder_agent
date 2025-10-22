"""
Manual Testing Script for IRA Orchestrator with Output Review

This script allows you to manually test the complete workflow:
1. Answer Planner's questions yourself
2. Review and approve Business Logic Plan
3. Review generated output
4. Provide refinement feedback
5. Approve final output

Run: python test_manual.py
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai.ira_builder.orchestrator import create_orchestrator, WorkflowPhase
from ai.ira_builder.utils.logger import setup_logging, get_logger

# Setup logging
setup_logging(log_level="INFO", pretty_print=True)
logger = get_logger(__name__)


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(text.center(80))
    print("=" * 80 + "\n")


def print_section(text):
    """Print a formatted section."""
    print("\n" + "-" * 80)
    print(text)
    print("-" * 80 + "\n")


async def main():
    """Manual testing workflow."""

    print_header("IRA ORCHESTRATOR - MANUAL TEST")

    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ ERROR: OPENAI_API_KEY not found in .env file")
        print("\nPlease add your OpenAI API key to .env file:")
        print("OPENAI_API_KEY=sk-your-key-here")
        return

    print(f"✓ Found API key: {api_key[:20]}...")

    # Get workflow configuration from user
    print("\n" + "=" * 80)
    print("WORKFLOW CONFIGURATION")
    print("=" * 80 + "\n")

    print("Let's configure your workflow:\n")

    # Workflow name
    workflow_name = input("1. Workflow Name (e.g., 'Sales_Analysis'): ").strip()
    if not workflow_name:
        workflow_name = "Manual_Test_Workflow"
        print(f"   Using default: {workflow_name}")

    # Workflow description
    print("\n2. Workflow Description")
    print("   (What should this workflow do?)")
    workflow_description = input("   Description: ").strip()
    if not workflow_description:
        workflow_description = "Load CSV, analyze data, and generate summary report"
        print(f"   Using default: {workflow_description}")

    # CSV files
    print("\n3. CSV File Path")
    print("   Available test file: tests/fixtures/sample_csvs/FBL3N.csv")
    csv_path = input("   Path (or press Enter for default): ").strip()
    if not csv_path:
        csv_path = "tests/fixtures/sample_csvs/FBL3N.csv"

    if not Path(csv_path).exists():
        print(f"\n❌ ERROR: CSV file not found: {csv_path}")
        return

    print(f"   ✓ Using: {csv_path}")

    # Output filename
    print("\n4. Output Filename")
    output_filename = input("   Filename (e.g., 'result.csv'): ").strip()
    if not output_filename:
        output_filename = "manual_test_output.csv"
        print(f"   Using default: {output_filename}")

    # Create orchestrator
    print_header("CREATING ORCHESTRATOR")

    try:
        orchestrator = create_orchestrator(
            workflow_name=workflow_name,
            workflow_description=workflow_description,
            csv_filepaths=[csv_path],
            output_filename=output_filename,
            model="gpt-5",
            max_planner_questions=10,
            max_coder_iterations=5,
            code_execution_timeout=120,
        )
        print("✅ Orchestrator created successfully!")
    except Exception as e:
        print(f"❌ Error creating orchestrator: {str(e)}")
        import traceback
        traceback.print_exc()
        return

    # ==========================================================================
    # PHASE 1: PLANNING
    # ==========================================================================
    print_header("PHASE 1: PLANNING")

    print("The Planner will now ask you questions to understand your requirements.")
    print("Answer each question to help define the workflow.\n")

    input("Press Enter to start planning phase...")

    try:
        # Start workflow
        result = await orchestrator.start()

        if result['status'] != 'success':
            print(f"❌ Failed to start: {result.get('error')}")
            return

        # Show first question
        print_section("Planner's Question")
        print(result['response'])
        print()

        # Q&A loop
        while orchestrator.state.phase == WorkflowPhase.PLANNING:
            user_answer = input("Your answer: ").strip()

            if not user_answer:
                print("⚠️  Please provide an answer")
                continue

            print("\nProcessing your answer...")
            result = await orchestrator.process_user_input(user_answer)

            if result['status'] != 'success':
                print(f"❌ Error: {result.get('error')}")
                continue

            print(f"✓ Question {result['questions_asked']} answered")

            # Check if plan is ready
            if orchestrator.is_plan_ready():
                print("\n✅ Business Logic Plan has been generated!")
                break

            # Show next response
            print_section("Planner's Response")
            print(result['response'])
            print()

    except Exception as e:
        print(f"❌ Error during planning: {str(e)}")
        import traceback
        traceback.print_exc()
        return

    # ==========================================================================
    # PHASE 2: PLAN REVIEW
    # ==========================================================================
    if not orchestrator.is_plan_ready():
        print("❌ Business Logic Plan was not generated")
        return

    print_header("PHASE 2: PLAN REVIEW")

    print("Here is the Business Logic Plan:\n")
    print_section("Business Logic Plan")
    print(orchestrator.state.business_logic_plan)
    print()

    # Ask user to approve
    while True:
        print("What would you like to do?")
        print("  1. Approve and generate code")
        print("  2. Request changes to the plan")
        print("  3. Cancel")

        choice = input("\nYour choice (1/2/3): ").strip()

        if choice == "1":
            print("\n✓ Plan approved! Moving to code generation...")
            break
        elif choice == "2":
            feedback = input("\nWhat would you like to change? ").strip()
            if feedback:
                print("\nRefining plan based on your feedback...")
                result = await orchestrator.refine_plan(feedback)
                if result['status'] == 'success':
                    print("\n✅ Plan refined!")
                    print_section("Updated Business Logic Plan")
                    print(result['business_logic_plan'])
                    print()
                else:
                    print(f"❌ Error: {result.get('error')}")
        elif choice == "3":
            print("\nTest cancelled.")
            return
        else:
            print("⚠️  Invalid choice. Please enter 1, 2, or 3.")

    # ==========================================================================
    # PHASE 3: CODE GENERATION
    # ==========================================================================
    print_header("PHASE 3: CODE GENERATION & EXECUTION")

    print("Generating Python code and executing it...")
    print("This may take 30-60 seconds...\n")

    try:
        result = await orchestrator.approve_plan_and_generate_code()

        if result['status'] != 'success':
            print(f"❌ Code generation failed: {result.get('error')}")
            return

        print("✅ Code generated and executed successfully!\n")
        print(f"✓ Phase: {result['phase']}")
        print(f"✓ Code iterations: {result['iterations']}")
        print(f"✓ Output file: {result['output_path']}")
        print(f"✓ Code saved to: {result['code_filepath']}")

        # Show output preview
        if result.get('output_preview'):
            print_section("Output Preview (first 10 rows)")
            print(result['output_preview'])

        # Show output summary
        if result.get('output_summary'):
            summary = result['output_summary']
            print_section("Output Summary")
            print(f"  Rows: {summary.get('row_count', 'N/A'):,}")
            print(f"  Columns: {summary.get('column_count', 'N/A')}")
            print(f"  Column Names: {', '.join(summary.get('columns', []))}")
            print()

    except Exception as e:
        print(f"❌ Error during code generation: {str(e)}")
        import traceback
        traceback.print_exc()
        return

    # ==========================================================================
    # PHASE 4: OUTPUT REVIEW
    # ==========================================================================
    if not orchestrator.is_output_ready():
        print("❌ Output is not ready for review")
        return

    print_header("PHASE 4: OUTPUT REVIEW")

    print("The code has been executed and output has been generated.")
    print("You can now review the output and request changes if needed.\n")

    # Output review loop
    refinement_count = 0
    max_refinements = 3

    while orchestrator.is_output_ready():
        print("What would you like to do?")
        print("  1. Approve output and complete workflow ✅")
        print("  2. Request changes to the output 🔄")
        print(f"     (Refinements used: {refinement_count}/{max_refinements})")

        choice = input("\nYour choice (1/2): ").strip()

        if choice == "1":
            # Approve and complete
            print("\n✓ Approving output and completing workflow...")

            try:
                final_result = await orchestrator.approve_output_and_complete()

                if final_result['status'] == 'success':
                    print_header("WORKFLOW COMPLETED!")

                    print("✅ SUCCESS!\n")
                    print(f"✓ Execution time: {final_result['execution_time']:.2f} seconds")
                    print(f"✓ Output file: {final_result['output_path']}")
                    print(f"✓ Workflow status: Completed")

                    # Show final summary
                    summary = orchestrator.get_workflow_summary()

                    print_section("Workflow Summary")
                    print(f"Workflow Name: {summary['workflow_name']}")
                    print(f"Phase: {summary['phase']}")
                    print(f"Started: {summary['started_at']}")
                    print(f"Completed: {summary['completed_at']}")
                    print(f"Success: {summary['is_successful']}")
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
                    print()

                    if summary['output_review_summary']['feedback_history']:
                        print("Refinement History:")
                        for entry in summary['output_review_summary']['feedback_history']:
                            print(f"  [{entry['iteration']}] {entry['feedback'][:80]}...")
                        print()

                    print_header("✅ TEST COMPLETED SUCCESSFULLY")
                    return
                else:
                    print(f"❌ Error completing workflow: {final_result.get('error')}")
                    return

            except Exception as e:
                print(f"❌ Error during completion: {str(e)}")
                import traceback
                traceback.print_exc()
                return

        elif choice == "2":
            # Request refinement
            if refinement_count >= max_refinements:
                print(f"\n⚠️  Maximum refinements ({max_refinements}) reached.")
                print("Please approve the current output or cancel.")
                continue

            print("\nDescribe what changes you'd like to make to the output.")
            print("Examples:")
            print("  - Add a new column showing percentages")
            print("  - Sort by amount in descending order")
            print("  - Filter to only show records above 1000")
            print("  - Add average calculation per group")
            print()

            feedback = input("Your feedback: ").strip()

            if not feedback:
                print("⚠️  Please provide feedback")
                continue

            print(f"\n🔄 Refining output (attempt {refinement_count + 1}/{max_refinements})...")
            print("This may take 30-60 seconds...\n")

            try:
                refine_result = await orchestrator.refine_output(
                    feedback=feedback,
                    max_refinement_iterations=max_refinements
                )

                if refine_result['status'] == 'success':
                    refinement_count += 1

                    print(f"✅ Output refined successfully!\n")
                    print(f"✓ Refinement iteration: {refine_result['refinement_iteration']}")
                    print(f"✓ Updated code saved to: {refine_result['code_filepath']}")
                    print(f"✓ Updated output: {refine_result['output_path']}")

                    # Show updated preview
                    if refine_result.get('output_preview'):
                        print_section("Updated Output Preview")
                        print(refine_result['output_preview'])

                    # Show updated summary
                    if refine_result.get('output_summary'):
                        summary = refine_result['output_summary']
                        print_section("Updated Output Summary")
                        print(f"  Rows: {summary.get('row_count', 'N/A'):,}")
                        print(f"  Columns: {summary.get('column_count', 'N/A')}")
                        print(f"  Column Names: {', '.join(summary.get('columns', []))}")
                        print()
                else:
                    print(f"❌ Refinement failed: {refine_result.get('error')}")
                    print("You can try again with different feedback or approve the current output.\n")

            except Exception as e:
                print(f"❌ Error during refinement: {str(e)}")
                import traceback
                traceback.print_exc()
                print("You can try again or approve the current output.\n")

        else:
            print("⚠️  Invalid choice. Please enter 1 or 2.")


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║                  IRA ORCHESTRATOR - MANUAL TEST SCRIPT                     ║
║                                                                            ║
║  This script will guide you through the complete workflow:                ║
║    1. Configure workflow settings                                         ║
║    2. Answer Planner's questions (manual input)                           ║
║    3. Review and approve Business Logic Plan                              ║
║    4. Review generated output                                             ║
║    5. Request refinements (optional)                                      ║
║    6. Approve final output                                                ║
║                                                                            ║
║  Requirements:                                                             ║
║    - Valid OPENAI_API_KEY in .env file                                    ║
║    - CSV file to analyze                                                  ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user (Ctrl+C)")
        print("Workflow state has been saved and can be resumed later.")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
