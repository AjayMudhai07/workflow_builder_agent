"""
Workflow Config Generator

This module uses LLM to generate production workflow configuration from workflow state.
The generated config is used to deploy workflows to production/staging environments.
"""

import json
import re
from typing import Dict, Any, List
from agent_framework import ChatAgent

from ai.ira_builder.utils.logger import get_logger
from ai.ira_builder.utils.llm_provider import create_chat_client
from ai.ira_builder.utils.config import get_config

logger = get_logger(__name__)


async def _transform_business_logic_plan(
    workflow_name: str,
    workflow_description: str,
    business_logic_plan: str,
    generated_code: str
) -> str:
    """
    Transform the business logic plan into a structured format for production use.

    Uses LLM to convert the plan into a standardized 6-section format with proper HTML formatting.

    Args:
        workflow_name: Name of the workflow
        workflow_description: Description of the workflow
        business_logic_plan: The original business logic plan
        generated_code: The generated code to understand the implementation

    Returns:
        Formatted plan string with HTML markup
    """
    from agent_framework import ChatAgent
    from agent_framework.openai import OpenAIChatClient
    from ai.ira_builder.utils.config import get_config
    import os

    logger.info("📝 Transforming business logic plan to structured format...")

    # Temporarily set environment variables for Groq
    config = get_config()
    original_api_key = os.environ.get('OPENAI_API_KEY')
    original_base_url = os.environ.get('OPENAI_BASE_URL')

    try:
        os.environ['OPENAI_API_KEY'] = config.groq_api_key
        os.environ['OPENAI_BASE_URL'] = config.groq_base_url

        prompt = f"""Transform the following business logic plan into a structured, professional format for production deployment.

**Workflow Name:** {workflow_name}
**Workflow Description:** {workflow_description}

**Original Business Logic Plan:**
{business_logic_plan}

**Generated Code (for context):**
```python
{generated_code}
```

**YOUR TASK:**
Transform this plan into a structured 6-section format with HTML <b> tags for emphasis. Use the following template:

<b>1. WORKFLOW PURPOSE</b>

[1-2 paragraphs explaining what this workflow does and why it exists. Focus on the business problem being solved.]

<b>2. INPUT REQUIREMENTS</b>

The workflow requires the following input files:

• <b>File Name 1</b>: [Description of what this file contains]
• <b>File Name 2</b>: [Description of what this file contains]

<b>3. BUSINESS LOGIC STEPS</b>

[Numbered list of processing steps, written in clear business language:]

1. [First step - what data is loaded and prepared]
2. [Second step - what transformations are applied]
3. [Third step - how data is matched or compared]
4. [Continue with all logic steps...]
5. [Final step - how results are organized]

<b>4. EXCEPTION CRITERIA</b>

An exception is flagged when:

• <b>Condition 1</b>: [Clear explanation of the first exception condition]
• <b>Condition 2</b>: [Clear explanation of the second exception condition]

[Add a paragraph explaining why these conditions matter for business operations]

<b>5. OUTPUT DESCRIPTION</b>

The results file contains the following business information for each exception:

• <b>Column 1 Name</b>: [Business meaning of this column]
• <b>Column 2 Name</b>: [Business meaning of this column]
• <b>Column 3 Name</b>: [Business meaning of this column]
[Continue for all output columns...]

<b>6. BUSINESS IMPACT</b>

<b>Why This Check Is Important:</b>

[Paragraph explaining the business value and compliance implications]

<b>Risks Identified:</b>

• [First risk or issue this workflow helps detect]
• [Second risk or issue]
• [Third risk or issue]

<b>Recommended Actions:</b>

• [First recommended action when exceptions are found]
• [Second recommended action]
• [Third recommended action]
• [Additional recommendations...]

**CRITICAL REQUIREMENTS:**

1. Use <b></b> HTML tags for section headers and key terms (not markdown bold **)
2. Use bullet points with • character (not dashes or asterisks)
3. Write in clear, professional business language
4. Focus on WHAT the workflow does and WHY, not technical implementation details
5. Extract input file names from the code or plan
6. List all output columns with business-friendly descriptions
7. Make it readable for non-technical business users and auditors
8. Keep the structure exactly as shown with all 6 sections
9. Each section should have substantial content (not just placeholders)

Return ONLY the formatted plan text, no other commentary."""

        chat_client = OpenAIChatClient(
            model_id=config.groq_model
        )

        agent = ChatAgent(
            name="Plan-Formatter",
            chat_client=chat_client,
            instructions="You are a business analyst formatting technical plans into professional business documentation.",
            tools=[]
        )

        thread = agent.get_new_thread()
        response = await agent.run(prompt, thread=thread)

        formatted_plan = str(response).strip()

        logger.info("✅ Business logic plan transformed to structured format")
        return formatted_plan

    finally:
        # Restore original environment variables
        if original_api_key is not None:
            os.environ['OPENAI_API_KEY'] = original_api_key
        elif 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']

        if original_base_url is not None:
            os.environ['OPENAI_BASE_URL'] = original_base_url
        elif 'OPENAI_BASE_URL' in os.environ:
            del os.environ['OPENAI_BASE_URL']


