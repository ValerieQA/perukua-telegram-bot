"""
Configuration for Peruquois Telegram Bot
Handles all settings and environment variables
"""

import os
from typing import Optional


class Config:
    """Configuration class for the bot"""

    def __init__(self):
        """Initialize configuration and check environment variables"""

        # Telegram Bot Token
        self.TELEGRAM_TOKEN = self._get_env_var("TELEGRAM_BOT_TOKEN")

        # OpenAI API Key
        self.OPENAI_API_KEY = self._get_env_var("OPENAI_API_KEY")

        # Notion API Token
        self.NOTION_TOKEN = self._get_env_var("NOTION_TOKEN")

        # Notion Database ID
        self.NOTION_DATABASE_ID = self._get_env_var("NOTION_DATABASE_ID")

        # Additional settings
        self.DEBUG = os.getenv("DEBUG", "False").lower() == "true"
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

        # OpenAI settings
        self.OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
        self.OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "1000"))
        self.OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))

        # Telegram settings
        self.TELEGRAM_TIMEOUT = int(os.getenv("TELEGRAM_TIMEOUT", "30"))

        # Validate required environment variables
        self._validate_config()

    def _get_env_var(self, var_name: str) -> str:
        """Get environment variable with validation"""
        value = os.getenv(var_name)
        if not value:
            raise ValueError(f"Environment variable {var_name} is not set")
        return value

    def _validate_config(self) -> None:
        """Check configuration validity"""
        required_vars = [
            "TELEGRAM_TOKEN",
            "OPENAI_API_KEY",
            "NOTION_TOKEN",
            "NOTION_DATABASE_ID"
        ]

        missing_vars = []
        for var in required_vars:
            if not hasattr(self, var) or not getattr(self, var):
                missing_vars.append(var)

        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}\n"
                f"Please create a .env file or set the environment variables manually."
            )

    def get_notion_headers(self) -> dict:
        """Get headers for Notion API"""
        return {
            "Authorization": f"Bearer {self.NOTION_TOKEN}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }

    def get_openai_headers(self) -> dict:
        """Get headers for OpenAI API"""
        return {
            "Authorization": f"Bearer {self.OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }

    def __str__(self) -> str:
        """String representation of configuration (without secrets)"""
        return f"""
Peruquois Bot Configuration:
- Debug mode: {self.DEBUG}
- Logging level: {self.LOG_LEVEL}
- OpenAI model: {self.OPENAI_MODEL}
- OpenAI max tokens: {self.OPENAI_MAX_TOKENS}
- OpenAI temperature: {self.OPENAI_TEMPERATURE}
- Telegram timeout: {self.TELEGRAM_TIMEOUT}
- Notion Database ID: {self.NOTION_DATABASE_ID[:8]}...
        """.strip()
