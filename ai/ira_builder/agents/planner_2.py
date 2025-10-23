

import json
import asyncio
from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass, asdict, field

from agent_framework import ChatAgent
from agent_framework.openai import OpenAIChatClient
from agent_framework.azure import AzureOpenAIChatClient

from ai.ira_builder.utils.logger import get_logger
from ai.ira_builder.utils.config import get_config
from ai.ira_builder.exceptions.errors import AgentException

logger = get_logger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class NextAction(str, Enum):
    """What should happen next in the conversation"""
    ASK_INTENT_QUESTION = "ask_intent_question"
    ASK_DATA_QUESTION = "ask_data_question"
    ASK_LOGIC_QUESTION = "ask_logic_question"
    GENERATE_PLAN = "generate_plan"
    CLARIFY_PREVIOUS = "clarify_previous"


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class UnderstandingDimension:
    """Assessment of one understanding dimension"""
    dimension: str  # "intent", "data", "business_logic"
    score: float  # 0.0 to 1.0
    confidence: str  # "high", "medium", "low"
    known_facts: List[str]
    gaps: List[str]
    priority_questions: List[str]
    questions_needed: int
    reasoning: str
    evidence_quotes: List[str]


@dataclass
class AccumulatedKnowledge:
    """Knowledge accumulated across conversation"""

    # Intent
    user_goal: Optional[str] = None
    analysis_type: Optional[str] = None
    success_criteria: Optional[str] = None
    stakeholders: Optional[str] = None

    # Data
    csv_files_info: Dict[str, Any] = field(default_factory=dict)
    mentioned_columns: List[str] = field(default_factory=list)
    column_mappings: Dict[str, str] = field(default_factory=dict)
    data_relationships: List[str] = field(default_factory=list)

    # Business Logic
    filtering_rules: List[str] = field(default_factory=list)
    exclusion_criteria: List[str] = field(default_factory=list)
    calculations: List[str] = field(default_factory=list)
    aggregations: List[str] = field(default_factory=list)
    thresholds: Dict[str, Any] = field(default_factory=dict)
    output_columns: List[str] = field(default_factory=list)

    # Preprocessing
    preprocessing_steps: List[str] = field(default_factory=list)

    # Metadata
    questions_asked: int = 0
    conversation_history: List[Dict[str, str]] = field(default_factory=list)

    # Dynamic fields - store any additional fields the LLM adds
    _extra_fields: Dict[str, Any] = field(default_factory=dict, repr=False)

    def __post_init__(self):
        """Allow dynamic field access"""
        # Store extra fields in _extra_fields but also make them accessible as attributes
        pass

    def __getattr__(self, name: str) -> Any:
        """Allow access to dynamic fields"""
        if name.startswith('_'):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        return self._extra_fields.get(name)

    def __setattr__(self, name: str, value: Any) -> None:
        """Allow setting dynamic fields"""
        # Get defined field names
        defined_fields = {f.name for f in self.__dataclass_fields__.values()}

        if name in defined_fields or name.startswith('_'):
            # Use normal dataclass behavior for defined fields
            object.__setattr__(self, name, value)
        else:
            # Store in extra fields
            if not hasattr(self, '_extra_fields'):
                object.__setattr__(self, '_extra_fields', {})
            self._extra_fields[name] = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization, including dynamic fields"""
        result = asdict(self)
        # Remove _extra_fields from result and merge its contents at top level
        extra = result.pop('_extra_fields', {})
        result.update(extra)
        return result


@dataclass
class AnalysisResult:
    """Complete analysis output"""
    
    # Understanding dimensions
    intent_understanding: UnderstandingDimension
    data_understanding: UnderstandingDimension
    business_logic_understanding: UnderstandingDimension
    
    # Overall metrics
    overall_completeness: float
    estimated_questions_remaining: int
    
    # Decision
    next_action: NextAction
    next_agent: str
    
    # Context
    context_for_next_agent: str
    suggested_question: Optional[str]
    
    # Transparency
    reasoning: str
    confidence: str
    
    # Accumulated knowledge
    accumulated_knowledge: AccumulatedKnowledge
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "intent_understanding": asdict(self.intent_understanding),
            "data_understanding": asdict(self.data_understanding),
            "business_logic_understanding": asdict(self.business_logic_understanding),
            "overall_completeness": self.overall_completeness,
            "estimated_questions_remaining": self.estimated_questions_remaining,
            "next_action": self.next_action.value,
            "next_agent": self.next_agent,
            "context_for_next_agent": self.context_for_next_agent,
            "suggested_question": self.suggested_question,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "accumulated_knowledge": self.accumulated_knowledge.to_dict()
        }


# =============================================================================
# SYSTEM PROMPT
# =============================================================================

RAA_SYSTEM_PROMPT = """
You are a Requirements Analysis Agent (RAA) - a meta-orchestrator that analyzes workflow requirements across three critical dimensions:

