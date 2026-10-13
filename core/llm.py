"""
Unified LLM Client for atui.
Communicates with OpenAI-compatible endpoints (including tokenfy, OpenAI, DeepSeek, etc.)
using Python standard library (urllib.request) for zero-dependency portability.
"""

import os
import json
import time
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional, Tuple

class LLMClient:
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "config.json"
        )
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[Warning] Failed to load config from {self.config_path}: {e}")
        return {
            "default_provider": "tokenfy",
            "default_model": "gemini-2.5-flash-lite",
            "providers": {
                "tokenfy": {
                    "base_url": "https://tokenfy.net/v1",
                    "api_key": "sk-3jzNsXzd1xb88KvprfrCHOQATapDqwt9LIYvlZKHVAH2zyRd"
                }
            }
        }

    def _resolve_provider(self, model: Optional[str] = None) -> Tuple[str, str, str]:
        providers = self.config.get("providers", {})
        default_pname = self.config.get("default_provider", "tokenfy")
        default_model = self.config.get("default_model", "gemini-2.5-flash-lite")

        target_model = model or default_model
        
        env_base_url = os.environ.get("OPENAI_BASE_URL")
        env_api_key = os.environ.get("OPENAI_API_KEY")

        chosen_provider = providers.get(default_pname, {})
        for pname, pdata in providers.items():
            if target_model in pdata.get("models", []):
                chosen_provider = pdata
                break

        base_url = env_base_url or chosen_provider.get("base_url", "https://tokenfy.net/v1")
        api_key = env_api_key or chosen_provider.get("api_key", "")

        if base_url.startswith("${"):
            base_url = "https://tokenfy.net/v1"
        if api_key.startswith("${"):
            api_key = ""

        if base_url.endswith("/"):
            base_url = base_url[:-1]

        return base_url, api_key, target_model

    def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        timeout: int = 60,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        base_url, api_key, target_model = self._resolve_provider(model)
        endpoint = f"{base_url}/chat/completions"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        payload: Dict[str, Any] = {
            "model": target_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        if tools and len(tools) > 0:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        data_bytes = json.dumps(payload).encode("utf-8")

        for attempt in range(1, max_retries + 1):
            req = urllib.request.Request(endpoint, data=data_bytes, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=timeout) as response:
                    body = response.read().decode("utf-8")
                    result = json.loads(body)
                    choices = result.get("choices", [])
                    if not choices:
                        raise ValueError(f"No choices returned by LLM: {result}")
                    return {
                        "success": True,
                        "message": choices[0].get("message", {}),
                        "finish_reason": choices[0].get("finish_reason", "stop"),
                        "usage": result.get("usage", {}),
                        "model": target_model
                    }
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8", "replace")
                if attempt == max_retries:
                    return {
                        "success": False,
                        "error": f"HTTP {e.code} Error on {endpoint}: {err_body}",
                        "message": {"role": "assistant", "content": ""}
                    }
                time.sleep(2 ** attempt)
            except Exception as e:
                if attempt == max_retries:
                    return {
                        "success": False,
                        "error": f"Request exception: {str(e)}",
                        "message": {"role": "assistant", "content": ""}
                    }
                time.sleep(2 ** attempt)

        return {
            "success": False,
            "error": "Exceeded max retries",
            "message": {"role": "assistant", "content": ""}
        }

default_client = LLMClient()
