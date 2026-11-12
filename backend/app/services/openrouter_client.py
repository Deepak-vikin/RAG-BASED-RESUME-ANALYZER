import json
import logging
from typing import List, AsyncGenerator, Dict, Any, Optional
import httpx
from backend.app.config import settings
from backend.app.core.exceptions import OpenRouterAPIError

logger = logging.getLogger(__name__)


class OpenRouterClient:
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = settings.OPENROUTER_BASE_URL.rstrip("/")
        self.default_model = settings.OPENROUTER_MODEL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": settings.OPENROUTER_SITE_URL,
            "X-Title": settings.OPENROUTER_APP_NAME,
            "Content-Type": "application/json"
        }

    def _verify_api_key(self):
        if not self.api_key or self.api_key.strip() == "" or "your_openrouter_api_key" in self.api_key.lower():
            raise OpenRouterAPIError(
                "OPENROUTER_API_KEY is not configured or invalid. "
                "Please configure a valid OpenRouter API key in backend/.env",
                status_code=401
            )

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1500
    ) -> Dict[str, Any]:
        """
        Standard non-streaming chat completion call to OpenRouter API.
        """
        self._verify_api_key()
        target_model = model or self.default_model
        payload = {
            "model": target_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }

        url = f"{self.base_url}/chat/completions"
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, headers=self.headers, json=payload)
                
                if response.status_code != 200:
                    err_msg = f"HTTP {response.status_code}: {response.text}"
                    logger.error(f"OpenRouter API error: {err_msg}")
                    raise OpenRouterAPIError(err_msg, status_code=response.status_code)

                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return {
                    "content": content,
                    "model": target_model,
                    "usage": data.get("usage", {})
                }
        except httpx.TimeoutException:
            raise OpenRouterAPIError("Request to OpenRouter timed out.", status_code=504)
        except httpx.RequestError as e:
            raise OpenRouterAPIError(f"Network error contacting OpenRouter: {str(e)}", status_code=503)

    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1500
    ) -> AsyncGenerator[str, None]:
        """
        Streaming chat completion yielding text chunks via Server-Sent Events (SSE).
        """
        self._verify_api_key()
        target_model = model or self.default_model
        payload = {
            "model": target_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True
        }

        url = f"{self.base_url}/chat/completions"
        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                async with client.stream("POST", url, headers=self.headers, json=payload) as response:
                    if response.status_code != 200:
                        err_text = await response.aread()
                        raise OpenRouterAPIError(
                            f"HTTP {response.status_code}: {err_text.decode('utf-8', errors='ignore')}",
                            status_code=response.status_code
                        )

                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        if line.startswith("data: "):
                            data_str = line[6:].strip()
                            if data_str == "[DONE]":
                                break
                            try:
                                chunk_json = json.loads(data_str)
                                choices = chunk_json.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})
                                    delta_text = delta.get("content", "")
                                    if delta_text:
                                        yield delta_text
                            except json.JSONDecodeError:
                                continue
        except httpx.TimeoutException:
            raise OpenRouterAPIError("Streaming connection to OpenRouter timed out.", status_code=504)
        except httpx.RequestError as e:
            raise OpenRouterAPIError(f"Network error during OpenRouter stream: {str(e)}", status_code=503)


openrouter_client = OpenRouterClient()

