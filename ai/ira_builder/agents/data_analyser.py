"""
Dataset Analyzer - Pre-analyzes CSV files to generate comprehensive understanding
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple, Annotated
from pathlib import Path
from dataclasses import dataclass, field
from pydantic import BaseModel, Field
import pandas as pd

from agent_framework import ChatAgent
from agent_framework.openai import OpenAIChatClient

from ai.ira_builder.tools.csv_tools import (
    analyze_csv_structure,
    get_csv_summary,
    compare_csv_schemas,
    detect_data_quality_issues,
    get_column_data_preview
)
from ai.ira_builder.utils.logger import get_logger
from ai.ira_builder.exceptions.errors import AgentException

logger = get_logger(__name__)


# =============================================================================
# CATEGORICAL ANALYSIS TOOLS
# =============================================================================

class CategoricalAnalysisTools:
    """
    Tools for analyzing categorical column values.
    These tools are provided to the LLM agent to intelligently gather
    categorical column information based on workflow requirements.
    """

    def __init__(self, file_path: str):
        """
        Initialize tools with file path context.

        Args:
            file_path: Path to the CSV/Excel file being analyzed
        """
        self.file_path = file_path
        # Track tool results for extraction
        self.tool_results = {}
        logger.debug(f"Initialized CategoricalAnalysisTools for {file_path}")

    async def get_categorical_column_filters(
        self,
        column_name: Annotated[str, Field(
            description="Name of the column to retrieve all unique values from. Only use for columns with less than 20 unique values."
        )]
    ) -> Dict[str, Any]:
        """
        Retrieves ALL unique values from a categorical column if it has <20 unique values.

        Use this tool when:
        - User mentions filtering on a column but doesn't specify exact values to match
        - You need to see ALL possible values to understand the full range of options
        - Column is truly categorical with low cardinality (<20 unique values)
        - You want to help map user's natural language to actual column values

        Example use cases:
        - User says "filter by document type" → Use this to see all document types available
        - User says "consider standard and credit only" → Use this on Document Type column
        - User says "filter cancelled cases" → Use this on Status column to see all statuses

        Returns:
            Dict with 'unique_values' list or 'error' message if column has >20 values
        """
        try:
            logger.info(f"Tool called: get_categorical_column_filters(column={column_name})")

            # Read file with appropriate format and encoding
            if self.file_path.endswith('.csv'):
                try:
                    df = await asyncio.to_thread(pd.read_csv, self.file_path, encoding='utf-8')
                except UnicodeDecodeError:
                    df = await asyncio.to_thread(pd.read_csv, self.file_path, encoding='ISO-8859-1')
            elif self.file_path.endswith(('.xlsx', '.xlsb')):
                df = await asyncio.to_thread(pd.read_excel, self.file_path)
            else:
                return {"error": "Unsupported file format. Only CSV and Excel files are supported."}

            # Validate column exists
            if column_name not in df.columns:
                available_cols = ", ".join(df.columns.tolist()[:10])
                return {"error": f"Column '{column_name}' not found. Available columns include: {available_cols}"}

            # Get unique values
            unique_values = df[column_name].dropna().unique().tolist()

            # Check if column is categorical (object type) and has reasonable cardinality
            if df[column_name].dtype == 'object':
                if len(unique_values) < 20:
                    logger.info(f"Retrieved {len(unique_values)} unique values for column '{column_name}'")
                    result = {
                        "column_name": column_name,
                        "unique_values": unique_values,
                        "count": len(unique_values)
                    }
                    # Track result for extraction
                    self.tool_results[column_name] = {
                        "values": unique_values,
                        "method": "get_all_values",
                        "count": len(unique_values)
                    }
                    return result
                else:
                    logger.warning(f"Column '{column_name}' has {len(unique_values)} unique values (>20 limit)")
                    return {
                        "error": f"Column '{column_name}' has {len(unique_values)} unique values, which exceeds the 20-value limit for this tool. Use get_matching_column_values() instead with a specific search keyword."
                    }
            else:
                return {
                    "error": f"Column '{column_name}' is not a categorical (text) column. It has dtype: {df[column_name].dtype}"
                }

        except Exception as e:
            logger.error(f"Error in get_categorical_column_filters: {str(e)}")
            return {"error": f"Tool execution failed: {str(e)}"}

    async def get_matching_column_values(
        self,
        column_name: Annotated[str, Field(
            description="Name of the column to search within"
        )],
        search_string: Annotated[str, Field(
            description="Substring to search for in column values (case-insensitive). Examples: 'Income Tax', 'standard', 'cancelled', 'WIRE'"
        )]
    ) -> Dict[str, Any]:
        """
        Finds column values that contain a specific substring (case-insensitive matching).

        Use this tool when:
        - User mentions a specific keyword to include/exclude (e.g., "exclude vendor names containing 'Income Tax'")
        - Column has too many unique values for get_categorical_column_filters (high cardinality)
        - You need fuzzy/partial matching rather than exact matches
        - User wants to filter based on pattern or substring

        Example use cases:
        - User says "exclude vendors containing Income Tax" → Use this with search_string="Income Tax"
        - User says "only WIRE transfers" → Use this on Payment Method with search_string="WIRE"
        - User says "filter standard document types" → Use this with search_string="standard"

        Returns:
            Dict with 'matching_values' list or 'error' message if no matches found
        """
        try:
            logger.info(f"Tool called: get_matching_column_values(column={column_name}, search='{search_string}')")

            # Read file with appropriate format and encoding
            if self.file_path.endswith('.csv'):
                try:
                    df = await asyncio.to_thread(pd.read_csv, self.file_path, encoding='utf-8')
                except UnicodeDecodeError:
                    df = await asyncio.to_thread(pd.read_csv, self.file_path, encoding='ISO-8859-1')
            elif self.file_path.endswith(('.xlsx', '.xlsb')):
                df = await asyncio.to_thread(pd.read_excel, self.file_path)
            else:
                return {"error": "Unsupported file format. Only CSV and Excel files are supported."}

            # Validate column exists
            if column_name not in df.columns:
                available_cols = ", ".join(df.columns.tolist()[:10])
                return {"error": f"Column '{column_name}' not found. Available columns include: {available_cols}"}

            # Find matches with case-insensitive search
            search_lower = search_string.lower()
            mask = df[column_name].astype(str).str.lower().str.contains(search_lower, na=False)
            matching_values = df.loc[mask, column_name].dropna().unique().tolist()

            if not matching_values:
                logger.warning(f"No values containing '{search_string}' found in column '{column_name}'")
                return {
                    "error": f"No values containing '{search_string}' found in column '{column_name}'. Try a different search term or check if the column name is correct."
                }

            logger.info(f"Found {len(matching_values)} matching values for '{search_string}' in column '{column_name}'")
            result = {
                "column_name": column_name,
                "search_string": search_string,
                "matching_values": matching_values,
                "count": len(matching_values)
            }
            # Track result for extraction (merge with existing if column already analyzed)
            if column_name in self.tool_results:
                # Merge values if same column searched with different keywords
                existing_values = self.tool_results[column_name].get("values", [])
                combined_values = list(set(existing_values + matching_values))
                self.tool_results[column_name] = {
                    "values": combined_values,
                    "method": "keyword_search",
                    "search_keywords": self.tool_results[column_name].get("search_keywords", []) + [search_string],
                    "count": len(combined_values)
                }
            else:
                self.tool_results[column_name] = {
                    "values": matching_values,
                    "method": "keyword_search",
                    "search_keywords": [search_string],
                    "count": len(matching_values)
                }
            return result

        except Exception as e:
            logger.error(f"Error in get_matching_column_values: {str(e)}")
            return {"error": f"Tool execution failed: {str(e)}"}


# =============================================================================
# PYDANTIC MODELS FOR STRUCTURED OUTPUT
# =============================================================================

class ColumnAnalysis(BaseModel):
    """LLM-generated analysis for a single column"""
    purpose: str = Field(
        description="Column purpose: identifier, date, amount, category, text, or boolean"
    )
    confidence: float = Field(
        description="Confidence score between 0.0 and 1.0"
    )
    reasoning: str = Field(
        description="Brief explanation of why this classification was chosen"
    )


class FileStructureAnalysis(BaseModel):
    """LLM-generated analysis of file structure"""
    business_domain: str = Field(
        description="Inferred business domain: financial_accounting, sales, inventory_management, human_resources, procurement, or general_business"
    )
    domain_confidence: float = Field(
        description="Confidence in domain classification between 0.0 and 1.0"
    )
    domain_reasoning: str = Field(
        description="Explanation of why this domain was chosen"
    )
    columns: List['ColumnWithName'] = Field(
        description="List of column analyses",
        default_factory=list
    )


class ColumnWithName(BaseModel):
    """Column analysis with column name"""
    column_name: str = Field(
        description="Name of the column"
    )
    purpose: str = Field(
        description="Column purpose: identifier, date, amount, category, text, or boolean"
    )
    confidence: float = Field(
        description="Confidence score between 0.0 and 1.0"
    )
    reasoning: str = Field(
        description="Brief explanation of why this classification was chosen"
    )


class QualityConcern(BaseModel):
    """A single data quality concern"""
    concern_type: str = Field(
        description="Type of concern: semantic_issue, business_logic_violation, data_integrity, suspicious_pattern, or potential_error"
    )
    severity: str = Field(
        description="Severity level: critical, high, medium, or low"
    )
    description: str = Field(
        description="Clear description of the quality concern"
    )
    affected_columns: List[str] = Field(
        description="List of column names affected by this concern",
        default_factory=list
    )
    evidence: str = Field(
        description="Specific evidence or examples supporting this concern"
    )
    recommendation: str = Field(
        description="Actionable recommendation to address this concern"
    )


class DataQualityAnalysis(BaseModel):
    """LLM-generated comprehensive data quality analysis"""
    overall_quality_score: float = Field(
        description="Overall data quality score between 0.0 (poor) and 1.0 (excellent)"
    )
    quality_summary: str = Field(
        description="Brief 1-2 sentence summary of overall data quality"
    )
    concerns: List[QualityConcern] = Field(
        description="List of identified data quality concerns",
        default_factory=list
    )
    positive_findings: List[str] = Field(
        description="List of positive data quality attributes found",
        default_factory=list
    )


class ColumnMappingSuggestion(BaseModel):
    """Mapping of business concept to potential column names"""
    concept: str = Field(
        description="Business concept or logical name"
    )
    suggested_columns: List[str] = Field(
        description="List of column names that might represent this concept",
        default_factory=list
    )


class ComprehensiveIntelligence(BaseModel):
    """LLM-generated comprehensive dataset intelligence"""
    dataset_summary: str = Field(
        description="Human-readable 2-3 sentence summary of the dataset"
    )
    business_domain: str = Field(
        description="Primary business domain: financial_accounting, sales, hr, inventory_management, procurement, or general_business"
    )
    suggested_analysis_types: List[str] = Field(
        description="List of analysis types possible with this data (e.g., duplicate_detection, reconciliation, compliance_check)",
        default_factory=list
    )
    column_mapping_suggestions: List[ColumnMappingSuggestion] = Field(
        description="Mappings of business concepts to actual column names",
        default_factory=list
    )
    key_insights: List[str] = Field(
        description="Key insights about the data, relationships, or patterns",
        default_factory=list
    )


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class ColumnClassification:
    """Intelligent classification of a column"""
    column_name: str
    data_type: str
    inferred_purpose: str  # identifier, date, amount, category, text, boolean
    confidence: float
    reasoning: str
    
    sample_values: List[Any]
    unique_count: int
    null_count: int
    null_percentage: float
    
    # Optional numerical metadata
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    mean_value: Optional[float] = None
    
    # Optional categorical metadata
    top_categories: Optional[List[Tuple[str, int]]] = None
    
    # Optional date metadata
    date_range: Optional[Tuple[str, str]] = None
    date_format: Optional[str] = None


@dataclass
class FileIntelligence:
    """Complete intelligence about a CSV file"""
    filename: str
    filepath: str
    row_count: int
    column_count: int
    file_size_mb: float
    
    columns: List[ColumnClassification]
    
    # Column groups
    identifier_columns: List[str] = field(default_factory=list)
    date_columns: List[str] = field(default_factory=list)
    amount_columns: List[str] = field(default_factory=list)
    category_columns: List[str] = field(default_factory=list)
    text_columns: List[str] = field(default_factory=list)
    boolean_columns: List[str] = field(default_factory=list)
    
    # Data quality (rule-based)
    has_duplicates: bool = False
    duplicate_count: int = 0
    quality_issues: List[Dict[str, Any]] = field(default_factory=list)

    # Data quality (LLM-powered semantic analysis)
    quality_score: float = 0.0
    quality_summary: str = ""
    quality_concerns: List[Dict[str, Any]] = field(default_factory=list)
    positive_quality_findings: List[str] = field(default_factory=list)

    # Business context
    inferred_business_domain: str = ""
    file_description: str = ""

    # Categorical enrichment (LLM-powered tool-based analysis)
    categorical_enrichment: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DatasetIntelligence:
    """Complete intelligence about entire dataset"""
    
    files: List[FileIntelligence]
    total_files: int
    
    # Cross-file analysis
    common_columns: List[str] = field(default_factory=list)
    potential_join_keys: List[str] = field(default_factory=list)
    file_relationships: Dict[str, Any] = field(default_factory=dict)
    
    # Totals
    total_rows: int = 0
    total_columns: int = 0
    
    # LLM-generated insights
    dataset_summary: str = ""
    business_domain: str = ""
    suggested_analysis_types: List[str] = field(default_factory=list)
    column_mapping_suggestions: Dict[str, List[str]] = field(default_factory=dict)
    
    # Ready-to-use context
    formatted_context: str = ""


# =============================================================================
# DATASET ANALYZER
# =============================================================================

class DatasetAnalyzer:
    """
    Pre-analyzes CSV files to generate comprehensive dataset understanding
    """
    
    def __init__(self, chat_client: Optional[Any] = None, model: str = "gpt-4o"):
        """Initialize dataset analyzer"""
        logger.info("Initializing Dataset Analyzer")

        # LLM for intelligent analysis
        if chat_client is None:
            from ai.ira_builder.utils.config import get_config
            config = get_config()
            import os
            os.environ['OPENAI_API_KEY'] = config.openai_api_key
            from agent_framework.openai import OpenAIChatClient
            chat_client = OpenAIChatClient(model_id=model)

        # Store chat client for creating enrichment agent later
        self.chat_client = chat_client
        self.model = model

        self.agent = ChatAgent(
            name="Dataset-Analyzer",
            chat_client=chat_client,
            instructions=DATASET_ANALYZER_PROMPT,
            tools=[]
        )

        # Store workflow description during analysis
        self.current_workflow_description = ""

        logger.info("Dataset Analyzer initialized")
    
    async def analyze_dataset(
        self,
        csv_filepaths: List[str],
        workflow_description: str
    ) -> DatasetIntelligence:
        """
        Analyze entire dataset and generate comprehensive understanding

        Args:
            csv_filepaths: List of CSV file paths
            workflow_description: User's workflow description (provides context)

        Returns:
            DatasetIntelligence with complete understanding
        """
        logger.info(f"Analyzing dataset with {len(csv_filepaths)} file(s)")

        # Store workflow description for use in enrichment
        self.current_workflow_description = workflow_description

        # Step 1: Analyze each file individually
        file_intelligences = []
        for filepath in csv_filepaths:
            file_intel = await self._analyze_single_file(filepath)
            file_intelligences.append(file_intel)
        
        # Step 2: Cross-file analysis (if multiple files)
        if len(csv_filepaths) > 1:
            cross_file_analysis = self._analyze_file_relationships(csv_filepaths)
        else:
            cross_file_analysis = {
                "common_columns": [],
                "potential_join_keys": [],
                "file_relationships": {}
            }
        
        # Step 3: LLM-powered comprehensive analysis
        dataset_intel = await self._generate_comprehensive_intelligence(
            file_intelligences=file_intelligences,
            cross_file_analysis=cross_file_analysis,
            workflow_description=workflow_description
        )
        
        logger.info("Dataset analysis complete")
        return dataset_intel
    
    async def _analyze_single_file(self, filepath: str) -> FileIntelligence:
        """Analyze a single CSV file using LLM intelligence"""
        logger.info(f"Analyzing file: {Path(filepath).name}")

        # Get raw metadata
        metadata = analyze_csv_structure(filepath)

        # Get quality issues
        quality_result = detect_data_quality_issues(filepath)

        # Use LLM to classify all columns and infer business domain
        llm_analysis = await self._llm_analyze_file_structure(metadata)

        # Build ColumnClassification objects from LLM analysis
        classified_columns = []
        for col_name in metadata["columns"]:
            llm_col_data = llm_analysis["columns"].get(col_name, {})

            # Get metadata for this column
            stats = metadata.get("statistics", {}).get(col_name, {})
            cat_info = metadata.get("categorical_info", {}).get(col_name, {})
            sample_data = metadata.get("sample_data", [])
            sample_values = [row.get(col_name) for row in sample_data[:5]]
            null_count = metadata.get("missing_values", {}).get(col_name, 0)
            null_pct = metadata.get("missing_percentage", {}).get(col_name, 0.0)
            unique_count = cat_info.get("unique_count", 0) if cat_info else 0

            classification = ColumnClassification(
                column_name=col_name,
                data_type=metadata["dtypes"][col_name],
                inferred_purpose=llm_col_data.get("purpose", "text"),
                confidence=llm_col_data.get("confidence", 0.5),
                reasoning=llm_col_data.get("reasoning", "LLM classification"),
                sample_values=sample_values,
                unique_count=unique_count,
                null_count=null_count,
                null_percentage=null_pct,
                min_value=stats.get("min"),
                max_value=stats.get("max"),
                mean_value=stats.get("mean"),
                top_categories=list(cat_info.get("top_values", {}).items())[:5] if cat_info else None
            )
            classified_columns.append(classification)

        # Group columns by purpose
        identifier_cols = [c.column_name for c in classified_columns if c.inferred_purpose == "identifier"]
        date_cols = [c.column_name for c in classified_columns if c.inferred_purpose == "date"]
        amount_cols = [c.column_name for c in classified_columns if c.inferred_purpose == "amount"]
        category_cols = [c.column_name for c in classified_columns if c.inferred_purpose == "category"]
        text_cols = [c.column_name for c in classified_columns if c.inferred_purpose == "text"]
        boolean_cols = [c.column_name for c in classified_columns if c.inferred_purpose == "boolean"]

        # Use LLM's business domain inference
        business_domain = llm_analysis.get("business_domain", "general_business")

        # Step 4: NEW - LLM-powered categorical enrichment (tool-based)
        categorical_enrichment = await self._enrich_categorical_columns(
            metadata=metadata,
            classified_columns=classified_columns,
            file_path=filepath
        )

        # Step 5: LLM-powered semantic quality analysis
        quality_analysis = await self._llm_analyze_data_quality(
            metadata=metadata,
            classified_columns=classified_columns,
            quality_result=quality_result,
            business_domain=business_domain
        )

        return FileIntelligence(
            filename=metadata["filename"],
            filepath=metadata["path"],
            row_count=metadata["row_count"],
            column_count=metadata["column_count"],
            file_size_mb=metadata["file_size_mb"],
            columns=classified_columns,
            identifier_columns=identifier_cols,
            date_columns=date_cols,
            amount_columns=amount_cols,
            category_columns=category_cols,
            text_columns=text_cols,
            boolean_columns=boolean_cols,
            # Rule-based quality
            has_duplicates=any(i["type"] == "duplicate_rows" for i in quality_result["issues"]),
            duplicate_count=next(
                (i["description"] for i in quality_result["issues"] if i["type"] == "duplicate_rows"),
                0
            ),
            quality_issues=quality_result["issues"],
            # LLM-powered quality
            quality_score=quality_analysis.get("quality_score", 0.0),
            quality_summary=quality_analysis.get("quality_summary", ""),
            quality_concerns=quality_analysis.get("concerns", []),
            positive_quality_findings=quality_analysis.get("positive_findings", []),
            # Business context
            inferred_business_domain=business_domain,
            file_description=f"{metadata['filename']} containing {metadata['row_count']:,} rows",
            # Categorical enrichment
            categorical_enrichment=categorical_enrichment
        )
    
    async def _llm_analyze_data_quality(
        self,
        metadata: Dict[str, Any],
        classified_columns: List[ColumnClassification],
        quality_result: Dict[str, Any],
        business_domain: str
    ) -> Dict[str, Any]:
        """
        Use LLM to analyze semantic data quality concerns

        Args:
            metadata: Raw CSV metadata
            classified_columns: Column classifications
            quality_result: Rule-based quality issues
            business_domain: Inferred business domain

        Returns:
            Dictionary with quality analysis
        """
        logger.info("Using LLM for semantic data quality analysis")

        # Build quality context for LLM
        rule_based_issues_summary = "\n".join([
            f"- {issue['type']}: {issue['description']}"
            for issue in quality_result["issues"][:10]  # Limit to first 10
        ]) if quality_result["issues"] else "No rule-based issues detected"

        # Build column summary
        column_summary = []
        for col in classified_columns[:20]:  # Limit to first 20 columns
            col_summary = f"{col.column_name} ({col.inferred_purpose})"
            if col.sample_values:
                samples = [str(v)[:30] for v in col.sample_values[:3] if v]
                col_summary += f": {', '.join(samples)}"
            column_summary.append(col_summary)

        # Build prompt for quality analysis
        prompt = f"""
