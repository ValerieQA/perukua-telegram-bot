"""
Конфигурация для Telegram бота Перукуа
Управляет всеми настройками и переменными окружения
"""

import os
from typing import Optional
from dotenv import load_dotenv


class Config:
    """Класс конфигурации для бота"""
    
    def __init__(self):
        """Инициализация конфигурации с проверкой переменных окружения"""

        # Загружаем переменные из .env файла
        load_dotenv()

        # Telegram Bot Token
        self.TELEGRAM_TOKEN = self._get_env_var("TELEGRAM_BOT_TOKEN")
        
        # OpenAI API Key
        self.OPENAI_API_KEY = self._get_env_var("OPENAI_API_KEY")
        
        # Notion API Token
        self.NOTION_TOKEN = self._get_env_var("NOTION_TOKEN")
        
        # Notion Database ID
        self.NOTION_DATABASE_ID = self._get_env_var("NOTION_DATABASE_ID")
        
        # Дополнительные настройки
        self.DEBUG = os.getenv("DEBUG", "False").lower() == "true"
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        
        # Настройки OpenAI
        self.OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
        self.OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "1000"))
        self.OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
        
        # Настройки Telegram
        self.TELEGRAM_TIMEOUT = int(os.getenv("TELEGRAM_TIMEOUT", "30"))
        
        # Проверяем, что все обязательные переменные установлены
        self._validate_config()
    
    def _get_env_var(self, var_name: str) -> str:
        """Получить переменную окружения с проверкой"""
        value = os.getenv(var_name)
        if not value:
            raise ValueError(f"Переменная окружения {var_name} не установлена")
        return value
    
    def _validate_config(self) -> None:
        """Проверить корректность конфигурации"""
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
                f"Отсутствуют обязательные переменные окружения: {', '.join(missing_vars)}\n"
                f"Создайте файл .env или установите переменные окружения."
            )
    
    def get_notion_headers(self) -> dict:
        """Получить заголовки для Notion API"""
        return {
            "Authorization": f"Bearer {self.NOTION_TOKEN}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
    
    def get_openai_headers(self) -> dict:
        """Получить заголовки для OpenAI API"""
        return {
            "Authorization": f"Bearer {self.OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
    
    def __str__(self) -> str:
        """Строковое представление конфигурации (без секретных данных)"""
        return f"""
Конфигурация бота Перукуа:
- Debug режим: {self.DEBUG}
- Уровень логирования: {self.LOG_LEVEL}
- OpenAI модель: {self.OPENAI_MODEL}
- OpenAI max tokens: {self.OPENAI_MAX_TOKENS}
- OpenAI temperature: {self.OPENAI_TEMPERATURE}
- Telegram timeout: {self.TELEGRAM_TIMEOUT}
- Notion Database ID: {self.NOTION_DATABASE_ID[:8]}...
        """.strip()

