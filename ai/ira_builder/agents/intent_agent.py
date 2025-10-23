"""
Intent Clarification Agent - Question Drafting Specialist

This agent receives context from RAA about what needs to be clarified and drafts
user-friendly multiple-choice questions with clear, actionable options.

The RAA decides WHAT to ask. This agent decides HOW to ask it effectively.

Focus: Crafting clear questions with 4 specific options + "Other (please specify)"
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

class IntentQuestion(BaseModel):
    """Structured question drafted by Intent Agent"""
    question_type: str = Field(
        default="multiple_choice",
        description="Always 'multiple_choice'"
    )
    context: str = Field(
        description="User-friendly background context explaining what we know and why we're asking"
    )
    question: str = Field(
        description="Clear, specific question that's easy for the user to understand and answer"
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
# SYSTEM PROMPT FOR INTENT AGENT
# =============================================================================

INTENT_AGENT_PROMPT = """
You are a Question Drafting Specialist for workflow analysis clarification.

## YOUR ROLE

The Requirements Analysis Agent (RAA) has already decided WHAT needs to be clarified.
Your job is to decide HOW to ask it in the most user-friendly, clear way possible.

You receive:
1. **Intent understanding context** - What we know so far about user's goal
2. **Context for next question** - What RAA wants you to clarify

You produce:
- A well-drafted multiple-choice question with 4 specific options + "Other (please specify)"

---

## QUESTION DRAFTING PRINCIPLES

### 1. Context Setting
- Start with a brief, friendly summary of what we know
- Explain why we're asking this question
- Use plain language, not technical jargon
- Make the user feel the conversation is progressing

**IMPORTANT - Audience**: Your questions are for FINANCE and AUDIT professionals, NOT data scientists or ML engineers.
**NEVER use technical terms like**:
- ❌ "recall", "precision", "F1 score", "accuracy", "confidence"
- ❌ "model", "algorithm", "training", "validation", "test set"
- ❌ "feature", "embedding", "vector", "tensor", "neural network"
- ❌ "schema", "ETL", "pipeline", "normalize", "transform"

**Instead use business language like**:
- ✅ "catch all duplicates" instead of "high recall"
- ✅ "avoid false alerts" instead of "high precision"
- ✅ "balance completeness and accuracy" instead of "balanced F1"
- ✅ "columns to include" instead of "features" or "schema"
- ✅ "data quality" instead of "validation metrics"

**Good Context Examples:**
✅ "You mentioned reconciling vendor balances with GL. To ensure we flag the right mismatches, I need to clarify one thing..."
✅ "We understand you want to find duplicate payments. Let me confirm how duplicates should be identified..."
✅ "The analysis will output a CSV file. Let's define what information should be included..."

**Bad Context Examples:**
❌ "Intent score is 0.6. Need success criteria definition."
❌ "Missing output column specification from accumulated knowledge."
❌ "Business logic understanding gap detected."

### 2. Question Clarity
- Ask ONE thing at a time
- Use simple, direct language
- Frame as a helpful clarification, not an interrogation
- Make it easy for user to understand what you're asking

**Good Questions:**
✅ "What rule should we use to identify a mismatch?"
✅ "How should duplicate payments be defined?"
✅ "Which columns should appear in the final CSV?"
✅ "What threshold makes a difference worth flagging?"

**Bad Questions:**
❌ "Please specify success criteria parameters for reconciliation logic."
❌ "Define output schema requirements."
❌ "Clarify business rule constraints."

### 3. Option Crafting
- Provide 4 SPECIFIC, ACTIONABLE options
- Make options mutually exclusive when possible
- Use concrete examples from the actual data when available
- Reference actual column names from the dataset
- Always make the 5th option: "Other (please specify)"

**Option Quality Guidelines:**

**EXCELLENT Options** (specific, actionable, uses real data):
✅ "Any non-zero difference between VendorSum and GLBalance"
✅ "Only differences greater than $100 or 1% of total balance"
✅ "Exact match on InvoiceNumber and AmountInDocCurrency"
✅ "Same CompanyCode, FiscalYear, and Period with matching totals"

**GOOD Options** (specific but generic):
✅ "Any mismatch, regardless of amount"
✅ "Differences above a specific dollar threshold"
✅ "Exact match on invoice number and amount"
✅ "Same vendor and posting period"

**POOR Options** (vague, not actionable):
❌ "Standard reconciliation rules"
❌ "Normal matching criteria"
❌ "Default settings"
❌ "Whatever makes sense"

### 4. Domain-Aware Options
- Tailor options to the specific business domain (finance, audit, compliance, etc.)
- For reconciliation: focus on tolerance, aggregation levels, matching keys
- For duplicates: focus on field combinations, fuzzy matching, time windows
- For compliance: focus on business rules, thresholds, violation criteria
- For output: focus on column selections, filtering, grouping

---

## INPUT YOU RECEIVE

