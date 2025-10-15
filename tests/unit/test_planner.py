"""
Unit tests for Planner Agent.

This module tests the PlannerAgent class implementation including:
- Agent initialization
- Workflow initialization
- Q&A sessions
- Business logic generation
- Refinement based on feedback
- Conversation history tracking
- Error handling
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from ira_builder.agents.planner import (
    PlannerAgent,
    create_planner_agent,
    PLANNER_INSTRUCTIONS,
)
from ira_builder.exceptions.errors import AgentException


class TestPlannerAgentInitialization:
    """Test suite for PlannerAgent initialization."""

    def test_init_with_defaults(self):
        """Test agent initialization with default parameters."""
        mock_client = Mock()
        with patch("ira.agents.planner.ChatAgent") as mock_agent:
            planner = PlannerAgent(chat_client=mock_client)

            assert planner.csv_filepaths == []
            assert planner.workflow_name == ""
            assert planner.workflow_description == ""
            assert planner.questions_asked == 0
            assert planner.max_questions == 10
            assert planner.conversation_history == []

    def test_init_with_custom_params(self):
        """Test agent initialization with custom parameters."""
        mock_client = Mock()

        with patch("ira.agents.planner.ChatAgent") as mock_agent:
            planner = PlannerAgent(
                chat_client=mock_client,
                model="gpt-4o-mini",
                temperature=0.5,
                max_questions=5,
            )

            assert planner.max_questions == 5

    def test_init_without_api_key(self):
        """Test agent initialization fails without API key."""
        with patch("ira.agents.planner.get_config") as mock_config:
            mock_config.return_value.openai_api_key = None
            mock_config.return_value.azure_openai_api_key = None

            with pytest.raises(AgentException, match="No API key configured"):
                PlannerAgent()

    def test_init_with_openai_client(self):
        """Test agent initialization with OpenAI client."""
        with patch("ira.agents.planner.get_config") as mock_config:
            with patch("ira.agents.planner.OpenAIChatClient") as mock_openai:
                with patch("ira.agents.planner.ChatAgent"):
                    mock_config.return_value.openai_api_key = "test-key"
                    mock_config.return_value.azure_openai_api_key = None

                    planner = PlannerAgent(model="gpt-4o")

                    mock_openai.assert_called_once_with(
                        model="gpt-4o",
                        temperature=0.7,
                    )

    def test_init_with_azure_client(self):
        """Test agent initialization with Azure client."""
        with patch("ira.agents.planner.get_config") as mock_config:
            with patch("ira.agents.planner.AzureOpenAIChatClient") as mock_azure:
                with patch("ira.agents.planner.ChatAgent"):
                    mock_config.return_value.openai_api_key = None
                    mock_config.return_value.azure_openai_api_key = "test-key"
                    mock_config.return_value.azure_openai_chat_deployment_name = "gpt-4"

                    planner = PlannerAgent()

                    mock_azure.assert_called_once()

    def test_agent_has_all_tools(self):
        """Test that agent is initialized with all required tools."""
        with patch("ira.agents.planner.ChatAgent") as mock_agent_class:
            mock_client = Mock()
            planner = PlannerAgent(chat_client=mock_client)

            # Get the tools passed to ChatAgent
            call_args = mock_agent_class.call_args
            tools = call_args[1]["tools"]

            # Should have 8 tools
            assert len(tools) == 8

            # Check tool names
            tool_names = [tool.__name__ for tool in tools]
            expected_tools = [
                "analyze_csv_structure",
                "get_csv_summary",
                "validate_column_references",
                "get_column_data_preview",
                "compare_csv_schemas",
                "detect_data_quality_issues",
                "validate_business_logic",
                "check_analysis_feasibility",
            ]

            for expected_tool in expected_tools:
                assert expected_tool in tool_names


class TestWorkflowInitialization:
    """Test suite for workflow initialization."""

    @pytest.fixture
    def planner(self):
        """Create a planner agent for testing."""
        mock_client = Mock()
        with patch("ira.agents.planner.ChatAgent"):
            planner = PlannerAgent(chat_client=mock_client)
            planner.agent = Mock()
            planner.agent.run = Mock(return_value="Hello! I've analyzed the CSV files...")
            return planner

    @pytest.fixture
    def sample_csv_files(self, sample_csvs_dir):
        """Get sample CSV file paths."""
        return [
            str(sample_csvs_dir / "sales_data.csv"),
            str(sample_csvs_dir / "products.csv"),
        ]

    def test_initialize_workflow_success(self, planner, sample_csv_files):
        """Test successful workflow initialization."""
        response = planner.initialize_workflow(
            workflow_name="Sales Analysis",
            workflow_description="Analyze Q4 sales data",
            csv_filepaths=sample_csv_files,
        )

        assert planner.workflow_name == "Sales Analysis"
        assert planner.workflow_description == "Analyze Q4 sales data"
        assert planner.csv_filepaths == sample_csv_files
        assert planner.questions_asked == 0
        assert len(planner.conversation_history) == 2  # User + assistant
        assert response == "Hello! I've analyzed the CSV files..."

    def test_initialize_workflow_calls_agent(self, planner, sample_csv_files):
        """Test that initialize_workflow calls the agent with correct prompt."""
        planner.initialize_workflow(
            workflow_name="Test Workflow",
            workflow_description="Test Description",
            csv_filepaths=sample_csv_files,
        )

        planner.agent.run.assert_called_once()
        call_args = planner.agent.run.call_args[0][0]

        assert "Test Workflow" in call_args
        assert "Test Description" in call_args
        assert "sales_data.csv" in call_args
        assert "products.csv" in call_args

    def test_initialize_workflow_error_handling(self, planner, sample_csv_files):
        """Test error handling during workflow initialization."""
        planner.agent.run.side_effect = Exception("API Error")

        with pytest.raises(AgentException, match="Failed to initialize workflow"):
            planner.initialize_workflow(
                workflow_name="Test",
                workflow_description="Test",
                csv_filepaths=sample_csv_files,
            )

    def test_initialize_workflow_resets_state(self, planner, sample_csv_files):
        """Test that initializing a new workflow resets previous state."""
        # First workflow
        planner.initialize_workflow(
            workflow_name="First",
            workflow_description="First workflow",
            csv_filepaths=["file1.csv"],
        )
        planner.questions_asked = 5

        # Second workflow
        planner.initialize_workflow(
            workflow_name="Second",
            workflow_description="Second workflow",
            csv_filepaths=sample_csv_files,
        )

        assert planner.workflow_name == "Second"
        assert planner.questions_asked == 0
        assert len(planner.conversation_history) == 2


class TestQASession:
    """Test suite for Q&A session functionality."""

    @pytest.fixture
    def planner(self):
        """Create initialized planner for testing."""
        mock_client = Mock()
        with patch("ira.agents.planner.ChatAgent"):
            planner = PlannerAgent(chat_client=mock_client)
            planner.agent = Mock()
            planner.agent.run = AsyncMock(return_value="What metrics do you want to calculate?")

            # Initialize workflow
            planner.workflow_name = "Test"
            planner.workflow_description = "Test"
            planner.csv_filepaths = ["test1.csv", "test2.csv"]
            planner.conversation_history = []

            return planner

    @pytest.mark.asyncio
    async def test_ask_question_success(self, planner):
        """Test successful question asking."""
        response = await planner.ask_question("I want to calculate total revenue")

        assert response == "What metrics do you want to calculate?"
        assert planner.questions_asked == 1
        assert len(planner.conversation_history) == 2

    @pytest.mark.asyncio
    async def test_ask_question_increments_counter(self, planner):
        """Test that asking questions increments counter."""
        await planner.ask_question("Answer 1")
        await planner.ask_question("Answer 2")
        await planner.ask_question("Answer 3")

        assert planner.questions_asked == 3

    @pytest.mark.asyncio
    async def test_ask_question_stores_history(self, planner):
        """Test that Q&A is stored in conversation history."""
        await planner.ask_question("My answer")

        assert len(planner.conversation_history) == 2
        assert planner.conversation_history[0]["role"] == "user"
        assert planner.conversation_history[0]["content"] == "My answer"
        assert planner.conversation_history[1]["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_ask_question_error_handling(self, planner):
        """Test error handling during Q&A."""
        planner.agent.run.side_effect = Exception("API Error")

        with pytest.raises(AgentException, match="Failed to process question"):
            await planner.ask_question("My answer")

    @pytest.mark.asyncio
    async def test_multiple_qa_rounds(self, planner):
        """Test multiple Q&A rounds."""
        responses = [
            "Question 1?",
            "Question 2?",
            "Question 3?",
        ]
        planner.agent.run.side_effect = [AsyncMock(return_value=r)() for r in responses]

        for i, expected_response in enumerate(responses, 1):
            response = await planner.ask_question(f"Answer {i}")
            assert planner.questions_asked == i


class TestBusinessLogicGeneration:
    """Test suite for business logic generation."""

    @pytest.fixture
    def planner(self):
        """Create planner for testing."""
        mock_client = Mock()
        with patch("ira.agents.planner.ChatAgent"):
            planner = PlannerAgent(chat_client=mock_client)
            planner.agent = Mock()
            planner.agent.run = AsyncMock(return_value="# Business Logic Document\n...")

            planner.workflow_name = "Test"
            planner.csv_filepaths = ["test.csv"]
            planner.conversation_history = []

            return planner

    @pytest.mark.asyncio
    async def test_generate_business_logic_success(self, planner):
        """Test successful business logic generation."""
        planner.questions_asked = 5

        logic = await planner.generate_business_logic()

        assert logic == "# Business Logic Document\n..."
        assert len(planner.conversation_history) == 2

    @pytest.mark.asyncio
    async def test_generate_business_logic_few_questions_warning(self, planner):
        """Test warning when generating with few questions."""
        planner.questions_asked = 2

        with patch("ira.agents.planner.logger") as mock_logger:
            await planner.generate_business_logic()
            mock_logger.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_business_logic_force_flag(self, planner):
        """Test force flag bypasses question count check."""
        planner.questions_asked = 1

        with patch("ira.agents.planner.logger") as mock_logger:
            await planner.generate_business_logic(force=True)
            # Should not log warning with force=True
            mock_logger.warning.assert_not_called()

    @pytest.mark.asyncio
    async def test_generate_business_logic_prompt_format(self, planner):
        """Test that generation prompt is correctly formatted."""
        planner.questions_asked = 5
        await planner.generate_business_logic()

        planner.agent.run.assert_called_once()
        call_args = planner.agent.run.call_args[0][0]

        assert "Business Logic Document" in call_args
        assert "Executive Summary" in call_args
        assert "Data Sources" in call_args
        assert "Detailed Requirements" in call_args

    @pytest.mark.asyncio
    async def test_generate_business_logic_error_handling(self, planner):
        """Test error handling during generation."""
        planner.questions_asked = 5
        planner.agent.run.side_effect = Exception("Generation failed")

        with pytest.raises(AgentException, match="Failed to generate business logic"):
            await planner.generate_business_logic()


class TestBusinessLogicRefinement:
    """Test suite for business logic refinement."""

    @pytest.fixture
    def planner(self):
        """Create planner with generated logic."""
        mock_client = Mock()
        with patch("ira.agents.planner.ChatAgent"):
            planner = PlannerAgent(chat_client=mock_client)
            planner.agent = Mock()
            planner.agent.run = AsyncMock(return_value="# Updated Business Logic\n...")

            planner.workflow_name = "Test"
            planner.conversation_history = []

            return planner

    @pytest.mark.asyncio
    async def test_refine_business_logic_success(self, planner):
        """Test successful refinement."""
        refined = await planner.refine_business_logic(
            "Please add handling for missing values"
        )

        assert refined == "# Updated Business Logic\n..."
        assert len(planner.conversation_history) == 2

    @pytest.mark.asyncio
    async def test_refine_business_logic_includes_feedback(self, planner):
        """Test that refinement prompt includes user feedback."""
        feedback = "Add error handling for duplicates"
        await planner.refine_business_logic(feedback)

        call_args = planner.agent.run.call_args[0][0]
        assert feedback in call_args

    @pytest.mark.asyncio
    async def test_refine_business_logic_error_handling(self, planner):
        """Test error handling during refinement."""
        planner.agent.run.side_effect = Exception("Refinement failed")

        with pytest.raises(AgentException, match="Failed to refine business logic"):
            await planner.refine_business_logic("Some feedback")


class TestConversationManagement:
    """Test suite for conversation management."""

    @pytest.fixture
    def planner(self):
        """Create planner for testing."""
        mock_client = Mock()
        with patch("ira.agents.planner.ChatAgent"):
            planner = PlannerAgent(chat_client=mock_client, max_questions=10)
            planner.workflow_name = "Test Workflow"
            planner.workflow_description = "Test Description"
            planner.csv_filepaths = ["test1.csv", "test2.csv"]
            planner.questions_asked = 5
            planner.conversation_history = [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there"},
            ]
            return planner

    def test_get_conversation_summary(self, planner):
        """Test getting conversation summary."""
        summary = planner.get_conversation_summary()

        assert summary["workflow_name"] == "Test Workflow"
        assert summary["workflow_description"] == "Test Description"
        assert summary["csv_files"] == ["test1.csv", "test2.csv"]
        assert summary["questions_asked"] == 5
        assert summary["max_questions"] == 10
        assert summary["conversation_length"] == 2
        assert "history" in summary

    def test_reset(self, planner):
        """Test resetting agent state."""
        planner.reset()

        assert planner.csv_filepaths == []
        assert planner.workflow_name == ""
        assert planner.workflow_description == ""
        assert planner.questions_asked == 0
        assert planner.conversation_history == []


class TestFactoryFunction:
    """Test suite for create_planner_agent factory function."""

    def test_create_planner_agent_defaults(self):
        """Test factory function with defaults."""
        with patch("ira.agents.planner.get_config") as mock_config:
            with patch("ira.agents.planner.OpenAIChatClient") as mock_client:
                with patch("ira.agents.planner.ChatAgent"):
                    mock_config.return_value.openai_api_key = "test-key"
                    mock_config.return_value.azure_openai_api_key = None

                    planner = create_planner_agent()

                    assert isinstance(planner, PlannerAgent)
                    mock_client.assert_called_once_with(
                        model="gpt-4o",
                        temperature=0.7,
                    )

    def test_create_planner_agent_custom_params(self):
        """Test factory function with custom parameters."""
        with patch("ira.agents.planner.get_config") as mock_config:
            with patch("ira.agents.planner.OpenAIChatClient") as mock_client:
                with patch("ira.agents.planner.ChatAgent"):
                    mock_config.return_value.openai_api_key = "test-key"

                    planner = create_planner_agent(
                        model="gpt-4o-mini",
                        temperature=0.5,
                        max_questions=5,
                    )

                    assert planner.max_questions == 5
                    mock_client.assert_called_once_with(
                        model="gpt-4o-mini",
                        temperature=0.5,
                    )

    def test_create_planner_agent_azure(self):
        """Test factory function with Azure."""
        with patch("ira.agents.planner.get_config") as mock_config:
            with patch("ira.agents.planner.AzureOpenAIChatClient") as mock_azure:
                with patch("ira.agents.planner.ChatAgent"):
                    mock_config.return_value.openai_api_key = None
                    mock_config.return_value.azure_openai_api_key = "test-key"
                    mock_config.return_value.azure_openai_endpoint = "https://test.openai.azure.com"
                    mock_config.return_value.azure_openai_chat_deployment_name = "gpt-4"

                    planner = create_planner_agent(use_azure=True)

                    assert isinstance(planner, PlannerAgent)
                    mock_azure.assert_called_once()

    def test_create_planner_agent_no_api_key(self):
        """Test factory function fails without API key."""
        with patch("ira.agents.planner.get_config") as mock_config:
            mock_config.return_value.openai_api_key = None
            mock_config.return_value.azure_openai_api_key = None

            with pytest.raises(AgentException, match="API key not configured"):
                create_planner_agent()

    def test_create_planner_agent_azure_no_key(self):
        """Test factory function fails for Azure without key."""
        with patch("ira.agents.planner.get_config") as mock_config:
            mock_config.return_value.azure_openai_api_key = None

            with pytest.raises(AgentException, match="Azure OpenAI API key not configured"):
                create_planner_agent(use_azure=True)


class TestInstructions:
    """Test suite for agent instructions."""

    def test_instructions_not_empty(self):
        """Test that instructions are defined."""
        assert PLANNER_INSTRUCTIONS
        assert len(PLANNER_INSTRUCTIONS) > 100

    def test_instructions_contain_key_sections(self):
        """Test that instructions contain required sections."""
        assert "Your Role" in PLANNER_INSTRUCTIONS
        assert "Your Process" in PLANNER_INSTRUCTIONS
        assert "Phase 1: Initial Analysis" in PLANNER_INSTRUCTIONS
        assert "Phase 2: Requirements Gathering" in PLANNER_INSTRUCTIONS
        assert "Phase 3: Business Logic Document Generation" in PLANNER_INSTRUCTIONS
        assert "Business Logic Document Structure" in PLANNER_INSTRUCTIONS

    def test_instructions_mention_tools(self):
        """Test that instructions mention available tools."""
        assert "analyze_csv_structure" in PLANNER_INSTRUCTIONS
        assert "get_csv_summary" in PLANNER_INSTRUCTIONS
        assert "validate_business_logic" in PLANNER_INSTRUCTIONS

    def test_instructions_have_guidelines(self):
        """Test that instructions include guidelines."""
        assert "Guidelines for Questions" in PLANNER_INSTRUCTIONS
        assert "Important Guidelines" in PLANNER_INSTRUCTIONS
        assert "Tone & Style" in PLANNER_INSTRUCTIONS


class TestIntegration:
    """Integration tests for complete workflows."""

    @pytest.fixture
    def sample_csv_files(self, sample_csvs_dir):
        """Get sample CSV file paths."""
        return [
            str(sample_csvs_dir / "sales_data.csv"),
            str(sample_csvs_dir / "products.csv"),
        ]

    @pytest.fixture
    def planner(self):
        """Create planner for integration testing."""
        mock_client = Mock()
        with patch("ira.agents.planner.ChatAgent"):
            planner = PlannerAgent(chat_client=mock_client, max_questions=5)
            planner.agent = Mock()
            return planner

    @pytest.mark.asyncio
    async def test_complete_workflow(self, planner, sample_csv_files):
        """Test complete workflow from init to business logic generation."""
        # Setup mock responses
        planner.agent.run = Mock(return_value="Initial analysis complete")
        planner.agent.run = AsyncMock(side_effect=[
            "Question 1?",
            "Question 2?",
            "Question 3?",
            "# Business Logic Document\n..."
        ])

        # Initialize
        init_response = planner.initialize_workflow(
            workflow_name="Integration Test",
            workflow_description="Test workflow",
            csv_filepaths=sample_csv_files,
        )

        # Q&A
        for i in range(3):
            await planner.ask_question(f"Answer {i+1}")

        # Generate
        logic = await planner.generate_business_logic()

        # Verify state
        assert planner.questions_asked == 3
        assert len(planner.conversation_history) > 0
        assert "Business Logic" in logic

    @pytest.mark.asyncio
    async def test_workflow_with_refinement(self, planner, sample_csv_files):
        """Test workflow including refinement step."""
        planner.agent.run = Mock(return_value="Initial")
        planner.agent.run = AsyncMock(side_effect=[
            "Question?",
            "# Business Logic\n...",
            "# Refined Business Logic\n..."
        ])

        # Initialize and generate
        planner.initialize_workflow("Test", "Test", sample_csv_files)
        await planner.ask_question("Answer")
        logic = await planner.generate_business_logic()

        # Refine
        refined = await planner.refine_business_logic("Add more detail")

        assert "Refined" in refined
