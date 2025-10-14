"""
Planner Agent implementation for IRA Workflow Builder.

The Planner Agent is responsible for:
1. Analyzing uploaded CSV files
2. Asking clarifying questions to understand business requirements
3. Generating comprehensive business logic documents
4. Iterating based on user feedback
"""

from typing import List, Dict, Any, Optional
from agent_framework import ChatAgent
from agent_framework.openai import OpenAIChatClient
from agent_framework.azure import AzureOpenAIChatClient

from ira.tools.csv_tools import (
    analyze_csv_structure,
    get_csv_summary,
    validate_column_references,
    get_column_data_preview,
    compare_csv_schemas,
    detect_data_quality_issues,
)
from ira.tools.validation_tools import (
    validate_business_logic,
    check_analysis_feasibility,
)
from ira.utils.logger import get_logger
from ira.utils.config import get_config
from ira.exceptions.errors import AgentException

logger = get_logger(__name__)


# Comprehensive instructions for the Planner Agent
PLANNER_INSTRUCTIONS = """
You are IRA-Planner, an expert business analyst specializing in data analysis requirements.

## Your Role
You help users define their data analysis needs by understanding their business objectives
and creating detailed, implementable specifications for data analysis workflows.

## Your Process

### Phase 1: Initial Analysis
1. Analyze the uploaded CSV files to understand:
   - Available columns and data types
   - Data quality (missing values, duplicates, etc.)
   - Statistical distributions
   - Potential relationships between files

2. Review the workflow name and description provided by the user
3. Form initial understanding of what they want to achieve

### Phase 2: Requirements Gathering (5-10 Questions)
Ask targeted, clarifying questions to understand:

**About Metrics & KPIs:**
- What specific metrics or KPIs are they trying to calculate?
- What are the key business questions they want answered?
- Are there specific thresholds or benchmarks to consider?

**About Data Operations:**
- Which columns should be used for filtering?
- What grouping or aggregation is needed?
- Should data from multiple files be joined? On which columns?
- Are there any calculations or transformations needed?

**About Output:**
- What format should the results be in?
- How should results be sorted or ordered?
- What columns should be included in the final output?
- Are there any specific formatting requirements?

**About Business Rules:**
- Are there any business rules or constraints to apply?
- Should any data be excluded or filtered out?
- How should edge cases be handled (missing values, duplicates, etc.)?

### Guidelines for Questions:
- Ask ONE question at a time for better conversation flow
- Be conversational and professional
- Use specific examples from the data when helpful
- Build on previous answers
- After 5-10 questions, assess if you have enough information

### Phase 3: Business Logic Document Generation
Once you have gathered sufficient information, create a comprehensive document with:

## Business Logic Document Structure:

# Business Logic Document - [Workflow Name]

## 1. Executive Summary
[2-3 sentences summarizing the analysis objective and expected outcome]

## 2. Data Sources
**Files:**
- [filename1]: [purpose and key columns]
- [filename2]: [purpose and key columns]

**Key Columns Used:**
- [column_name]: [description and usage]

## 3. Detailed Requirements
1. [Requirement 1 - be specific]
2. [Requirement 2 - be specific]
3. [Continue with all requirements...]

## 4. Analysis Steps
**Step-by-step implementation logic:**

1. **Data Loading**
   - Load [file1] from [path]
   - Load [file2] from [path]

2. **Data Preparation**
   - [Specific transformations]
   - [Handle missing values]
   - [Data type conversions]

3. **Data Integration** (if multiple files)
   - Join [file1] with [file2] on [column]
   - Type of join: [inner/left/right/outer]

4. **Filtering**
   - [Specific filter conditions]

5. **Aggregation**
   - Group by: [columns]
   - Aggregate: [metrics and functions]

6. **Calculations**
   - [Derived columns or calculations]

7. **Sorting & Output**
   - Sort by: [column] [ascending/descending]
   - Select columns: [list]

## 5. Expected Output
**Format:** CSV file

**Columns:**
1. [column1_name] ([data_type]): [description]
2. [column2_name] ([data_type]): [description]
3. [Continue for all output columns...]

**Sort Order:** [specify]

**Sample Output:**
```
[Show example of 2-3 rows of expected output]
```

## 6. Assumptions
- [Assumption 1]
- [Assumption 2]
- [Continue...]

## 7. Constraints & Business Rules
- [Rule 1]
- [Rule 2]
- [Continue...]

## 8. Edge Case Handling
- **Missing Values:** [how to handle]
- **Duplicates:** [how to handle]
- **Data Quality Issues:** [how to handle]

## 9. Validation Criteria
- [How to validate the results]
- [Expected ranges or checks]

---

### Important Guidelines:

1. **Be Specific:** Don't use vague terms like "various", "some", "etc."
2. **Use Actual Column Names:** Reference real columns from the CSV files
3. **Be Implementation-Ready:** Write as if a Python developer will code directly from this
4. **Include Examples:** Show sample data or expected output when helpful
5. **Consider Data Quality:** Address issues found in the CSV analysis
6. **Validate Feasibility:** Ensure all referenced columns exist

### Tools Available to You:

You have access to these tools - use them proactively:

1. **analyze_csv_structure(filepath)** - Get complete CSV metadata
2. **get_csv_summary(filepaths)** - Get formatted summary
3. **get_column_data_preview(filepath, column_name, num_samples)** - Show sample data
4. **validate_column_references(column_names, available_columns)** - Check columns exist
5. **compare_csv_schemas(filepaths)** - Compare multiple files
6. **detect_data_quality_issues(filepath)** - Find data problems
7. **validate_business_logic(logic_dict)** - Check logic completeness
8. **check_analysis_feasibility(logic_dict, csv_metadata)** - Verify feasibility

Use these tools to:
- Show users actual data examples when asking questions
- Validate your understanding
- Check if proposed analysis is feasible
- Ensure column names are correct

### Tone & Style:
- Professional but friendly
- Patient and thorough
- Clear and specific
- Proactive in using tools
- Transparent about limitations

Remember: Your goal is to create a business logic document so clear and detailed that
a Python developer can implement it without asking any additional questions.
"""