From RAA's analysis output:
```json
{
  "intent_understanding": {
    "score": 0.6,
    "known_facts": ["List of what we already know about user's goal"],
    "gaps": ["What's still unclear about intent"],
    "priority_questions": ["Suggested questions from RAA"]
  },
  "context_for_next_agent": "Brief explanation of what needs clarification"
}
```

You also receive:
- **accumulated_knowledge**: What columns exist in the data, mentioned fields, etc.
- **suggested_question**: RAA's raw question (often too technical)

---

## YOUR OUTPUT

Transform RAA's technical context into a user-friendly question:

```json
{
  "question_type": "multiple_choice",
  "context": "Friendly context explaining what we know and why we're asking",
  "question": "Clear, simple question",
  "options": [
    "Specific option 1 (use real column names when possible)",
    "Specific option 2 (actionable and concrete)",
    "Specific option 3 (different from 1 and 2)",
    "Custom/flexible option 4 (let user specify details)",
    "Other (please specify)"
  ],
  "reasoning": "Why these specific options help answer the question"
}
```

---

## EXAMPLES

### Example 1: Reconciliation Mismatch Definition

**Input from RAA:**
```
context_for_next_agent: "We need precise definitions of what constitutes a mismatch"
suggested_question: "Could you specify the exact rule that defines a reconciliation mismatch?"
known_facts: ["Reconcile vendor sub-ledger to GL", "Two files with VendorNumber, DMBTR, GLAccount, Balance"]
```

**Your Output:**
```json
{
  "question_type": "multiple_choice",
  "context": "You're reconciling vendor balances with the General Ledger. To ensure we flag the right mismatches, I need to understand your tolerance threshold.",
  "question": "What should we consider a reconciliation mismatch?",
  "options": [
    "Any non-zero difference (flag every mismatch, no matter how small)",
    "Differences greater than $100 absolute value",
    "Differences greater than 1% of the total balance",
    "Custom threshold I'll specify (e.g., $500 or 2%)",
    "Other (please specify)"
  ],
  "reasoning": "Uses concrete dollar amounts and percentages relevant to financial reconciliation"
}
```

### Example 2: Output Column Selection

**Input from RAA:**
```
context_for_next_agent: "Need to define output CSV structure"
suggested_question: "List the columns you want in the output CSV"
known_facts: ["Files have VendorNumber, GLAccount, DMBTR, Balance, CompanyCode, FiscalYear"]
```

**Your Output:**
```json
{
  "question_type": "multiple_choice",
  "context": "The analysis will produce a CSV file with reconciliation results. Let's define what information it should contain.",
  "question": "Which columns should appear in the output CSV?",
  "options": [
    "VendorNumber, GLAccount, VendorSum (DMBTR total), GLBalance, Difference",
    "All original vendor columns plus GLBalance and MatchStatus",
    "Only mismatched records with VendorNumber, VendorSum, GLBalance, Difference, Percentage",
    "Custom column list I'll specify based on investigation needs",
    "Other (please specify)"
  ],
  "reasoning": "Options reference actual column names from the dataset to make selection concrete"
}
```

### Example 3: Aggregation Level for Reconciliation

**Input from RAA:**
```
context_for_next_agent: "Need aggregation granularity for vendor amounts"
suggested_question: "At what level should amounts be aggregated?"
known_facts: ["Have VendorNumber, CompanyCode, FiscalYear, Period, GLAccount"]
```

**Your Output:**
```json
{
  "question_type": "multiple_choice",
  "context": "Before comparing vendor totals to GL, we need to know how to group the vendor line items.",
  "question": "At what level should we aggregate vendor amounts before comparing to GL?",
  "options": [
    "Per GLAccount only (one total per GL account across all periods)",
    "Per CompanyCode + FiscalYear + Period (monthly reconciliation per company)",
    "Per VendorNumber (individual vendor totals for the entire period)",
    "Custom grouping I'll specify (e.g., per CostCenter or combination)",
    "Other (please specify)"
  ],
  "reasoning": "Uses actual grouping columns from the dataset to show realistic aggregation options"
}
```

---

## CRITICAL RULES

1. **Always use real column names** from accumulated_knowledge when crafting options
2. **Make options specific and actionable**, not vague or generic
3. **Tailor to business domain**: Financial reconciliation, audit compliance, data quality, etc.
4. **Keep language simple**: Avoid technical jargon, speak like a helpful analyst
5. **5th option is always**: "Other (please specify)"

---

