"""
Production API Client Service

This module provides a client for interacting with the IRA Production Data Manager API.
It handles workflow check creation, updates, and retrieval operations.
"""

import requests
import json
import os
from typing import Dict, Optional, Any, Literal
from pathlib import Path

from ai.ira_builder.utils.logger import get_logger

logger = get_logger(__name__)

# API Configuration
STAGING_SERVER_IP = "https://api-stg.irame.ai/datamanager/internal/v1"
PRODUCTION_SERVER_IP = "https://api-prod.irame.ai/datamanager/internal/v1"
STAGING_TOKEN = os.getenv("STAGING_API_TOKEN", "d321e9dd-265b-4a16-b690-3c1708b47a10")
PRODUCTION_TOKEN = os.getenv("PRODUCTION_API_TOKEN", "65e704ad-83be-40b1-a597-8c4e70a30596")


class ProductionAPIClient:
    """Client for interacting with IRA Production Data Manager API."""

    def __init__(self, mode: Literal["Staging", "Production"] = "Staging"):
        """
        Initialize the Production API Client.

        Args:
            mode: Either "Staging" or "Production" to determine which environment to use
        """
        self.mode = mode

        if mode == "Staging":
            self.base_url = STAGING_SERVER_IP
            self.api_token = STAGING_TOKEN
        else:
            self.base_url = PRODUCTION_SERVER_IP
            self.api_token = PRODUCTION_TOKEN

        self.headers = {
            "x-app-token": self.api_token,
            "accept": "application/json",
            "Content-Type": "application/json"
        }

        logger.info(f"Production API Client initialized for {mode} environment")

    def get_workflow_check(self, workflow_check_id: str) -> Optional[Dict[str, Any]]:
        """
        Gets a workflow check by ID from the Data Manager API.

        Args:
            workflow_check_id: ID of the workflow check to retrieve

        Returns:
            Dict containing the workflow check data, or None if error occurred
        """
        url = f'{self.base_url}/workflow-checks/{workflow_check_id}'

        try:
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                logger.info(f"✅ Retrieved workflow check: {workflow_check_id}")
                return response.json()
            else:
                logger.error(f"❌ Failed to get workflow check: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None

        except Exception as e:
            logger.error(f"❌ Error in get_workflow_check: {str(e)}", exc_info=True)
            return None

    def make_workflow_live(
        self,
        workflow_config: Dict[str, Any],
        business_process_id: str
    ) -> Optional[int]:
        """
        Creates a workflow check by calling the Data Manager API with the provided workflow configuration.
        This makes the workflow "live" in production/staging environment.

        Args:
            workflow_config: Dictionary containing the workflow configuration with keys:
                - name: Workflow name
                - description: Workflow description
                - check_id: Unique identifier for the check
                - tags: List of tags
                - data: Dictionary containing:
                    - plan: Business Logic Plan
                    - code: Code to generate output dataframe
                    - analyst_instruction: Analysis instructions
                    - statistical_analysis_code: Code to generate analysis report
                    - required_files: Files and columns required
            business_process_id: ID of the business process this check belongs to

        Returns:
            HTTP status code of the response, or None if error occurred
        """
        # Save workflow config for debugging
        debug_path = Path('sample_to_be_live_workflow_config.json')
        try:
            with open(debug_path, 'w', encoding='utf-8') as f:
                json.dump(workflow_config, f, indent=2, ensure_ascii=False)
            logger.info(f"📝 Saved workflow config to: {debug_path}")
        except Exception as e:
            logger.warning(f"Could not save debug config: {e}")

        url = f'{self.base_url}/workflow-checks'

        # Build payload
        payload = {
            "name": workflow_config.get("name", ""),
            "description": workflow_config.get("description", ""),
            "tags": workflow_config.get("tags", []),
            "check_id": workflow_config.get("check_id", ""),
            "business_process_id": business_process_id,
            "data": workflow_config.get("data", {})
        }

        # Add optional components if they exist
        for field in ["plan", "file_mapping_user", "file_mapping_ira"]:
            if field in workflow_config:
                payload[field] = workflow_config[field]

        try:
            logger.info(f"🚀 Making workflow live in {self.mode}...")
            logger.info(f"   - Workflow: {payload['name']}")
            logger.info(f"   - Check ID: {payload['check_id']}")
            logger.info(f"   - Business Process ID: {business_process_id}")
            logger.info(f"   - API URL: {url}")
            logger.info(f"📤 Request Payload:")
            logger.info(json.dumps(payload, indent=2))

            response = requests.post(url, headers=self.headers, json=payload)

            logger.info(f"📡 Production API Response:")
            logger.info(f"   - Status Code: {response.status_code}")
            logger.info(f"   - Headers: {dict(response.headers)}")

            try:
                response_json = response.json()
                logger.info(f"   - Response Body: {json.dumps(response_json, indent=2)}")
            except:
                logger.info(f"   - Response Text: {response.text}")

            if response.status_code == 200:
                logger.info(f"✅ Workflow successfully made live!")
                return response.status_code
            else:
                logger.error(f"❌ Workflow check creation failed: {response.status_code}")
                return response.status_code

        except Exception as e:
            logger.error(f"❌ Error in make_workflow_live: {str(e)}", exc_info=True)
            return None

    def update_workflow_check(
        self,
        workflow_check_id: str,
        workflow_config: Dict[str, Any],
        business_process_id: str
    ) -> Optional[int]:
        """
        Updates an existing workflow check by ID using the Data Manager API.

        Args:
            workflow_check_id: ID of the workflow check to update
            workflow_config: Dictionary containing the workflow configuration to update
            business_process_id: ID of the business process this check belongs to

        Returns:
            HTTP status code of the response, or None if error occurred
        """
        url = f'{self.base_url}/workflow-checks/{workflow_check_id}'

        # Structure payload the same way as make_workflow_live
        payload = {
            "name": workflow_config.get("name", ""),
            "description": workflow_config.get("description", ""),
            "tags": workflow_config.get("tags", []),
            "check_id": workflow_config.get("check_id", ""),
            "business_process_id": business_process_id,
            "data": workflow_config.get("data", {})
        }

        # Add optional components if they exist
        for field in ["plan", "file_mapping_user", "file_mapping_ira"]:
            if field in workflow_config:
                payload[field] = workflow_config[field]

        try:
            logger.info(f"🔄 Updating workflow check: {workflow_check_id}")

            response = requests.put(url, headers=self.headers, json=payload)

            if response.status_code == 200:
                logger.info(f"✅ Workflow check updated successfully!")
                return response.status_code
            else:
                logger.error(f"❌ Workflow check update failed: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return response.status_code

        except Exception as e:
            logger.error(f"❌ Error in update_workflow_check: {str(e)}", exc_info=True)
            return None

    def get_session_queries(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch queries for a given session ID.

        Args:
            session_id: The session ID to fetch queries for

        Returns:
            Response data if successful, None otherwise
        """
        # Remove any trailing slashes and adjust path
        base_url = self.base_url.rstrip('/')

        # If base URL already contains the path, use it directly
        if '/datamanager/internal/v1' in base_url:
            url = f"{base_url}/sessions/{session_id}/queries"
        else:
            url = f"{base_url}/datamanager/internal/v1/sessions/{session_id}/queries"

        try:
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                logger.info(f"✅ Retrieved session queries for: {session_id}")
                return response.json()
            else:
                logger.error(f"❌ Failed to get session queries: {response.status_code}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error in get_session_queries: {str(e)}", exc_info=True)
            return None


# Singleton instance
_client_cache: Dict[str, ProductionAPIClient] = {}


def get_production_api_client(mode: Literal["Staging", "Production"] = "Staging") -> ProductionAPIClient:
    """
    Get or create a ProductionAPIClient instance.

    Args:
        mode: Either "Staging" or "Production"

    Returns:
        ProductionAPIClient instance
    """
    if mode not in _client_cache:
        _client_cache[mode] = ProductionAPIClient(mode=mode)

    return _client_cache[mode]
