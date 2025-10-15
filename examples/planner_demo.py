"""
Example usage of the Planner Agent.

This script demonstrates how to use the Planner Agent to:
1. Analyze CSV files
2. Gather requirements through Q&A
3. Generate business logic documents
4. Refine based on feedback

Run with: python examples/planner_demo.py
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ira_builder.agents.planner import create_planner_agent, PlannerAgent
from ira_builder.utils.logger import setup_logging, get_logger

# Setup logging
setup_logging(log_level="INFO", pretty_print=True)
logger = get_logger(__name__)


async def demo_basic_workflow():
    """
    Demonstrate basic workflow with the Planner Agent.
    """
    print("=" * 80)
    print("IRA Workflow Builder - Planner Agent Demo")
    print("=" * 80)
    print()

    # Create the Planner Agent
    print("Creating Planner Agent...")
    planner = create_planner_agent(
        model="gpt-4o",
        temperature=0.7,
        max_questions=10
    )
    print("✓ Planner Agent created\n")

    # Define workflow context
    workflow_name = "Q4 Sales Analysis"
    workflow_description = (
        "Analyze Q4 sales data to identify top performing products and categories. "
        "Need to understand which products generate the most revenue and quantity sold."
    )

    # Use sample CSV files from tests
    fixtures_dir = Path(__file__).parent.parent / "tests" / "fixtures" / "sample_csvs"
    csv_files = [
        str(fixtures_dir / "sales_data.csv"),
        str(fixtures_dir / "products.csv"),
    ]

    print(f"Workflow: {workflow_name}")
    print(f"Description: {workflow_description}")
    print(f"CSV Files: {len(csv_files)} files")
    print()

    # Initialize workflow
    print("Initializing workflow...")
    print("-" * 80)

    initial_response = planner.initialize_workflow(
        workflow_name=workflow_name,
        workflow_description=workflow_description,
        csv_filepaths=csv_files
    )

    print(initial_response)
    print("-" * 80)
    print()

    # Simulate Q&A Session
    print("Simulating Q&A Session (automated responses)...")
    print()

    # Predefined answers for demo
    qa_pairs = [
        {
            "user": "I want to calculate total revenue and total quantity sold for each product",
            "context": "Answering about metrics..."
        },
        {
            "user": "Group by product_name and product_id, and show the category as well",
            "context": "Answering about grouping..."
        },
        {
            "user": "Filter out any products marked as discontinued",
            "context": "Answering about filters..."
        },
        {
            "user": "Sort by total revenue in descending order, highest revenue first",
            "context": "Answering about sorting..."
        },
        {
            "user": "The output should be a CSV file with columns: product_id, product_name, category, total_revenue, total_quantity_sold",
            "context": "Answering about output format..."
        },
    ]

    for i, qa in enumerate(qa_pairs, 1):
        print(f"\nQ&A Round {i}/{len(qa_pairs)}")
        print(f"User: {qa['user']}")
        print()

        response = await planner.ask_question(qa["user"])

        print(f"Agent: {response[:200]}...")
        print("-" * 80)

        # Stop if agent is ready to generate business logic
        if any(keyword in response.lower() for keyword in ["enough information", "generate", "business logic document"]):
            print("\n✓ Agent has enough information!")
            break

    # Generate business logic
    print("\n" + "=" * 80)
    print("Generating Business Logic Document...")
    print("=" * 80)
    print()

    business_logic = await planner.generate_business_logic()

    print(business_logic)
    print()

    # Get conversation summary
    summary = planner.get_conversation_summary()
    print("=" * 80)
    print("Conversation Summary:")
    print(f"  - Questions Asked: {summary['questions_asked']}/{summary['max_questions']}")
    print(f"  - Total Messages: {summary['conversation_length']}")
    print(f"  - Workflow: {summary['workflow_name']}")
    print("=" * 80)

    return planner, business_logic


async def demo_refinement():
    """
    Demonstrate refining business logic based on feedback.
    """
    print("\n\n" + "=" * 80)
    print("Demo: Refining Business Logic")
    print("=" * 80)
    print()

    # First, run basic workflow to get initial business logic
    planner, initial_logic = await demo_basic_workflow()

    # Simulate user feedback
    feedback = (
        "Please add handling for missing values in the total_amount column. "
        "If total_amount is missing, the row should be excluded from the analysis."
    )

    print("\nUser Feedback:")
    print(f"  '{feedback}'")
    print()

    print("Refining business logic...")
    print("-" * 80)

    refined_logic = await planner.refine_business_logic(feedback)

    print(refined_logic)
    print()

    print("=" * 80)
    print("✓ Business logic refined successfully!")
    print("=" * 80)


async def demo_interactive_mode():
    """
    Interactive mode - actual Q&A with user input.
    """
    print("\n\n" + "=" * 80)
    print("Interactive Mode - Planner Agent")
    print("=" * 80)
    print()

    print("This mode allows you to interact directly with the Planner Agent.")
    print("Type 'quit' to exit or 'generate' to create business logic document.")
    print()

    # Create agent
    planner = create_planner_agent(model="gpt-4o", max_questions=10)

    # Get workflow details from user
    print("Enter workflow details:")
    workflow_name = input("  Workflow Name: ").strip() or "Data Analysis"
    workflow_description = input("  Description: ").strip() or "Analyze data files"

    # Use sample CSV files
    fixtures_dir = Path(__file__).parent.parent / "tests" / "fixtures" / "sample_csvs"
    csv_files = [
        str(fixtures_dir / "sales_data.csv"),
        str(fixtures_dir / "products.csv"),
    ]

    print(f"\n  Using sample CSV files from: {fixtures_dir}")
    print()

    # Initialize
    print("Initializing workflow...")
    print("-" * 80)
    response = planner.initialize_workflow(workflow_name, workflow_description, csv_files)
    print(response)
    print("-" * 80)
    print()

    # Q&A Loop
    while planner.questions_asked < planner.max_questions:
        user_input = input("You: ").strip()

        if not user_input:
            continue

        if user_input.lower() == 'quit':
            print("Exiting interactive mode.")
            break

        if user_input.lower() == 'generate':
            print("\nGenerating business logic document...")
            logic = await planner.generate_business_logic(force=True)
            print("\n" + "=" * 80)
            print(logic)
            print("=" * 80)
            break

        # Get agent response
        response = await planner.ask_question(user_input)
        print(f"\nAgent: {response}\n")

    print("\n✓ Interactive session complete!")


async def main():
    """Main entry point."""
    print("\nIRA Workflow Builder - Planner Agent Examples")
    print()
    print("Choose a demo:")
    print("  1. Basic Workflow (automated)")
    print("  2. Refinement Demo (automated)")
    print("  3. Interactive Mode (manual)")
    print("  4. Run All Demos")
    print()

    choice = input("Enter choice (1-4): ").strip()

    try:
        if choice == "1":
            await demo_basic_workflow()
        elif choice == "2":
            await demo_refinement()
        elif choice == "3":
            await demo_interactive_mode()
        elif choice == "4":
            print("\nRunning all demos...")
            await demo_basic_workflow()
            await demo_refinement()
        else:
            print("Invalid choice. Running basic workflow demo...")
            await demo_basic_workflow()

        print("\n✓ Demo completed successfully!")

    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        logger.error(f"Demo failed: {str(e)}")
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Check if API key is configured
    import os
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("AZURE_OPENAI_API_KEY"):
        print("ERROR: No API key configured!")
        print("Please set OPENAI_API_KEY or AZURE_OPENAI_API_KEY environment variable.")
        print()
        print("Example:")
        print("  export OPENAI_API_KEY='sk-your-key-here'")
        print()
        sys.exit(1)

    # Run demos
    asyncio.run(main())
