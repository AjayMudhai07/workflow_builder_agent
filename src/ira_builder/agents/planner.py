"""
Planner Agent implementation for IRA Workflow Builder.

The Planner Agent is responsible for:
1. Analyzing uploaded CSV files
2. Asking clarifying questions to understand business requirements
3. Generating comprehensive business logic documents
4. Iterating based on user feedback
"""

from typing import List, Dict, Any, Optional, Literal
from enum import Enum
from agent_framework import ChatAgent
from agent_framework.openai import OpenAIChatClient
from agent_framework.azure import AzureOpenAIChatClient
from agent_framework._memory import ContextProvider, Context
from agent_framework._types import ChatMessage

from ira_builder.tools.csv_tools import (
    analyze_csv_structure,
    get_csv_summary,
    validate_column_references,
    get_column_data_preview,
    compare_csv_schemas,
    detect_data_quality_issues,
)
from ira_builder.tools.validation_tools import (
    validate_business_logic,
    check_analysis_feasibility,
)
from ira_builder.utils.logger import get_logger
from ira_builder.utils.config import get_config
from ira_builder.exceptions.errors import AgentException

logger = get_logger(__name__)


# Comprehensive instructions for the Planner Agent
PLANNER_INSTRUCTIONS = """
You are an expert workflow designer specializing in data processing workflows. Your task is to help users build a complete, implementable workflow by understanding their requirements through a conversational interview process.

## ⚠️ CRITICAL DIRECTIVES - READ THESE FIRST ⚠️

**1. ALWAYS ANALYZE CSV FILES FIRST**
Before asking ANY questions to the user, you MUST use your tools (analyze_csv_structure or get_csv_summary) to analyze ALL provided CSV files. Review columns, data types, and sample values. Only after understanding the data structure should you ask your first question.

**2. NEVER ASK ABOUT DATA PREPROCESSING, FORMATS, OR CONVERSIONS**

Your job is ONLY to understand BUSINESS LOGIC (AFTER analyzing the CSV files):
- What business rule determines if something is an exception?
- What thresholds or criteria apply?
- What should be included/excluded based on BUSINESS rules?

If the workflow mentions date comparisons:
- DO NOT ask about date formats (YYYYMMDD, Excel serial, etc.)
- DO NOT ask about date conversions or parsing
- ASSUME dates are ready for direct comparison
- ONLY ask about the BUSINESS RULE (e.g., "flag if document month > posting month")

## Default Assumptions (DO NOT ask questions about these)

The following aspects are FIXED and should NOT be questioned:

1. **Pre-processing:** Assume ALL data is clean, validated, and ready to use. DO NOT ask about:
   - Data cleaning, validation, or quality checks
   - Handling missing values or nulls
   - Data type conversions or casting
   - **Date/time format conversions or parsing - NEVER ask how dates are formatted or stored**
   - Currency conversions
   - String formatting or normalization
   - Encoding issues

2. **Output Format:** Output will ALWAYS be a single CSV file containing the results. DO NOT ask about output format.

3. **Focus Area:** Your questions should focus ONLY on understanding the **business logic** and **business rules** for the workflow.

**CRITICAL RULE FOR DATE COLUMNS:**
- If the workflow mentions comparing dates (e.g., "document date vs posting date"), simply use the date columns that exist in the data
- DO NOT ask about date formats, conversions, or how dates are stored
- Assume all date columns are ready for direct comparison (month extraction, year extraction, etc.)
- Focus ONLY on the BUSINESS RULE: what date comparison determines an exception?

---

# Your Objectives

1. **ANALYZE CSV FILES FIRST:** Before asking ANY questions, you MUST use your tools to analyze the CSV files
2. **Understand Business Logic:** Ask targeted questions to understand the user's business rules and decision criteria
3. **Identify Relevant Data:** Determine which columns are needed for the business logic
4. **Define Business Rules:** Establish the specific conditions, filters, and calculations
5. **Create Plan:** Generate a comprehensive, implementable business logic plan

# Conversation Guidelines

## MANDATORY FIRST STEP: CSV Analysis

**CHECK YOUR MEMORY FIRST:**
- If you see "CSV Data Structure (ALREADY ANALYZED - IN YOUR MEMORY)" in your context, the CSV analysis is ALREADY DONE
- DO NOT call analyze_csv_structure() or get_csv_summary() if the data is already in your memory
- Simply reference the columns from your memory when formulating questions

**IF CSV is NOT yet in your memory, THEN:**

1. Use `analyze_csv_structure(filepath)` or `get_csv_summary(filepaths)` to understand the data
2. Review all available columns, data types, and sample values
3. Identify which columns are likely relevant to the workflow description
4. Only AFTER analyzing the CSV files should you ask your first question

**DO NOT SKIP THIS STEP.** The user expects you to understand their data before asking questions.

## Question Format

Ask **ONE question at a time** using this exact format:

```
[Brief context based on previous answers]

[Single clear question referencing specific columns or logic]

Please select one option:
A) [Specific choice with column references]
B) [Specific choice with column references]
C) [Specific choice with column references]
D) [Specific choice with column references]
E) Other (please specify)
```

## Requirements Gathering

Through your questions, systematically gather information about **BUSINESS LOGIC ONLY**:

- **Business Rules:** What conditions determine if a record should be included/flagged?
- **Decision Criteria:** What thresholds, comparisons, or logic gates apply?
- **Calculations:** What business metrics or derived values are needed?
- **Filtering Logic:** What criteria determine which records to include in the output?
- **Grouping/Aggregation:** How should results be organized or summarized?
- **Output Structure:** Proactively propose the ideal output dataframe based on the workflow (see "Output Dataframe Design" section)

**Smart Question Strategy:**

- If the workflow description mentions specific concepts (e.g., "document date vs posting date"), infer which columns to use from the available data
- If a previous answer clearly implies what columns to use, don't ask again
- Focus questions on business decisions that cannot be inferred (thresholds, criteria, edge cases)

**CRITICAL - DO NOT ask about:**
- ❌ Data cleaning, validation, or quality checks
- ❌ Missing value handling or null checks
- ❌ **Date/time format conversions or parsing (NEVER ask "how are dates stored" or "what format are dates in")**
- ❌ Currency conversions or exchange rates
- ❌ Data type conversions or casting
- ❌ String formatting or normalization
- ❌ File format or output structure
- ❌ Any form of data preprocessing

**For date comparisons, focus ONLY on business rules:**
- ✅ "Should we flag all cases where document month > posting month?"
- ✅ "Do we need a threshold (e.g., more than 1 month difference)?"
- ✅ "Should quarter-end exceptions be treated differently?"

## Behavioral Rules

- **One Question Rule:** Never ask multiple questions in a single response
- **Multiple Choice:** Always provide A-E options for every question
- **Specific References:** Use actual column names from the available data
- **Context Awareness:** Build naturally on previous answers
- **User Flexibility:** Accept answers beyond provided options when user specifies
- **Quality Over Speed:** Gather sufficient information (typically 5-8 questions) before generating plan
- **Avoid Redundancy:** If the answer to a question is already clear from the workflow description or previous answers, DO NOT ask that question
- **Make Reasonable Inferences:** Use common sense to infer obvious details rather than asking unnecessary clarifying questions
- **Final Review:** Before generating the plan, ALWAYS ask a final review question to catch anything missed

## Output Dataframe Design (CRITICAL)

**BEFORE asking about output columns, you MUST first analyze and determine the ideal output structure.**

When it's time to ask about the output dataframe:

1. **THINK FIRST** - Based on:
   - Workflow name and description
   - Business logic gathered from conversation
   - Input CSV columns available
   - Purpose of the analysis

2. **DETERMINE IDEAL OUTPUT** - Ask yourself:
   - What columns are needed to identify each exception/result? (e.g., Company Code, Document Number, etc.)
   - What columns contain the business logic criteria? (e.g., Document Date, Posting Date)
   - What columns help understand WHY this is an exception? (e.g., Amount, Document Type)
   - What derived/calculated columns are needed? (e.g., Date Difference, Month/Quarter info)
   - What contextual columns help with investigation? (e.g., Vendor, Description, Reference)

3. **PROPOSE THE OUTPUT** - Instead of asking "what columns do you want?", present your recommendation:

```
Based on our conversation about [workflow purpose], I recommend the output CSV should contain:

**Identification Columns:**
- [Column 1]: [Why it's needed]
- [Column 2]: [Why it's needed]

**Business Logic Columns:**
- [Column 3]: [Why it's needed]
- [Column 4]: [Why it's needed]

**Context Columns:**
- [Column 5]: [Why it's needed]

**Calculated Columns:**
- [Column 6]: [What it contains and why]

This ensures each row in the output represents [what each row means] and provides all information needed for [investigation/review/action].

Please select one option:
A) This output structure looks perfect - proceed with this
B) Add these additional columns: [let me specify]
C) Remove some columns: [let me specify which ones]
D) Modify the structure: [let me explain how]
E) Other (please specify)
```

**REMEMBER:** The goal is to generate a SINGLE CSV file that:
- Contains all flagged exceptions/results
- Has enough context for users to investigate each case
- Is actionable and ready for review
- Includes both original data and derived insights

## Final Review Question (MANDATORY)

Before generating the business logic plan, you MUST ask this final review question:

"Before I generate the complete business logic plan, is there anything else I should know? Any additional:

Please select one option:
A) No, I think we've covered everything - please generate the plan
B) Yes, there are additional filtering criteria I want to add
C) Yes, there are specific exclusions or edge cases to consider
D) Yes, there are additional columns or calculations needed
E) Other (please specify)"

### Tools Available to You:

You have access to these tools - use them proactively:

1. **analyze_csv_structure(filepath)** - Get complete CSV metadata
2. **get_csv_summary(filepaths)** - Get formatted summary
3. **get_column_data_preview(filepath, column_name, num_samples)** - Show sample data
4. **validate_column_references(column_names, available_columns)** - Check columns exist
5. **compare_csv_schemas(filepaths)** - Compare multiple files
6. **detect_data_quality_issues(filepath)** - Find data problems

Use these tools to understand the data structure, but remember: NEVER ask about data preprocessing or format conversions.

---

# Question Flow Summary

Your workflow should follow this EXACT logical progression:

**STEP 0: CSV Analysis (MANDATORY - BEFORE ANY QUESTIONS)**
   - Use `analyze_csv_structure()` or `get_csv_summary()` to analyze ALL provided CSV files
   - Review columns, data types, sample values
   - Understand the data structure before asking questions
   - **YOU MUST DO THIS FIRST - NO EXCEPTIONS**

**STEP 1: Business Logic Questions** (3-5 questions):
   - What determines an exception/result?
   - What thresholds or criteria apply?
   - What exclusions or special cases exist?

**STEP 2: Output Structure Proposal** (1 question):
   - THINK about the ideal output based on workflow + conversation
   - PROPOSE a specific output structure with reasoning
   - ASK for confirmation/modifications

**STEP 3: Final Review Question** (1 question):
   - Catch anything missed
   - Confirm readiness to generate plan

**Total: CSV Analysis + 5-8 questions to gather complete requirements**

---

Remember: Your goal is to gather BUSINESS LOGIC requirements through a structured interview process, proactively design the ideal output structure, then generate a complete, implementable business logic plan that produces a SINGLE, actionable CSV file.
"""


