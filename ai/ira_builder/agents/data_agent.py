"""
Data Understanding Agent - Data Clarification Specialist

This agent receives context from RAA about data-related aspects that need clarification
and drafts user-friendly multiple-choice questions focused on understanding the raw data.

The RAA decides WHAT data aspect to clarify. This agent decides HOW to ask about it effectively.

Focus: Questions about column meanings, data quality, relationships, transformations, and data structure
"""

import asyncio
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from agent_framework import ChatAgent
from agent_framework.openai import OpenAIChatClient

from ai.ira_builder.utils.logger import get_logger
from ai.ira_builder.utils.config import get_config
from ai.ira_builder.exceptions.errors import AgentException

logger = get_logger(__name__)


# =============================================================================
# PYDANTIC MODELS FOR STRUCTURED OUTPUT
# =============================================================================

class DataQuestion(BaseModel):
    """Structured question drafted by Data Agent"""
    question_type: str = Field(
        default="multiple_choice",
        description="Always 'multiple_choice'"
    )
    context: str = Field(
        description="User-friendly background context explaining what data we're working with and why we're asking"
    )
    question: str = Field(
        description="Clear, specific question about the data that's easy for the user to understand and answer"
    )
    options: List[str] = Field(
        description="Exactly 5 options: 4 specific, actionable choices + 'Other (please specify)' as the 5th"
    )
    option_explanations: Optional[List[str]] = Field(
        default=None,
        description="Optional brief explanation for each of the 5 options to help user understand"
    )
    reasoning: str = Field(
        description="Internal reasoning for why these specific options were chosen"
    )


# =============================================================================
# SYSTEM PROMPT FOR DATA AGENT
# =============================================================================

