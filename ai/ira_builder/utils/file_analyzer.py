"""
File Analyzer Module

This module uses LLM to analyze uploaded CSV files and generate:
1. Column descriptions for each column in each file
2. File descriptions for each uploaded file
3. Overall dataset description combining all files

The analysis helps provide rich context to the Planner agent.
"""

import json
import pandas as pd
from typing import Dict, List, Any, Optional
from pathlib import Path
from agent_framework import ChatAgent
from ai.ira_builder.utils.logger import get_logger
from ai.ira_builder.utils.llm_provider import create_chat_client
from ai.ira_builder.utils.config import get_config

logger = get_logger(__name__)


async def get_column_descriptions(data_input: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Generates descriptions for columns based on input data structure using LLM.

    Args:
        data_input (dict): Dictionary containing 'columns' and 'rows'
                          - columns: list of dicts with 'name' and 'type'
                          - rows: list of strings representing CSV rows (or first few rows)

    Returns:
        list: List of dictionaries with 'name' and 'description' for each column
    """
    try:
        columns = data_input.get("columns", [])
        rows = data_input.get("rows", [])

        if not columns:
            logger.warning("No columns provided for description generation")
            return []

        # Create column data type mapping
        column_data_type = {col["name"]: col["type"] for col in columns}

        # Parse first row data
        first_row_data = {}
        if rows:
            # Assuming comma-separated values in the first row
            column_names = [col["name"] for col in columns]
            first_row_values = rows[0].split(',')

            # Map column names to first row values
            for i, col_name in enumerate(column_names):
                if i < len(first_row_values):
                    first_row_data[col_name] = first_row_values[i].strip()
                else:
                    first_row_data[col_name] = ""

        # Generate user message for column descriptions
        user_message = f"""
You are tasked with analyzing the column names of a spreadsheet to provide a one-liner description for each column. Follow these steps to complete the task:

1. **Analyze the Data**: Based on the data type of each column and the first row of data provided below, try to understand what sort of data is stored in this spreadsheet.
2. **Generate Descriptions**: Using your understanding of the data, provide a one-liner description for every column in the spreadsheet.

Your response should be structured in JSON format, where each column name is a key, and its corresponding one-liner description is the value.

Column Data Type : {column_data_type}
First Row Data : {first_row_data}

**Instructions**:
- Ensure your descriptions are concise yet informative.
- If you encounter a column name or data type that is unclear, make an educated guess about the nature of the data based on the first row's content.
- Your final output should strictly adhere to the JSON format specified above, with each column name followed by its description enclosed in quotation marks.

**Example Output Format:**
{{
  "column1": "Description of column 1",
  "column2": "Description of column 2"
}}

**Please proceed with analyzing the spreadsheet columns and generating their descriptions as instructed.**
        """

        system_message = "You are a senior Data Analyst at a very big company."

        # Create LLM chat client (using Groq for fast analysis)
        config = get_config()
        chat_client = create_chat_client(
            provider=config.coder_provider,
            model=None
        )

        # Create agent for column description
        agent = ChatAgent(
            name="Column-Description-Analyzer",
            chat_client=chat_client,
            instructions=system_message,
            tools=[]
        )

        logger.info(f"Generating column descriptions for {len(columns)} columns...")

        # Get LLM response
        thread = agent.get_new_thread()
        response = await agent.run(user_message, thread=thread)

        # Parse JSON response
        response_text = str(response)

        # Try to extract JSON from response
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
                json_text = response_text.strip()

            # Parse JSON
            descriptions_dict = json.loads(json_text)

            # Convert to list format
            column_descriptions = [
                {
                    "name": col["name"],
                    "description": descriptions_dict.get(col["name"], "No description available")
                }
                for col in columns
            ]

            logger.info(f"✅ Successfully generated descriptions for {len(column_descriptions)} columns")
            return column_descriptions

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response text: {response_text}")

            # Fallback: return columns with generic descriptions
            return [
                {
                    "name": col["name"],
                    "description": f"{col['type']} column"
                }
                for col in columns
            ]

    except Exception as e:
        logger.error(f"Error generating column descriptions: {str(e)}", exc_info=True)
        # Return columns with generic descriptions as fallback
        return [
            {
                "name": col["name"],
                "description": "Column description unavailable"
            }
            for col in data_input.get("columns", [])
        ]


async def get_file_description(file_name: str, columns_with_descriptions: List[Dict[str, str]]) -> str:
    """
    Generates an overall description of the file based on column descriptions.

    Args:
        file_name (str): Name of the file being analyzed
        columns_with_descriptions (list): List of dictionaries with 'name' and 'description'
                                        for each column (output from get_column_descriptions)

    Returns:
        str: A concise description of the overall file
    """
    try:
        if not columns_with_descriptions:
            return "Unable to generate file description - no column information available"

        # Prepare the dataset structure for analysis
        dataset_info = {
            "dataset": {
                "columns": columns_with_descriptions
            }
        }

        user_message = f"""
Given a dataset in JSON format, where the data provides details about the columns within a file (including the names of the columns and their descriptions), your task is to analyze the dataset.
Based on your analysis, generate a concise one or two-sentence description summarizing the content and key characteristics of this data.
Ensure your summary captures the essence of what the dataset represents, highlighting any notable themes or patterns you observe.

**Note:** Never mention file formats in your response

Dataset : {dataset_info}

**Please provide only the description, without any additional formatting or explanation.**
        """

        system_message = "You are a senior Data Analyst at a very big company."

        # Create LLM chat client (using Groq for fast analysis)
        config = get_config()
        chat_client = create_chat_client(
            provider=config.coder_provider,
            model=None
        )

        # Create agent for file description
        agent = ChatAgent(
            name="File-Description-Analyzer",
            chat_client=chat_client,
            instructions=system_message,
            tools=[]
        )

        logger.info(f"Generating file description for: {file_name}")

        # Get LLM response
        thread = agent.get_new_thread()
        response = await agent.run(user_message, thread=thread)

        file_description = str(response).strip()

        logger.info(f"✅ Generated file description: {file_description[:100]}...")
        return file_description

    except Exception as e:
        logger.error(f"Error generating file description: {str(e)}", exc_info=True)
        return f"Data file containing {len(columns_with_descriptions)} columns"


async def get_dataset_description(file_descriptions: List[Dict[str, str]]) -> Dict[str, str]:
    """
    Generates an overall dataset description based on multiple file descriptions.

    Args:
        file_descriptions (list): List containing file information
                                 Format: [
                                     {
                                         "file_name": "File 1 name",
                                         "file_description": "description of file 1"
                                     },
                                     {
                                         "file_name": "File 2 name",
                                         "file_description": "description of file 2"
                                     }
                                 ]

    Returns:
        dict: Dictionary with dataset description
              Format: {"dataset_description": "string"}
    """
    try:
        # Validate input
        if not file_descriptions or not isinstance(file_descriptions, list):
            return {"dataset_description": "Unable to generate description - no file information provided"}

        # Check if any files provided
        if len(file_descriptions) == 0:
            return {"dataset_description": "Unable to generate description - no files provided"}

        # If only one file, use its description as dataset description
        if len(file_descriptions) == 1:
            return {
                "dataset_description": file_descriptions[0].get("file_description", "Dataset description unavailable")
            }

        # Create user message for dataset description generation
        user_message = f"""
You are tasked with analyzing multiple files within a dataset to provide an overall dataset description. Based on the individual file descriptions provided below, generate a comprehensive 2-3 sentence summary that captures the essence and purpose of the entire dataset.

Instructions:
- Analyze the relationships and common themes across all files
- Identify the overall purpose and scope of the dataset
- Generate a cohesive description that explains what this dataset represents as a whole
- Focus on the business context, data domain, and potential use cases
- Keep the description concise but informative (2-3 sentences)
- Do not mention individual file names in the final description
- Focus on the collective value and insights the dataset provides

Please provide only the dataset description without any additional formatting or explanation.

File Details: {file_descriptions}
        """

        system_message = "You are a senior Data Analyst at a very big company."

        # Create LLM chat client (using Groq for fast analysis)
        config = get_config()
        chat_client = create_chat_client(
            provider=config.coder_provider,
            model=None
        )

        # Create agent for dataset description
        agent = ChatAgent(
            name="Dataset-Description-Analyzer",
            chat_client=chat_client,
            instructions=system_message,
            tools=[]
        )

        logger.info(f"Generating dataset description from {len(file_descriptions)} files...")

        # Get LLM response
        thread = agent.get_new_thread()
        response = await agent.run(user_message, thread=thread)

        dataset_description = str(response).strip()

        logger.info(f"✅ Generated dataset description: {dataset_description[:100]}...")
        return {"dataset_description": dataset_description}

    except Exception as e:
        logger.error(f"Error generating dataset description: {str(e)}", exc_info=True)
        return {
            "dataset_description": f"Dataset containing {len(file_descriptions)} files with various data columns"
        }


async def analyze_csv_file(file_path: str, max_rows_for_sample: int = 5) -> Dict[str, Any]:
    """
    Analyzes a CSV file and generates column descriptions and file description.

    Args:
        file_path (str): Path to the CSV file
        max_rows_for_sample (int): Number of rows to use for sample data analysis

    Returns:
        dict: Dictionary containing:
            - file_name: Name of the file
            - columns: List of column info with names and types
            - column_descriptions: List of dicts with name and description
            - file_description: Overall file description
    """
    try:
        # Import the helper function
        from ai.ira_builder.tools.csv_tools import read_csv_with_encoding

        # Read CSV file with automatic encoding detection
        df = read_csv_with_encoding(file_path)
        file_name = Path(file_path).name
        logger.info(f"Analyzing file: {file_name} ({len(df)} rows, {len(df.columns)} columns)")

        # Get column info
        columns = [
            {
                "name": col,
                "type": str(df[col].dtype)
            }
            for col in df.columns
        ]

        # Get first few rows as strings for context
        rows = []
        for i in range(min(max_rows_for_sample, len(df))):
            row_str = ','.join([str(val) for val in df.iloc[i].values])
            rows.append(row_str)

        # Prepare data input for column description
        data_input = {
            "columns": columns,
            "rows": rows
        }

        # Step 1: Get column descriptions
        column_descriptions = await get_column_descriptions(data_input)

        # Step 2: Get file description
        file_description = await get_file_description(file_name, column_descriptions)

        result = {
            "file_name": file_name,
            "file_path": file_path,
            "columns": columns,
            "column_descriptions": column_descriptions,
            "file_description": file_description,
            "row_count": len(df),
            "column_count": len(df.columns)
        }

        logger.info(f"✅ Completed analysis for: {file_name}")
        return result

    except Exception as e:
        logger.error(f"Error analyzing CSV file {file_path}: {str(e)}", exc_info=True)
        raise


async def analyze_dataset(file_paths: List[str]) -> Dict[str, Any]:
    """
    Analyzes multiple CSV files and generates an overall dataset description.

    Args:
        file_paths (list): List of paths to CSV files

    Returns:
        dict: Dictionary containing:
            - files: List of file analysis results
            - dataset_description: Overall dataset description
    """
    try:
        logger.info(f"Starting dataset analysis for {len(file_paths)} files...")

        # Analyze each file
        file_analyses = []
        for file_path in file_paths:
            file_analysis = await analyze_csv_file(file_path)
            file_analyses.append(file_analysis)

        # Prepare file descriptions for dataset description generation
        file_descriptions = [
            {
                "file_name": analysis["file_name"],
                "file_description": analysis["file_description"]
            }
            for analysis in file_analyses
        ]

        # Step 3: Get dataset description
        dataset_desc_result = await get_dataset_description(file_descriptions)

        result = {
            "files": file_analyses,
            "dataset_description": dataset_desc_result["dataset_description"],
            "total_files": len(file_analyses),
            "total_columns": sum(f["column_count"] for f in file_analyses),
            "total_rows": sum(f["row_count"] for f in file_analyses)
        }

        logger.info(f"✅ Completed dataset analysis:")
        logger.info(f"   - Files: {result['total_files']}")
        logger.info(f"   - Total Columns: {result['total_columns']}")
        logger.info(f"   - Total Rows: {result['total_rows']}")
        logger.info(f"   - Dataset Description: {result['dataset_description'][:100]}...")

        return result

    except Exception as e:
        logger.error(f"Error analyzing dataset: {str(e)}", exc_info=True)
        raise
