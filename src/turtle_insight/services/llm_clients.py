"""Concrete LLM clients for the inference gate (ADR-0003).

Both implement the :class:`~turtle_insight.services.inference.LLMClient`
protocol (``complete(*, model, system, messages) -> Completion``) and are
*injected* into :class:`Inference` — the gate itself never imports an SDK.

- ``OllamaClient``: local fast tier over Ollama's HTTP API (httpx).
- ``AnthropicClient``: deep tier over the Anthropic SDK (injected client; the
  SDK is imported lazily only when built from settings).

``build_client``/``build_inference`` pick the client from settings: a local
Ollama endpoint if configured, otherwise Anthropic if an API key is present.
"""

from __future__ import annotations

from typing import Any

import httpx

from ..config.settings import Settings
from .inference import Completion, Inference, LLMClient, Message


class OllamaClient:
    """Fast-tier client backed by a local Ollama server (``/api/chat``)."""

    def __init__(
        self, base_url: str, *, client: httpx.Client | None = None, timeout: float = 60.0
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = client or httpx.Client(timeout=timeout)

    def complete(self, *, model: str, system: str | None, messages: list[Message]) -> Completion:
        chat: list[Message] = []
        if system:
            chat.append({"role": "system", "content": system})
        chat.extend(messages)
        response = self._client.post(
            f"{self._base_url}/api/chat",
            json={"model": model, "messages": chat, "stream": False},
        )
        response.raise_for_status()
        data = response.json()
        return Completion(
            text=str(data["message"]["content"]),
            input_tokens=int(data.get("prompt_eval_count", 0)),
            output_tokens=int(data.get("eval_count", 0)),
        )


class AnthropicClient:
    """Deep-tier client over an injected Anthropic SDK client."""

    def __init__(self, client: Any, *, max_tokens: int = 1024) -> None:
        self._client = client
        self._max_tokens = max_tokens

    def complete(self, *, model: str, system: str | None, messages: list[Message]) -> Completion:
        kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": self._max_tokens,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system
        response = self._client.messages.create(**kwargs)
        text = "".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        )
        return Completion(
            text=text,
            input_tokens=int(response.usage.input_tokens),
            output_tokens=int(response.usage.output_tokens),
        )

    @classmethod
    def from_settings(cls, settings: Settings) -> AnthropicClient:
        import anthropic  # imported lazily so the SDK is optional

        return cls(anthropic.Anthropic(api_key=settings.anthropic_api_key))


def build_client(settings: Settings) -> LLMClient | None:
    """Pick an LLM client from settings (local Ollama preferred, else Anthropic)."""
    if settings.ti_ollama_url:
        return OllamaClient(settings.ti_ollama_url)
    if settings.anthropic_api_key:
        return AnthropicClient.from_settings(settings)
    return None


def build_inference(settings: Settings) -> Inference:
    """Build a fully-wired inference gate from settings."""
    return Inference(settings, build_client(settings))
