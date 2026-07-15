"""LLM client with OpenAI support and deterministic demo fallback."""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Thin wrapper around chat completions with JSON-mode helpers."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._client = None
        if self.settings.llm_enabled:
            try:
                from openai import OpenAI

                self._client = OpenAI(api_key=self.settings.openai_api_key)
            except Exception as exc:  # noqa: BLE001
                logger.warning("OpenAI client init failed: %s — using demo mode", exc)

    @property
    def available(self) -> bool:
        return self._client is not None

    def chat(
        self,
        system: str,
        user: str,
        *,
        temperature: float | None = None,
        json_mode: bool = False,
    ) -> str:
        if not self._client:
            raise RuntimeError("LLM not available — use demo heuristics")

        kwargs: dict[str, Any] = {
            "model": self.settings.openai_model,
            "temperature": temperature if temperature is not None else self.settings.llm_temperature,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = self._client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""

    def chat_json(
        self,
        system: str,
        user: str,
        *,
        temperature: float | None = None,
    ) -> dict[str, Any]:
        raw = self.chat(system, user, temperature=temperature, json_mode=True)
        return parse_json_response(raw)

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not self._client:
            # Deterministic pseudo-embeddings for demo / offline
            return [_hash_embed(t, dim=64) for t in texts]
        response = self._client.embeddings.create(
            model=self.settings.openai_embedding_model,
            input=texts,
        )
        return [item.embedding for item in response.data]


def parse_json_response(raw: str) -> dict[str, Any]:
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", raw)
        if match:
            return json.loads(match.group())
        raise


def _hash_embed(text: str, dim: int = 64) -> list[float]:
    """Simple bag-of-chars hash embedding for offline RAG demos."""
    vec = [0.0] * dim
    tokens = re.findall(r"[a-z0-9+#\.]+", text.lower())
    for tok in tokens:
        h = hash(tok) % dim
        vec[h] += 1.0
    norm = sum(v * v for v in vec) ** 0.5 or 1.0
    return [v / norm for v in vec]


_llm: LLMClient | None = None


def get_llm() -> LLMClient:
    global _llm
    if _llm is None:
        _llm = LLMClient()
    return _llm