class PlannerAgent:
    """
    Planner Agent for gathering requirements and generating business logic.

    This agent analyzes CSV files, asks clarifying questions, and generates
    comprehensive business logic documents for data analysis workflows.

    Attributes:
        agent: The underlying ChatAgent instance
        csv_filepaths: List of CSV file paths being analyzed
        workflow_name: Name of the workflow
        workflow_description: Description of what workflow should do
        questions_asked: Number of questions asked so far
        max_questions: Maximum number of questions to ask
        conversation_history: History of all interactions
    """

    def __init__(
        self,
        chat_client: Optional[Any] = None,
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_questions: int = 10,
    ):
        """
        Initialize the Planner Agent.

        Args:
            chat_client: Optional chat client instance (OpenAI or Azure)
            model: Model name to use (default: gpt-4o)
            temperature: Temperature for generation (0.0-1.0)
            max_questions: Maximum questions to ask (default: 10)
        """
        logger.info("Initializing Planner Agent")

        # Use provided chat client or create default
        if chat_client is None:
            config = get_config()
            if config.openai_api_key:
                chat_client = OpenAIChatClient(
                    model=model,
                    temperature=temperature,
                )
            elif config.azure_openai_api_key:
                chat_client = AzureOpenAIChatClient(
                    deployment_name=config.azure_openai_chat_deployment_name,
                    temperature=temperature,
                )
            else:
                raise AgentException(
                    "No API key configured. Set OPENAI_API_KEY or AZURE_OPENAI_API_KEY"
                )

        # Create the agent with tools
        self.agent = ChatAgent(
            name="IRA-Planner",
            chat_client=chat_client,
            instructions=PLANNER_INSTRUCTIONS,
            tools=[
                analyze_csv_structure,
                get_csv_summary,
                validate_column_references,
                get_column_data_preview,
                compare_csv_schemas,
                detect_data_quality_issues,
                validate_business_logic,
                check_analysis_feasibility,
            ],
        )

        self.csv_filepaths: List[str] = []
        self.workflow_name: str = ""
        self.workflow_description: str = ""
        self.questions_asked: int = 0
        self.max_questions: int = max_questions
        self.conversation_history: List[Dict[str, Any]] = []

        logger.info(f"Planner Agent initialized with model: {model}")

    def initialize_workflow(
        self,
        workflow_name: str,
        workflow_description: str,
        csv_filepaths: List[str],
    ) -> str:
        """
        Initialize a new workflow with context.

        Args:
            workflow_name: Name of the workflow
            workflow_description: Description of analysis goals
            csv_filepaths: List of CSV file paths to analyze

        Returns:
            Initial message from the agent

        Example:
            >>> planner = PlannerAgent()
            >>> response = planner.initialize_workflow(
            ...     "Sales Analysis Q4",
            ...     "Analyze Q4 sales to identify top products",
            ...     ["data/sales_q4.csv", "data/products.csv"]
            ... )
            >>> print(response)
        """
        logger.info(f"Initializing workflow: {workflow_name}")

        self.workflow_name = workflow_name
        self.workflow_description = workflow_description
        self.csv_filepaths = csv_filepaths
        self.questions_asked = 0
        self.conversation_history = []

        # Create initial context prompt
        context_prompt = f"""
I'm starting a new data analysis workflow. Here's the context:

**Workflow Name:** {workflow_name}

**Workflow Description:** {workflow_description}

**CSV Files Provided:**
{chr(10).join(f"- {fp}" for fp in csv_filepaths)}

Please:
1. Analyze the CSV files using your tools
2. Review the workflow description
3. Start asking me clarifying questions to understand my exact requirements

Remember to ask ONE question at a time, and you can ask up to {self.max_questions} questions.
Let's begin!
"""

        try:
            response = self.agent.run(context_prompt)
            self.conversation_history.append({
                "role": "user",
                "content": context_prompt,
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": response,
            })

            logger.info("Workflow initialized successfully")
            return response

        except Exception as e:
            logger.error(f"Error initializing workflow: {str(e)}")
            raise AgentException(f"Failed to initialize workflow: {str(e)}")

    async def ask_question(self, user_response: str) -> str:
        """
        Process user's response and ask next question or generate business logic.

        Args:
            user_response: User's answer to previous question

        Returns:
            Next question or business logic document

        Example:
            >>> response = await planner.ask_question(
            ...     "I want to calculate total revenue by product category"
            ... )
        """
        logger.info(f"Processing user response (Question #{self.questions_asked + 1})")

        self.questions_asked += 1

        try:
            response = await self.agent.run(user_response)

            self.conversation_history.append({
                "role": "user",
                "content": user_response,
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": response,
            })

            logger.info(f"Questions asked: {self.questions_asked}/{self.max_questions}")
            return response

        except Exception as e:
            logger.error(f"Error processing question: {str(e)}")
            raise AgentException(f"Failed to process question: {str(e)}")

    async def generate_business_logic(self, force: bool = False) -> str:
        """
        Generate business logic document based on gathered information.

        Args:
            force: Force generation even if not all questions asked

        Returns:
            Business logic document as markdown string

        Example:
            >>> logic_doc = await planner.generate_business_logic()
            >>> print(logic_doc)
        """
        logger.info("Generating business logic document")

        if not force and self.questions_asked < 3:
            logger.warning(f"Only {self.questions_asked} questions asked. Recommend asking more.")

        prompt = """
Based on our conversation, please generate the complete Business Logic Document now.

Follow the exact structure specified in your instructions:
1. Executive Summary
2. Data Sources
3. Detailed Requirements
4. Analysis Steps
5. Expected Output
6. Assumptions
7. Constraints & Business Rules
8. Edge Case Handling
9. Validation Criteria

Make sure to:
- Use actual column names from the CSV files
- Be specific and implementation-ready
- Include sample expected output
- Validate that all referenced columns exist
- Check feasibility using your tools

Generate the document now.
"""

        try:
            response = await self.agent.run(prompt)

            self.conversation_history.append({
                "role": "user",
                "content": prompt,
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": response,
            })

            logger.info("Business logic document generated successfully")
            return response

        except Exception as e:
            logger.error(f"Error generating business logic: {str(e)}")
            raise AgentException(f"Failed to generate business logic: {str(e)}")

    async def refine_business_logic(self, feedback: str) -> str:
        """
        Refine business logic based on user feedback.

        Args:
            feedback: User's feedback on the business logic document

        Returns:
            Refined business logic document

        Example:
            >>> refined = await planner.refine_business_logic(
            ...     "Please add handling for missing values in the amount column"
            ... )
        """
        logger.info("Refining business logic based on feedback")

        prompt = f"""
The user has provided feedback on the business logic document:

"{feedback}"

Please update the Business Logic Document to address this feedback.
Provide the complete updated document.
"""

        try:
            response = await self.agent.run(prompt)

            self.conversation_history.append({
                "role": "user",
                "content": prompt,
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": response,
            })

            logger.info("Business logic refined successfully")
            return response

        except Exception as e:
            logger.error(f"Error refining business logic: {str(e)}")
            raise AgentException(f"Failed to refine business logic: {str(e)}")

    def get_conversation_summary(self) -> Dict[str, Any]:
        """
        Get summary of the conversation so far.

        Returns:
            Dictionary containing conversation statistics and history

        Example:
            >>> summary = planner.get_conversation_summary()
            >>> print(f"Questions asked: {summary['questions_asked']}")
        """
        return {
            "workflow_name": self.workflow_name,
            "workflow_description": self.workflow_description,
            "csv_files": self.csv_filepaths,
            "questions_asked": self.questions_asked,
            "max_questions": self.max_questions,
            "conversation_length": len(self.conversation_history),
            "history": self.conversation_history,
        }

    def reset(self):
        """
        Reset the agent state for a new workflow.

        Example:
            >>> planner.reset()
            >>> # Ready for new workflow
        """
        logger.info("Resetting Planner Agent state")

        self.csv_filepaths = []
        self.workflow_name = ""
        self.workflow_description = ""
        self.questions_asked = 0
        self.conversation_history = []


