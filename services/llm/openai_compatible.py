"""One adapter for the whole OpenAI-compatible ecosystem.

Works against OpenAI, DeepSeek, GLM (Z.AI), Kimi (Moonshot), Grok (xAI) and
Qwen (DashScope) — only ``base_url``/``model``/``api_key`` differ, all supplied
by the model registry. ``httpx`` is imported lazily so the package still
imports (and the offline echo path still runs) when it is not installed.
"""
from __future__ import annotations

import os

from services.llm.base import Completion, Message


class OpenAICompatibleProvider:
    name = "openai_compatible"

    def __init__(self, model: str, base_url: str, env_key: str | None = None) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = os.getenv(env_key) if env_key else None
        if not self.api_key:
            raise RuntimeError(
                f"Missing API key (env: {env_key}). Set it, or use the offline 'echo' provider."
            )

    def complete(self, messages: list[Message], *, temperature: float = 0.2) -> Completion:
        import httpx  # lazy: only needed when actually calling a remote model

        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
        }
        resp = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json=payload,
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        text = data["choices"][0]["message"]["content"]
        return Completion(text=text, model=self.model, raw=data)