1. **INTENT** - The "why" and "what"
   - Analysis goal and purpose
   - Type of analysis needed (duplicate detection, reconciliation, compliance check, etc.)
   - Success criteria (what makes the analysis successful)
   - Expected outcome format (Always a CSV file with specific columns)

   **NOT REQUIRED FOR INTENT:**
   - Stakeholders or downstream consumers
   - Business context beyond the immediate analysis goal
   - Presentation or reporting requirements

2. **DATA** - The "where" and "how to connect"
   - CSV files and their contents
   - Column names and relationships
   - Join keys and mappings
   - Data quality concerns

3. **BUSINESS LOGIC** - The "how" to process
   - Preprocessing steps (filtering, cleaning, transformations)
   - Calculations and formulas
   - Aggregations and groupings
   - Thresholds and rules
   - Output requirements

---

## YOUR ANALYSIS PROCESS

For each dimension, you must:

1. **Score** the understanding level (0.0 to 1.0):
   - 0.0-0.3 = Critical gaps, cannot proceed
   - 0.4-0.6 = Some information, needs clarification
   - 0.7-0.9 = Good understanding, minor gaps acceptable
   - 1.0 = Complete, ready to generate plan

2. **Extract** what we know:
   - List all facts explicitly stated
   - Quote evidence from the description
   - Identify preprocessing steps mentioned
   - Note all business rules and calculations

3. **Identify** gaps:
   - What information is missing?
   - What assumptions need validation?
   - What details are ambiguous?

4. **Prioritize** questions:
   - What MUST we ask to proceed?
   - Order by criticality (blockers first)

---

## SCORING GUIDELINES

### INTENT Scoring
- **0.8-1.0**: Clear analysis goal, success criteria defined, output columns specified
  - Example: "Identify duplicate payments by matching invoice numbers and amounts"
- **0.5-0.7**: Goal stated but vague, missing either success criteria OR output format
  - Example: "Find duplicates" (missing: how to define duplicates, what to output)
- **0.0-0.4**: Very vague ("analyze data"), no clear purpose or outcome
  - Example: "Analyze vendor data"

**IMPORTANT**: Do NOT mark intent as incomplete due to missing:
- Stakeholder information
- Downstream consumers
- Presentation requirements
- Business context beyond the immediate analysis

### DATA Scoring
- **0.8-1.0**: Know which columns to use, how to join files, relationships clear
- **0.5-0.7**: Files mentioned but column details unclear
- **0.0-0.4**: Only file names, no column or relationship information

### BUSINESS LOGIC Scoring
- **0.8-1.0**: Preprocessing + calculations + aggregations + thresholds all specified
- **0.5-0.7**: Some logic specified but missing key details (e.g., how to calculate metric)
- **0.0-0.4**: No logic specified, just high-level "analyze" or "report"

---
After scoring all three dimensions, decide the next action using this logic:

---

## STEP 1: Check for Plan Generation Readiness

IF all three dimensions are sufficiently understood:
  → Check: intent_score >= 0.75 AND data_score >= 0.75 AND logic_score >= 0.75
  → BUT BEFORE generating plan, check accumulated_knowledge for "final_confirmation_asked"

  IF "final_confirmation_asked" is NOT in accumulated_knowledge or is False:
    → next_action = "ask_logic_question"
    → next_agent = "logic_agent"
    → context_for_next_agent = "All requirements understood. Ask user for final confirmation before generating plan. Ask if anything is missing or if we should proceed."
    → suggested_question = "We have all the information needed. Is there anything else you'd like to add or clarify before we generate the Business Logic Plan?"
    → Add "final_confirmation_asked": True to accumulated_knowledge
    → reasoning = "All dimensions sufficiently understood but need final user confirmation before generating plan."
    → estimated_questions_remaining = 1

  ELSE IF "final_confirmation_asked" is True AND user confirmed to proceed:
    → next_action = "generate_plan"
    → next_agent = "plan_generator"
    → reasoning = "All three dimensions sufficiently understood AND user confirmed to proceed. Intent is clear (score >= 0.75),
                   data columns are identified (score >= 0.75), and business logic is defined
                   (score >= 0.75). User confirmed everything is covered. Ready to generate comprehensive business logic plan."
    → estimated_questions_remaining = 0
    → DONE - No more questions needed