Analyze the data quality of this CSV file and identify potential concerns that could affect analysis.

**File Context:**
- Filename: {metadata["filename"]}
- Business Domain: {business_domain}
- Rows: {metadata["row_count"]:,}
- Columns: {metadata["column_count"]}

**Sample Column Data:**
{chr(10).join(column_summary)}

**Rule-Based Quality Issues Detected:**
{rule_based_issues_summary}

**Your Task - Identify SEMANTIC Data Quality Concerns:**

Look for issues beyond simple statistics:

1. **Semantic Issues**: Data that doesn't make business sense
   - Example: Negative invoice amounts (should be positive)
   - Example: Customer names containing numbers
   - Example: Document dates after posting dates
   - Example: Future transaction dates

2. **Business Logic Violations**: Data violating business rules
   - Example: Vendor payments without vendor identifiers
   - Example: GL entries without account codes
   - Example: Missing mandatory fields for the business domain

3. **Data Integrity**: Logical inconsistencies
   - Example: Total amounts that don't match line item sums
   - Example: Closed status with future dates
   - Example: Zero quantities with non-zero amounts

4. **Suspicious Patterns**: Unusual patterns worth investigating
   - Example: Many transactions on exact round numbers
   - Example: Unusual distribution of values
   - Example: Identical values repeating suspiciously

