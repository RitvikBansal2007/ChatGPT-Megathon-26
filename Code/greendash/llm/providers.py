"""Provider adapters for the LLM gateway.

An adapter turns the gateway's LLMProvider interface into one vendor SDK call. It
holds no keys and makes no call at import or construction time: the client is
supplied by the caller as a zero-argument factory, so tests can pass a fake and the
real key handling stays wherever the project already keeps it.

Wiring the existing Gemini client (done by whoever owns that client, not here):

    provider = GeminiProvider(get_client, model_id="<model id from config>")
    gateway = LLMGateway(provider)
    result = gateway.explain(evidence_pack)

An adapter must not log prompts or replies, and any exception it raises is treated
by the gateway as a provider failure (retry once, then deterministic fallback).
"""
from typing import Any, Callable, Optional


class ProviderError(Exception):
    """The provider answered, but not with usable text."""


class GeminiProvider:
    """LLMProvider backed by a google-genai style client.

    The client must expose client.models.generate_content(model=, contents=, config=).
    Settings are passed per call so config the project already declares (temperature
    0, token cap, timeout) is applied rather than ignored.
    """

    def __init__(self, client_factory: Callable[[], Any], *, model_id: str,
                 temperature: float = 0.0,
                 on_response: Optional[Callable[[Any, int], None]] = None):
        """on_response(response, prompt_chars) is called with every raw reply, e.g. to
        meter cost. If it raises, the exception reaches the gateway as a provider
        failure; raise NonRetryableProviderError (gateway.py) to stop retries."""
        if not model_id:
            raise ValueError("model_id is required")
        self._client_factory = client_factory
        self._model_id = model_id
        self._temperature = temperature
        self._on_response = on_response

    def generate(self, *, system: str, user: str, max_tokens: int, timeout_s: float) -> str:
        client = self._client_factory()
        response = client.models.generate_content(
            model=self._model_id,
            contents=user,
            config={
                "system_instruction": system,
                "temperature": self._temperature,
                "max_output_tokens": max_tokens,
                "response_mime_type": "application/json",
                "http_options": {"timeout": int(timeout_s * 1000)},  # milliseconds
            },
        )
        if self._on_response is not None:
            self._on_response(response, len(system) + len(user))
        text = getattr(response, "text", None)
        if not isinstance(text, str) or not text:
            raise ProviderError("empty or non-text reply")
        return text