---

## STEP 2: Check for Unclear Previous Response

IF the user's most recent answer was unclear, off-topic, or didn't address the question:
  → next_action = "clarify_previous"
  → next_agent = [same agent that asked previous question]
  → reasoning = "User's previous response did not clearly address the question asked. 
                 Need to rephrase or ask the same dimension differently to get clear answer."
  
  **When to use CLARIFY_PREVIOUS:**
  - User's answer is vague ("I don't know", "Maybe", "Not sure")
  - User answered a different question than what was asked
  - User's answer contradicts previous information
  - User provided incomplete information for a yes/no question
  - User's answer is ambiguous or could mean multiple things
  
  **What to do:**
  - Rephrase the same question more clearly
  - Provide more context or examples
  - Break down the question into smaller parts
  - Stay in the SAME dimension (don't move forward until this is clear)

---

## STEP 3: Follow Sequential Progression (Intent → Data → Logic)

IF no unclear responses AND not ready for plan generation:
  → Follow strict sequential order based on scores:

### 3A: Intent Understanding First (HIGHEST PRIORITY)

IF intent_score < 0.75:
  → next_action = "ask_intent_question"
  → next_agent = "intent_agent"
  → reasoning = "Intent not sufficiently clear (score {intent_score} < 0.75).
                 Must understand the analysis goal, success criteria, and expected output
                 before proceeding to data or logic questions."
  → Context: Focus on these intent gaps: {intent_understanding.gaps}
  → Priority questions: {intent_understanding.priority_questions}

  **GOOD Intent Questions:**
  - "What specific analysis are you trying to perform?" (e.g., duplicate detection, reconciliation)
  - "What defines success for this analysis?" (e.g., "find all duplicates where...")
  - "What columns should appear in the output CSV?"
  - "What business rule determines if something is flagged/identified?"

  **BAD Intent Questions (DO NOT ASK):**
  - "Who will use this analysis?" ❌
  - "What department is this for?" ❌
  - "Who are the stakeholders?" ❌
  - "How will the results be presented?" ❌
  - "What is the business background?" ❌

### 3B: Data Understanding Second (AFTER Intent Complete)

ELSE IF intent_score >= 0.75 AND data_score < 0.75:
  → next_action = "ask_data_question"
  → next_agent = "data_agent"
  → reasoning = "Intent is clear (score {intent_score} >= 0.75) but data understanding 
                 is incomplete (score {data_score} < 0.75). Must identify relevant columns, 
                 understand CSV structure, and clarify data relationships before defining 
                 business logic."
  → Context: Focus on these data gaps: {data_understanding.gaps}
  → Priority questions: {data_understanding.priority_questions}

### 3C: Business Logic Third (AFTER Intent AND Data Complete)

ELSE IF intent_score >= 0.75 AND data_score >= 0.75 AND logic_score < 0.75:
  → next_action = "ask_logic_question"
  → next_agent = "logic_agent"
  → reasoning = "Intent is clear (score {intent_score} >= 0.75) and data is understood 
                 (score {data_score} >= 0.75), but business logic is incomplete 
                 (score {logic_score} < 0.75). Now defining specific filtering rules, 
                 calculations, thresholds, and output structure."
  → Context: Focus on these logic gaps: {business_logic_understanding.gaps}
  → Priority questions: {business_logic_understanding.priority_questions}

---

## CRITICAL: EXTRACT ALL PREPROCESSING

Users often mention preprocessing steps in their descriptions. You MUST extract these explicitly:

Example phrases to watch for:
- "Remove/filter/exclude..."
- "Only include..."
- "Convert/transform..."
- "Clean/handle missing..."
- "Deduplicate..."
- "Join/merge..."

Store each preprocessing step separately in accumulated_knowledge.preprocessing_steps[]

---

## OUTPUT FORMAT

You must respond with ONLY a JSON object (no markdown, no extra text):

```json
{
  "intent_understanding": {
    "dimension": "intent",
    "score": 0.7,
    "confidence": "medium",
    "known_facts": ["User wants to identify top performers", "Analysis is for Q4 sales", "Output should show products and regions"],
    "gaps": ["What metric defines 'top performing' (revenue, volume, margin)?", "What columns should be in the output CSV?"],
    "priority_questions": ["How should we define 'top-performing' - by revenue, sales volume, or another metric?"],
    "questions_needed": 2,
    "reasoning": "Goal is clear but success criteria for 'top performing' needs definition",
    "evidence_quotes": ["identify top-performing products and regions"]
  },
  "data_understanding": {
    "dimension": "data",
    "score": 0.4,
    "confidence": "low",
    "known_facts": ["3 CSV files provided", "sales_2024.csv, products.csv, regions.csv"],
    "gaps": ["Don't know column names", "How to join files?", "Which columns contain 'sales'?"],
    "priority_questions": ["What are the column names in each CSV?", "How should we join these files?"],
    "questions_needed": 3,
    "reasoning": "Files provided but no schema or relationship information",
    "evidence_quotes": []
  },
  "business_logic_understanding": {
    "dimension": "business_logic",
    "score": 0.3,
    "confidence": "low",
    "known_facts": ["Need to identify top performers"],
    "gaps": ["How to calculate 'top performing'?", "Any preprocessing needed?", "Output format?"],
    "priority_questions": ["How should we define 'top-performing' products?", "What aggregations do you need?"],
    "questions_needed": 3,
    "reasoning": "Very high-level requirement with no calculation details",
    "evidence_quotes": ["identify top-performing products and regions"]
  },
  "overall_completeness": 0.47,
  "estimated_questions_remaining": 5,
  "next_action": "ask_data_question",
  "next_agent": "data_clarification_agent",
  "context_for_next_agent": "User wants Q4 sales analysis. We have 3 CSV files but no schema information. Need to understand columns and relationships before proceeding.",
  "suggested_question": "Could you tell me what columns are in your CSV files and how they relate to each other?",
  "reasoning": "Data dimension has lowest score (0.4). Without knowing column names and relationships, we cannot proceed with any meaningful analysis.",
  "confidence": "high",
  "accumulated_knowledge": {
    "user_goal": "Identify top-performing products and regions in Q4 sales",
    "analysis_type": "sales_performance_ranking",
    "success_criteria": "Rank by total revenue, include only products with >10 sales",
    "stakeholders": null,
    "csv_files_info": {
      "sales_2024.csv": {},
      "products.csv": {},
      "regions.csv": {}
    },
    "mentioned_columns": [],
    "column_mappings": {},
    "data_relationships": [],
    "filtering_rules": [],
    "exclusion_criteria": [],
    "calculations": [],
    "aggregations": [],
    "thresholds": {},
    "output_columns": [],
    "preprocessing_steps": [],
    "questions_asked": 0,
    "conversation_history": []
  }
}
```

---

## KEY PRINCIPLES

1. **Be Strict**: Don't assume information not explicitly stated
2. **Extract Everything**: Capture all preprocessing, rules, and calculations mentioned
3. **Prioritize Blockers**: Questions about missing critical information come first
4. **Be Consistent**: Use the same JSON structure every time
5. **Quote Evidence**: Always include quotes from user's description to justify your assessment
6. **Update Accumulated Knowledge**: Extract every detail into the appropriate field

## CRITICAL: INTENT DIMENSION RULES

**For Intent scoring, ONLY consider:**
- ✅ Analysis goal clarity (what type of analysis: duplicate detection, reconciliation, etc.)
- ✅ Success criteria (how to determine if something should be flagged/included)
- ✅ Output format (what columns in the final CSV)
- ✅ Business rules that define the analysis logic

**For Intent scoring, IGNORE:**
- ❌ Stakeholders or who will use the results
- ❌ Downstream consumers or departments
- ❌ Presentation or reporting requirements
- ❌ Business context beyond the immediate analysis goal

**If intent_score is low ONLY because stakeholder info is missing, DO NOT lower the score.**
**Intent is about WHAT to analyze and HOW to define success, NOT about WHO uses it.**

---

Now analyze the workflow requirements and provide your assessment.
"""


# =============================================================================
# REQUIREMENTS ANALYSIS AGENT
# =============================================================================

class RequirementsAnalysisAgent:
    """
    Meta-orchestrator that analyzes requirements and routes to specialized agents
    """
    
    def __init__(
        self,
        chat_client: Optional[Any] = None,
        model: str = "gpt-4o",
        temperature: float = 0.3  # Lower temp for more consistent analysis
    ):
        """
        Initialize the Requirements Analysis Agent
        
        Args:
            chat_client: Optional chat client instance
            model: Model to use for analysis
            temperature: Generation temperature
        """
        logger.info("Initializing Requirements Analysis Agent")
        
        # Use provided chat client or create default
        if chat_client is None:
            config = get_config()
            if config.openai_api_key:
                import os
                os.environ['OPENAI_API_KEY'] = config.openai_api_key
                chat_client = OpenAIChatClient(model_id=model)
            elif config.azure_openai_api_key:
                chat_client = AzureOpenAIChatClient(
                    deployment_name=config.azure_openai_chat_deployment_name
                )
            else:
                raise AgentException(
                    "No API key configured. Set OPENAI_API_KEY or AZURE_OPENAI_API_KEY"
                )
        
        # Create the agent
        self.agent = ChatAgent(
            name="Requirements-Analyzer",
            chat_client=chat_client,
            instructions=RAA_SYSTEM_PROMPT,
            tools=[],  # No tools needed - pure analysis
        )
        
        self.thread = None
        self.accumulated_knowledge = AccumulatedKnowledge()
        
        logger.info(f"Requirements Analysis Agent initialized with model: {model}")
    
    async def analyze_initial_input(
        self,
        workflow_name: str,
        workflow_description: str,
        csv_filepaths: List[str],
        dataset_intelligence: Optional[Any] = None
    ) -> AnalysisResult:
        """
        Analyze initial workflow input from user

        Args:
            workflow_name: Name of the workflow
            workflow_description: User's description of what they want
            csv_filepaths: List of CSV file paths
            dataset_intelligence: Optional pre-analyzed DatasetIntelligence from DatasetAnalyzer

        Returns:
            AnalysisResult with understanding assessment and next action
        """
        logger.info("Analyzing initial workflow input")

        # Create new thread for this workflow
        self.thread = self.agent.get_new_thread()

        # Extract just filenames for cleaner prompt
        import os
        filenames = [os.path.basename(fp) for fp in csv_filepaths]

        # Build data intelligence context if provided
        data_intelligence_context = ""
        if dataset_intelligence:
            logger.info("Using pre-analyzed dataset intelligence")
            data_intelligence_context = f"""

{dataset_intelligence.formatted_context}

IMPORTANT: The above dataset intelligence has been pre-analyzed. You have complete information about:
- File structures and column names
- Column classifications (identifiers, dates, amounts, categories)
- Business domain inference
- Cross-file relationships and potential join keys

Use this intelligence to:
1. SKIP basic data questions about column names or file structure
2. INCREASE your data_understanding score significantly (should be >= 0.7)
3. Focus questions on BUSINESS LOGIC and specific INTENT clarifications
4. Pre-populate accumulated_knowledge with column information

"""

            # Pre-populate accumulated knowledge with data intelligence
            if hasattr(dataset_intelligence, 'files') and dataset_intelligence.files:
                for file_intel in dataset_intelligence.files:
                    file_info = {
                        "rows": file_intel.row_count,
                        "columns": file_intel.column_count,
                        "business_domain": file_intel.inferred_business_domain
                    }

                    # Add categorical enrichment data if available
                    if hasattr(file_intel, 'categorical_enrichment') and file_intel.categorical_enrichment:
                        file_info["categorical_enrichment"] = file_intel.categorical_enrichment
                        logger.info(f"Added categorical enrichment for {file_intel.filename}: {len(file_intel.categorical_enrichment)} columns")

                    self.accumulated_knowledge.csv_files_info[file_intel.filename] = file_info
                    self.accumulated_knowledge.mentioned_columns.extend(
                        [col.column_name for col in file_intel.columns]
                    )

            # Add cross-file relationships
            if hasattr(dataset_intelligence, 'potential_join_keys'):
                self.accumulated_knowledge.data_relationships.extend(
                    [f"Potential join key: {key}" for key in dataset_intelligence.potential_join_keys]
                )

        # Build analysis prompt
        prompt = f"""
Please analyze the following workflow requirements:

**Workflow Name**: {workflow_name}

**Workflow Description**:
{workflow_description}

**CSV Files Provided**: {len(csv_filepaths)} file(s)
{chr(10).join(f"- {fname}" for fname in filenames)}
{data_intelligence_context}

Analyze this input and provide your assessment as a structured JSON response.
Remember to:
1. Score each dimension (intent, data, business_logic) from 0.0 to 1.0
2. Identify what we know and what gaps exist
3. Extract all preprocessing steps and business logic mentioned
4. Decide the next action based on lowest score
5. Provide context for the next agent to use
6. If dataset intelligence is provided, your data_understanding score should reflect that knowledge

Output ONLY the JSON object, no additional text.
"""
        
        try:
            # Get analysis from agent
            response = await self.agent.run(prompt, thread=self.thread)
            response_text = str(response.text) if hasattr(response, 'text') else str(response)
            
            # Parse JSON response
            analysis_dict = self._parse_json_response(response_text)
            
            # Convert to AnalysisResult
            result = self._dict_to_analysis_result(analysis_dict)
            
            # Update accumulated knowledge
            self.accumulated_knowledge = result.accumulated_knowledge
            
            logger.info(f"Initial analysis complete. Next action: {result.next_action.value}")
            logger.info(f"Completeness: {result.overall_completeness:.2f}")
            logger.info(f"Intent: {result.intent_understanding.score:.2f}, "
                       f"Data: {result.data_understanding.score:.2f}, "
                       f"Logic: {result.business_logic_understanding.score:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing initial input: {str(e)}", exc_info=True)
            raise AgentException(f"Failed to analyze requirements: {str(e)}")
    
    async def analyze_user_response(
        self,
        user_response: str,
        previous_question: str,
        previous_state: str
    ) -> AnalysisResult:
        """
        Analyze user's response to a question
        
        Args:
            user_response: User's answer
            previous_question: The question that was asked
            previous_state: Which agent asked the question ("intent", "data", "logic")
            
        Returns:
            Updated AnalysisResult with new understanding assessment
        """
        logger.info(f"Analyzing user response in context of {previous_state} question")
        
        if not self.thread:
            raise AgentException("No conversation thread exists. Call analyze_initial_input first.")
        
        # Build analysis prompt with conversation context
        prompt = f"""
The user was asked a {previous_state} question and has responded. Please update your analysis.

**Previous Question Asked**:
{previous_question}

**User's Response**:
{user_response}

**Current Accumulated Knowledge**:
{json.dumps(self.accumulated_knowledge.to_dict(), indent=2)}

Update your analysis based on this new information:
1. Update scores for dimensions that improved
2. Add new facts learned from the response
3. Update gaps that were filled or new gaps discovered
4. Decide the next action (which dimension to address next)
5. Provide updated context for the next agent

Output ONLY the updated JSON analysis object.
"""
        
        try:
            # Get updated analysis
            response = await self.agent.run(prompt, thread=self.thread)
            response_text = str(response.text) if hasattr(response, 'text') else str(response)
            
            # Parse JSON response
            analysis_dict = self._parse_json_response(response_text)
            
            # Convert to AnalysisResult
            result = self._dict_to_analysis_result(analysis_dict)
            
            # Update accumulated knowledge
            result.accumulated_knowledge.questions_asked = self.accumulated_knowledge.questions_asked + 1
            result.accumulated_knowledge.conversation_history.append({
                "question": previous_question,
                "answer": user_response,
                "state": previous_state
            })
            self.accumulated_knowledge = result.accumulated_knowledge
            
            logger.info(f"Updated analysis complete. Next action: {result.next_action.value}")
            logger.info(f"Completeness: {result.overall_completeness:.2f}")
            logger.info(f"Intent: {result.intent_understanding.score:.2f}, "
                       f"Data: {result.data_understanding.score:.2f}, "
                       f"Logic: {result.business_logic_understanding.score:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing user response: {str(e)}", exc_info=True)
            raise AgentException(f"Failed to analyze response: {str(e)}")
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse JSON from agent response, handling markdown code blocks
        
        Args:
            response_text: Raw response from agent
            
        Returns:
            Parsed JSON dictionary
        """
        import re
        
        # Remove markdown code blocks if present
        json_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = response_text.strip()
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {str(e)}")
            logger.error(f"Response text: {response_text[:500]}...")
            raise AgentException(f"Agent returned invalid JSON: {str(e)}")
    
    def _dict_to_analysis_result(self, analysis_dict: Dict[str, Any]) -> AnalysisResult:
        """
        Convert dictionary to AnalysisResult dataclass

        Args:
            analysis_dict: Dictionary from agent response

        Returns:
            AnalysisResult object
        """
        # Parse understanding dimensions
        intent = UnderstandingDimension(**analysis_dict["intent_understanding"])
        data = UnderstandingDimension(**analysis_dict["data_understanding"])
        logic = UnderstandingDimension(**analysis_dict["business_logic_understanding"])

        # Parse accumulated knowledge - handle both defined and dynamic fields
        from dataclasses import fields as get_dataclass_fields

        knowledge_dict = analysis_dict["accumulated_knowledge"]
        defined_fields = {f.name for f in get_dataclass_fields(AccumulatedKnowledge) if f.name != '_extra_fields'}

        # Separate defined fields and extra fields
        defined_values = {k: v for k, v in knowledge_dict.items() if k in defined_fields}
        extra_values = {k: v for k, v in knowledge_dict.items() if k not in defined_fields}

        # Log any extra fields the LLM added
        if extra_values:
            logger.info(f"LLM added dynamic fields to AccumulatedKnowledge: {list(extra_values.keys())}")

        # Create knowledge object with defined fields
        knowledge = AccumulatedKnowledge(**defined_values)

        # Add extra fields
        for key, value in extra_values.items():
            setattr(knowledge, key, value)
        
        # Create AnalysisResult
        return AnalysisResult(
            intent_understanding=intent,
            data_understanding=data,
            business_logic_understanding=logic,
            overall_completeness=analysis_dict["overall_completeness"],
            estimated_questions_remaining=analysis_dict["estimated_questions_remaining"],
            next_action=NextAction(analysis_dict["next_action"]),
            next_agent=analysis_dict["next_agent"],
            context_for_next_agent=analysis_dict["context_for_next_agent"],
            suggested_question=analysis_dict.get("suggested_question"),
            reasoning=analysis_dict["reasoning"],
            confidence=analysis_dict["confidence"],
            accumulated_knowledge=knowledge
        )
    
    def get_current_understanding(self) -> Dict[str, float]:
        """
        Get current understanding scores
        
        Returns:
            Dictionary with current scores for each dimension
        """
        # This would be populated after first analysis
        return {
            "intent": 0.0,
            "data": 0.0,
            "business_logic": 0.0,
            "overall": 0.0
        }
    
    def reset(self):
        """Reset agent state for new workflow"""
        logger.info("Resetting Requirements Analysis Agent")
        self.thread = None
        self.accumulated_knowledge = AccumulatedKnowledge()


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_requirements_analysis_agent(
    model: Optional[str] = None,
    temperature: float = 0.3,
    provider: Optional[str] = None,
    use_azure: bool = False
) -> RequirementsAnalysisAgent:
    """
    Factory function to create Requirements Analysis Agent
    
    Args:
        model: Model name
        temperature: Generation temperature
        provider: LLM provider
        use_azure: Whether to use Azure OpenAI
        
    Returns:
        Configured RequirementsAnalysisAgent instance
    """
    from ai.ira_builder.utils.llm_provider import create_chat_client
    
    config = get_config()
    provider = provider or config.llm_provider
    
    logger.info(f"Creating Requirements Analysis Agent (provider={provider}, model={model})")
    
    try:
        chat_client = create_chat_client(
            provider=provider,
            model=model,
            use_azure=use_azure
        )
        
        return RequirementsAnalysisAgent(
            chat_client=chat_client,
            model=model or config.openai_model,
            temperature=temperature
        )
        
    except Exception as e:
        logger.error(f"Error creating Requirements Analysis Agent: {str(e)}")
        raise AgentException(f"Failed to create agent: {str(e)}")