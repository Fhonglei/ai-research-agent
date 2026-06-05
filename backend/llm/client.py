from __future__ import annotations

from typing import Any, Optional

from openai import OpenAI

from config import config


class LLMClient:
    def __init__(
        self,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.provider = (provider or config.LLM_PROVIDER).lower()
        self.model = model or config.active_model

        if self.provider == "anthropic":
            try:
                import anthropic
            except ImportError as exc:
                raise RuntimeError("Install the anthropic package to use LLM_PROVIDER=anthropic") from exc
            self.client = anthropic.Anthropic(api_key=api_key or config.ANTHROPIC_API_KEY)
            return

        self.client = OpenAI(
            api_key=api_key or config.DEEPSEEK_API_KEY,
            base_url=config.DEEPSEEK_BASE_URL,
        )

    def complete(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int,
        temperature: Optional[float] = None,
        json_schema: Optional[dict[str, Any]] = None,
    ) -> str:
        if self.provider == "anthropic":
            return self._complete_anthropic(
                system=system,
                user=user,
                max_tokens=max_tokens,
                json_schema=json_schema,
            )

        return self._complete_openai_compatible(
            system=system,
            user=user,
            max_tokens=max_tokens,
            temperature=temperature,
            json_schema=json_schema,
        )

    def _complete_openai_compatible(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int,
        temperature: Optional[float],
        json_schema: Optional[dict[str, Any]],
    ) -> str:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if temperature is not None:
            kwargs["temperature"] = temperature
        if json_schema is not None:
            kwargs["response_format"] = {"type": "json_object"}

        response = self.client.chat.completions.create(**kwargs)
        return (response.choices[0].message.content or "").strip()

    def _complete_anthropic(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int,
        json_schema: Optional[dict[str, Any]],
    ) -> str:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user}],
            "thinking": {"type": "adaptive"},
            "output_config": {"effort": "high"},
        }
        if json_schema is not None:
            kwargs["output_config"]["format"] = {
                "type": "json_schema",
                "schema": json_schema,
            }

        response = self.client.messages.create(**kwargs)
        return "".join(block.text for block in response.content if block.type == "text").strip()
