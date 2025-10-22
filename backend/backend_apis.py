import boto3
import os
import requests
import json
import logging
from pprint import pprint
from typing import Dict, Optional,Any




#########################################################################
from dotenv import find_dotenv, load_dotenv
from pathlib import Path

env_path = Path('.')/'.env'
load_dotenv(dotenv_path=env_path, override=True)

#########################################################################

#########################################################################

staging_server_ip = "https://api-stg.irame.ai/datamanager/internal/v1"
production_server_ip = "https://api-prod.irame.ai/datamanager/internal/v1"
production_token = "65e704ad-83be-40b1-a597-8c4e70a30596"
staging_token = "d321e9dd-265b-4a16-b690-3c1708b47a10"
#########################################################################
# backend_server_ip = staging_server_ip
# api_token = staging_token
#########################################################################




def get_workflow_check(
    workflow_check_id: str,
    mode: str
) -> Optional[Dict[str, Any]]:
    """
    Gets a workflow check by ID from the Data Manager API.
    
    Args:
        workflow_check_id: ID of the workflow check to retrieve
        mode: Either "Staging" or "Production" to determine which environment to use
        
    Returns:
        Dict containing the workflow check data, or None if error occurred
    """
    if mode == "Staging":
        backend_server_ip = staging_server_ip
        api_token = staging_token
    else:
        backend_server_ip = production_server_ip
        api_token = production_token

    url = f'{backend_server_ip}/workflow-checks/{workflow_check_id}'
    headers = {
        "x-app-token": api_token,
        "accept": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            response=response.json()
            # print("-"*55)
            # print(json.dumps(response,indent=4))
            # print("-"*55) 
            # input()
            return response
        else:
            print(f"Failed to get workflow check: {response.status_code}")
            return None
    except Exception as e:
        print(f"An error occurred in get_workflow_check: {e}")
        return None


def make_workflow_live(
    workflow_config: Dict[str, Any],
    business_process_id: str,
    mode : str
):
    """
    Creates a workflow check by calling the Data Manager API with the provided workflow configuration.
    
    Args:
        workflow_config_path: Path to the JSON file containing the workflow configuration
        data_manager_url: Base URL of the Data Manager API
        data_manager_app_token: App token for authentication
        business_process_id: ID of the business process this check belongs to
        check_id: Unique identifier for the check
        name: (Optional) Override name for the check
        description: (Optional) Override description for the check
        tags: (Optional) Additional tags for the check
    """
    with open('sample_to_be_live_worfklow_config.json', 'w', encoding='utf-8') as f:
        json.dump(workflow_config, f, indent=2, ensure_ascii=False)
        
    if mode=="Staging":
        backend_server_ip=staging_server_ip
        api_token = staging_token
    else:
        backend_server_ip=production_server_ip
        api_token = production_token

    


    url = f'{backend_server_ip}/workflow-checks'
    headers = {
            "x-app-token": api_token,
            "accept": "application/json"
        }

    
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
        response = requests.post(url, headers=headers, json=payload)
       
        
        if response.status_code != 200:
            print("Workflow check creation failed", response.status_code)
        return response.status_code
    except Exception as e:
        print(f"An error occurred in create_workflow_check: {e}")
        return None


def update_workflow_check(
    workflow_check_id: str,
    workflow_config: Dict[str, Any],
    business_process_id: str,
    mode: str
) -> Optional[int]:
    """
    Updates an existing workflow check by ID using the Data Manager API.
    
    Args:
        workflow_check_id: ID of the workflow check to update
        workflow_config: Dictionary containing the workflow configuration to update
        business_process_id: ID of the business process this check belongs to
        mode: Either "Staging" or "Production" to determine which environment to use
        
    Returns:
        HTTP status code of the response, or None if error occurred
    """
    if mode == "Staging":
        backend_server_ip = staging_server_ip
        api_token = staging_token
    else:
        backend_server_ip = production_server_ip
        api_token = production_token

    url = f'{backend_server_ip}/workflow-checks/{workflow_check_id}'
    headers = {
        "x-app-token": api_token,
        "Content-Type": "application/json"
    }

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
        response = requests.put(url, headers=headers, json=payload)
        print(response.status_code)
      
        
        if response.status_code != 200:
            print(f"Workflow check update failed: {response.status_code}")
            print(f"Response: {response.text}")
        
        return response.status_code
        
    except Exception as e:
        print(f"An error occurred in update_workflow_check: {e}")
        return None
    
    
def get_session_queries(session_id: str, mode: str) -> Optional[dict]:
    """
    Fetch queries for a given session ID.
    
    Args:
        session_id (str): The session ID to fetch queries for
        mode (str): Either "Staging" or "Production" to determine which environment to use
        
    Returns:
        dict: Response data if successful, None otherwise
    """
    # Select backend based on mode
    if mode == "Staging":
        backend_server_ip = staging_server_ip
        api_token = staging_token
    else:
        backend_server_ip = production_server_ip
        api_token = production_token
    
    # Remove any trailing slashes and adjust path
    base_url = backend_server_ip.rstrip('/')
    
    # If base URL already contains the path, use it directly
    if '/datamanager/internal/v1' in base_url:
        url = f"{base_url}/sessions/{session_id}/queries"
    else:
        url = f"{base_url}/datamanager/internal/v1/sessions/{session_id}/queries"
    
    headers = {
        'x-app-token': api_token
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
            
    except requests.exceptions.RequestException as e:
        return None


