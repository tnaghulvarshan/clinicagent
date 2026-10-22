"""
Configuration loader and settings validation for Hospital AI Agent.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load .env file from project root
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")


class Settings:
    """Central configuration validated against environment variables."""

    def __init__(self) -> None:
        # Gemini credentials (sync GEMINI_API_KEY and GOOGLE_API_KEY)
        self.google_api_key: str = (
            os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or ""
        ).strip()

        # Synchronize back to environment so Google ADK and Google GenAI libraries find it
        if self.google_api_key:
            os.environ["GOOGLE_API_KEY"] = self.google_api_key
            os.environ["GEMINI_API_KEY"] = self.google_api_key

        self.gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()
        self.gemini_realtime_model: str = os.getenv(
            "GEMINI_REALTIME_MODEL", "gemini-2.5-flash-native-audio-preview-12-2025"
        ).strip()

        # LiveKit configuration
        self.livekit_url: str = os.getenv("LIVEKIT_URL", "").strip()
        self.livekit_api_key: str = os.getenv("LIVEKIT_API_KEY", "").strip()
        self.livekit_api_secret: str = os.getenv("LIVEKIT_API_SECRET", "").strip()

        # Database and configuration paths
        db_env = os.getenv("DATABASE_PATH", "hospital.db").strip()
        self.database_path: Path = (
            Path(db_env) if Path(db_env).is_absolute() else ROOT_DIR / db_env
        )

        config_env = os.getenv("CONFIG_PATH", "config/hospital_config.yaml").strip()
        self.config_path: Path = (
            Path(config_env)
            if Path(config_env).is_absolute()
            else ROOT_DIR / config_env
        )

        # Timezone & Hospital settings
        self.timezone: str = os.getenv("HOSPITAL_TIMEZONE", "Asia/Kolkata").strip()
        self.receptionist_phone: str = os.getenv(
            "RECEPTIONIST_PHONE", "+91-44-2499-1000"
        ).strip()
        self.emergency_hotline: str = os.getenv(
            "EMERGENCY_HOTLINE", "+91-44-2499-1066"
        ).strip()

        # Flags
        self.demo_mode: bool = (
            os.getenv("DEMO_MODE", "true").lower() in ("1", "true", "yes")
        )
        self.debug_conversation_logging: bool = (
            os.getenv("DEBUG_CONVERSATION_LOGGING", "false").lower()
            in ("1", "true", "yes")
        )

    def validate_gemini(self) -> None:
        """Validate that a Gemini API key is configured."""
        if not self.google_api_key:
            raise ValueError(
                "Missing GEMINI_API_KEY or GOOGLE_API_KEY in environment or .env file.\n"
                "Please configure your Google AI Studio key in .env to use the Gemini agents."
            )

    def validate_livekit(self) -> None:
        """Validate that LiveKit credentials are configured for real-time voice."""
        missing = []
        if not self.livekit_url:
            missing.append("LIVEKIT_URL")
        if not self.livekit_api_key:
            missing.append("LIVEKIT_API_KEY")
        if not self.livekit_api_secret:
            missing.append("LIVEKIT_API_SECRET")

        if missing:
            raise ValueError(
                f"Missing required LiveKit setting(s): {', '.join(missing)}.\n"
                "To run the real-time voice session, configure these in .env with your LiveKit project details."
            )

    def __repr__(self) -> str:
        # Safeguard: Never print API keys
        return (
            f"Settings(gemini_model='{self.gemini_model}', "
            f"has_gemini_key={bool(self.google_api_key)}, "
            f"has_livekit={bool(self.livekit_url and self.livekit_api_key)}, "
            f"timezone='{self.timezone}', "
            f"database='{self.database_path.name}', "
            f"demo_mode={self.demo_mode})"
        )


settings = Settings()
