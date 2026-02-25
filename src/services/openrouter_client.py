"""
OpenRouter client for fallback AI provider.
Used when OpenAI quota is exceeded.
"""
import httpx
import json
from typing import Dict, Any, List, Optional
import os
from pathlib import Path


def load_openrouter_config() -> Dict[str, str]:
    """
    Load OpenRouter configuration from .env files.
    
    Returns:
        Dictionary with api_key and base_url
    """
    config = {
        "api_key": "",
        "base_url": "https://openrouter.ai/api/v1",
        "model": "google/gemini-2.0-flash-lite-preview-02-05"  # Free tier model
    }
    
    # Strategy 1: Load from src/.env
    src_env_path = Path(__file__).parent.parent / ".env"
    if src_env_path.exists():
        from dotenv import dotenv_values
        env_vars = dotenv_values(src_env_path)
        config["api_key"] = env_vars.get("OPENROUTER_API_KEY", "").strip()
        config["model"] = env_vars.get("OPENROUTER_MODEL", config["model"])
    
    # Strategy 2: Load from project root .env
    if not config["api_key"]:
        root_env_path = Path(__file__).parent.parent.parent.parent / ".env"
        if root_env_path.exists():
            from dotenv import dotenv_values
            env_vars = dotenv_values(root_env_path)
            config["api_key"] = env_vars.get("OPENROUTER_API_KEY", "").strip()
            config["model"] = env_vars.get("OPENROUTER_MODEL", config["model"])
    
    # Strategy 3: Environment variables
    if not config["api_key"]:
        config["api_key"] = os.getenv("OPENROUTER_API_KEY", "").strip()
        config["model"] = os.getenv("OPENROUTER_MODEL", config["model"])
    
    # Use OPENROUTER_BASE_URL if provided
    base_url = os.getenv("OPENROUTER_BASE_URL", "").strip()
    if base_url:
        config["base_url"] = base_url
    
    return config


class OpenRouterResponse:
    """Mock OpenAI response structure for compatibility."""
    
    def __init__(self, data: Dict[str, Any]):
        self.choices = []
        for choice_data in data.get("choices", []):
            self.choices.append(OpenRouterChoice(choice_data))


class OpenRouterChoice:
    """Mock OpenAI choice structure."""
    
    def __init__(self, data: Dict[str, Any]):
        self.message = OpenRouterMessage(data.get("message", {}))
        self.finish_reason = data.get("finish_reason", "stop")


class OpenRouterMessage:
    """Mock OpenAI message structure."""
    
    def __init__(self, data: Dict[str, Any]):
        self.content = data.get("content", "")
        self.role = data.get("role", "assistant")
        self.tool_calls = data.get("tool_calls", None)
        
        # Convert tool_calls to OpenAI-compatible format
        if self.tool_calls:
            formatted_calls = []
            for tc in self.tool_calls:
                formatted_calls.append(OpenRouterToolCall(tc))
            self.tool_calls = formatted_calls


class OpenRouterToolCall:
    """Mock OpenAI tool call structure."""
    
    def __init__(self, data: Dict[str, Any]):
        self.id = data.get("id", "")
        self.type = "function"
        self.function = OpenRouterFunction(data.get("function", {}))


class OpenRouterFunction:
    """Mock OpenAI function structure."""
    
    def __init__(self, data: Dict[str, Any]):
        self.name = data.get("name", "")
        self.arguments = data.get("arguments", "{}")


async def call_openrouter_chat(
    messages: List[Dict[str, Any]],
    tools: Optional[List[Dict[str, Any]]] = None,
    tool_choice: str = "auto"
) -> OpenRouterResponse:
    """
    Call OpenRouter API with messages and optional tools.
    
    Args:
        messages: List of message dictionaries (OpenAI format)
        tools: Optional list of tool definitions
        tool_choice: Tool choice strategy ("auto", "none", "required")
    
    Returns:
        OpenRouterResponse object (OpenAI-compatible structure)
    
    Raises:
        Exception: If API call fails
    """
    config = load_openrouter_config()
    
    if not config["api_key"]:
        raise Exception("OpenRouter API key not configured")
    
    # Prepare request body
    body = {
        "model": config["model"],
        "messages": messages,
    }
    
    # Add tools if provided
    if tools:
        body["tools"] = tools
        body["tool_choice"] = tool_choice
    
    # Set max_tokens to 512 for free tier compatibility
    body["max_tokens"] = 512

    # Prepare headers
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/todo-chatbot",  # Required by OpenRouter
        "X-Title": "Todo AI Chatbot",  # Required by OpenRouter
    }
    
    # Make the request
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{config['base_url']}/chat/completions",
                headers=headers,
                json=body
            )
            
            if response.status_code != 200:
                error_msg = f"OpenRouter API error: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f" - {error_data.get('error', {}).get('message', 'Unknown error')}"
                except:
                    error_msg += f" - {response.text}"
                raise Exception(error_msg)
            
            response_data = response.json()
            return OpenRouterResponse(response_data)
            
        except httpx.TimeoutException:
            raise Exception("OpenRouter request timed out")
        except httpx.ConnectError:
            raise Exception("Cannot connect to OpenRouter service")
        except Exception as e:
            raise Exception(f"OpenRouter error: {str(e)}")


def get_openrouter_model_name() -> str:
    """Get the configured OpenRouter model name."""
    config = load_openrouter_config()
    return config["model"]


def is_openrouter_configured() -> bool:
    """Check if OpenRouter is properly configured."""
    config = load_openrouter_config()
    return bool(config["api_key"])
