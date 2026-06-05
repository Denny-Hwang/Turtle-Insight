"""P3 unit tests: the tiered inference gate (mocked LLM client)."""

from __future__ import annotations

import pytest

from turtle_insight.config.settings import Settings
from turtle_insight.services.inference import (
    Completion,
    Inference,
    InferenceError,
    Message,
)


class FakeClient:
    def __init__(self) -> None:
        self.models: list[str] = []

    def complete(self, *, model: str, system: str | None, messages: list[Message]) -> Completion:
        self.models.append(model)
        return Completion(text=f"echo:{model}", input_tokens=10, output_tokens=5)


def _settings(**overrides: str) -> Settings:
    return Settings(_env_file=None, **overrides)


_MSG: list[Message] = [{"role": "user", "content": "hi"}]


def test_deep_uses_configured_model() -> None:
    inf = Inference(_settings(ti_deep_model="deep-x"), FakeClient())
    result = inf.deep(_MSG, prompt_version="v1")
    assert result.model == "deep-x"
    assert result.tier == "deep"
    assert (result.input_tokens, result.output_tokens) == (10, 5)


def test_fast_falls_back_to_deep_when_unset() -> None:
    inf = Inference(_settings(ti_deep_model="deep-x"), FakeClient())
    result = inf.fast(_MSG, prompt_version="v1")
    assert result.tier == "deep"
    assert result.model == "deep-x"


def test_fast_uses_fast_model_when_set() -> None:
    inf = Inference(_settings(ti_deep_model="deep-x", ti_fast_model="fast-y"), FakeClient())
    result = inf.fast(_MSG, prompt_version="v1")
    assert result.tier == "fast"
    assert result.model == "fast-y"


def test_deep_without_model_raises() -> None:
    inf = Inference(_settings(), FakeClient())
    with pytest.raises(InferenceError):
        inf.deep(_MSG, prompt_version="v1")


def test_run_without_client_raises() -> None:
    inf = Inference(_settings(ti_deep_model="deep-x"))
    with pytest.raises(InferenceError):
        inf.deep(_MSG, prompt_version="v1")
