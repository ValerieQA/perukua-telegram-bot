#!/usr/bin/env python3
"""
Telegram Bot для Перукуа - Персональный ассистент для управления проектами
Интегрируется с Notion API для управления проектами и OpenAI API для обработки естественного языка
"""

import os
import logging
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any

from telegram import Update, Message
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes
)

from config import Config
from notion_api import NotionAPI
from openai_api import OpenAIAPI

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class PerukuaBot:
    """Основной класс Telegram бота для Перукуа"""
    
    def __init__(self):
        self.config = Config()
        self.notion = NotionAPI()
        self.openai = OpenAIAPI()
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /start"""
        welcome_message = """
🌟 Привет, Перукуа! Я твой персональный ассистент для управления проектами.

Я помогу тебе:
• Сохранять новые идеи и проекты
• Отслеживать статус текущих проектов
• Организовывать твои творческие замыслы
• Напоминать о важных задачах

Просто пиши мне как обычно - голосом или текстом. Я пойму, что ты хочешь сделать, и организую всё за тебя.

Доступные команды:
/start - показать это сообщение
/projects - показать все проекты
/active - показать активные проекты
/help - помощь

Готова начать? Расскажи мне о своих идеях! ✨
        """
        await update.message.reply_text(welcome_message)
        
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /help"""
        help_message = """
🔮 Как я работаю:

📝 **Создание проектов:**
Просто расскажи мне о своей идее:
• "У меня есть идея для новой песни о материнстве"
• "Хочу создать курс по женской энергии"
• "Планирую ретрит в горах"

📊 **Обновление статуса:**
• "Начала работать над песней о луне"
• "Приостанавливаю работу над курсом"
• "Завершила запись альбома"

📋 **Просмотр проектов:**
• "Что у меня в работе?"
• "Покажи все мои песни"
• "Какие курсы я планирую?"

🎯 **Типы проектов:**
• Песни (Song)
• Книги (Book)
• Курсы (Course)
• Ретриты (Retreat)
• Мастер-классы (Workshop)
• Альбомы (Album)

💫 Пиши естественно - я пойму твои намерения и организую всё сама!
        """
        await update.message.reply_text(help_message)
        
    async def projects_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /projects - показать все проекты"""
        try:
            projects = await self.notion.get_all_projects()
            
            if not projects:
                await update.message.reply_text("У тебя пока нет сохранённых проектов. Расскажи мне о своих идеях! ✨")
                return
                
            message = "🌟 **Все твои проекты:**\n\n"
            
            # Группируем проекты по типам
            projects_by_type = {}
            for project in projects:
                project_type = project.get('type', 'Другое')
                if project_type not in projects_by_type:
                    projects_by_type[project_type] = []
                projects_by_type[project_type].append(project)
            
            # Формируем сообщение
            for project_type, type_projects in projects_by_type.items():
                message += f"**{project_type}:**\n"
                for project in type_projects:
                    name = project.get('name', 'Без названия')
                    status = project.get('status', 'Неизвестно')
                    status_emoji = self._get_status_emoji(status)
                    message += f"  {status_emoji} {name} - {status}\n"
                message += "\n"
                
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Ошибка при получении проектов: {e}")
            await update.message.reply_text("Произошла ошибка при получении списка проектов. Попробуй позже.")
            
    async def active_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /active - показать активные проекты"""
        try:
            projects = await self.notion.get_projects_by_status("In Progress")
            
            if not projects:
                await update.message.reply_text("У тебя нет активных проектов. Время начать что-то новое! 🚀")
                return
                
            message = "🔥 **Твои активные проекты:**\n\n"
            
            for project in projects:
                name = project.get('name', 'Без названия')
                project_type = project.get('type', 'Проект')
                date = project.get('date', '')
                tags = project.get('tags', [])
                
                message += f"🎯 **{name}** ({project_type})\n"
                if date:
                    message += f"   📅 {date}\n"
                if tags:
                    message += f"   🏷️ {', '.join(tags)}\n"
                message += "\n"
                
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Ошибка при получении активных проектов: {e}")
            await update.message.reply_text("Произошла ошибка при получении активных проектов. Попробуй позже.")
    
    async def handle_voice_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик голосовых сообщений"""
        try:
            # Отправляем сообщение о том, что обрабатываем голосовое сообщение
            processing_msg = await update.message.reply_text("🎤 Слушаю твоё сообщение...")
            
            # Получаем файл голосового сообщения
            voice_file = await update.message.voice.get_file()
            
            # Скачиваем файл
            voice_path = f"/tmp/voice_{update.message.message_id}.ogg"
            await voice_file.download_to_drive(voice_path)
            
            # Транскрибируем голосовое сообщение
            transcription = await self.openai.transcribe_audio(voice_path)
            
            # Удаляем временный файл
            os.remove(voice_path)
            
            if not transcription:
                await processing_msg.edit_text("Не удалось распознать голосовое сообщение. Попробуй ещё раз.")
                return
            
            # Обрабатываем транскрибированный текст
            await processing_msg.edit_text(f"📝 Я услышала: \"{transcription}\"\n\nОбрабатываю...")
            await self._process_text_message(update, context, transcription, processing_msg)
            
        except Exception as e:
            logger.error(f"Ошибка при обработке голосового сообщения: {e}")
            await update.message.reply_text("Произошла ошибка при обработке голосового сообщения. Попробуй написать текстом.")
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик текстовых сообщений"""
        try:
            # Отправляем сообщение о том, что обрабатываем запрос
            processing_msg = await update.message.reply_text("💭 Обрабатываю твой запрос...")
            
            text = update.message.text
            await self._process_text_message(update, context, text, processing_msg)
            
        except Exception as e:
            logger.error(f"Ошибка при обработке текстового сообщения: {e}")
            await update.message.reply_text("Произошла ошибка при обработке сообщения. Попробуй ещё раз.")
    
    async def _process_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                  text: str, processing_msg: Message) -> None:
        """Внутренний метод для обработки текстовых сообщений"""
        try:
            # Анализируем намерение пользователя с помощью OpenAI
            intent_analysis = await self.openai.analyze_intent(text)
            
            if not intent_analysis:
                await processing_msg.edit_text("Не удалось понять твой запрос. Попробуй переформулировать.")
                return
            
            action = intent_analysis.get('action')
            
            if action == 'create_project':
                await self._handle_create_project(intent_analysis, processing_msg)
            elif action == 'update_project':
                await self._handle_update_project(intent_analysis, processing_msg)
            elif action == 'query_projects':
                await self._handle_query_projects(intent_analysis, processing_msg)
            elif action == 'general_chat':
                await self._handle_general_chat(intent_analysis, processing_msg)
            else:
                await processing_msg.edit_text("Я поняла твоё сообщение, но не знаю, как на него ответить. Попробуй быть более конкретной.")
                
        except Exception as e:
            logger.error(f"Ошибка при обработке сообщения: {e}")
            await processing_msg.edit_text("Произошла ошибка при обработке. Попробуй ещё раз.")
    
    async def _handle_create_project(self, intent_analysis: Dict[str, Any], processing_msg: Message) -> None:
        """Обработка создания нового проекта"""
        try:
            project_data = intent_analysis.get('project_data', {})
            
            # Создаём проект в Notion
            created_project = await self.notion.create_project(project_data)
            
            if created_project:
                name = project_data.get('name', 'Новый проект')
                project_type = project_data.get('type', 'Проект')
                
                response = await self.openai.generate_response(
                    f"Проект '{name}' типа '{project_type}' успешно создан",
                    "create_success"
                )
                
                await processing_msg.edit_text(f"✨ {response}")
            else:
                await processing_msg.edit_text("Не удалось создать проект. Попробуй ещё раз.")
                
        except Exception as e:
            logger.error(f"Ошибка при создании проекта: {e}")
            await processing_msg.edit_text("Произошла ошибка при создании проекта.")
    
    async def _handle_update_project(self, intent_analysis: Dict[str, Any], processing_msg: Message) -> None:
        """Обработка обновления существующего проекта"""
        try:
            project_name = intent_analysis.get('project_name')
            new_status = intent_analysis.get('new_status')
            
            if not project_name or not new_status:
                await processing_msg.edit_text("Не удалось определить, какой проект и как обновить. Уточни, пожалуйста.")
                return
            
            # Обновляем проект в Notion
            updated = await self.notion.update_project_status(project_name, new_status)
            
            if updated:
                response = await self.openai.generate_response(
                    f"Статус проекта '{project_name}' изменён на '{new_status}'",
                    "update_success"
                )
                await processing_msg.edit_text(f"🔄 {response}")
            else:
                await processing_msg.edit_text(f"Не удалось найти проект '{project_name}' или обновить его статус.")
                
        except Exception as e:
            logger.error(f"Ошибка при обновлении проекта: {e}")
            await processing_msg.edit_text("Произошла ошибка при обновлении проекта.")
    
    async def _handle_query_projects(self, intent_analysis: Dict[str, Any], processing_msg: Message) -> None:
        """Обработка запросов информации о проектах"""
        try:
            query_type = intent_analysis.get('query_type')
            filters = intent_analysis.get('filters', {})
            
            projects = []
            
            if query_type == 'by_status':
                status = filters.get('status')
                projects = await self.notion.get_projects_by_status(status)
            elif query_type == 'by_type':
                project_type = filters.get('type')
                projects = await self.notion.get_projects_by_type(project_type)
            else:
                projects = await self.notion.get_all_projects()
            
            if not projects:
                await processing_msg.edit_text("По твоему запросу проектов не найдено.")
                return
            
            # Формируем ответ с помощью OpenAI
            response = await self.openai.format_projects_response(projects, query_type)
            await processing_msg.edit_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Ошибка при запросе проектов: {e}")
            await processing_msg.edit_text("Произошла ошибка при поиске проектов.")
    
    async def _handle_general_chat(self, intent_analysis: Dict[str, Any], processing_msg: Message) -> None:
        """Обработка общих сообщений"""
        try:
            message = intent_analysis.get('message', '')
            response = await self.openai.generate_response(message, "general_chat")
            await processing_msg.edit_text(response)
            
        except Exception as e:
            logger.error(f"Ошибка при обработке общего сообщения: {e}")
            await processing_msg.edit_text("Произошла ошибка при обработке сообщения.")
    
    def _get_status_emoji(self, status: str) -> str:
        """Получить эмодзи для статуса проекта"""
        emoji_map = {
            'Idea': '💡',
            'In Progress': '🔥',
            'Paused': '⏸️',
            'Completed': '✅',
            'Released': '🚀',
            'Archived': '📦'
        }
        return emoji_map.get(status, '📋')

def main():
    """Основная функция запуска бота"""
    # Создаём экземпляр бота
    bot = PerukuaBot()
    
    # Создаём приложение Telegram
    application = Application.builder().token(bot.config.TELEGRAM_TOKEN).build()
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", bot.start_command))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(CommandHandler("projects", bot.projects_command))
    application.add_handler(CommandHandler("active", bot.active_command))
    
    # Добавляем обработчики сообщений
    application.add_handler(MessageHandler(filters.VOICE, bot.handle_voice_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_text_message))
    
    # Запускаем бота
    logger.info("Запуск бота Перукуа...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

