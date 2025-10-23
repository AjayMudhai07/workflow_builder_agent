"""
Business Logic Plan Generator for RAA System.

This agent generates HTML-formatted business logic plans from RAA's accumulated
knowledge after Intent, Data, and Logic agents have gathered requirements.

Differences from Old Planner System:
- Uses RAA's accumulated_knowledge (not planner conversation history)
- Extracts Q&A from Intent/Data/Logic agent interactions
- Uses Dataset Analyzer results (not CSV tools)
- Same HTML output format as old system for compatibility
"""

from typing import Dict, Any, Optional, List
from agent_framework import ChatAgent
from ai.ira_builder.utils.logger import get_logger

logger = get_logger(__name__)


# System prompt for business logic plan generation
BUSINESS_LOGIC_PLAN_PROMPT = """You are generating a Business Logic Plan document for FINANCE/AUDIT USERS based on accumulated knowledge from a requirements gathering conversation.

**IMPORTANT:** This document is for FINANCE and AUDIT professionals, NOT technical developers.
- Focus on BUSINESS LOGIC and BUSINESS RULES
- Do NOT include technical implementation details like file loading, parsing, or preprocessing
- Describe WHAT should happen, not HOW to code it

You will receive:
1. Workflow context (name, description, CSV files)
2. Dataset description and file analysis
3. Accumulated knowledge from Intent Agent (goals, success criteria)
4. Accumulated knowledge from Data Agent (column meanings, relationships)
5. Accumulated knowledge from Logic Agent (rules, thresholds, calculations)
6. Q&A pairs from all three agents

Your task is to synthesize ALL this information into a comprehensive Business Logic Plan.

---

# EXACT OUTPUT FORMAT (MANDATORY)

You MUST follow this EXACT structure and format (use HTML bold tags as shown):

<b>Business Logic Plan: {WORKFLOW_NAME}</b>

<b>Data Source</b>

<b>{FILENAME_1}</b>
<b>Required Columns</b>: ["Column1", "Column2", "Column3", ...]
<b>File Description</b>: {Description from file analysis}

{Additional files if present - same format}

<b>Business Requirements</b>

Start with the user's initial workflow description, then list all clarifying questions and answers:

<b>Initial Requirement</b>: [User's original workflow description - what they initially provided]

<b>Clarifying Questions & Answers:</b>

<b>Q1</b>: [Question text - NO multiple choice options, just the question]
<b>A1</b>: [User's answer]

<b>Q2</b>: [Question text]
<b>A2</b>: [User's answer]

[Continue for ALL questions from all three agents...]

<b>Business Logic</b>

Synthesize the business rules from the accumulated knowledge. Focus on:
- What records to include/exclude (filtering rules)
- What constitutes a match/duplicate (matching criteria)
- What thresholds trigger flags (business thresholds)
- What calculations to perform (derived metrics)
- How to handle exceptions (edge cases)
- What grouping/aggregation applies (business grouping)

**CRITICAL**: When writing business rules involving categorical columns, USE THE EXACT VALUES from the "Categorical Column Values" section in the file analysis. Do NOT use different capitalization, abbreviations, or assumed values.

Format as numbered rules:

<b>Rule 1</b>: [Business rule from Logic Agent - e.g., "Flag records where Document Date month-year is later than Posting Date month-year"]

<b>Rule 2</b>: [Exception/exclusion rule - e.g., "Exclude entries containing 'reversal' in Document Header Text or Text fields"]

<b>Rule 3</b>: [Threshold or criteria - e.g., "Include all amounts without minimum threshold"]

<b>Rule 4</b>: [Filtering rule using EXACT categorical values - e.g., "Include only Document Type 'STANDARD' and 'CREDIT' (exclude 'Stndrd' or other variants)"]

<b>Rule 5</b>: [Derived calculation - e.g., "Calculate month difference between Document Date and Posting Date"]

[Continue with all business rules extracted from the accumulated knowledge...]

<b>Output Columns</b>

List each column that should appear in the output CSV. Include:
- Original columns from input files (for identification and context)
- Calculated/derived columns (business metrics)

Format each as:

<b>ColumnName</b>: [What it contains and why it's needed for review/audit]
<b>CalculatedColumn</b>: [What it calculates and business meaning]

[Continue for ALL output columns...]

---

# CRITICAL FORMATTING RULES

1. **Data Source section:**
   - Use ONLY the filename (e.g., "FBL3N.csv"), NOT the full path
   - List each file with its required columns
   - Include file description from analysis if available
   - Format: <b>filename</b> then <b>Required Columns</b>: [...]

2. **Business Requirements section:**
   - FIRST: Include user's initial workflow description as <b>Initial Requirement</b>
   - THEN: List all clarifying questions under <b>Clarifying Questions & Answers:</b>
   - Extract ONLY the question text (no multiple choice options)
   - Include questions from ALL three agents (Intent, Data, Logic)
   - Maintain chronological order
   - Format: <b>Q#</b>: question, <b>A#</b>: answer

3. **Business Logic section:**
   - Focus on BUSINESS RULES, not technical steps
   - NO file loading steps (e.g., "Load data from...")
   - NO preprocessing steps (e.g., "Parse date columns", "Convert to datetime")
   - NO technical implementation (e.g., "Create helper columns", "Build boolean mask")
   - Describe WHAT business rules apply, not HOW to implement them
   - Use language finance/audit users understand
   - Extract rules from Logic Agent's accumulated knowledge

4. **Output Columns section:**
   - Simple format: <b>ColumnName</b>: business description
   - Explain WHY each column is useful for review/audit
   - Include both original and calculated columns
   - Provide business context for each column

5. **General Rules:**
   - Use HTML <b> tags for all headers and labels
   - Use plain text for descriptions
   - Use arrays for column lists: ["Col1", "Col2", ...]
   - Maintain consistent formatting throughout
   - Focus on business value and auditability

---

# EXTRACTION GUIDELINES

## From Intent Understanding:
- Extract user_goal → Incorporate into business logic
- Extract success_criteria → Use to frame requirements
- Extract analysis_type → Mention in context
- Extract stakeholders → Consider in output design

## From Data Understanding:
- Extract columns_understood → Use for Required Columns
- Extract column_meanings → Use for column descriptions
- Extract relationships_identified → Mention in business logic
- Extract data_quality_insights → Consider for rules

## From Business Logic Understanding:
- Extract filtering_rules → Convert to Business Logic rules
- Extract matching_criteria → Convert to matching rules
- Extract thresholds → Convert to threshold rules
- Extract calculations → Convert to calculation rules
- Extract output_columns → Use for Output Columns section

## From Q&A History:
- Extract all questions asked (Intent + Data + Logic)
- Extract user's answers
- Maintain chronological order
- Remove multiple choice options from questions

---

Generate the complete Business Logic Plan now following this exact format.

Output ONLY the Business Logic Plan with proper HTML formatting. Do not include any additional commentary or explanations outside the plan structure.
"""