**Important:**
- Focus on SEMANTIC issues, not just statistical ones
- Consider the business domain context (e.g., financial rules for accounting data)
- Provide specific evidence with column names and examples
- Be practical - only flag issues that genuinely affect analysis quality
- If data looks good, say so! Include positive findings.

**Output a quality score:**
- 0.9-1.0: Excellent quality, ready for analysis
- 0.7-0.9: Good quality with minor concerns
- 0.5-0.7: Moderate quality, notable issues exist
- 0.3-0.5: Poor quality, significant issues
- 0.0-0.3: Very poor quality, major problems
"""

        try:
            # Get LLM quality analysis with structured output
            response = await self.agent.run(prompt, response_format=DataQualityAnalysis)

            if response.value:
                quality_model = response.value

                # Convert to dict format
                quality_analysis = {
                    "quality_score": quality_model.overall_quality_score,
                    "quality_summary": quality_model.quality_summary,
                    "concerns": [
                        {
                            "type": concern.concern_type,
                            "severity": concern.severity,
                            "description": concern.description,
                            "affected_columns": concern.affected_columns,
                            "evidence": concern.evidence,
                            "recommendation": concern.recommendation
                        }
                        for concern in quality_model.concerns
                    ],
                    "positive_findings": quality_model.positive_findings
                }

                logger.info(f"Quality analysis: score={quality_model.overall_quality_score:.2f}, concerns={len(quality_model.concerns)}")
                return quality_analysis
            else:
                logger.warning("LLM quality analysis returned no value")
                return self._default_quality_analysis()

        except Exception as e:
            logger.error(f"LLM quality analysis failed: {str(e)}")
            return self._default_quality_analysis()

    def _default_quality_analysis(self) -> Dict[str, Any]:
        """Fallback quality analysis if LLM fails"""
        return {
            "quality_score": 0.7,
            "quality_summary": "Quality analysis unavailable - using rule-based checks only",
            "concerns": [],
            "positive_findings": []
        }

    async def _enrich_categorical_columns(
        self,
        metadata: Dict[str, Any],
        classified_columns: List[ColumnClassification],
        file_path: str
    ) -> Dict[str, Any]:
        """
        Use LLM with tools to enrich categorical columns based on workflow requirements.

        This method creates a temporary agent with categorical analysis tools and lets
        the LLM intelligently decide which columns to analyze and which tool to use.

        Args:
            metadata: Raw CSV metadata
            classified_columns: Column classifications
            file_path: Path to the CSV file

        Returns:
            Dictionary mapping column names to their enrichment data:
            {
                "column_name": {
                    "values": [...],
                    "method": "get_all_values" | "keyword_search",
                    "search_keyword": "..." (if applicable),
                    "reason": "why this column was analyzed"
                }
            }
        """
        # Skip enrichment if no workflow description provided
        if not self.current_workflow_description:
            logger.info("No workflow description provided, skipping categorical enrichment")
            return {}

        logger.info("Starting LLM-guided categorical column enrichment")

        try:
            # Create tools bound to this file
            tools = CategoricalAnalysisTools(file_path)

            # Create temporary agent with tools
            enrichment_agent = ChatAgent(
                name="Categorical-Enrichment-Agent",
                chat_client=self.chat_client,
                instructions=CATEGORICAL_ENRICHMENT_PROMPT,
                tools=[tools.get_categorical_column_filters, tools.get_matching_column_values]
            )

            # Build categorical columns summary for LLM
            categorical_cols_summary = []
            for col in classified_columns:
                if col.inferred_purpose == "category":
                    samples_str = ", ".join([str(v)[:30] for v in col.sample_values[:3] if v])
                    categorical_cols_summary.append(
                        f"- **{col.column_name}**: {col.unique_count} unique values, "
                        f"samples: [{samples_str}]"
                    )

            if not categorical_cols_summary:
                logger.info("No categorical columns found, skipping enrichment")
                return {}

            categorical_cols_text = "\n".join(categorical_cols_summary)

            # Build prompt for enrichment agent
            prompt = f"""
