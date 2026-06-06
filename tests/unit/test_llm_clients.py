"""P11 unit tests: injectable LLM clients (Ollama via httpx mock; Anthropic fake)."""

from __future__ import annotations

import json
from typing import Any

import httpx

from turtle_insight.config.settings import Settings
from turtle_insight.services.inference import Message
from turtle_insight.services.llm_clients import (
    AnthropicClient,
    OllamaClient,
    build_client,
    build_inference,
)

_MSG: list[Message] = [{"role": "user", "content": "q"}]


def _ollama(handler: httpx.MockTransport) -> OllamaClient:
    return OllamaClient("http://localhost:11434", client=httpx.Client(transport=handler))


def test_ollama_client_builds_request_and_parses_response() -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(json.loads(request.content))
        assert request.url.path == "/api/chat"
        return httpx.Response(
            200, json={"message": {"content": "hi"}, "prompt_eval_count": 5, "eval_count": 3}
        )

    client = _ollama(httpx.MockTransport(handler))
    completion = client.complete(model="llama3", system="sys", messages=_MSG)

    assert completion.text == "hi"
    assert (completion.input_tokens, completion.output_tokens) == (5, 3)
    assert seen["model"] == "llama3"
    assert seen["messages"][0] == {"role": "system", "content": "sys"}
    assert seen["stream"] is False


def test_anthropic_client_maps_sdk_response() -> None:
    class _Block:
        type = "text"
        text = "ok"

    class _Usage:
        input_tokens = 7
        output_tokens = 2

    class _Response:
        content = [_Block()]
        usage = _Usage()

    class _Messages:
        def __init__(self) -> None:
            self.kwargs: dict[str, Any] = {}

        def create(self, **kwargs: Any) -> _Response:
            self.kwargs = kwargs
            return _Response()

    class _SDK:
        def __init__(self) -> None:
            self.messages = _Messages()

    sdk = _SDK()
    completion = AnthropicClient(sdk).complete(model="claude-x", system="s", messages=_MSG)

    assert completion.text == "ok"
    assert (completion.input_tokens, completion.output_tokens) == (7, 2)
    assert sdk.messages.kwargs["model"] == "claude-x"
    assert sdk.messages.kwargs["system"] == "s"


def test_build_client_prefers_ollama_then_anthropic_then_none() -> None:
    assert isinstance(
        build_client(Settings(_env_file=None, ti_ollama_url="http://x")), OllamaClient
    )
    assert build_client(Settings(_env_file=None)) is None


def test_build_inference_wires_ollama_fast_tier() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"message": {"content": "pong"}})

    settings = Settings(_env_file=None, ti_fast_model="llama3", ti_ollama_url="http://localhost")
    inference = build_inference(settings)
    # Swap in a mocked transport so no live call is made.
    inference._client = _ollama(httpx.MockTransport(handler))  # type: ignore[attr-defined]
    result = inference.fast(_MSG, prompt_version="v1")
    assert result.tier == "fast"
    assert result.model == "llama3"
    assert result.text == "pong"