async def _identify_required_files_and_columns(
    generated_code: str,
    file_analysis_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Step 1: Identify which files and columns from the CSV analysis are actually used in the code.

    Args:
        generated_code: The generated code
        file_analysis_results: Analysis of the CSV files with original column names

    Returns:
        Dictionary mapping file names to lists of original column names used
    """
    from agent_framework import ChatAgent
    from agent_framework.openai import OpenAIChatClient
    from ai.ira_builder.utils.config import get_config
    import json
    import os

    logger.info("🔍 Step 1: Identifying required files and columns from CSV analysis...")

    # Temporarily set environment variables for Groq
    config = get_config()
    original_api_key = os.environ.get('OPENAI_API_KEY')
    original_base_url = os.environ.get('OPENAI_BASE_URL')

    try:
        os.environ['OPENAI_API_KEY'] = config.groq_api_key
        os.environ['OPENAI_BASE_URL'] = config.groq_base_url

        prompt = f"""You are analyzing code to identify which CSV files and columns are actually used.

**CSV Files Analysis (Original Column Names):**
{json.dumps(file_analysis_results, indent=2)}

**Generated Code:**
```python
{generated_code}
```

**YOUR TASK:**
Analyze the code and identify which columns from the CSV files are actually READ/USED (not created).

Look for:
1. Columns in DATE_COLS, NUMERIC_COLS, STRING_COLS lists
2. Columns in required_columns list
3. Columns accessed for reading: df['column'], df[['col1', 'col2']]
4. DO NOT include columns that are created: df['new_col'] = ...

Return a JSON object mapping file names to their used columns:

{{
  "files": [
    {{
      "file_name": "file_name_from_analysis",
      "used_columns": ["original_column_name_1", "original_column_name_2", ...]
    }}
  ]
}}

**IMPORTANT**: Use the EXACT column names as they appear in the CSV Files Analysis, not how they appear in the code.

Return ONLY the JSON, no other text."""

        chat_client = OpenAIChatClient(
            model_id=config.groq_model
        )

        agent = ChatAgent(
            name="File-Column-Identifier",
            chat_client=chat_client,
            instructions="You are a data analyst identifying which CSV columns are used in code.",
            tools=[]
        )

        thread = agent.get_new_thread()
        response = await agent.run(prompt, thread=thread)

        # Parse response
        if isinstance(response, dict):
            result = response
        else:
            response_text = str(response)
            # Extract JSON
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                result = json.loads(json_match.group(0))
            else:
                raise ValueError("Could not parse file/column identification response")

        logger.info(f"✅ Identified {len(result.get('files', []))} file(s) with required columns")
        return result

    finally:
        # Restore original environment variables
        if original_api_key is not None:
            os.environ['OPENAI_API_KEY'] = original_api_key
        elif 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']

        if original_base_url is not None:
            os.environ['OPENAI_BASE_URL'] = original_base_url
        elif 'OPENAI_BASE_URL' in os.environ:
            del os.environ['OPENAI_BASE_URL']


async def _map_columns_to_code_names(
    generated_code: str,
    identified_files: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Step 2: Map original CSV column names to how they're named in the code.

    Args:
        generated_code: The generated code
        identified_files: Output from step 1 with original column names

    Returns:
        Dictionary with required_files structure using code column names
    """
    from agent_framework import ChatAgent
    from agent_framework.openai import OpenAIChatClient
    from ai.ira_builder.utils.config import get_config
    import json
    import os

    logger.info("🔄 Step 2: Mapping column names to code usage...")

    # Temporarily set environment variables for Groq
    config = get_config()
    original_api_key = os.environ.get('OPENAI_API_KEY')
    original_base_url = os.environ.get('OPENAI_BASE_URL')

    try:
        os.environ['OPENAI_API_KEY'] = config.groq_api_key
        os.environ['OPENAI_BASE_URL'] = config.groq_base_url

        prompt = f"""You are mapping CSV column names to how they're used in code.

**Files and Original Column Names Identified:**
{json.dumps(identified_files, indent=2)}

**Generated Code:**
```python
{generated_code}
```

**YOUR TASK:**
For each file and column, find the EXACT name used in the code.

Return a JSON object with this structure:

{{
  "csv_files": [
    {{
      "file_name": "file_name_without_extension",
      "description": "Brief description of the file",
      "required_columns": [
        {{
          "name": "EXACT_column_name_as_used_in_code",
          "description": "Column description",
          "data_type": "string|numeric|date"
        }}
      ]
    }}
  ]
}}

**CRITICAL RULES:**
1. The "name" field MUST be the EXACT column name as it appears in the code
2. Check DATE_COLS for date columns, NUMERIC_COLS for numeric columns
3. Check the required_columns list in the code
4. Column names must match PRECISELY (case-sensitive, with exact spacing/punctuation)
5. Determine data_type based on which list the column appears in (DATE_COLS=date, NUMERIC_COLS=numeric, default=string)

Return ONLY the JSON, no other text."""

        chat_client = OpenAIChatClient(
            model_id=config.groq_model
        )

        agent = ChatAgent(
            name="Column-Name-Mapper",
            chat_client=chat_client,
            instructions="You are a data analyst mapping column names between CSV and code.",
            tools=[]
        )

        thread = agent.get_new_thread()
        response = await agent.run(prompt, thread=thread)

        # Parse response
        if isinstance(response, dict):
            result = response
        else:
            response_text = str(response)
            # Extract JSON
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                result = json.loads(json_match.group(0))
            else:
                raise ValueError("Could not parse column mapping response")

        logger.info(f"✅ Mapped columns for {len(result.get('csv_files', []))} file(s)")
        return result

    finally:
        # Restore original environment variables
        if original_api_key is not None:
            os.environ['OPENAI_API_KEY'] = original_api_key
        elif 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']

        if original_base_url is not None:
            os.environ['OPENAI_BASE_URL'] = original_base_url
        elif 'OPENAI_BASE_URL' in os.environ:
            del os.environ['OPENAI_BASE_URL']


async def generate_workflow_config(
    workflow_name: str,
    workflow_description: str,
    business_logic_plan: str,
    generated_code: str,
    analysis_instructions: str,
    analysis_code: str,
    file_analysis_results: Dict[str, Any],
    check_id: str
) -> Dict[str, Any]:
    """
    Generate production workflow configuration using LLM.

    Args:
        workflow_name: Name of the workflow
        workflow_description: Description of the workflow
        business_logic_plan: The approved business logic plan
        generated_code: The approved code that generates output dataframe
        analysis_instructions: The approved analysis instructions
        analysis_code: The approved code that generates analysis report
        file_analysis_results: Results from file analysis (columns, descriptions)
        check_id: Unique check ID for this workflow

    Returns:
        Dictionary containing the workflow configuration in the format required by production API
    """
    try:
        logger.info("🔧 Generating workflow configuration using three-step process...")

        # Step 0: Transform business logic plan to structured format
        formatted_plan = await _transform_business_logic_plan(
            workflow_name,
            workflow_description,
            business_logic_plan,
            generated_code
        )

        # Step 1: Identify which files and columns are used (from CSV analysis)
        identified_files = await _identify_required_files_and_columns(generated_code, file_analysis_results)

        # Step 2: Map those columns to code names
        required_files_info = await _map_columns_to_code_names(generated_code, identified_files)

        # Create the prompt for LLM
        user_message = f"""
You are tasked with generating a production workflow configuration JSON for deployment.

**Workflow Information:**
- Name: {workflow_name}
- Description: {workflow_description}
- Check ID: {check_id}

**Business Logic Plan (Structured Format):**
```
{formatted_plan}
```

**Generated Code (Data Processing):**
```python
{generated_code}
```

**Analysis Instructions:**
```
{analysis_instructions}
```

**Analysis Code (Report Generation):**
```python
{analysis_code}
```

**Required Files Information:**
{json.dumps(required_files_info, indent=2)}

**YOUR TASK:**
Generate a complete workflow configuration JSON that follows this EXACT structure:

{{
  "name": "<workflow_name>",
  "description": "<workflow_description>",
  "check_id": "<check_id>",
  "tags": ["<relevant_tags>"],
  "data": {{
    "plan": "<business_logic_plan>",
    "code": "<generated_code_with_triple_backticks>",
    "analyst_instruction": "<analysis_instructions>",
    "statistical_analysis_code": "<analysis_code_with_triple_backticks>",
    "required_files": {{
      "csv_files": [
        {{
          "file_name": "<file_name_without_extension>",
          "description": "<file_description>",
          "required_columns": [
            {{
              "name": "<exact_column_name_as_used_in_code>",
              "description": "<column_description>",
              "data_type": "<column_data_type>"
            }}
          ]
        }}
      ]
    }}
  }}
}}

**CRITICAL REQUIREMENTS:**

1. **Code Fields**: The "code" and "statistical_analysis_code" fields MUST be wrapped in triple backticks:
   - Format: "```python\\n<code>\\n```"
   - Include the language identifier "python"

2. **Required Files**:
   - Use the "Required Files Information" provided above AS-IS
   - This has already been carefully generated to include only INPUT columns (not calculated/output columns)
   - Simply copy it into the "required_files" section of your JSON response
   - DO NOT modify the column names or structure

3. **Tags**: Generate relevant tags based on the workflow purpose (e.g., ["VEN"], ["FIN"], etc.)

4. **Plan**: Use the structured business logic plan PROVIDED ABOVE (it's already formatted with HTML tags)
   - DO NOT modify the formatting or structure
   - The plan is already in the required production format with 6 sections
   - Just copy it as-is into the "plan" field

5. **Analyst Instruction**: Use the analysis instructions as-is, but keep it concise (1-2 sentences)

**IMPORTANT**: Return ONLY the JSON configuration, no additional text or explanation.
"""

        system_message = "You are a senior data engineer responsible for deploying workflows to production environments. You generate precise, production-ready configuration files."

        # Create LLM chat client
        from agent_framework import ChatAgent
        from agent_framework.openai import OpenAIChatClient
        import os

        config = get_config()

        # Temporarily set environment variables for Groq
        original_api_key = os.environ.get('OPENAI_API_KEY')
        original_base_url = os.environ.get('OPENAI_BASE_URL')

        try:
            os.environ['OPENAI_API_KEY'] = config.groq_api_key
            os.environ['OPENAI_BASE_URL'] = config.groq_base_url

            chat_client = OpenAIChatClient(
                model_id=config.groq_model
            )

            # Create agent for workflow config generation
            agent = ChatAgent(
                name="Workflow-Config-Generator",
                chat_client=chat_client,
                instructions=system_message,
                tools=[]
            )

            logger.info("📤 Sending workflow config generation request to LLM...")

            # Get LLM response
            thread = agent.get_new_thread()
            response = await agent.run(user_message, thread=thread)

            # Parse JSON response
            # The response might be a dict, string, or other type
            if isinstance(response, dict):
                # If response is already a dict, use it directly
                workflow_config = response
                logger.info("✅ Response is already a dictionary!")
            elif isinstance(response, str):
                response_text = response
                logger.debug(f"Response text (first 500 chars): {response_text[:500]}")

                # Extract JSON from response
                try:
                    # Look for JSON block in response
                    if "```json" in response_text:
                        json_start = response_text.find("```json") + 7
                        json_end = response_text.find("```", json_start)
                        json_text = response_text[json_start:json_end].strip()
                    elif "```" in response_text:
                        json_start = response_text.find("```") + 3
                        json_end = response_text.find("```", json_start)
                        json_text = response_text[json_start:json_end].strip()
                    else:
                        # Try to find JSON object
                        json_match = re.search(r'\{[\s\S]*\}', response_text)
                        if json_match:
                            json_text = json_match.group(0)
                        else:
                            json_text = response_text.strip()

                    logger.debug(f"Extracted JSON text (first 500 chars): {json_text[:500]}")

                    # Parse JSON
                    workflow_config = json.loads(json_text)
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Failed to parse JSON response: {e}")
                    logger.error(f"Response text: {response_text}")
                    raise ValueError(f"LLM did not return valid JSON: {e}")
            else:
                # Try converting to string and parsing
                response_text = str(response)
                logger.debug(f"Response type: {type(response)}, converted to string (first 500 chars): {response_text[:500]}")

                try:
                    # Try to find JSON object
                    json_match = re.search(r'\{[\s\S]*\}', response_text)
                    if json_match:
                        json_text = json_match.group(0)
                        workflow_config = json.loads(json_text)
                    else:
                        raise ValueError(f"No JSON object found in response")
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Failed to parse JSON response: {e}")
                    logger.error(f"Response text: {response_text}")
                    raise ValueError(f"LLM did not return valid JSON: {e}")

            # Log success
            logger.info("✅ Successfully generated workflow configuration!")
            logger.info(f"   - Name: {workflow_config.get('name')}")
            logger.info(f"   - Check ID: {workflow_config.get('check_id')}")
            logger.info(f"   - Tags: {workflow_config.get('tags')}")

            return workflow_config

        finally:
            # Restore original environment variables
            if original_api_key is not None:
                os.environ['OPENAI_API_KEY'] = original_api_key
            elif 'OPENAI_API_KEY' in os.environ:
                del os.environ['OPENAI_API_KEY']

            if original_base_url is not None:
                os.environ['OPENAI_BASE_URL'] = original_base_url
            elif 'OPENAI_BASE_URL' in os.environ:
                del os.environ['OPENAI_BASE_URL']

    except ValueError as e:
        # Re-raise ValueError (already handled above)
        raise
    except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON response: {e}")
            logger.debug(f"Response text: {response_text}")
            raise ValueError(f"LLM did not return valid JSON: {e}")

    except Exception as e:
        logger.error(f"❌ Error generating workflow config: {str(e)}", exc_info=True)
        raise


def _extract_required_files_info(file_analysis_results: Dict[str, Any], generated_code: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Extract required files and columns information from file analysis results.
    Filters to only include files and columns that are actually used in the code.

    Args:
        file_analysis_results: Results from file analysis
        generated_code: The generated code to check which columns are used

    Returns:
        Dictionary with csv_files list containing file and column information
    """
    required_files = []

    if not file_analysis_results or "files" not in file_analysis_results:
        return {"csv_files": []}

    for file_info in file_analysis_results["files"]:
        file_name = file_info.get("file_name", "")
        file_description = file_info.get("file_description", "")
        column_descriptions = file_info.get("column_descriptions", [])
        columns = file_info.get("columns", [])

        # Remove file extension for file_name
        file_name_no_ext = file_name.rsplit('.', 1)[0] if '.' in file_name else file_name

        # Filter columns that are actually used in the code
        required_columns = []
        for col_desc in column_descriptions:
            col_name = col_desc.get("name", "")

            # Check if column is mentioned in the code (case-sensitive check)
            if col_name and (f'"{col_name}"' in generated_code or f"'{col_name}'" in generated_code or f'["{col_name}"]' in generated_code or f"['{col_name}']" in generated_code):
                # Find corresponding column info for data_type
                col_type = "object"  # default
                for col in columns:
                    if col.get("name") == col_name:
                        col_type = col.get("type", "object")
                        break

                required_columns.append({
                    "name": col_name,
                    "description": col_desc.get("description", ""),
                    "data_type": col_type
                })

        # Only include file if it has required columns
        if required_columns:
            required_files.append({
                "file_name": file_name_no_ext,
                "description": file_description,
                "required_columns": required_columns
            })

    return {"csv_files": required_files}


async def validate_workflow_config(workflow_config: Dict[str, Any]) -> bool:
    """
    Validate that the workflow config has all required fields.

    Args:
        workflow_config: The workflow configuration to validate

    Returns:
        True if valid, raises ValueError if invalid
    """
    required_top_level = ["name", "description", "check_id", "tags", "data"]
    required_data_fields = ["plan", "code", "analyst_instruction", "statistical_analysis_code", "required_files"]

    # Check top-level fields
    for field in required_top_level:
        if field not in workflow_config:
            raise ValueError(f"Missing required field: {field}")

    # Check data fields
    data = workflow_config.get("data", {})
    for field in required_data_fields:
        if field not in data:
            raise ValueError(f"Missing required field in data: {field}")

    # Check code formatting
    if not data["code"].startswith("```"):
        raise ValueError("Code field must be wrapped in triple backticks")

    if not data["statistical_analysis_code"].startswith("```"):
        raise ValueError("Statistical analysis code field must be wrapped in triple backticks")

    # Check required_files structure
    required_files = data.get("required_files", {})
    if "csv_files" not in required_files:
        raise ValueError("required_files must have csv_files field")

    if not isinstance(required_files["csv_files"], list):
        raise ValueError("csv_files must be a list")

    logger.info("✅ Workflow config validation passed")
    return True