Analyze the workflow description and identify which categorical columns need value expansion.

**WORKFLOW DESCRIPTION:**
{self.current_workflow_description}

**CATEGORICAL COLUMNS AVAILABLE:**
{categorical_cols_text}

**YOUR TASK:**
1. Parse the workflow for filtering keywords and column references
2. Match workflow mentions to actual categorical columns (handle fuzzy matching)
3. For each relevant column, decide which tool to use based on the decision framework
4. Call the appropriate tools to gather categorical information

**Remember:**
- Only analyze columns explicitly or strongly implied in the workflow
- Use get_categorical_column_filters() for columns with <20 values when user doesn't mention specific keywords
- Use get_matching_column_values() when user mentions specific patterns to match
- Be selective - focus on quality over quantity
- If a tool returns an error, try an alternative approach or skip that column

Start by analyzing the workflow and identifying which columns are mentioned.
Then call the appropriate tools one by one.
"""

            # Run the enrichment agent - it will call tools as needed
            logger.info("Running enrichment agent with tools...")
            response = await enrichment_agent.run(prompt)

            # DEBUG: Log the response to understand structure
            logger.debug(f"Enrichment agent response type: {type(response)}")
            logger.debug(f"Enrichment agent response attributes: {[a for a in dir(response) if not a.startswith('_')]}")

            # Extract enrichment results from tools (tracked during execution)
            enrichment_results = tools.tool_results.copy()

            if enrichment_results:
                logger.info(f"Successfully enriched {len(enrichment_results)} categorical columns")
                for col_name, data in enrichment_results.items():
                    value_count = len(data.get("values", []))
                    method = data.get("method", "unknown")
                    logger.info(f"  - {col_name}: {value_count} values via {method}")
            else:
                logger.info("No categorical columns were enriched (none matched workflow requirements)")

            return enrichment_results

        except Exception as e:
            logger.error(f"Error in categorical enrichment: {str(e)}", exc_info=True)
            return {}


    async def _llm_analyze_file_structure(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use LLM to intelligently analyze file structure, classify columns, and infer business domain

        Args:
            metadata: Raw CSV metadata from analyze_csv_structure

        Returns:
            Dictionary with column classifications and business domain
        """
        logger.info("Using LLM for intelligent file structure analysis")

        # Build column information for LLM
        columns_info = []
        for col_name in metadata["columns"]:
            col_info = {
                "name": col_name,
                "dtype": metadata["dtypes"].get(col_name, "unknown"),
                "sample_values": [],
                "null_percentage": metadata.get("missing_percentage", {}).get(col_name, 0.0),
                "unique_count": 0
            }

            # Add sample values
            sample_data = metadata.get("sample_data", [])
            col_info["sample_values"] = [str(row.get(col_name, ""))[:50] for row in sample_data[:5]]

            # Add statistics if numeric
            stats = metadata.get("statistics", {}).get(col_name, {})
            if stats:
                col_info["min"] = stats.get("min")
                col_info["max"] = stats.get("max")
                col_info["mean"] = stats.get("mean")

            # Add categorical info
            cat_info = metadata.get("categorical_info", {}).get(col_name, {})
            if cat_info:
                col_info["unique_count"] = cat_info.get("unique_count", 0)
                col_info["top_values"] = list(cat_info.get("top_values", {}).keys())[:5]

            columns_info.append(col_info)

        # Build prompt for LLM with structured output
        prompt = f"""
Analyze this CSV file structure and classify each column intelligently.

**File Information:**
- Filename: {metadata["filename"]}
- Row count: {metadata["row_count"]:,}
- Columns: {metadata["column_count"]}

**Column Details:**
{self._format_columns_for_llm(columns_info)}

**Your Task:**
1. Classify each column's **purpose** into one of:
   - identifier: Unique IDs, codes, keys (e.g., Invoice_No, Customer_ID, Document_Number)
   - date: Date/time fields (e.g., Posting_Date, Doc_Date, Created_On)
   - amount: Monetary or numerical values (e.g., Amount, Price, Balance, Quantity)
   - category: Categorical fields with limited values (e.g., Status, Type, Region)
   - text: Free-text or descriptive fields (e.g., Description, Comments, Name)
   - boolean: True/false or binary fields

2. Provide **confidence** (0.0-1.0) for each classification

3. Provide **reasoning** explaining why you classified it that way

4. Infer the **business_domain** from filename and column patterns:
   - financial_accounting: GL, vendor, invoice, payment, ledger data
   - sales: Sales orders, customers, revenue
   - inventory_management: Materials, stock, warehouse
   - human_resources: Employee, payroll, HR
   - procurement: Purchase orders, suppliers
   - general_business: Other business data

**Important:**
- Base classification on column NAME, DATA TYPE, and SAMPLE VALUES
- SAP column names often have patterns like "MATNR" (material), "BELNR" (document), "BUDAT" (posting date)
- Consider uniqueness: high unique count suggests identifier or text, low suggests category
- Be specific in reasoning - reference actual column characteristics
"""

        try:
            # Get LLM analysis with structured output
            response = await self.agent.run(prompt, response_format=FileStructureAnalysis)

            # Access structured output from response.value
            if response.value:
                analysis_model = response.value

                # Convert Pydantic model to dict format expected by rest of code
                analysis = {
                    "business_domain": analysis_model.business_domain,
                    "domain_confidence": analysis_model.domain_confidence,
                    "domain_reasoning": analysis_model.domain_reasoning,
                    "columns": {
                        col.column_name: {
                            "purpose": col.purpose,
                            "confidence": col.confidence,
                            "reasoning": col.reasoning
                        }
                        for col in analysis_model.columns
                    }
                }

                logger.info(f"LLM classified {len(analysis.get('columns', {}))} columns, domain: {analysis.get('business_domain')}")
                return analysis
            else:
                logger.warning("LLM response has no value, falling back to rule-based")
                return self._fallback_rule_based_analysis(metadata)

        except Exception as e:
            logger.error(f"LLM analysis failed: {str(e)}, falling back to rule-based")
            return self._fallback_rule_based_analysis(metadata)

    def _format_columns_for_llm(self, columns_info: List[Dict[str, Any]]) -> str:
        """Format column information for LLM prompt"""
        lines = []
        for i, col in enumerate(columns_info, 1):
            lines.append(f"\n{i}. **{col['name']}**")
            lines.append(f"   - Type: {col['dtype']}")
            lines.append(f"   - Sample values: {', '.join(str(v) for v in col['sample_values'][:3])}")
            lines.append(f"   - Unique count: {col['unique_count']}")
            lines.append(f"   - Null %: {col['null_percentage']:.1f}%")

            if col.get('min') is not None:
                lines.append(f"   - Range: {col['min']} to {col['max']}")

            if col.get('top_values'):
                lines.append(f"   - Top values: {', '.join(str(v) for v in col['top_values'][:3])}")

        return '\n'.join(lines)

    def _fallback_rule_based_analysis(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback to rule-based classification if LLM fails"""
        logger.info("Using fallback rule-based classification")

        columns_analysis = {}
        for col_name in metadata["columns"]:
            classification = self._classify_column(col_name, metadata)
            columns_analysis[col_name] = {
                "purpose": classification.inferred_purpose,
                "confidence": classification.confidence,
                "reasoning": classification.reasoning
            }

        # Rule-based domain inference
        business_domain = self._infer_business_domain(
            filename=metadata["filename"],
            columns=metadata["columns"]
        )

        return {
            "business_domain": business_domain,
            "domain_confidence": 0.7,
            "domain_reasoning": "Rule-based inference",
            "columns": columns_analysis
        }

    def _classify_column(self, column_name: str, metadata: Dict[str, Any]) -> ColumnClassification:
        """
        Classify a column's purpose using heuristics
        """
        dtype = metadata["dtypes"][column_name]
        col_lower = column_name.lower()
        
        # Get sample values
        sample_data = metadata.get("sample_data", [])
        sample_values = [row.get(column_name) for row in sample_data[:5]]
        
        # Get statistics if available
        stats = metadata.get("statistics", {}).get(column_name, {})
        cat_info = metadata.get("categorical_info", {}).get(column_name, {})
        
        # Get null info
        null_count = metadata.get("missing_values", {}).get(column_name, 0)
        null_pct = metadata.get("missing_percentage", {}).get(column_name, 0.0)
        
        unique_count = cat_info.get("unique_count", 0) if cat_info else 0
        
        # Classification logic
        purpose = "text"  # default
        confidence = 0.5
        reasoning = ""
        
        # IDENTIFIER detection
        if any(keyword in col_lower for keyword in ["id", "number", "code", "key", "_no", "_num"]):
            purpose = "identifier"
            confidence = 0.9
            reasoning = f"Column name contains identifier keyword ('{col_lower}')"
        
        # DATE detection
        elif any(keyword in col_lower for keyword in ["date", "time", "day", "month", "year", "dt_"]):
            purpose = "date"
            confidence = 0.85
            reasoning = f"Column name contains date/time keyword"
        
        # AMOUNT detection
        elif any(keyword in col_lower for keyword in ["amount", "price", "cost", "value", "balance", "total", "sum"]):
            purpose = "amount"
            confidence = 0.85
            reasoning = f"Column name suggests monetary/numerical value"
        
        # BOOLEAN detection
        elif dtype == "bool" or (cat_info and unique_count <= 2):
            purpose = "boolean"
            confidence = 0.9
            reasoning = "Column has only 2 unique values (likely boolean)"
        
        # CATEGORY detection
        elif cat_info and unique_count < 50:  # Few unique values = categorical
            purpose = "category"
            confidence = 0.8
            reasoning = f"Column has {unique_count} unique values (categorical)"
        
        # TEXT detection (long strings)
        elif "object" in dtype and cat_info and unique_count > 100:
            purpose = "text"
            confidence = 0.7
            reasoning = f"Column has many unique text values ({unique_count})"
        
        return ColumnClassification(
            column_name=column_name,
            data_type=dtype,
            inferred_purpose=purpose,
            confidence=confidence,
            reasoning=reasoning,
            sample_values=sample_values,
            unique_count=unique_count,
            null_count=null_count,
            null_percentage=null_pct,
            min_value=stats.get("min"),
            max_value=stats.get("max"),
            mean_value=stats.get("mean"),
            top_categories=list(cat_info.get("top_values", {}).items())[:5] if cat_info else None
        )
    
    def _infer_business_domain(self, filename: str, columns: List[str]) -> str:
        """Infer business domain from filename and columns"""
        filename_lower = filename.lower()
        columns_lower = [c.lower() for c in columns]
        
        # Financial/Accounting
        if any(k in filename_lower for k in ["fbl", "vendor", "invoice", "payment", "gl_", "ledger"]):
            return "financial_accounting"
        if any(k in " ".join(columns_lower) for k in ["debit", "credit", "posting", "document"]):
            return "financial_accounting"
        
        # Sales
        if any(k in filename_lower for k in ["sales", "order", "customer", "revenue"]):
            return "sales"
        
        # HR
        if any(k in filename_lower for k in ["employee", "payroll", "hr", "staff"]):
            return "human_resources"
        
        # Inventory
        if any(k in filename_lower for k in ["inventory", "stock", "warehouse", "product"]):
            return "inventory_management"
        
        return "general_business"
    
    def _analyze_file_relationships(self, filepaths: List[str]) -> Dict[str, Any]:
        """Analyze relationships between multiple CSV files"""
        logger.info("Analyzing cross-file relationships")
        
        schema_comparison = compare_csv_schemas(filepaths)
        
        return {
            "common_columns": schema_comparison["common_columns"],
            "potential_join_keys": schema_comparison["suggested_join_keys"],
            "file_relationships": schema_comparison
        }
    
    async def _generate_comprehensive_intelligence(
        self,
        file_intelligences: List[FileIntelligence],
        cross_file_analysis: Dict[str, Any],
        workflow_description: str
    ) -> DatasetIntelligence:
        """
        Use LLM to generate comprehensive dataset understanding
        """
        logger.info("Generating comprehensive dataset intelligence with LLM")
        
        # Build context for LLM
        files_context = []
        for file_intel in file_intelligences:
            file_ctx = f"""
File: {file_intel.filename}
Rows: {file_intel.row_count:,}
Business Domain: {file_intel.inferred_business_domain}

Column Classification:
- Identifiers: {', '.join(file_intel.identifier_columns) or 'None'}
- Dates: {', '.join(file_intel.date_columns) or 'None'}
- Amounts: {', '.join(file_intel.amount_columns) or 'None'}
- Categories: {', '.join(file_intel.category_columns[:5]) or 'None'}  # Show first 5
- Text fields: {', '.join(file_intel.text_columns[:5]) or 'None'}
"""
            files_context.append(file_ctx)
        
        prompt = f"""
Analyze this dataset and provide comprehensive intelligence.

WORKFLOW DESCRIPTION (user's goal):
{workflow_description}

DATASET FILES:
{''.join(files_context)}

CROSS-FILE ANALYSIS:
Common columns: {', '.join(cross_file_analysis['common_columns']) or 'None'}
Potential join keys: {', '.join(cross_file_analysis['potential_join_keys']) or 'None'}

Focus on:
1. What type of data this is (financial, sales, etc.)
2. What analyses are possible given the columns (duplicate_detection, reconciliation, compliance_check, etc.)
3. Which columns map to the user's workflow description
4. Any obvious relationships or patterns between files
5. Key insights about data structure and relationships
"""

        try:
            response = await self.agent.run(prompt, response_format=ComprehensiveIntelligence)

            if response.value:
                intel_model = response.value

                # Convert column mapping suggestions to dict format for backward compatibility
                column_mapping_dict = {
                    mapping.concept: mapping.suggested_columns
                    for mapping in intel_model.column_mapping_suggestions
                }

                llm_analysis = {
                    "dataset_summary": intel_model.dataset_summary,
                    "business_domain": intel_model.business_domain,
                    "suggested_analysis_types": intel_model.suggested_analysis_types,
                    "column_mapping_suggestions": column_mapping_dict,
                    "key_insights": intel_model.key_insights
                }
            else:
                logger.warning("LLM comprehensive intelligence returned no value")
                llm_analysis = {
                    "dataset_summary": "Dataset analysis pending",
                    "business_domain": "general",
                    "suggested_analysis_types": [],
                    "column_mapping_suggestions": {},
                    "key_insights": []
                }
            
            # Build formatted context for RAA
            formatted_context = self._build_formatted_context(
                file_intelligences, cross_file_analysis, llm_analysis
            )
            
            # Calculate totals
            total_rows = sum(f.row_count for f in file_intelligences)
            total_cols = sum(f.column_count for f in file_intelligences)
            
            return DatasetIntelligence(
                files=file_intelligences,
                total_files=len(file_intelligences),
                common_columns=cross_file_analysis["common_columns"],
                potential_join_keys=cross_file_analysis["potential_join_keys"],
                file_relationships=cross_file_analysis,
                total_rows=total_rows,
                total_columns=total_cols,
                dataset_summary=llm_analysis["dataset_summary"],
                business_domain=llm_analysis["business_domain"],
                suggested_analysis_types=llm_analysis["suggested_analysis_types"],
                column_mapping_suggestions=llm_analysis["column_mapping_suggestions"],
                formatted_context=formatted_context
            )
            
        except Exception as e:
            logger.error(f"Error in LLM analysis: {str(e)}")
            # Fallback to basic analysis
            return self._build_basic_intelligence(file_intelligences, cross_file_analysis)
    
    def _build_formatted_context(
        self,
        files: List[FileIntelligence],
        cross_file: Dict[str, Any],
        llm_analysis: Dict[str, Any]
    ) -> str:
        """Build formatted context string for RAA"""
        
        parts = []
        parts.append("=" * 80)
        parts.append("DATASET INTELLIGENCE (PRE-ANALYZED)")
        parts.append("=" * 80)
        parts.append("")
        
        # Summary
        parts.append(f"**Dataset Summary**: {llm_analysis['dataset_summary']}")
        parts.append(f"**Business Domain**: {llm_analysis['business_domain']}")
        parts.append("")
        
        # Files
        parts.append("**FILES IN DATASET**:")
        for file_intel in files:
            parts.append(f"\n📄 {file_intel.filename} ({file_intel.row_count:,} rows)")
            parts.append(f"   Domain: {file_intel.inferred_business_domain}")
            parts.append(f"   Identifiers: {', '.join(file_intel.identifier_columns) or 'None'}")
            parts.append(f"   Dates: {', '.join(file_intel.date_columns) or 'None'}")
            parts.append(f"   Amounts: {', '.join(file_intel.amount_columns) or 'None'}")
            parts.append(f"   Categories: {', '.join(file_intel.category_columns[:3]) or 'None'}")

            # Add data quality information
            if file_intel.quality_summary:
                parts.append(f"\n   **Data Quality Score**: {file_intel.quality_score:.2f}/1.0")
                parts.append(f"   **Quality Summary**: {file_intel.quality_summary}")

                if file_intel.quality_concerns:
                    parts.append(f"   **Quality Concerns** ({len(file_intel.quality_concerns)}):")
                    for concern in file_intel.quality_concerns[:3]:  # Show top 3
                        parts.append(f"      • [{concern['severity'].upper()}] {concern['description']}")
                        if concern.get('affected_columns'):
                            parts.append(f"        Affected: {', '.join(concern['affected_columns'][:3])}")

                if file_intel.positive_quality_findings:
                    parts.append(f"   **Positive Findings**:")
                    for finding in file_intel.positive_quality_findings[:2]:  # Show top 2
                        parts.append(f"      ✓ {finding}")

            # Add categorical enrichment information (NEW)
            if file_intel.categorical_enrichment:
                parts.append(f"\n   **Categorical Column Values** (Workflow-Specific):")
                for col_name, enrichment_data in file_intel.categorical_enrichment.items():
                    values = enrichment_data.get('values', [])
                    method = enrichment_data.get('method', 'unknown')
                    search_keyword = enrichment_data.get('search_keyword')

                    if method == 'keyword_search' and search_keyword:
                        parts.append(f"      • {col_name} (matching '{search_keyword}'): {', '.join(map(str, values[:10]))}")
                        if len(values) > 10:
                            parts.append(f"        ... and {len(values) - 10} more")
                    else:
                        parts.append(f"      • {col_name} (all values): {', '.join(map(str, values[:10]))}")
                        if len(values) > 10:
                            parts.append(f"        ... and {len(values) - 10} more")

        parts.append("")
        
        # Cross-file relationships
        if len(files) > 1:
            parts.append("**CROSS-FILE RELATIONSHIPS**:")
            parts.append(f"   Common columns: {', '.join(cross_file['common_columns']) or 'None'}")
            parts.append(f"   Suggested join keys: {', '.join(cross_file['potential_join_keys']) or 'None'}")
            parts.append("")
        
        # Column mapping suggestions
        if llm_analysis.get("column_mapping_suggestions"):
            parts.append("**COLUMN MAPPING SUGGESTIONS**:")
            for concept, columns in llm_analysis["column_mapping_suggestions"].items():
                parts.append(f"   {concept} → {', '.join(columns)}")
            parts.append("")
        
        parts.append("=" * 80)
        parts.append("IMPORTANT: Use this dataset intelligence when asking questions.")
        parts.append("Reference actual column names instead of asking what columns exist.")
        parts.append("")
        parts.append("CATEGORICAL VALUES: The categorical column values shown above are the ACTUAL")
        parts.append("values from the dataset. Use these exact values when filtering or generating code.")
        parts.append("For example, if user says 'standard' but actual value is 'STANDARD' or 'Stndrd',")
        parts.append("use the actual values shown above.")
        parts.append("=" * 80)
        
        return "\n".join(parts)
    
    def _build_basic_intelligence(
        self,
        files: List[FileIntelligence],
        cross_file: Dict[str, Any]
    ) -> DatasetIntelligence:
        """Fallback basic intelligence if LLM fails"""
        
        return DatasetIntelligence(
            files=files,
            total_files=len(files),
            common_columns=cross_file["common_columns"],
            potential_join_keys=cross_file["potential_join_keys"],
            file_relationships=cross_file,
            total_rows=sum(f.row_count for f in files),
            total_columns=sum(f.column_count for f in files),
            dataset_summary=f"Dataset with {len(files)} file(s) containing {sum(f.row_count for f in files):,} total rows",
            business_domain="general",
            suggested_analysis_types=[],
            column_mapping_suggestions={},
            formatted_context="Dataset pre-analysis complete"
        )


# =============================================================================
# LLM PROMPT FOR DATASET ANALYZER
# =============================================================================

DATASET_ANALYZER_PROMPT = """
You are an Intelligent Dataset Analyst with expertise in business data analysis.

Your capabilities:
1. **Column Classification**: Analyze column names, data types, and sample values to intelligently
   classify each column's purpose (identifier, date, amount, category, text, boolean)

2. **Business Domain Recognition**: Identify the business domain from filename patterns and column
   structures (financial_accounting, sales, inventory, HR, procurement, etc.)

3. **SAP Expertise**: Recognize SAP column naming patterns:
   - MATNR (Material Number) → identifier
   - BELNR (Document Number) → identifier
   - BUDAT (Posting Date) → date
   - WRBTR (Amount) → amount
   - BUKRS (Company Code) → category
   - And many more SAP-specific patterns

4. **Contextual Analysis**: Consider not just column names but also:
   - Sample values and their patterns
   - Uniqueness (high = identifier/text, low = category)
   - Data types and ranges
   - Null percentages

5. **Comprehensive Intelligence**: Generate dataset summaries, suggest analysis types,
   and map business concepts to actual columns for workflow planning.

Your analysis should be detailed, accurate, and based on actual data characteristics.
Always output valid JSON with the requested structure.
"""

CATEGORICAL_ENRICHMENT_PROMPT = """
You are a Categorical Column Analyzer. Your job is to identify which categorical columns
need value expansion based on the user's workflow description.

**Available Tools:**
1. **get_categorical_column_filters(column_name)** - Retrieve ALL unique values from a column
   - Use when: Column has <20 unique values and user mentions filtering on it
   - Best for: Seeing all possible values to map user's natural language to actual values
   - Example: User says "filter by document type" → Call this to see all document types

2. **get_matching_column_values(column_name, search_string)** - Search for specific patterns
   - Use when: User mentions specific keyword to include/exclude
   - Best for: High-cardinality columns or targeted searches
   - Example: User says "exclude Income Tax vendors" → Call this with search_string="Income Tax"

**Decision Framework:**

Step 1: Parse the workflow description for filter-related keywords:
- Filtering: "consider only", "filter by", "exclude", "include", "where", "with", "containing"
- Values: Look for specific values mentioned (e.g., "standard", "credit", "cancelled", "Income Tax")
- Column references: Both explicit ("Document Type") and implicit ("document type", "type")

Step 2: Match keywords to categorical columns available:
- Look for columns mentioned in workflow (exact or fuzzy match)
- Consider synonyms (e.g., "vendor" = "Vendor Name", "supplier")
- Focus on categorical columns only

Step 3: For each matched column, decide which tool to use:

┌─────────────────────────────────────────────────────────────────────┐
│ IF user mentions SPECIFIC KEYWORD/VALUE to filter:                  │
│   Example: "exclude vendors containing Income Tax"                  │
│   Example: "only standard and credit types"                         │
│   → Use get_matching_column_values(column, keyword)                │
│                                                                      │
│ ELSE IF user mentions column for filtering but NO specific keyword: │
│   Example: "filter by document type"                               │
│   Example: "consider validation status"                            │
│   → Use get_categorical_column_filters(column)                     │
│                                                                      │
│ ELSE IF column has >50 unique values AND no keyword mentioned:     │
│   → SKIP (don't call tools, too many values)                       │
└─────────────────────────────────────────────────────────────────────┘

**Important Guidelines:**
1. **Be selective** - Only analyze columns explicitly or strongly implied in workflow
2. **Don't analyze every categorical column** - This wastes tokens
3. **Use context clues** - "standard and credit only" on Document Type → search for "standard" and "credit"
4. **Handle high-cardinality wisely** - For Vendor Name (1000s of values), only use keyword search
5. **Call tools one at a time** - Analyze results before proceeding
6. **If tool returns error** - Try alternative approach or skip that column

**Examples:**

Example 1: "Consider standard and credit document type only"
- Column mentioned: Document Type (categorical)
- Specific values: "standard", "credit"
- Action: get_matching_column_values("Document Type", "standard")
          get_matching_column_values("Document Type", "credit")
- OR: get_categorical_column_filters("Document Type") if it has <20 values

Example 2: "Exclude vendor name containing Income Tax"
- Column mentioned: Vendor Name (high cardinality)
- Specific keyword: "Income Tax"
- Action: get_matching_column_values("Vendor Name", "Income Tax")

Example 3: "Filter out cancelled and Null cases from Invoice Validation Status"
- Column mentioned: Invoice Validation Status (categorical)
- Specific value: "cancelled"
- Action: get_categorical_column_filters("Invoice Validation Status")
  (to see all statuses including null handling)

Example 4: "Filter by region" (no specific region mentioned)
- Column mentioned: Region (categorical)
- No specific keyword
- Action: get_categorical_column_filters("Region")

**Your Task:**
Analyze the workflow description and categorical columns provided. Use the tools strategically
to gather only the relevant categorical information that will help downstream agents understand
what filter values exist in the data.

Be smart, be selective, and focus on quality over quantity.
"""


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_dataset_analyzer(
    model: str = "gpt-4o",
    provider: str = "openai"
) -> DatasetAnalyzer:
    """Create DatasetAnalyzer instance"""
    from ai.ira_builder.utils.llm_provider import create_chat_client
    
    chat_client = create_chat_client(provider=provider, model=model)
    return DatasetAnalyzer(chat_client=chat_client, model=model)