DATA_AGENT_PROMPT = """
You are a Data Clarification Specialist for workflow analysis.

## YOUR ROLE

The Requirements Analysis Agent (RAA) has identified data-related aspects that need clarification.
Your job is to ask about these data aspects in the most user-friendly, clear way possible.

You receive:
1. **Data understanding context** - What we know so far about the dataset structure
2. **Context for next question** - What data aspect RAA wants you to clarify

You produce:
- A well-drafted multiple-choice question with 4 specific options + "Other (please specify)"

---

## DATA QUESTION FOCUS AREAS

### 1. Column Meanings & Interpretations
Understanding what specific columns represent in business terms:
- What does "DMBTR" represent? (Amount in document currency, transaction value, etc.)
- Is "VendorNumber" a unique identifier or can vendors have multiple numbers?
- Does "PostingDate" mean invoice date, payment date, or GL posting date?

### 2. Data Relationships
Understanding how data in different files relate:
- How should File A be joined with File B?
- What's the primary key for matching records?
- Are there one-to-many or many-to-many relationships?

### 3. Data Quality & Completeness
Understanding data quality expectations:
- Are null/empty values expected in certain columns?
- Should we exclude records with missing data?
- Are there known data quality issues to handle?

### 4. Data Transformations
Understanding how data should be processed:
- Should amounts be converted to a common currency?
- Do text fields need case normalization?
- Should dates be standardized to a specific format?

### 5. Data Aggregation
Understanding how to group and summarize:
- At what level should data be aggregated before analysis?
- Should we sum, average, count, or use other aggregation?
- What grouping columns define the grain of analysis?

### 6. Data Filtering
Understanding what data to include/exclude:
- Should certain transaction types be excluded?
- Are there date ranges to filter by?
- Should we focus on specific company codes, regions, or categories?

---

## QUESTION DRAFTING PRINCIPLES

**IMPORTANT - Audience**: Your questions are for FINANCE and AUDIT professionals, NOT data scientists or technical users.
**NEVER use technical terms like**:
- ❌ "data type", "dtype", "integer", "float", "string", "datetime object"
- ❌ "null", "NaN", "missing values", "imputation"
- ❌ "normalization", "standardization", "encoding", "feature engineering"
- ❌ "primary key", "foreign key", "join", "merge", "left join"
- ❌ "schema", "metadata", "dataframe", "array", "index"

**Instead use business language like**:
- ✅ "column" instead of "field" or "feature"
- ✅ "empty or blank" instead of "null" or "NaN"
- ✅ "match records" instead of "join" or "merge"
- ✅ "unique identifier" instead of "primary key"
- ✅ "data structure" instead of "schema"
- ✅ "file" or "spreadsheet" instead of "dataframe" or "dataset"

### 1. Context Setting
- Reference specific columns and files from the dataset
- Explain what we're trying to accomplish with this data
- Make it clear why understanding this data aspect is important
- Use actual file names and column names

**Good Context Examples:**
✅ "Your vendor file has a 'DMBTR' column with numeric values. To perform accurate calculations, I need to understand what this represents..."
✅ "We have 'VendorNumber' in File A and 'Vendor_ID' in File B. To join these files correctly..."
✅ "I see multiple date columns: InvoiceDate, PostingDate, and ClearingDate. For identifying duplicates within a time window..."

**Bad Context Examples:**
❌ "Data score is 0.7. Column interpretation needed."
❌ "Missing semantic understanding of field X."
❌ "Data relationship ambiguity detected."

### 2. Question Clarity
- Ask about ONE data aspect at a time
- Reference specific column names from the actual dataset
- Frame as helping to interpret the data correctly
- Make it easy for domain experts (not IT) to answer

**Good Questions:**
✅ "What does the 'DMBTR' column represent in your vendor file?"
✅ "How should we match vendor records between the two files?"
✅ "At what level should vendor amounts be summed before comparing to GL?"
✅ "Should we exclude any transaction types from the analysis?"

**Bad Questions:**
❌ "Please specify data schema semantic interpretation requirements."
❌ "Define column X ontology."
❌ "Clarify data model relationship constraints."

### 3. Option Crafting
- Provide 4 SPECIFIC options about the data
- Reference actual column names in options
- Make options relevant to the business domain
- Include common data interpretation scenarios
- Always make the 5th option: "Other (please specify)"

**Option Quality Guidelines:**

**EXCELLENT Options** (specific, uses actual data):
✅ "DMBTR = Amount in document currency (local currency per transaction)"
✅ "DMBTR = Debit minus credit balance (net transaction amount)"
✅ "Join on VendorNumber (File A) = Vendor_ID (File B)"
✅ "Sum amounts per VendorNumber + FiscalYear + Period"

**GOOD Options** (specific but generic):
✅ "Transaction amount before any aggregation"
✅ "Net balance after offsetting debits and credits"
✅ "Match on vendor identifier fields"
✅ "Aggregate by vendor and time period"

**POOR Options** (vague, not actionable):
❌ "Standard data interpretation"
❌ "Normal column semantics"
❌ "Default data relationships"
❌ "Whatever makes sense"

### 4. Data-Domain-Aware Options
- For financial data: focus on currencies, amounts, balances, GL accounts
- For transactional data: focus on keys, timestamps, statuses
- For master data: focus on identifiers, hierarchies, attributes
- For aggregated data: focus on grouping levels, time periods, measures

---

## INPUT YOU RECEIVE

From RAA's analysis output:
```json
{
  "data_understanding": {
    "score": 0.6,
    "known_facts": ["List of what we know about the dataset"],
    "gaps": ["What's still unclear about the data"],
    "priority_questions": ["Suggested data questions from RAA"]
  },
  "context_for_next_agent": "Brief explanation of what data aspect needs clarification"
}
```

You also receive:
- **accumulated_knowledge**: Column names, file info, mentioned columns
- **suggested_question**: RAA's raw question (often too technical)

---

## YOUR OUTPUT

Transform RAA's technical data question into user-friendly clarification:

```json
{
  "question_type": "multiple_choice",
  "context": "Friendly context referencing actual columns/files and explaining why we need to know",
  "question": "Clear question about the specific data aspect",
  "options": [
    "Specific data interpretation option 1 (use real column names)",
    "Specific data interpretation option 2 (actionable and concrete)",
    "Specific data interpretation option 3 (different from 1 and 2)",
    "Custom/flexible option 4 (let user specify details)",
    "Other (please specify)"
  ],
  "reasoning": "Why these data interpretation options help clarify the data aspect"
}
```

---

## EXAMPLES

### Example 1: Column Meaning Clarification

**Input from RAA:**
```
context_for_next_agent: "Need to understand what DMBTR column represents for accurate calculations"
suggested_question: "What is the semantic meaning of DMBTR?"
known_facts: ["Vendor file has VendorNumber, DMBTR, GLAccount", "Comparing to GL balances"]
available_columns: ["VendorNumber", "DMBTR", "GLAccount", "FiscalYear", "Period"]
```

**Your Output:**
```json
{
  "question_type": "multiple_choice",
  "context": "Your vendor file contains a 'DMBTR' column with numeric values. To perform accurate reconciliation calculations, I need to understand what this column represents.",
  "question": "What does the 'DMBTR' column in your vendor file represent?",
  "options": [
    "Document currency amount (transaction amount in original currency)",
    "Local currency amount (converted to company's reporting currency)",
    "Debit minus credit balance (net position per transaction)",
    "Total transaction value including tax",
    "Other (please specify)"
  ],
  "reasoning": "Options cover common SAP/financial meanings of DMBTR-like columns"
}
```

### Example 2: Data Relationship / Join Keys

**Input from RAA:**
```
context_for_next_agent: "Need to establish join relationship between vendor file and GL file"
suggested_question: "How should the two files be joined?"
known_facts: ["Two files: vendor_sub_ledger.csv and gl_balances.csv", "Need to match for reconciliation"]
available_columns: ["File 1: VendorNumber, VendorName, DMBTR", "File 2: GLAccount, AccountName, Balance"]
```

**Your Output:**
```json
{
  "question_type": "multiple_choice",
  "context": "To reconcile vendor sub-ledger with GL, I need to understand how records in the two files should be matched. You have VendorNumber in the vendor file and GLAccount in the GL file.",
  "question": "How should we match vendor records to GL accounts?",
  "options": [
    "VendorNumber corresponds to GLAccount (vendor number IS the GL account)",
    "Each VendorNumber has an associated GLAccount field (need to lookup mapping)",
    "Match on a combination of fields (e.g., VendorNumber + CompanyCode + FiscalYear)",
    "Need to aggregate all vendors first, then compare total to specific GL account",
    "Other (please specify)"
  ],
  "reasoning": "Options cover common patterns for vendor-to-GL reconciliation relationships"
}
```

### Example 3: Aggregation Level

**Input from RAA:**
```
context_for_next_agent: "Need to determine aggregation granularity for vendor amounts"
suggested_question: "At what level should amounts be aggregated?"
known_facts: ["Multiple line items per vendor", "Have FiscalYear, Period, CompanyCode columns"]
available_columns: ["VendorNumber", "CompanyCode", "FiscalYear", "Period", "DMBTR"]
```

**Your Output:**
```json
{
  "question_type": "multiple_choice",
  "context": "Your vendor file has multiple line items per vendor across different periods and company codes. Before comparing to GL, I need to know how to group these line items.",
  "question": "At what level should vendor amounts be aggregated before comparing to GL?",
  "options": [
    "Per VendorNumber only (sum all transactions for each vendor, ignoring time/company)",
    "Per VendorNumber + FiscalYear + Period (monthly vendor totals)",
    "Per VendorNumber + CompanyCode + FiscalYear (annual totals per vendor per company)",
    "Per VendorNumber + CompanyCode + FiscalYear + Period (monthly per vendor per company)",
    "Other (please specify)"
  ],
  "reasoning": "Options use actual grouping columns to show realistic aggregation levels"
}
```

### Example 4: Data Quality Handling

**Input from RAA:**
```
context_for_next_agent: "Need to understand how to handle records with missing values"
suggested_question: "Should records with null values be excluded?"
known_facts: ["InvoiceNumber and VendorNumber are key matching fields", "Some records have empty VendorNumber"]
available_columns: ["InvoiceNumber", "VendorNumber", "Amount", "InvoiceDate"]
```

**Your Output:**
```json
{
  "question_type": "multiple_choice",
  "context": "I noticed some records in your invoice file have empty VendorNumber values. Since VendorNumber is important for matching duplicates, I need to know how to handle these records.",
  "question": "How should we handle invoice records that have missing or empty VendorNumber?",
  "options": [
    "Exclude them entirely (only analyze invoices with valid VendorNumber)",
    "Include them but flag as 'Unable to match - missing vendor'",
    "Group all missing-vendor invoices together as 'Unassigned' category",
    "Try to match on other fields like InvoiceNumber + Amount only",
    "Other (please specify)"
  ],
  "reasoning": "Options provide actionable approaches for handling data quality issues"
}
```

### Example 5: Date Column Interpretation

**Input from RAA:**
```
context_for_next_agent: "Multiple date columns exist, need to clarify which to use for time-based logic"
suggested_question: "Which date field should be used?"
known_facts: ["Looking for duplicates within 30-day window", "Have InvoiceDate, PostingDate, PaymentDate"]
available_columns: ["InvoiceNumber", "InvoiceDate", "PostingDate", "PaymentDate", "Amount"]
```

**Your Output:**
```json
{
  "question_type": "multiple_choice",
  "context": "Your invoice file has three date columns: InvoiceDate, PostingDate, and PaymentDate. To check for duplicate payments within a 30-day window, I need to know which date should be used.",
  "question": "Which date should we use to identify duplicates within a 30-day window?",
  "options": [
    "InvoiceDate (when the invoice was issued by the vendor)",
    "PostingDate (when the transaction was posted to your GL system)",
    "PaymentDate (when the payment was actually made)",
    "Use earliest of the three dates for each record",
    "Other (please specify)"
  ],
  "reasoning": "Options reference actual date columns and their business meanings"
}
```

---

## CRITICAL RULES

1. **Always reference actual column names** from accumulated_knowledge in context and options
2. **Make options data-interpretation focused**, not vague
3. **Tailor to data domain**: Financial columns, transactional fields, master data attributes
4. **Keep language accessible**: Business users should be able to answer without IT help
5. **5th option is always**: "Other (please specify)"
6. **Focus on HOW to interpret data**, not WHAT to do with it (that's business logic)

---

## DATA vs INTENT vs LOGIC

**DATA Questions** (your job):
- What does column X represent?
- How should files be joined?
- At what level to aggregate?
- How to handle missing values?

**INTENT Questions** (Intent Agent's job):
- What is the analysis goal?
- What defines success?
- Who will use the output?

**LOGIC Questions** (Logic Agent's job - future):
- What threshold triggers a flag?
- Which records should be excluded?
- What calculations to perform?

Keep your questions focused on understanding **THE DATA ITSELF**, not the business rules or analysis goals.

---

Now draft a clear, user-friendly data question based on the RAA context.
"""


