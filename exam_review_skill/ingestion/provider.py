from __future__ import annotations

import os
from typing import Callable

from .types import ProviderUnderstanding, RenderedPage


class ProviderUnavailable(RuntimeError):
    """Raised when a provider is not configured or fails. Never fabricates content."""


class MultimodalProvider:
    """Capability-described multimodal understanding provider.

    Capabilities are descriptive and allow the pipeline to route without assuming a
    single vendor:
        supports_images           - accepts rendered page images
        supports_pdf              - accepts PDF documents directly
        supports_structured_output- returns structured blocks/formulas/tables
        supports_long_context     - handles long documents
    """

    name = "base"
    capabilities: dict[str, bool] = {
        "supports_images": False,
        "supports_pdf": False,
        "supports_structured_output": False,
        "supports_long_context": False,
    }

    def understand_page(
        self, page: RenderedPage, *, native_text: str = "", context: dict | None = None
    ) -> ProviderUnderstanding:
        raise NotImplementedError

    def is_available(self) -> bool:
        return True


class SyntheticProvider(MultimodalProvider):
    """Deterministic, clearly-flagged provider for tests / fixtures / demo / CI.

    Output is marked synthetic=True and must never be written to real state.
    It never invents knowledge: it only restructures the native text that was given.
    """

    name = "synthetic"
    capabilities = {
        "supports_images": True,
        "supports_pdf": True,
        "supports_structured_output": True,
        "supports_long_context": True,
    }

    def __init__(self, *, confidence: float = 0.5):
        self._confidence = min(confidence, 0.5)  # capped: synthetic never looks verified

    def understand_page(
        self, page: RenderedPage, *, native_text: str = "", context: dict | None = None
    ) -> ProviderUnderstanding:
        text = native_text or ""
        return ProviderUnderstanding(
            page_or_slide=page.page_or_slide,
            text_blocks=[{"role": "text", "text": text}] if text.strip() else [],
            formulas=[],
            tables=[],
            figures=[],
            handwriting=[],
            exam=None,
            source_language=context.get("language_hint") if context else None,
            confidence=self._confidence,
            synthetic=True,
            method="multimodal",
            warning="synthetic provider (tests/fixtures/demo/CI only)",
        )


class _ConfiguredAPIMultimodalProvider(MultimodalProvider):
    """Base for real API providers. Fails closed until configured via env vars.

    Subclasses define `_endpoint`, `_api_key_env`, and request/response mapping.
    No vendor is hard-coded in the pipeline: selection happens by name in the registry.
    """

    name = "api-base"
    _api_key_env = ""
    _endpoint = ""
    capabilities = {
        "supports_images": True,
        "supports_pdf": True,
        "supports_structured_output": True,
        "supports_long_context": True,
    }

    def _api_key(self) -> str:
        key = os.environ.get(self._api_key_env, "").strip()
        if not key:
            raise ProviderUnavailable(
                f"{self.name}: {self._api_key_env} is not set (fail closed)"
            )
        return key

    def is_available(self) -> bool:
        return bool(os.environ.get(self._api_key_env, "").strip())

    def understand_page(
        self, page: RenderedPage, *, native_text: str = "", context: dict | None = None
    ) -> ProviderUnderstanding:
        key = self._api_key()  # raises when unset
        payload = self._build_payload(page, native_text=native_text, context=context)
        response = self._call(payload, api_key=key)
        return self._parse_response(response, page_or_slide=page.page_or_slide)

    def _build_payload(self, page: RenderedPage, *, native_text: str, context: dict | None) -> dict:
        raise NotImplementedError

    def _call(self, payload: dict, *, api_key: str) -> dict:
        raise NotImplementedError

    def _parse_response(self, response: dict, *, page_or_slide: str) -> ProviderUnderstanding:
        raise NotImplementedError


