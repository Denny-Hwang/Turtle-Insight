"""LLM inference gate — the single entry point for all model calls (ADR-0003).

Deep tier = Claude (model id from ``TI_DEEP_MODEL``); fast tier = optional
local model (``TI_FAST_MODEL``), falling back to deep when unset. Model
identifiers come from settings only — never hardcoded (engineering.md). The
concrete LLM client is injected (a real Claude client in production, a fake in
tests), so this module performs no network IO itself. Every call logs
``prompt_version`` and token counts.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

from ..config.settings import Settings

logger = logging.getLogger("turtle_insight.inference")

Message = dict[str, str]


class InferenceError(RuntimeError):
    """Raised when an inference call cannot be made (e.g. model/client missing)."""


@dataclass(frozen=True)
class Completion:
    text: str
    input_tokens: int
    output_tokens: int


class LLMClient(Protocol):
    def complete(
        self, *, model: str, system: str | None, messages: list[Message]
    ) -> Completion: ...


@dataclass(frozen=True)
class InferenceResult:
    text: str
    model: str
    tier: str
    prompt_version: str
    input_tokens: int
    output_tokens: int


class Inference:
    """Tiered inference gate. The LLM client is injected (no live IO here)."""

    def __init__(self, settings: Settings, client: LLMClient | None = None) -> None:
        self._settings = settings
        self._client = client

    def deep(
        self, messages: list[Message], *, prompt_version: str, system: str | None = None
    ) -> InferenceResult:
        model = self._settings.ti_deep_model
        if not model:
            raise InferenceError("TI_DEEP_MODEL is not configured")
        return self._run("deep", model, messages, system, prompt_version)

    def fast(
        self, messages: list[Message], *, prompt_version: str, system: str | None = None
    ) -> InferenceResult:
        fast_model = self._settings.ti_fast_model
        if fast_model:
            return self._run("fast", fast_model, messages, system, prompt_version)
        # No fast model configured: fall back to the deep tier.
        return self.deep(messages, prompt_version=prompt_version, system=system)

    def _run(
        self,
        tier: str,
        model: str,
        messages: list[Message],
        system: str | None,
        prompt_version: str,
    ) -> InferenceResult:
        if self._client is None:
            raise InferenceError("no LLM client configured; inject one via Inference(client=...)")
        completion = self._client.complete(model=model, system=system, messages=messages)
        logger.info(
            "inference tier=%s model=%s prompt_version=%s input_tokens=%d output_tokens=%d",
            tier,
            model,
            prompt_version,
            completion.input_tokens,
            completion.output_tokens,
        )
        return InferenceResult(
            text=completion.text,
            model=model,
            tier=tier,
            prompt_version=prompt_version,
            input_tokens=completion.input_tokens,
            output_tokens=completion.output_tokens,
        )