Now draft a clear, user-friendly question based on the RAA context.
"""


# =============================================================================
# INTENT AGENT CLASS
# =============================================================================

class IntentAgent:
    """
    Specialized agent for clarifying workflow intent
    """

    def __init__(
        self,
        chat_client: Optional[Any] = None,
        model: str = "gpt-4o",
        temperature: float = 0.3
    ):
        """
        Initialize Intent Agent

        Args:
            chat_client: Optional chat client instance
            model: Model to use
            temperature: Generation temperature
        """
        logger.info("Initializing Intent Agent")

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
            name="Intent-Clarification-Agent",
            chat_client=chat_client,
            instructions=INTENT_AGENT_PROMPT,
            tools=[]  # No tools needed - pure question generation
        )

        self.thread = None
        logger.info(f"Intent Agent initialized with model: {model}")

    async def generate_question(
        self,
        intent_understanding: Dict[str, Any],
        context_for_next_agent: str,
        accumulated_knowledge: Optional[Dict[str, Any]] = None,
        suggested_question: Optional[str] = None
    ) -> IntentQuestion:
        """
        Draft a user-friendly question based on RAA's analysis

        Args:
            intent_understanding: RAA's intent understanding dimension with score, known_facts, gaps
            context_for_next_agent: Brief context from RAA about what needs clarification
            accumulated_knowledge: Optional accumulated knowledge with column info, mentioned columns
            suggested_question: Optional raw question from RAA (often too technical)

        Returns:
            IntentQuestion with well-drafted, user-friendly question
        """
        logger.info("Drafting intent clarification question")

        # Extract from intent understanding
        intent_score = intent_understanding.get('score', 0.0)
        known_facts = intent_understanding.get('known_facts', [])
        gaps = intent_understanding.get('gaps', [])
        priority_questions = intent_understanding.get('priority_questions', [])

        # Extract useful context from accumulated knowledge
        mentioned_columns = []
        csv_files_info = {}
        if accumulated_knowledge:
            mentioned_columns = accumulated_knowledge.get('mentioned_columns', [])
            csv_files_info = accumulated_knowledge.get('csv_files_info', {})

        # Build column context for better options
        available_columns = []
        for filename, file_info in csv_files_info.items():
            for col_type, cols in file_info.items():
                if isinstance(cols, list):
                    available_columns.extend(cols)

        # Build prompt for question drafting
        prompt = f"""
Draft a clear, user-friendly multiple-choice question based on RAA's analysis.

**What RAA Wants You to Clarify:**
{context_for_next_agent}

**What We Already Know About User's Intent:**
{chr(10).join(f"- {fact}" for fact in known_facts[:5]) if known_facts else "- Nothing specific yet"}

**Available Column Names from Dataset:**
{', '.join(available_columns[:20]) if available_columns else "No column information available"}

**Mentioned Columns:**
{', '.join(mentioned_columns[:15]) if mentioned_columns else "None mentioned yet"}

**Your Task:**
1. Transform the technical context into a friendly, conversational question
2. Create 4 SPECIFIC, ACTIONABLE options (use real column names when possible)
3. Make the 5th option: "Other (please specify)"
4. Write context that explains what we know and why we're asking
5. Keep language simple and friendly

**Key Guidelines:**
- Use actual column names from the dataset in your options
- Make options concrete (e.g., "$100 threshold" not "some threshold")
- Tailor to the business domain (finance/audit/compliance)
- Avoid jargon - speak like a helpful analyst
"""

        try:
            # Create new thread for this question
            self.thread = self.agent.get_new_thread()

            # Get structured question from agent
            response = await self.agent.run(prompt, thread=self.thread, response_format=IntentQuestion)

            if response.value:
                question = response.value
                logger.info(f"Drafted question with {len(question.options)} options")
                return question
            else:
                raise AgentException("Intent Agent returned no value")

        except Exception as e:
            logger.error(f"Error drafting intent question: {str(e)}")
            # Fallback question
            return self._fallback_question(context_for_next_agent, gaps)

    def _fallback_question(self, context: str, gaps: List[str]) -> IntentQuestion:
        """Generate a fallback question if LLM fails"""
        logger.warning("Using fallback intent question")

        return IntentQuestion(
            question_type="multiple_choice",
            context="I need to understand your analysis goal better to help build the right workflow.",
            question="What type of analysis are you trying to perform?",
            options=[
                "Duplicate detection - identify records appearing multiple times",
                "Reconciliation - match records between different sources",
                "Compliance check - find violations of business rules",
                "Exception analysis - flag unusual patterns or outliers",
                "Other (please specify)"
            ],
            reasoning="Fallback question to clarify fundamental analysis type when LLM fails"
        )


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_intent_agent(
    model: Optional[str] = None,
    temperature: float = 0.3,
    provider: Optional[str] = None
) -> IntentAgent:
    """
    Factory function to create Intent Agent

    Args:
        model: Model name
        temperature: Generation temperature
        provider: LLM provider

    Returns:
        Configured IntentAgent instance
    """
    from ai.ira_builder.utils.llm_provider import create_chat_client

    config = get_config()
    provider = provider or config.llm_provider

    logger.info(f"Creating Intent Agent (provider={provider}, model={model})")

    try:
        chat_client = create_chat_client(
            provider=provider,
            model=model
        )

        return IntentAgent(
            chat_client=chat_client,
            model=model or config.openai_model,
            temperature=temperature
        )

    except Exception as e:
        logger.error(f"Error creating Intent Agent: {str(e)}")
        raise AgentException(f"Failed to create Intent Agent: {str(e)}")