class OpenAIVisionProvider(_ConfiguredAPIMultimodalProvider):
    name = "openai"
    _api_key_env = "OPENAI_API_KEY"
    _endpoint = "https://api.openai.com/v1/responses"

    def _build_payload(self, page, *, native_text, context) -> dict:
        return {
            "model": os.environ.get("EXAM_REVIEW_OPENAI_VISION_MODEL", "gpt-4o"),
            "input": [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_image", "image_url": f"data:image/png;base64,{_b64(page.image_png)}"},
                        {"type": "input_text", "text": _vision_prompt(native_text=native_text)},
                    ],
                }
            ],
        }

    def _call(self, payload, *, api_key) -> dict:
        import json
        import urllib.request

        request = urllib.request.Request(
            self._endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))

    def _parse_response(self, response, *, page_or_slide) -> ProviderUnderstanding:
        return _parse_structured_response(response, page_or_slide=page_or_slide, method="multimodal")


class DeepSeekVisionProvider(_ConfiguredAPIMultimodalProvider):
    name = "deepseek"
    _api_key_env = "DEEPSEEK_API_KEY"
    _endpoint = "https://api.deepseek.com/chat/completions"

    def _build_payload(self, page, *, native_text, context) -> dict:
        return {
            "model": os.environ.get("EXAM_REVIEW_DEEPSEEK_VISION_MODEL", "deepseek-chat"),
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{_b64(page.image_png)}"}},
                        {"type": "text", "text": _vision_prompt(native_text=native_text)},
                    ],
                }
            ],
        }

    def _call(self, payload, *, api_key) -> dict:
        import json
        import urllib.request

        request = urllib.request.Request(
            self._endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))

    def _parse_response(self, response, *, page_or_slide) -> ProviderUnderstanding:
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        return _parse_structured_response({"output_text": content}, page_or_slide=page_or_slide, method="multimodal")


def _b64(data: bytes) -> str:
    import base64

    return base64.b64encode(data).decode("ascii")


def _vision_prompt(*, native_text: str) -> str:
    return (
        "Return strict JSON for this page: "
        '{"text_blocks":[{"role":"text","text":"..."}],'
        '"formulas":[{"text":"...","signals":[]}],'
        '"tables":[{"text":"...","rows":3,"cols":2}],'
        '"figures":[{"kind":"diagram","caption":""}],'
        '"handwriting":[{"text":""}],'
        '"source_language":"zh-CN|en-US|mixed",'
        '"confidence":0.0} '
        "Do not invent content that is not visible. "
        f"Native text layer (may be empty):\n{native_text[:2000]}"
    )


def _parse_structured_response(response: dict, *, page_or_slide: str, method: str) -> ProviderUnderstanding:
    import json
    import re

    raw = response.get("output_text") or response.get("output") or ""
    if isinstance(raw, list):
        raw = "\n".join(x.get("text", "") for x in raw if isinstance(x, dict))
    text = str(raw)
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        raise ProviderUnavailable("provider returned no structured JSON")
    data = json.loads(match.group(0))
    confidence = float(data.get("confidence", 0.5))
    return ProviderUnderstanding(
        page_or_slide=page_or_slide,
        text_blocks=data.get("text_blocks", []),
        formulas=[],
        tables=data.get("tables", []),
        figures=data.get("figures", []),
        handwriting=data.get("handwriting", []),
        exam=None,
        source_language=data.get("source_language"),
        confidence=confidence,
        synthetic=False,
        method=method,
    )


_REGISTRY: dict[str, Callable[[], MultimodalProvider]] = {
    "synthetic": SyntheticProvider,
    "openai": OpenAIVisionProvider,
    "deepseek": DeepSeekVisionProvider,
}


def register_provider(name: str, factory: Callable[[], MultimodalProvider]) -> None:
    """Extend the provider registry at runtime (no single-vendor hard-coding)."""
    _REGISTRY[name] = factory


def available_providers() -> list[str]:
    return sorted(_REGISTRY)


def get_provider(name: str) -> MultimodalProvider:
    if not name:
        raise ProviderUnavailable("no multimodal provider configured (fail closed)")
    if name not in _REGISTRY:
        raise ProviderUnavailable(f"unknown provider {name!r}; available: {available_providers()}")
    return _REGISTRY[name]()