class BusinessLogicPlanGenerator:
    """
    Agent for generating business logic plans from RAA accumulated knowledge.

    This agent synthesizes information from Intent, Data, and Logic agents
    into a comprehensive, business-focused HTML plan document.

    Attributes:
        agent: The underlying ChatAgent instance for plan generation
        model: Model name used for generation
        temperature: Temperature setting for generation
    """

    def __init__(
        self,
        chat_client: Any,
        model: str = "gpt-5",
        temperature: float = 0.3,
    ):
        """
        Initialize the Business Logic Plan Generator.

        Args:
            chat_client: Chat client instance (OpenAI, Azure, or Groq)
            model: Model name to use
            temperature: Temperature for generation (0.0-1.0)
        """
        logger.info("Initializing Business Logic Plan Generator")

        # Create the agent without tools (formatting task only)
        self.agent = ChatAgent(
            name="Business-Logic-Plan-Generator",
            chat_client=chat_client,
            instructions=BUSINESS_LOGIC_PLAN_PROMPT,
            tools=[],  # No tools needed for formatting
        )

        self.model = model
        self.temperature = temperature

        logger.info(f"Business Logic Plan Generator initialized with model: {model}")

    def _extract_filenames(self, csv_filepaths: List[str]) -> List[str]:
        """
        Extract just filenames from full paths.

        Args:
            csv_filepaths: List of full file paths

        Returns:
            List of filenames without paths
        """
        import os
        return [os.path.basename(fp) for fp in csv_filepaths]

    def _format_qa_from_agents(
        self,
        intent_qa: Optional[List[Dict[str, str]]] = None,
        data_qa: Optional[List[Dict[str, str]]] = None,
        logic_qa: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """
        Format Q&A pairs from all three agents chronologically.

        Args:
            intent_qa: Q&A pairs from Intent Agent
            data_qa: Q&A pairs from Data Agent
            logic_qa: Q&A pairs from Logic Agent

        Returns:
            Formatted Q&A string
        """
        all_qa = []

        # Collect all Q&A with agent type
        if intent_qa:
            for qa in intent_qa:
                all_qa.append({
                    "question": qa.get("question", ""),
                    "answer": qa.get("answer", ""),
                    "agent": "intent"
                })

        if data_qa:
            for qa in data_qa:
                all_qa.append({
                    "question": qa.get("question", ""),
                    "answer": qa.get("answer", ""),
                    "agent": "data"
                })

        if logic_qa:
            for qa in logic_qa:
                all_qa.append({
                    "question": qa.get("question", ""),
                    "answer": qa.get("answer", ""),
                    "agent": "logic"
                })

        # Format as string
        formatted = []
        for i, qa in enumerate(all_qa, 1):
            formatted.append(f"Q{i} (from {qa['agent'].title()} Agent): {qa['question']}")
            formatted.append(f"A{i}: {qa['answer']}")
            formatted.append("")  # Blank line

        return "\n".join(formatted)

    def _format_accumulated_knowledge(
        self,
        accumulated_knowledge: Dict[str, Any]
    ) -> str:
        """
        Format accumulated knowledge for context.

        Args:
            accumulated_knowledge: RAA's accumulated knowledge dict

        Returns:
            Formatted string representation
        """
        sections = []

        # Intent knowledge
        sections.append("**Intent Understanding:**")
        sections.append(f"- User Goal: {accumulated_knowledge.get('user_goal', 'Not specified')}")
        sections.append(f"- Analysis Type: {accumulated_knowledge.get('analysis_type', 'Not specified')}")
        sections.append(f"- Success Criteria: {accumulated_knowledge.get('success_criteria', 'Not specified')}")
        sections.append(f"- Stakeholders: {accumulated_knowledge.get('stakeholders', 'Not specified')}")
        sections.append("")

        # Data knowledge
        sections.append("**Data Understanding:**")
        mentioned_cols = accumulated_knowledge.get('mentioned_columns', [])
        sections.append(f"- Mentioned Columns: {', '.join(mentioned_cols) if mentioned_cols else 'None'}")

        col_mappings = accumulated_knowledge.get('column_mappings', {})
        if col_mappings:
            sections.append("- Column Meanings:")
            for col, meaning in col_mappings.items():
                sections.append(f"  - {col}: {meaning}")

        relationships = accumulated_knowledge.get('data_relationships', [])
        if relationships:
            sections.append(f"- Data Relationships: {', '.join(relationships)}")
        sections.append("")

        # Business logic knowledge
        sections.append("**Business Logic Understanding:**")

        filtering = accumulated_knowledge.get('filtering_rules', [])
        if filtering:
            sections.append("- Filtering Rules:")
            for rule in filtering:
                sections.append(f"  - {rule}")

        exclusions = accumulated_knowledge.get('exclusion_criteria', [])
        if exclusions:
            sections.append("- Exclusion Criteria:")
            for exc in exclusions:
                sections.append(f"  - {exc}")

        calculations = accumulated_knowledge.get('calculations', [])
        if calculations:
            sections.append("- Calculations:")
            for calc in calculations:
                sections.append(f"  - {calc}")

        thresholds = accumulated_knowledge.get('thresholds', {})
        if thresholds:
            sections.append("- Thresholds:")
            for key, val in thresholds.items():
                sections.append(f"  - {key}: {val}")

        output_cols = accumulated_knowledge.get('output_columns', [])
        if output_cols:
            sections.append(f"- Output Columns: {', '.join(output_cols)}")

        sections.append("")

        return "\n".join(sections)

    def _format_file_analysis(
        self,
        file_analysis: Dict[str, Any]
    ) -> str:
        """
        Format file analysis results including categorical enrichment.

        Args:
            file_analysis: Dataset analyzer results (may include categorical_enrichment)

        Returns:
            Formatted string
        """
        sections = []

        # Overall dataset description
        dataset_desc = file_analysis.get("dataset_description", "")
        if dataset_desc:
            sections.append("**Dataset Description:**")
            sections.append(dataset_desc)
            sections.append("")

        # File details
        files = file_analysis.get("files", [])
        if files:
            sections.append("**File Details:**")
            for file_info in files:
                file_name = file_info.get("file_name", "Unknown")
                file_desc = file_info.get("file_description", "No description")
                sections.append(f"\n**{file_name}:**")
                sections.append(f"Description: {file_desc}")

                col_descs = file_info.get("column_descriptions", [])
                if col_descs:
                    sections.append("Columns:")
                    for col_desc in col_descs:
                        col_name = col_desc.get("name", "Unknown")
                        col_description = col_desc.get("description", "No description")
                        sections.append(f"  - {col_name}: {col_description}")

                # IMPORTANT: Include categorical enrichment if available
                categorical_enrichment = file_info.get("categorical_enrichment", {})
                if categorical_enrichment:
                    sections.append("\n**Categorical Column Values (ACTUAL VALUES FROM DATA):**")
                    for col_name, enrichment_data in categorical_enrichment.items():
                        values = enrichment_data.get('values', [])
                        method = enrichment_data.get('method', 'unknown')
                        count = enrichment_data.get('count', len(values))

                        if values:
                            # Show first 10 values
                            values_str = ', '.join([f'"{v}"' for v in values[:10]])
                            if count > 10:
                                values_str += f" (and {count - 10} more)"

                            sections.append(f"  - {col_name}: {values_str}")
                    sections.append("")
                    sections.append("NOTE: Use these EXACT values when generating business logic rules involving categorical columns.")

            sections.append("")

        return "\n".join(sections)

    async def generate_plan(
        self,
        workflow_name: str,
        workflow_description: str,
        csv_filepaths: List[str],
        accumulated_knowledge: Dict[str, Any],
        file_analysis: Dict[str, Any],
        intent_qa: Optional[List[Dict[str, str]]] = None,
        data_qa: Optional[List[Dict[str, str]]] = None,
        logic_qa: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """
        Generate business logic plan from RAA accumulated knowledge.

        Args:
            workflow_name: Name of the workflow
            workflow_description: Description of the workflow
            csv_filepaths: List of CSV file paths
            accumulated_knowledge: RAA's accumulated knowledge
            file_analysis: Dataset analyzer results
            intent_qa: Q&A pairs from Intent Agent
            data_qa: Q&A pairs from Data Agent
            logic_qa: Q&A pairs from Logic Agent

        Returns:
            HTML-formatted business logic plan

        Example:
            >>> generator = BusinessLogicPlanGenerator(chat_client, "gpt-5")
            >>> plan = await generator.generate_plan(
            ...     workflow_name="Find Duplicate Invoices",
            ...     workflow_description="Identify duplicate payments",
            ...     csv_filepaths=["data/invoices.csv"],
            ...     accumulated_knowledge=raa.accumulated_knowledge.to_dict(),
            ...     file_analysis=analyzer_results,
            ...     intent_qa=[{"question": "What defines success?", "answer": "..."}],
            ...     data_qa=[{"question": "What is DMBTR?", "answer": "..."}],
            ...     logic_qa=[{"question": "What is duplicate?", "answer": "..."}]
            ... )
        """
        logger.info("Generating business logic plan from RAA knowledge")

        try:
            # Extract filenames
            filenames = self._extract_filenames(csv_filepaths)

            # Format Q&A from all agents
            qa_formatted = self._format_qa_from_agents(intent_qa, data_qa, logic_qa)

            # Format accumulated knowledge
            knowledge_formatted = self._format_accumulated_knowledge(accumulated_knowledge)

            # Format file analysis
            file_analysis_formatted = self._format_file_analysis(file_analysis)

            # Build the context prompt
            context_prompt = f"""
**Workflow Context:**
- Name: {workflow_name}
- Description: {workflow_description}
- CSV Files: {', '.join(filenames)}

{file_analysis_formatted}

{knowledge_formatted}

**Questions & Answers (Chronological):**

{qa_formatted}

---

Based on ALL the information above, generate the complete Business Logic Plan following the EXACT format specified in your instructions.

Remember:
1. Use HTML <b> tags for all headers
2. Include ALL files in Data Source section
3. In Business Requirements section:
   - FIRST: Include the workflow description as <b>Initial Requirement</b>
   - THEN: List all clarifying questions under <b>Clarifying Questions & Answers:</b>
4. Synthesize business rules from accumulated knowledge in Business Logic section
5. List ALL output columns with business descriptions
6. Focus on BUSINESS LOGIC for finance/audit users, NOT technical implementation

IMPORTANT: The user's workflow description often contains analysis steps and initial requirements.
Include this as the <b>Initial Requirement</b> before listing the Q&A pairs. The Q&A pairs are
clarifications that build upon this initial requirement.

Generate the complete plan now.
"""

            logger.info("Calling LLM to generate business logic plan...")

            # Generate the plan
            plan_text = await self.agent.run(context_prompt)

            logger.info("Business logic plan generated successfully")
            logger.info(f"Plan length: {len(str(plan_text))} characters")

            return str(plan_text)

        except Exception as e:
            logger.error(f"Error generating business logic plan: {str(e)}")
            raise Exception(f"Failed to generate business logic plan: {str(e)}")


def create_business_logic_plan_generator(
    model: Optional[str] = None,
    temperature: float = 0.3,
    provider: Optional[str] = None,
) -> BusinessLogicPlanGenerator:
    """
    Factory function to create a Business Logic Plan Generator instance.

    Args:
        model: Model name (or None to use provider default)
        temperature: Temperature for generation (0.0-1.0)
        provider: LLM provider ("openai", "groq", or None for config default)

    Returns:
        Configured BusinessLogicPlanGenerator instance

    Raises:
        Exception: If configuration is invalid

    Example:
        >>> # Use OpenAI (default)
        >>> generator = create_business_logic_plan_generator(
        ...     model="gpt-5",
        ...     temperature=0.3
        ... )

        >>> # Use Groq
        >>> generator = create_business_logic_plan_generator(
        ...     provider="groq",
        ...     model="llama-3.3-70b-versatile"
        ... )

        >>> # Use config defaults
        >>> generator = create_business_logic_plan_generator()
    """
    from ai.ira_builder.utils.llm_provider import create_chat_client
    from ai.ira_builder.utils.config import get_config

    config = get_config()

    # Determine provider (use planner provider by default)
    provider = provider or config.planner_provider

    logger.info(f"Creating Business Logic Plan Generator (provider={provider}, model={model or 'default'})")

    try:
        # Create chat client using factory
        chat_client = create_chat_client(
            provider=provider,
            model=model,
            use_azure=False
        )

        # Determine actual model name
        if model is None:
            if provider == "groq":
                model = config.groq_model
            else:
                model = config.openai_model

        return BusinessLogicPlanGenerator(
            chat_client=chat_client,
            model=model,
            temperature=temperature,
        )

    except Exception as e:
        logger.error(f"Error creating Business Logic Plan Generator: {str(e)}")
        raise Exception(f"Failed to create Business Logic Plan Generator: {str(e)}")
