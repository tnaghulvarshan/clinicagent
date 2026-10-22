"""
Dual-mode Gemini model adapter for Google ADK agents.
Routes text chat to gemini-3.5-flash and real-time live audio to gemini-2.5-flash-native-audio.
"""

from __future__ import annotations

import contextlib
from typing import AsyncIterator
from google.adk.models.google_llm import Gemini, BaseLlmConnection, LlmResponse
from google.adk.models.llm_request import LlmRequest
from config.settings import settings


class HospitalGeminiModel(Gemini):
    """
    Subclasses ADK Gemini to seamlessly support both standard text chat
    (via generateContent) and ADK Web / Live bidirectional audio (via bidiGenerateContent).
    """

    def __init__(self, **kwargs) -> None:
        model_name = kwargs.pop("model", settings.gemini_model)
        super().__init__(model=model_name, **kwargs)

    @contextlib.asynccontextmanager
    async def connect(
        self, llm_request: LlmRequest
    ) -> AsyncIterator[BaseLlmConnection]:
        """
        Dynamically route live WebSocket connections to the Gemini model
        that supports bidiGenerateContent bidirectional audio.
        """
        llm_request.model = settings.gemini_realtime_model
        # Configure instant spoken response with warm voice
        if llm_request.live_connect_config:
            if not llm_request.live_connect_config.response_modalities:
                llm_request.live_connect_config.response_modalities = ["AUDIO"]
            from google.genai import types
            llm_request.live_connect_config.thinking_config = types.ThinkingConfig(
                thinking_budget=0,
            )
            llm_request.live_connect_config.speech_config = types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Aoede")
                )
            )
        async with super().connect(llm_request) as conn:
            yield conn

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncIterator[LlmResponse]:
        """
        Wrapper around generate_content_async with automatic retry on 503 capacity spikes
        and seamless fallback to gemini-3.5-flash-lite.
        """
        import asyncio
        max_retries = 3
        delay = 1.5
        for attempt in range(max_retries):
            try:
                async for response in super().generate_content_async(
                    llm_request, stream=stream
                ):
                    yield response
                return
            except Exception as e:
                err_str = str(e)
                is_503 = (
                    "503" in err_str
                    or "UNAVAILABLE" in err_str
                    or "high demand" in err_str
                    or "ResourceExhausted" in err_str
                )
                if is_503 and attempt < max_retries - 1:
                    print(
                        f"[HospitalGeminiModel] 503 capacity spike on {llm_request.model}. "
                        f"Retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries})..."
                    )
                    await asyncio.sleep(delay)
                    delay *= 1.5
                    continue
                # On high demand, fall back to gemini-3.5-flash-lite
                if is_503 and llm_request.model != "gemini-3.5-flash-lite":
                    try:
                        print(
                            f"[HospitalGeminiModel] Falling back to gemini-3.5-flash-lite due to high demand on {llm_request.model}..."
                        )
                        llm_request.model = "gemini-3.5-flash-lite"
                        async for response in super().generate_content_async(
                            llm_request, stream=stream
                        ):
                            yield response
                        return
                    except Exception:
                        pass
                raise e


# Reusable dual-mode LLM instance
hospital_llm = HospitalGeminiModel()