class PlannerResponseType(str, Enum):
    """Enum for different types of responses from the Planner Agent."""
    QUESTION = "question"
    BUSINESS_LOGIC_PLAN = "business_logic_plan"
    ACKNOWLEDGMENT = "acknowledgment"
    ERROR = "error"


class PlannerResponse:
    """
    Structured response from the Planner Agent.

    This class encapsulates the agent's response with metadata to help
    the UI and other components route and handle the response appropriately.

    Attributes:
        response_type: Type of response (question, business_logic_plan, etc.)
        content: The actual text content from the agent
        metadata: Additional metadata about the response
    """

    def __init__(
        self,
        response_type: PlannerResponseType,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a PlannerResponse.

        Args:
            response_type: Type of response
            content: The actual response text
            metadata: Optional metadata dictionary
        """
        self.response_type = response_type
        self.content = content
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert response to dictionary format.

        Returns:
            Dictionary representation of the response

        Example:
            >>> response.to_dict()
            {
                "response_type": "question",
                "content": "What threshold should we use?",
                "metadata": {"question_number": 3}
            }
        """
        return {
            "response_type": self.response_type.value,
            "content": self.content,
            "metadata": self.metadata,
        }

    def __str__(self) -> str:
        """Return the content when converting to string."""
        return self.content

    def __repr__(self) -> str:
        """Return detailed representation."""
        return f"PlannerResponse(type={self.response_type.value}, content_length={len(self.content)})"


class CSVAnalysisMemory(ContextProvider):
    """
    Context provider that maintains CSV analysis in memory throughout the session.

    This provider injects CSV analysis information as additional context before
    each agent invocation, ensuring the agent always has access to the data structure.
    """

    def __init__(self):
        """Initialize the CSV analysis memory."""
        self.csv_analysis: Optional[str] = None
        self.workflow_context: Optional[str] = None

    def set_csv_analysis(self, analysis: str):
        """
        Store CSV analysis results in memory.

        Args:
            analysis: The CSV analysis summary to store
        """
        self.csv_analysis = analysis
        logger.info("Stored CSV analysis in memory")

    def set_workflow_context(self, workflow_name: str, workflow_description: str, csv_files: List[str]):
        """
        Store workflow context in memory.

        Args:
            workflow_name: Name of the workflow
            workflow_description: Description of the workflow
            csv_files: List of CSV file paths
        """
        self.workflow_context = f"""
**Workflow Context:**
- Name: {workflow_name}
- Description: {workflow_description}
- Files: {', '.join(csv_files)}
"""
        logger.info("Stored workflow context in memory")

    async def invoking(self, messages, **kwargs):
        """
        Inject CSV analysis as context before each invocation.

        This method is called by the framework before each agent run,
        allowing us to inject the CSV analysis as persistent context.

        Args:
            messages: Current conversation messages
            **kwargs: Additional keyword arguments

        Returns:
            Context object with CSV analysis as additional instructions
        """
        if self.csv_analysis or self.workflow_context:
            # Build the context instructions
            context_parts = []

            if self.workflow_context:
                context_parts.append(self.workflow_context)

            if self.csv_analysis:
                context_parts.append("\n**CSV Data Structure (ALREADY ANALYZED - IN YOUR MEMORY):**\n")
                context_parts.append(self.csv_analysis)
                context_parts.append("\n**IMPORTANT:** This CSV analysis is ALREADY COMPLETE and stored in your memory.")
                context_parts.append("DO NOT call analyze_csv_structure() or get_csv_summary() again.")
                context_parts.append("Simply reference these columns directly when formulating questions.")

            context_instructions = "\n".join(context_parts)

            return Context(instructions=context_instructions)

        return Context()

    async def invoked(self, **kwargs):
        """
        Called after each invocation. Can be used to track conversation state.

        Args:
            **kwargs: Additional keyword arguments including 'response'
        """
        pass

    async def thread_created(self, **kwargs):
        """
        Called when a new thread is created.

        Args:
            **kwargs: Additional keyword arguments including 'thread'
        """
        pass


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
        thread: AgentThread for maintaining conversation context
        csv_memory: CSVAnalysisMemory for persisting CSV analysis
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
                    model_id=model,
                )
            elif config.azure_openai_api_key:
                chat_client = AzureOpenAIChatClient(
                    deployment_name=config.azure_openai_chat_deployment_name,
                )
            else:
                raise AgentException(
                    "No API key configured. Set OPENAI_API_KEY or AZURE_OPENAI_API_KEY"
                )

        # Create CSV analysis memory provider
        self.csv_memory = CSVAnalysisMemory()

        # Create the agent with tools and context provider
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
            context_providers=[self.csv_memory],
        )

        self.csv_filepaths: List[str] = []
        self.workflow_name: str = ""
        self.workflow_description: str = ""
        self.questions_asked: int = 0
        self.max_questions: int = max_questions
        self.conversation_history: List[Dict[str, Any]] = []
        self.thread = None  # Will be initialized when workflow starts
        self.current_business_logic_plan: Optional[str] = None  # Stores the latest plan

        logger.info(f"Planner Agent initialized with model: {model}")

    def _extract_csv_analysis_from_response(self, response) -> Optional[str]:
        """
        Extract CSV analysis information from agent response.

        The agent response may contain tool calls that analyzed CSV files.
        This method extracts that information to store in memory.

        Args:
            response: The agent's response object

        Returns:
            CSV analysis summary as a string, or None if no analysis found
        """
        try:
            # Check if response has tool calls or content with CSV analysis
            if hasattr(response, 'tool_calls') and response.tool_calls:
                # Extract tool call results related to CSV analysis
                csv_info_parts = []
                for tool_call in response.tool_calls:
                    if hasattr(tool_call, 'name') and tool_call.name in [
                        'analyze_csv_structure', 'get_csv_summary'
                    ]:
                        if hasattr(tool_call, 'result'):
                            csv_info_parts.append(str(tool_call.result))

                if csv_info_parts:
                    return "\n\n".join(csv_info_parts)

            # Alternatively, check if the response text contains CSV analysis
            response_text = str(response) if hasattr(response, '__str__') else response
            if 'column' in response_text.lower() and ('csv' in response_text.lower() or 'data' in response_text.lower()):
                return response_text

        except Exception as e:
            logger.warning(f"Error extracting CSV analysis from response: {str(e)}")

        return None

    def _detect_response_type(self, content: str) -> PlannerResponseType:
        """
        Detect the type of response from the agent's content.

        Args:
            content: The agent's response text

        Returns:
            PlannerResponseType enum value
        """
        content_lower = content.lower()

        # Check for Business Logic Plan markers (enhanced detection)
        plan_markers = [
            "# business logic plan",
            "## **workflow purpose**",
            "## **required files**",
            "## **requirements**",
            "## **business logic**",
            "## **output dataframe structure**",
            "### workflow plan:",
            "**objective:**",
            "**steps:**"
        ]

        # Strong indicators of a plan
        if any(marker in content_lower for marker in plan_markers):
            return PlannerResponseType.BUSINESS_LOGIC_PLAN

        # Check for plan-like structure (has workflow/objective/steps sections)
        if (("workflow" in content_lower and "objective" in content_lower) or
            ("workflow" in content_lower and "steps:" in content_lower) or
            ("load data" in content_lower and "output" in content_lower and len(content) > 500)):
            return PlannerResponseType.BUSINESS_LOGIC_PLAN

        # Check for question markers (A-E options)
        if ("please select one option:" in content_lower or
            "please select:" in content_lower) and (
            "\na)" in content_lower or "\nb)" in content_lower or
            "a)" in content_lower[:200]):  # Check first 200 chars for options
            return PlannerResponseType.QUESTION

        # Check for acknowledgment/continuation
        if any(phrase in content_lower for phrase in [
            "i've analyzed", "i've reviewed", "thank you for", "understood",
            "i'll proceed", "let me now", "moving forward", "if you need",
            "feel free", "have a", "good luck"
        ]) and len(content.split()) < 150:  # Short acknowledgments
            return PlannerResponseType.ACKNOWLEDGMENT

        # Default to QUESTION if it contains a question mark
        if "?" in content:
            return PlannerResponseType.QUESTION

        # Default acknowledgment for other cases
        return PlannerResponseType.ACKNOWLEDGMENT

    async def initialize_workflow(
        self,
        workflow_name: str,
        workflow_description: str,
        csv_filepaths: List[str],
    ) -> PlannerResponse:
        """
        Initialize a new workflow with context.

        Args:
            workflow_name: Name of the workflow
            workflow_description: Description of analysis goals
            csv_filepaths: List of CSV file paths to analyze

        Returns:
            PlannerResponse object containing the initial message and metadata

        Example:
            >>> planner = PlannerAgent()
            >>> response = await planner.initialize_workflow(
            ...     "Sales Analysis Q4",
            ...     "Analyze Q4 sales to identify top products",
            ...     ["data/sales_q4.csv", "data/products.csv"]
            ... )
            >>> print(response.content)
            >>> print(response.response_type)
        """
        logger.info(f"Initializing workflow: {workflow_name}")

        self.workflow_name = workflow_name
        self.workflow_description = workflow_description
        self.csv_filepaths = csv_filepaths
        self.questions_asked = 0
        self.conversation_history = []

        # Store workflow context in memory
        self.csv_memory.set_workflow_context(workflow_name, workflow_description, csv_filepaths)

        # Create a new thread for this workflow conversation
        self.thread = self.agent.get_new_thread()
        logger.info("Created new conversation thread")

        # Create initial context prompt
        # Note: If CSV was pre-analyzed, tell agent it's already done
        if self.csv_memory.csv_analysis:
            context_prompt = f"""
I'm starting a new data analysis workflow. Here's the context:

**Workflow Name:** {workflow_name}

**Workflow Description:** {workflow_description}

**CSV Files Provided:**
{chr(10).join(f"- {fp}" for fp in csv_filepaths)}

**IMPORTANT:** The CSV files have ALREADY been analyzed and the structure is available in your memory (injected as context). You do NOT need to call analyze_csv_structure() or get_csv_summary() again.

Review the CSV data structure in your memory, then start asking me clarifying questions to understand my exact business logic requirements.

Remember to ask ONE question at a time, and you can ask up to {self.max_questions} questions.
Let's begin!
"""
        else:
            context_prompt = f"""
I'm starting a new data analysis workflow. Here's the context:

**Workflow Name:** {workflow_name}

**Workflow Description:** {workflow_description}

**CSV Files Provided:**
{chr(10).join(f"- {fp}" for fp in csv_filepaths)}

**CRITICAL INSTRUCTION:**
Before asking me ANY questions, you MUST first:
1. Use analyze_csv_structure() or get_csv_summary() to analyze ALL the CSV files provided above
2. Review all columns, data types, and sample values in the data
3. Understand what data is available before formulating your questions

Only AFTER you have analyzed the CSV files should you ask your first question.

Remember to ask ONE question at a time, and you can ask up to {self.max_questions} questions.
Let's begin by analyzing the CSV files!
"""

        try:
            # Pre-analyze CSV files and store in memory BEFORE first agent interaction
            logger.info("Pre-analyzing CSV files...")
            try:
                csv_summary = get_csv_summary(csv_filepaths)
                self.csv_memory.set_csv_analysis(csv_summary)
                logger.info("CSV analysis stored in memory")
            except Exception as csv_error:
                logger.warning(f"Could not pre-analyze CSV files: {str(csv_error)}")
                # Continue anyway - agent will analyze during conversation

            response = await self.agent.run(context_prompt, thread=self.thread)
            self.conversation_history.append({
                "role": "user",
                "content": context_prompt,
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": response,
            })

            # If CSV analysis wasn't stored yet, try to extract from response
            if not self.csv_memory.csv_analysis:
                csv_analysis = self._extract_csv_analysis_from_response(response)
                if csv_analysis:
                    self.csv_memory.set_csv_analysis(csv_analysis)

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
            # Pass the thread to maintain conversation context
            response = await self.agent.run(user_response, thread=self.thread)

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
Based on our conversation, please generate the complete Business Logic Plan now in MARKDOWN format.