def create_planner_agent(
    model: str = "gpt-4o",
    temperature: float = 0.7,
    max_questions: int = 10,
    use_azure: bool = False,
) -> PlannerAgent:
    """
    Factory function to create a Planner Agent instance.

    Args:
        model: Model name or Azure deployment name
        temperature: Temperature for generation (0.0-1.0)
        max_questions: Maximum questions to ask
        use_azure: Whether to use Azure OpenAI

    Returns:
        Configured PlannerAgent instance

    Raises:
        AgentException: If configuration is invalid

    Example:
        >>> planner = create_planner_agent(model="gpt-4o", temperature=0.7)
        >>> response = planner.initialize_workflow(
        ...     "Sales Analysis",
        ...     "Analyze sales data",
        ...     ["sales.csv"]
        ... )
    """
    logger.info(f"Creating Planner Agent (model={model}, azure={use_azure})")

    config = get_config()

    try:
        if use_azure:
            if not config.azure_openai_api_key:
                raise AgentException("Azure OpenAI API key not configured")

            chat_client = AzureOpenAIChatClient(
                endpoint=config.azure_openai_endpoint,
                deployment_name=model or config.azure_openai_chat_deployment_name,
                temperature=temperature,
            )
        else:
            if not config.openai_api_key:
                raise AgentException("OpenAI API key not configured")

            chat_client = OpenAIChatClient(
                model=model,
                temperature=temperature,
            )

        return PlannerAgent(
            chat_client=chat_client,
            temperature=temperature,
            max_questions=max_questions,
        )

    except Exception as e:
        logger.error(f"Error creating Planner Agent: {str(e)}")
        raise AgentException(f"Failed to create Planner Agent: {str(e)}")
