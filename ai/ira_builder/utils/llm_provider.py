"""
LLM Provider abstraction for IRA Workflow Builder.

Supports multiple LLM providers (OpenAI, Groq, Azure OpenAI) with a unified interface.
"""

import os
from typing import Union, Optional
from agent_framework.openai import OpenAIChatClient
from agent_framework.azure import AzureOpenAIChatClient

from ai.ira_builder.utils.config import get_config
from ai.ira_builder.utils.logger import get_logger
from ai.ira_builder.exceptions.errors import AgentException

logger = get_logger(__name__)


def create_chat_client(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    use_azure: bool = False
) -> Union[OpenAIChatClient, AzureOpenAIChatClient]:
    """
    Factory function to create appropriate chat client based on provider.

    This function abstracts the creation of chat clients for different LLM providers
    (OpenAI, Groq, Azure OpenAI), allowing easy switching between providers without
    changing agent code.

    Args:
        provider: LLM provider to use ("openai", "groq", or None for config default)
        model: Model ID to use (or None for provider default)
        use_azure: Whether to use Azure OpenAI (only applies to OpenAI provider)

    Returns:
        Configured chat client instance (OpenAIChatClient or AzureOpenAIChatClient)

    Raises:
        AgentException: If provider configuration is invalid or API key is missing
        ValueError: If unknown provider is specified

    Example:
        >>> # Use OpenAI
        >>> client = create_chat_client(provider="openai", model="gpt-4o")

        >>> # Use Groq
        >>> client = create_chat_client(provider="groq", model="llama-3.3-70b-versatile")

        >>> # Use config default
        >>> client = create_chat_client()
    """
    config = get_config()

    # Use provider from config if not specified
    if provider is None:
        provider = config.llm_provider

    provider = provider.lower()

    logger.info(f"Creating chat client for provider: {provider}")

    # ==========================================
    # Groq Provider
    # ==========================================
    if provider == "groq":
        if not config.groq_api_key:
            raise AgentException(
                "Groq API key not configured. Please set GROQ_API_KEY in .env file."
            )

        # Determine model to use
        model_id = model or config.groq_model

        logger.info(f"Using Groq model: {model_id}")

        # Set Groq API key in environment (OpenAI client will use it)
        os.environ['OPENAI_API_KEY'] = config.groq_api_key

        # Create OpenAI-compatible client with Groq base URL
        return OpenAIChatClient(
            model_id=model_id,
            base_url=config.groq_base_url
        )

    # ==========================================
    # OpenAI Provider (including Azure)
    # ==========================================
    elif provider == "openai":
        if use_azure:
            # Azure OpenAI
            if not config.azure_openai_api_key:
                raise AgentException(
                    "Azure OpenAI API key not configured. "
                    "Please set AZURE_OPENAI_API_KEY in .env file."
                )

            if not config.azure_openai_endpoint:
                raise AgentException(
                    "Azure OpenAI endpoint not configured. "
                    "Please set AZURE_OPENAI_ENDPOINT in .env file."
                )

            deployment_name = model or config.azure_openai_chat_deployment_name

            logger.info(f"Using Azure OpenAI deployment: {deployment_name}")

            return AzureOpenAIChatClient(
                endpoint=config.azure_openai_endpoint,
                deployment_name=deployment_name,
            )
        else:
            # Standard OpenAI
            if not config.openai_api_key:
                raise AgentException(
                    "OpenAI API key not configured. "
                    "Please set OPENAI_API_KEY in .env file."
                )

            model_id = model or config.openai_model

            logger.info(f"Using OpenAI model: {model_id}")

            # Set OpenAI API key in environment to ensure .env takes precedence
            os.environ['OPENAI_API_KEY'] = config.openai_api_key

            return OpenAIChatClient(
                model_id=model_id,
            )

    # ==========================================
    # Unknown Provider
    # ==========================================
    else:
        raise ValueError(
            f"Unknown LLM provider: {provider}. "
            f"Supported providers: 'openai', 'groq'"
        )


def get_provider_info() -> dict:
    """
    Get information about the currently configured LLM provider.

    Returns:
        Dictionary containing provider name, model, and configuration status

    Example:
        >>> info = get_provider_info()
        >>> print(f"Using {info['provider']} with model {info['model']}")
    """
    config = get_config()

    provider = config.llm_provider.lower()

    if provider == "groq":
        return {
            "provider": "groq",
            "model": config.groq_model,
            "base_url": config.groq_base_url,
            "api_key_configured": bool(config.groq_api_key)
        }
    elif provider == "openai":
        return {
            "provider": "openai",
            "model": config.openai_model,
            "api_key_configured": bool(config.openai_api_key)
        }
    else:
        return {
            "provider": "unknown",
            "model": None,
            "api_key_configured": False
        }


def validate_provider_config(provider: Optional[str] = None) -> tuple[bool, str]:
    """
    Validate that the specified provider is properly configured.

    Args:
        provider: Provider to validate (or None for config default)

    Returns:
        Tuple of (is_valid, error_message)
        If valid, error_message will be empty string

    Example:
        >>> is_valid, error = validate_provider_config("groq")
        >>> if not is_valid:
        ...     print(f"Configuration error: {error}")
    """
    config = get_config()

    if provider is None:
        provider = config.llm_provider

    provider = provider.lower()

    if provider == "groq":
        if not config.groq_api_key:
            return False, "Groq API key not configured (GROQ_API_KEY)"
        if not config.groq_model:
            return False, "Groq model not configured (GROQ_MODEL)"
        return True, ""

    elif provider == "openai":
        if not config.openai_api_key:
            return False, "OpenAI API key not configured (OPENAI_API_KEY)"
        if not config.openai_model:
            return False, "OpenAI model not configured (OPENAI_MODEL)"
        return True, ""

    else:
        return False, f"Unknown provider: {provider}"
