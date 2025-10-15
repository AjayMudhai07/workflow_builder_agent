"""
Custom test script for Planner Agent with your own CSV files.

This script allows you to test the Planner Agent with your specific
workflow name, description, and CSV files.

Usage:
    python test_my_workflow.py
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ira_builder.agents.planner import create_planner_agent
from ira_builder.utils.logger import setup_logging, get_logger

# Setup logging
setup_logging(log_level="INFO", pretty_print=True)
logger = get_logger(__name__)


async def test_planner_with_my_data():
    """
    Test Planner Agent with your CSV files.
    """
    print("=" * 80)
    print("IRA Workflow Builder - Planner Agent Test")
    print("=" * 80)
    print()

    # ========================================
    # CONFIGURATION - EDIT THESE VALUES
    # ========================================

    # Your workflow details
    WORKFLOW_NAME = "Expenses document date for later period v/s posting date in previous period / qtr"  
    WORKFLOW_DESCRIPTION = (
       "This workflow identifies potential accounting irregularities where expense transactions have been recorded with timing mismatches between their document dates and posting dates. Specifically, it detects cases where an expense document is dated in a later accounting period (month or quarter) than when it was actually posted to the company's books. This pattern may indicate backdating, improper period cut-off, or data entry errors that could distort financial reporting across accounting periods."
    ) 

    # Your CSV file paths (absolute or relative)
    CSV_FILES = [
       "tests/fixtures/sample_csvs/FBL3N.csv"
    ]

    # Agent configuration
    MODEL = "gpt-5"  # or "gpt-4o-mini" for faster/cheaper
    TEMPERATURE = 0.7
    MAX_QUESTIONS = 10

    # ========================================
    # END CONFIGURATION
    # ========================================

    print(f"Workflow Name: {WORKFLOW_NAME}")
    print(f"Description: {WORKFLOW_DESCRIPTION}")
    print(f"CSV Files: {len(CSV_FILES)} files")
    for i, file in enumerate(CSV_FILES, 1):
        print(f"  {i}. {file}")
    print()

    # Verify CSV files exist
    print("Verifying CSV files...")
    for csv_file in CSV_FILES:
        csv_path = Path(csv_file)
        if not csv_path.exists():
            print(f"❌ ERROR: File not found: {csv_file}")
            print(f"   Please check the path and try again.")
            return
        print(f"  ✓ Found: {csv_file}")
    print()

    # Create the Planner Agent
    print(f"Creating Planner Agent (model: {MODEL})...")
    try:
        planner = create_planner_agent(
            model=MODEL,
            temperature=TEMPERATURE,
            max_questions=MAX_QUESTIONS
        )
        print("✓ Planner Agent created successfully\n")
    except Exception as e:
        print(f"❌ ERROR creating agent: {str(e)}")
        print("\nPossible issues:")
        print("  1. OPENAI_API_KEY not set (run: export OPENAI_API_KEY='your-key')")
        print("  2. Invalid model name")
        print("  3. Network connection issue")
        return

    # Initialize workflow
    print("-" * 80)
    print("Initializing workflow...")
    print("-" * 80)
    print()
    print("-" * 80)
    print("Q&A Session")
    print("-" * 80)
    print()
    print("The agent will ask you questions to understand your requirements.")
    print("Answer each question, or type:")
    print("  'generate' - to generate business logic now")
    print("  'quit' - to exit")
    print("-" * 80)

    try:
        initial_response = await planner.initialize_workflow(
            workflow_name=WORKFLOW_NAME,
            workflow_description=WORKFLOW_DESCRIPTION,
            csv_filepaths=CSV_FILES
        )
        print(initial_response)
        print()
    except Exception as e:
        print(f"❌ ERROR initializing workflow: {str(e)}")
        return

    # Interactive Q&A Session
   

    while planner.questions_asked < planner.max_questions:
        print('-'*55)
        print(f"\n[Question {planner.questions_asked + 1}/{planner.max_questions}]")
        user_input = input("You: ").strip()

        if not user_input:
            print("Please provide an answer.")
            continue

        if user_input.lower() == 'quit':
            print("\nExiting Q&A session.")
            break

        if user_input.lower() == 'generate':
            print("\nGenerating business logic document...")
            break

        # Get agent response
        try:
            response = await planner.ask_question(user_input)
            print(f"\nAgent: {response}")
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            break

    # Generate Business Logic
    print("\n" + "=" * 80)
    print("Generating Business Logic Document...")
    print("=" * 80)
    print()

    try:
        business_logic = await planner.generate_business_logic(force=True)
        print(business_logic)
        print()
    except Exception as e:
        print(f"❌ ERROR generating business logic: {str(e)}")
        return

    # Show conversation summary
    summary = planner.get_conversation_summary()
    print("=" * 80)
    print("Conversation Summary:")
    print(f"  - Workflow: {summary['workflow_name']}")
    print(f"  - Questions Asked: {summary['questions_asked']}/{summary['max_questions']}")
    print(f"  - Total Messages: {summary['conversation_length']}")
    print("=" * 80)
    print()

    # Optional: Refinement
    print("Would you like to refine the business logic? (yes/no)")
    refine = input("> ").strip().lower()

    if refine in ['yes', 'y']:
        print("\nEnter your feedback for refinement:")
        feedback = input("> ").strip()

        if feedback:
            print("\nRefining business logic...")
            try:
                refined_logic = await planner.refine_business_logic(feedback)
                print("\n" + "=" * 80)
                print("Refined Business Logic:")
                print("=" * 80)
                print()
                print(refined_logic)
                print()
            except Exception as e:
                print(f"❌ ERROR refining: {str(e)}")

    print("\n✓ Test completed successfully!")


def main():
    """Main entry point."""
    # Check for API key
    import os
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("AZURE_OPENAI_API_KEY"):
        print("=" * 80)
        print("ERROR: No API key configured!")
        print("=" * 80)
        print()
        print("Please add your OpenAI API key to the .env file:")
        print()
        print("  1. Open the .env file in the project root")
        print("  2. Add or update: OPENAI_API_KEY=sk-your-key-here")
        print()
        print("Or for Azure OpenAI, add to .env:")
        print()
        print("  AZURE_OPENAI_API_KEY=your-azure-key")
        print("  AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com")
        print("  AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=gpt-4")
        print()
        sys.exit(1)

    # Run the test
    try:
        asyncio.run(test_planner_with_my_data())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