You MUST follow this EXACT structure:

# Business Logic Plan

## **Workflow Purpose**
[Clear description of what this workflow accomplishes and why it's needed]

## **Required Files**

Provide the required files in JSON format for easy parsing by the coder agent:

```json
[
  {
    "file_name": "filename1.csv",
    "required_columns": [
      "Column_Name_1",
      "Column_Name_2",
      "Column_Name_3"
    ]
  },
  {
    "file_name": "filename2.csv",
    "required_columns": [
      "Column_Name_4",
      "Column_Name_5"
    ]
  }
]
```

**Column Descriptions:**
- **Column_Name_1**: [Description of what this column contains]
- **Column_Name_2**: [Description of what this column contains]
- **Column_Name_3**: [Description of what this column contains]
[Continue for all required columns...]

## **Requirements**
Conversation summary showing the questions asked and responses given:

**Q1: [Question asked by IRA]**
- User Response: [What the user answered]

**Q2: [Question asked by IRA]**
- User Response: [What the user answered]

**Q3: [Question asked by IRA]**
- User Response: [What the user answered]

[Continue for all questions asked during the conversation...]

## **Business Logic**
Detailed step-by-step logic to generate the answer dataframe:

1. **Load Data:**
   - [Describe data loading requirements]

2. **Filter Records:**
   - [Describe filtering criteria based on conversation]
   - [Include specific conditions, thresholds, comparisons]

3. **Apply Business Rules:**
   - [Describe each business rule in detail]
   - [Include calculations, comparisons, logic gates]

4. **Create Derived Columns:**
   - [List any calculated/derived columns and their formulas]

5. **Final Dataset:**
   - [Describe the final filtering and selection]

## **Output Dataframe Structure**
List all columns in the output CSV with their descriptions:

| Column Name | Description | Source/Calculation |
|-------------|-------------|-------------------|
| [Column 1] | [What this column contains] | [From input / Calculated: formula] |
| [Column 2] | [What this column contains] | [From input / Calculated: formula] |
| [Column 3] | [What this column contains] | [From input / Calculated: formula] |
[Continue for all output columns...]

**Note:** Each row in the output represents [what each row means - e.g., "one flagged exception transaction requiring review"].

---

IMPORTANT:
- Use the ACTUAL column names from the CSV files
- Reference ALL questions and answers from our conversation in the Requirements section
- Be specific and implementation-ready in the Business Logic section
- Include both original columns and calculated columns in the Output Dataframe Structure
- Validate that all referenced columns exist using your tools before generating

Generate the document now.
"""

        try:
            # Pass the thread to maintain conversation context
            response = await self.agent.run(prompt, thread=self.thread)

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
            # Pass the thread to maintain conversation context
            response = await self.agent.run(prompt, thread=self.thread)

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
        self.thread = None  # Clear the thread

        # Clear CSV memory
        self.csv_memory.csv_analysis = None
        self.csv_memory.workflow_context = None
        logger.info("Cleared CSV memory")


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
            )
        else:
            if not config.openai_api_key:
                raise AgentException("OpenAI API key not configured")

            chat_client = OpenAIChatClient(
                model_id=model,
            )

        return PlannerAgent(
            chat_client=chat_client,
            model=model,
            temperature=temperature,
            max_questions=max_questions,
        )

    except Exception as e:
        logger.error(f"Error creating Planner Agent: {str(e)}")
        raise AgentException(f"Failed to create Planner Agent: {str(e)}")