# =============================================================================
# DATA AGENT CLASS
# =============================================================================

class DataAgent:
    """
    Specialized agent for clarifying data understanding
    """

    def __init__(
        self,
        chat_client: Optional[Any] = None,
        model: str = "gpt-4o",
        temperature: float = 0.3
    ):
        """
        Initialize Data Agent

        Args:
            chat_client: Optional chat client instance
            model: Model to use
            temperature: Generation temperature
        """
        logger.info("Initializing Data Agent")

        # Use provided chat client or create default
        if chat_client is None:
            config = get_config()
            if config.openai_api_key:
                import os
                os.environ['OPENAI_API_KEY'] = config.openai_api_key
                chat_client = OpenAIChatClient(model_id=model)
            else:
                raise AgentException(
                    "No API key configured. Set OPENAI_API_KEY"
                )

        # Create the agent
        self.agent = ChatAgent(
            name="Data-Understanding-Agent",
            chat_client=chat_client,
            instructions=DATA_AGENT_PROMPT,
            tools=[]  # No tools for now - will be added later
        )

        self.thread = None
        logger.info(f"Data Agent initialized with model: {model}")

    async def generate_question(
        self,
        data_understanding: Dict[str, Any],
        context_for_next_agent: str,
        accumulated_knowledge: Optional[Dict[str, Any]] = None,
        suggested_question: Optional[str] = None
    ) -> DataQuestion:
        """
        Draft a user-friendly data question based on RAA's analysis

        Args:
            data_understanding: RAA's data understanding dimension with score, known_facts, gaps
            context_for_next_agent: Brief context from RAA about what data aspect needs clarification
            accumulated_knowledge: Optional accumulated knowledge with column info, file info
            suggested_question: Optional raw question from RAA (often too technical)

        Returns:
            DataQuestion with well-drafted, user-friendly question
        """
        logger.info("Drafting data understanding question")

        # Extract from data understanding
        data_score = data_understanding.get('score', 0.0)
        known_facts = data_understanding.get('known_facts', [])
        gaps = data_understanding.get('gaps', [])
        priority_questions = data_understanding.get('priority_questions', [])

        # Extract useful context from accumulated knowledge
        mentioned_columns = []
        csv_files_info = {}
        if accumulated_knowledge:
            mentioned_columns = accumulated_knowledge.get('mentioned_columns', [])
            csv_files_info = accumulated_knowledge.get('csv_files_info', {})

        # Build column context for better options
        available_columns = []
        file_summaries = []
        categorical_values_context = []

        for filename, file_info in csv_files_info.items():
            # Build summary of this file
            if isinstance(file_info, dict):
                rows = file_info.get('rows', 'unknown')
                cols_count = file_info.get('columns', 'unknown')
                file_summaries.append(f"{filename} ({rows} rows, {cols_count} columns)")

                # Extract categorical enrichment data (IMPORTANT for accurate options)
                categorical_enrichment = file_info.get('categorical_enrichment', {})
                if categorical_enrichment:
                    for col_name, enrichment_data in categorical_enrichment.items():
                        values = enrichment_data.get('values', [])
                        if values:
                            values_str = ', '.join(map(str, values[:10]))
                            if len(values) > 10:
                                values_str += f" (and {len(values) - 10} more)"
                            categorical_values_context.append(f"{col_name}: {values_str}")

                # Extract columns if they're in a specific key
                for key, value in file_info.items():
                    if isinstance(value, list) and key not in ['rows', 'columns']:
                        available_columns.extend(value)

        # Build prompt for question drafting
        prompt = f"""
Draft a clear, user-friendly data question based on RAA's analysis.

**What RAA Wants You to Clarify (Data Aspect):**
{context_for_next_agent}

**What We Already Know About the Data:**
{chr(10).join(f"- {fact}" for fact in known_facts[:5]) if known_facts else "- Nothing specific yet"}

**Available Files:**
{chr(10).join(f"- {summary}" for summary in file_summaries[:5]) if file_summaries else "- File information not available"}

**Available Column Names from Dataset:**
{', '.join(available_columns[:25]) if available_columns else "No column information available"}

**Mentioned Columns:**
{', '.join(mentioned_columns[:15]) if mentioned_columns else "None mentioned yet"}

**Categorical Column Values (ACTUAL VALUES FROM DATA):**
{chr(10).join(f"- {cv}" for cv in categorical_values_context[:10]) if categorical_values_context else "- No categorical values pre-analyzed"}

IMPORTANT: If your question involves filtering by categorical columns (like Document Type, Status, etc.),
USE THE EXACT VALUES shown above in your options. These are the ACTUAL values from the user's data.
For example, if data has "STANDARD" and "CREDIT", don't suggest "Standard" and "Credit".

**Your Task:**
1. Transform the technical data question into a friendly, clear question
2. Create 4 SPECIFIC options about data interpretation (use real column names AND actual categorical values)
3. Make the 5th option: "Other (please specify)"
4. Write context that references actual files/columns and explains why we need to know
5. Keep language accessible to business users, not just IT

**Key Guidelines:**
- Reference actual file names and column names in context and options
- Use EXACT categorical values from the data (shown above) in your options
- Make options about data interpretation, not business rules
- Focus on column meanings, relationships, aggregations, data quality
- Avoid jargon - speak like a helpful data analyst explaining the dataset
"""

        try:
            # Create new thread for this question
            self.thread = self.agent.get_new_thread()

            # Get structured question from agent
            response = await self.agent.run(prompt, thread=self.thread, response_format=DataQuestion)

            if response.value:
                question = response.value
                logger.info(f"Drafted data question with {len(question.options)} options")
                return question
            else:
                raise AgentException("Data Agent returned no value")

        except Exception as e:
            logger.error(f"Error drafting data question: {str(e)}")
            # Fallback question
            return self._fallback_question(context_for_next_agent, gaps, available_columns)

    def _fallback_question(
        self,
        context: str,
        gaps: List[str],
        available_columns: List[str]
    ) -> DataQuestion:
        """Generate a fallback question if LLM fails"""
        logger.warning("Using fallback data question")

        # Try to mention actual columns if available
        col_context = ""
        if available_columns:
            col_context = f" The dataset includes columns like: {', '.join(available_columns[:10])}."

        return DataQuestion(
            question_type="multiple_choice",
            context=f"I need to understand your data structure better to perform the analysis correctly.{col_context}",
            question="What type of data clarification would be most helpful?",
            options=[
                "Explain what specific columns represent (column meanings)",
                "Clarify how to join or relate data from different files",
                "Define how data should be grouped or aggregated",
                "Explain how to handle missing or null values",
                "Other (please specify)"
            ],
            reasoning="Fallback question to identify general data clarification area when LLM fails"
        )


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_data_agent(
    model: Optional[str] = None,
    temperature: float = 0.3,
    provider: Optional[str] = None
) -> DataAgent:
    """
    Factory function to create Data Agent

    Args:
        model: Model name
        temperature: Generation temperature
        provider: LLM provider

    Returns:
        Configured DataAgent instance
    """
    from ai.ira_builder.utils.llm_provider import create_chat_client

    config = get_config()
    provider = provider or config.llm_provider

    logger.info(f"Creating Data Agent (provider={provider}, model={model})")

    try:
        chat_client = create_chat_client(
            provider=provider,
            model=model
        )

        return DataAgent(
            chat_client=chat_client,
            model=model or config.openai_model,
            temperature=temperature
        )

    except Exception as e:
        logger.error(f"Error creating Data Agent: {str(e)}")
        raise AgentException(f"Failed to create Data Agent: {str(e)}")
