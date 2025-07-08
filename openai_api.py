"""
Модуль для работы с OpenAI API
Обрабатывает транскрипцию голосовых сообщений, анализ намерений и генерацию ответов
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, Any, Optional, List

from config import Config

logger = logging.getLogger(__name__ )

class OpenAIAPI:
    """Класс для работы с OpenAI API"""
    
    def __init__(self):
        self.config = Config()
        self.base_url = "https://api.openai.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.config.OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }

