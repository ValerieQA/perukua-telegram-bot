#!/usr/bin/env python3
"""
Telegram Bot for Peruquois — Personal assistant for project management
Integrates with the Notion API for project handling and the OpenAI API for natural-language processing
"""

import os
import logging
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any

from telegram import Update, Message, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

from config import Config
from notion_api import NotionAPI
from openai_api import OpenAIAPI

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class PeruquoisBot:
    """Main Telegram bot class for Peruquois"""

    def __init__(self):
        self.config = Config()
        self.notion = NotionAPI()
        self.openai = OpenAIAPI()

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler for /start command"""
        welcome_message = """
🌟 Hello, Peruquois! I'm your personal assistant for project management.

I'll help you:
• Save new ideas and projects  
• Track the status of current projects  
• Organise your creative concepts  
• Remind you about important tasks  

Just talk to me naturally—in voice or text. I’ll understand what you want to do and organise everything for you.

Available commands:
/start    – show this message  
/projects – show all projects  
/active   – show active projects  
/help     – command reference  

Ready to begin? Tell me about your ideas! ✨
        """
        await update.message.reply_text(welcome_message)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler for /help command"""
        help_message = """
🔮 **How I work**

📝 **Creating projects**  
Just tell me about your idea, for example:  
• “I have an idea for a new song about motherhood”  
• “I want to create a course on feminine energy”  
• “I'm planning a retreat in the mountains”

📊 **Updating status**  
• “Started working on the moon song”  
• “Pausing work on the course”  
• “Finished recording the album”

📋 **Viewing projects**  
• “What am I working on?”  
• “Show me all my songs”  
• “What courses am I planning?”

🎯 **Project types**  
• Songs (Song)  
• Books (Book)  
• Courses (Course)  
• Retreats (Retreat)  
• Workshops (Workshop)  
• Albums (Album)

💫 Just write naturally—I’ll infer your intentions and organise everything myself!
        """
        await update.message.reply_text(help_message)

    async def projects_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler for /projects command — show all projects"""
        try:
            projects = await self.notion.get_all_projects()

            if not projects:
                await update.message.reply_text("You don’t have any saved projects yet. Share your ideas with me! ✨")
                return

            message = "🌟 **All your projects:**\n\n"

            # Group projects by type
            projects_by_type: Dict[str, list] = {}
            for project in projects:
                project_type = project.get('type', 'Other')
                projects_by_type.setdefault(project_type, []).append(project)

            # Build the message
            for project_type, type_projects in projects_by_type.items():
                message += f"**{project_type}:**\n"
                for project in type_projects:
                    name = project.get('name', 'Untitled')
                    status = project.get('status', 'Unknown')
                    status_emoji = self._get_status_emoji(status)
                    message += f"  {status_emoji} {name} – {status}\n"
                message += "\n"

            await update.message.reply_text(message, parse_mode='Markdown')

        except Exception as e:
            logger.error(f"Error getting projects: {e}")
            await update.message.reply_text("An error occurred while retrieving the project list. Please try again later.")

    async def active_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler for /active command — show active projects"""
        try:
            projects = await self.notion.get_projects_by_status("In Progress")

            if not projects:
                await update.message.reply_text("You have no active projects. Time to start something new! 🚀")
                return

            message = "🔥 **Your active projects:**\n\n"
            for project in projects:
                name = project.get('name', 'Untitled')
                project_type = project.get('type', 'Project')
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
            logger.error(f"Error getting active projects: {e}")
            await update.message.reply_text("An error occurred while getting active projects. Please try again later.")

    async def handle_voice_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler for voice messages"""
        try:
            processing_msg = await update.message.reply_text("🎤 Listening to your message…")

            # Retrieve voice file
            voice_file = await update.message.voice.get_file()

            # Save locally
            voice_path = f"/tmp/voice_{update.message.message_id}.ogg"
            await voice_file.download_to_drive(voice_path)

            # Transcribe the voice message
            transcription = await self.openai.transcribe_audio(voice_path)

            # Remove temporary file
            os.remove(voice_path)

            if not transcription:
                await processing_msg.edit_text("Could not recognise the voice message. Please try again.")
                return

            # Process the transcribed text
            await processing_msg.edit_text(f"📝 I heard: “{transcription}”\n\nProcessing…")
            await self._process_text_message(update, context, transcription, processing_msg,
                                             original_transcription=transcription)

        except Exception as e:
            logger.error(f"Error processing voice message: {e}")
            await update.message.reply_text("An error occurred while processing the voice message. Please try typing instead.")

    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler for text messages"""
        try:
            processing_msg = await update.message.reply_text("💭 Processing your request…")

            text = update.message.text
            await self._process_text_message(update, context, text, processing_msg)

        except Exception as e:
            logger.error(f"Error processing text message: {e}")
            await update.message.reply_text("An error occurred while processing the message. Please try again.")

    async def _process_text_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        text: str,
        processing_msg: Message,
        original_transcription: str | None = None
    ) -> None:
        """Internal method for processing text messages"""
        try:
            # Analyze intent with enhanced column optimization
            intent_analysis = await self.openai.enhanced_intent_analysis(text)
            if not intent_analysis:
                await processing_msg.edit_text("I couldn’t understand that. Could you rephrase?")
                return

            action = intent_analysis.get('action')

            if action == 'create_project':
                await self._handle_create_project(intent_analysis, processing_msg, original_transcription)
            elif action == 'clarify_intent':
                await self._handle_clarify_intent(intent_analysis, processing_msg, original_transcription)
            elif action == 'update_status':
                await self._handle_update_status(intent_analysis, processing_msg)
            elif action == 'add_notes':
                await self._handle_add_notes(intent_analysis, processing_msg, original_transcription)
            elif action == 'update_project_info':
                await self._handle_update_project_info(intent_analysis, processing_msg)
            elif action == 'archive_project':
                await self._handle_archive_project(intent_analysis, processing_msg)
            elif action == 'update_project':            # Backward compatibility
                await self._handle_update_project(intent_analysis, processing_msg)
            elif action == 'query_projects':
                await self._handle_query_projects(intent_analysis, processing_msg)
            elif action == 'general_chat':
                await self._handle_general_chat(intent_analysis, processing_msg)
            else:
                await processing_msg.edit_text(
                    "I understand the message, but I’m not sure how to respond. Could you be more specific?"
                )

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await processing_msg.edit_text("An error occurred during processing. Please try again.")

    # ---------- Handlers for specific actions ----------

    async def _handle_create_project(
        self,
        intent_analysis: Dict[str, Any],
        processing_msg: Message,
        original_transcription: str | None = None
    ) -> None:
        """Handle creating a new project"""
        try:
            project_data = intent_analysis.get('project_data', {})

            # Attach original transcription to Original Audio field
            if original_transcription:
                project_data['original_audio'] = original_transcription

            # Keep processed notes in the notes field
            # (notes field will be saved to "Processed Notes" column)

            # Create project in Notion
            created_project = await self.notion.create_project(project_data)

            if created_project:
                name = project_data.get('name', 'New Project')
                project_type = project_data.get('type', 'Project')

                response = await self.openai.generate_response(
                    f"Project '{name}' of type '{project_type}' created successfully",
                    "create_success"
                )
                await processing_msg.edit_text(f"✨ {response}")
            else:
                await processing_msg.edit_text("Could not create the project. Please try again.")

        except Exception as e:
            logger.error(f"Error creating project: {e}")
            await processing_msg.edit_text("An error occurred while creating the project.")

    async def _handle_update_project(self, intent_analysis: Dict[str, Any], processing_msg: Message) -> None:
        """Handle updating an existing project (legacy path)"""
        try:
            project_name = intent_analysis.get('project_name')
            new_status = intent_analysis.get('new_status')

            if not project_name or not new_status:
                await processing_msg.edit_text("Which project should be updated? Please clarify.")
                return

            updated = await self.notion.update_project_status(project_name, new_status)

            if updated:
                response = await self.openai.generate_response(
                    f"Project '{project_name}' status changed to '{new_status}'",
                    "update_success"
                )
                await processing_msg.edit_text(f"🔄 {response}")
            else:
                await processing_msg.edit_text(f"Could not find project '{project_name}' or update its status.")

        except Exception as e:
            logger.error(f"Error updating project: {e}")
            await processing_msg.edit_text("An error occurred while updating the project.")

    async def _handle_query_projects(self, intent_analysis: Dict[str, Any], processing_msg: Message) -> None:
        """Handle project information queries"""
        try:
            query_type = intent_analysis.get('query_type')
            filters = intent_analysis.get('filters', {})

            projects: list[Dict[str, Any]] = []

            if query_type == 'by_status':
                status = filters.get('status')
                projects = await self.notion.get_projects_by_status(status)
            elif query_type == 'by_type':
                project_type = filters.get('type')
                projects = await self.notion.get_projects_by_type(project_type)
            else:
                projects = await self.notion.get_all_projects()

            if not projects:
                await processing_msg.edit_text("No projects found matching your query.")
                return

            response = await self.openai.format_projects_response(projects, query_type)
            await processing_msg.edit_text(response, parse_mode='Markdown')

        except Exception as e:
            logger.error(f"Error querying projects: {e}")
            await processing_msg.edit_text("An error occurred while searching for projects.")

    async def _handle_general_chat(self, intent_analysis: Dict[str, Any], processing_msg: Message) -> None:
        """Handle general (non-actionable) messages"""
        try:
            original_message = intent_analysis.get('message', '')
            response = await self.openai.generate_response(original_message, "general_chat")
            await processing_msg.edit_text(response)

        except Exception as e:
            logger.error(f"Error handling general chat: {e}")
            await processing_msg.edit_text("An error occurred while processing the message.")

    async def _handle_update_status(self, intent_analysis: Dict[str, Any], processing_msg: Message) -> None:
        """Handle project status updates"""
        try:
            project_identifier = intent_analysis.get('project_identifier', '')
            new_status = intent_analysis.get('new_status', '')
            reason = intent_analysis.get('reason', '')

            if not project_identifier or not new_status:
                await processing_msg.edit_text("Project or new status not specified.")
                return

            project = await self.notion.find_project_by_keywords(project_identifier)
            if not project:
                await processing_msg.edit_text(f"Project '{project_identifier}' not found.")
                return

            success = await self.notion.update_project_status(project['name'], new_status)

            if success:
                emoji = self._get_status_emoji(new_status)
                response = f"{emoji} Project '{project['name']}' status changed to '{new_status}'"
                if reason:
                    response += f"\nReason: {reason}"
                await processing_msg.edit_text(response)
            else:
                await processing_msg.edit_text(f"Could not update project '{project['name']}'.")

        except Exception as e:
            logger.error(f"Error updating status: {e}")
            await processing_msg.edit_text("An error occurred while updating the status.")

    async def _handle_add_notes(
        self,
        intent_analysis: Dict[str, Any],
        processing_msg: Message,
        original_transcription: str | None = None
    ) -> None:
        """Handle adding notes to a project"""
        try:
            project_identifier = intent_analysis.get('project_identifier', '')
            additional_notes = intent_analysis.get('additional_notes', '')
            note_type = intent_analysis.get('note_type', 'update')

            if not project_identifier or not additional_notes:
                await processing_msg.edit_text("Project or notes not specified.")
                return

            project = await self.notion.find_project_by_keywords(project_identifier)
            if not project:
                await processing_msg.edit_text(f"Project '{project_identifier}' not found.")
                return

            # Add original transcription to Original Audio if available
            update_data = {}
            if original_transcription:
                update_data['original_audio'] = original_transcription
            
            # Add processed notes
            if additional_notes:
                update_data['additional_notes'] = additional_notes
                update_data['note_type'] = note_type

            success = await self.notion.add_notes_to_project(project_identifier, update_data)

            if success:
                await processing_msg.edit_text(f"📝 Notes added to project '{project['name']}'")
            else:
                await processing_msg.edit_text(f"Could not add notes to project '{project['name']}'.")

        except Exception as e:
            logger.error(f"Error adding notes: {e}")
            await processing_msg.edit_text("An error occurred while adding notes.")

    async def _handle_update_project_info(self, intent_analysis: Dict[str, Any], processing_msg: Message) -> None:
        """Handle updating project metadata"""
        try:
            project_identifier = intent_analysis.get('project_identifier', '')
            updates = intent_analysis.get('updates', {})

            if not project_identifier or not updates:
                await processing_msg.edit_text("Project or changes not specified.")
                return

            project = await self.notion.find_project_by_keywords(project_identifier)
            if not project:
                await processing_msg.edit_text(f"Project '{project_identifier}' not found.")
                return

            success = await self.notion.update_project_info(project_identifier, updates)

            if success:
                changes: list[str] = []
                if 'name' in updates:
                    changes.append(f"name → '{updates['name']}'")
                if 'type' in updates:
                    changes.append(f"type → '{updates['type']}'")
                if 'tags' in updates:
                    changes.append(f"tags → {updates['tags']}")

                response = f"✏️ Project '{project['name']}' updated:\n"
                response += "\n".join(f"• {ch}" for ch in changes)
                await processing_msg.edit_text(response)
            else:
                await processing_msg.edit_text(f"Could not update project '{project['name']}'.")

        except Exception as e:
            logger.error(f"Error updating project info: {e}")
            await processing_msg.edit_text("An error occurred while updating project information.")

    async def _handle_archive_project(self, intent_analysis: Dict[str, Any], processing_msg: Message) -> None:
        """Handle archiving a project"""
        try:
            project_identifier = intent_analysis.get('project_identifier', '')
            reason = intent_analysis.get('reason', '')

            if not project_identifier:
                await processing_msg.edit_text("Project to archive not specified.")
                return

            project = await self.notion.find_project_by_keywords(project_identifier)
            if not project:
                await processing_msg.edit_text(f"Project '{project_identifier}' not found.")
                return

            success = await self.notion.archive_project(project_identifier, reason)

            if success:
                response = f"📦 Project '{project['name']}' archived"
                if reason:
                    response += f"\nReason: {reason}"
                await processing_msg.edit_text(response)
            else:
                await processing_msg.edit_text(f"Could not archive project '{project['name']}'.")

        except Exception as e:
            logger.error(f"Error archiving project: {e}")
            await processing_msg.edit_text("An error occurred while archiving the project.")

    async def _handle_clarify_intent(
        self,
        intent_analysis: Dict[str, Any],
        processing_msg: Message,
        original_transcription: str | None = None
    ) -> None:
        """Handle intent clarification by showing similar projects"""
        try:
            search_keywords = intent_analysis.get('search_keywords', '')
            project_data = intent_analysis.get('project_data', {})
            
            if not search_keywords:
                # Fallback to creating new project if no keywords
                await self._handle_create_project(intent_analysis, processing_msg, original_transcription)
                return
            
            # Search for similar projects
            similar_projects = await self.notion.find_similar_projects(search_keywords, limit=5)
            
            if not similar_projects:
                # No similar projects found, create new one
                await self._handle_create_project(intent_analysis, processing_msg, original_transcription)
                return
            
            # Store context for callback handling
            context_data = {
                'intent_analysis': intent_analysis,
                'original_transcription': original_transcription,
                'similar_projects': similar_projects
            }
            
            # Create inline keyboard with options
            keyboard = []
            
            # Add buttons for similar projects (max 5)
            for i, project in enumerate(similar_projects[:5]):
                project_name = project.get('name', 'Untitled')
                project_type = project.get('type', 'Project')
                button_text = f"{i+1}. {project_name} ({project_type})"
                callback_data = f"select_project_{i}"
                keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
            
            # Add "Create New Project" and "Cancel" options
            keyboard.append([InlineKeyboardButton("🆕 Create New Project", callback_data="create_new")])
            keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Store context in user_data for callback handling
            user_id = processing_msg.chat.id
            if not hasattr(processing_msg, 'bot'):
                # This is a workaround - we'll store in a class variable
                if not hasattr(self, '_pending_contexts'):
                    self._pending_contexts = {}
                self._pending_contexts[user_id] = context_data
            
            # Format message with similar projects
            message_text = "🤔 I hear you want to make changes. I found some similar projects:\n\n"
            
            for i, project in enumerate(similar_projects[:5]):
                name = project.get('name', 'Untitled')
                project_type = project.get('type', 'Project')
                status = project.get('status', 'Unknown')
                
                # Add emoji for project type
                type_emojis = {
                    'Song': '🎵', 'Book': '📖', 'Course': '🎓',
                    'Retreat': '🏔️', 'Workshop': '🛠️', 'Album': '💿', 'Project': '📋'
                }
                emoji = type_emojis.get(project_type, '📋')
                
                message_text += f"{i+1}️⃣ {emoji} **{name}**\n"
                message_text += f"    Type: {project_type} | Status: {status}\n\n"
            
            message_text += "Choose an option below:"
            
            await processing_msg.edit_text(message_text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error handling clarify intent: {e}")
            await processing_msg.edit_text("An error occurred while searching for similar projects.")

    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle callback queries from inline keyboards"""
        try:
            query = update.callback_query
            await query.answer()  # Acknowledge the callback query
            
            user_id = query.message.chat.id
            callback_data = query.data
            
            # Retrieve stored context
            if not hasattr(self, '_pending_contexts') or user_id not in self._pending_contexts:
                await query.edit_message_text("Session expired. Please try again.")
                return
            
            context_data = self._pending_contexts[user_id]
            intent_analysis = context_data['intent_analysis']
            original_transcription = context_data['original_transcription']
            similar_projects = context_data['similar_projects']
            
            if callback_data == "cancel":
                await query.edit_message_text("Operation cancelled.")
                del self._pending_contexts[user_id]
                return
            
            elif callback_data == "create_new":
                # Create new project
                await query.edit_message_text("Creating new project...")
                await self._handle_create_project(intent_analysis, query.message, original_transcription)
                del self._pending_contexts[user_id]
                return
            
            elif callback_data.startswith("select_project_"):
                # Add to existing project
                project_index = int(callback_data.split("_")[-1])
                if project_index < len(similar_projects):
                    selected_project = similar_projects[project_index]
                    project_name = selected_project.get('name', 'Untitled')
                    
                    await query.edit_message_text(f"Adding notes to '{project_name}'...")
                    
                    # Prepare data for adding notes
                    project_data = intent_analysis.get('project_data', {})
                    additional_notes = project_data.get('notes', '')
                    
                    # Create update data
                    update_data = {}
                    if original_transcription:
                        update_data['original_audio'] = original_transcription
                    
                    # Always add processed notes if we have project_data
                    if additional_notes:
                        update_data['additional_notes'] = additional_notes
                        update_data['note_type'] = 'update'
                    elif original_transcription:
                        # If no processed notes but we have transcription, create a basic note
                        update_data['additional_notes'] = "Audio transcription added to project"
                        update_data['note_type'] = 'update'
                    
                    # Add notes to the selected project
                    success = await self.notion.add_notes_to_project(project_name, update_data)
                    
                    if success:
                        await query.edit_message_text(f"✅ Notes added to '{project_name}' successfully!")
                    else:
                        await query.edit_message_text(f"❌ Failed to add notes to '{project_name}'.")
                    
                    del self._pending_contexts[user_id]
                else:
                    await query.edit_message_text("Invalid selection. Please try again.")
            
        except Exception as e:
            logger.error(f"Error handling callback query: {e}")
            await query.edit_message_text("An error occurred while processing your selection.")

    # ---------- Utility ----------

    @staticmethod
    def _get_status_emoji(status: str) -> str:
        """Return an emoji for the given project status"""
        return {
            'Idea': '💡',
            'In Progress': '🔥',
            'Paused': '⏸️',
            'Completed': '✅',
            'Released': '🚀',
            'Archived': '📦'
        }.get(status, '📋')

# ---------- Entry point ----------

def main() -> None:
    """Start the bot"""
    bot = PeruquoisBot()

    application = Application.builder().token(bot.config.TELEGRAM_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", bot.start_command))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(CommandHandler("projects", bot.projects_command))
    application.add_handler(CommandHandler("active", bot.active_command))

    # Message handlers
    application.add_handler(MessageHandler(filters.VOICE, bot.handle_voice_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_text_message))
    
    # Callback query handler for inline buttons
    application.add_handler(CallbackQueryHandler(bot.handle_callback_query))

    logger.info("Starting Peruquois bot…")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
