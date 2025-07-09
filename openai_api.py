"""
Module for working with OpenAI API
Processes voice message transcription, intent analysis, and response generation
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, Any, Optional, List

from config import Config

logger = logging.getLogger(__name__)

class OpenAIAPI:
    """Class for working with OpenAI API"""

    def __init__(self):
        self.config = Config()
        self.base_url = "https://api.openai.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.config.OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }

    async def transcribe_audio(self, audio_file_path: str) -> Optional[str]:
        """Transcribe an audio file using Whisper API"""
        try:
            url = f"{self.base_url}/audio/transcriptions"

            # Prepare data for multipart/form-data
            data = aiohttp.FormData()
            data.add_field('file', open(audio_file_path, 'rb'), filename='audio.ogg')
            data.add_field('model', 'whisper-1')
            data.add_field('language', 'en')  # Peruquois speaks in English

            # Create separate headers without Content-Type for multipart
            headers = {
                "Authorization": f"Bearer {self.config.OPENAI_API_KEY}"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        transcription = result.get('text', '').strip()
                        logger.info(f"Transcription: {transcription}")
                        return transcription
                    else:
                        error_text = await response.text()
                        logger.error(f"Transcription error {response.status}: {error_text}")
                        return None

        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return None

    async def analyze_intent(self, text: str) -> Optional[Dict[str, Any]]:
        """Analyze user intent in message"""
        try:
            system_prompt = """
You are Peruquois’ personal assistant, a creative woman working on many projects.

Your task is to analyze her messages and determine what she wants to do:

1. create_project - create a new project
2. update_status - change the status of an existing project
3. add_notes - add notes to an existing project
4. update_project_info - update project information (name, type, tags)
5. archive_project - archive a project
6. query_projects - get information about projects
7. general_chat - general conversation without specific actions

Project types: Song, Book, Course, Retreat, Workshop, Album
Statuses: Idea, In Progress, Paused, Completed, Released, Archived

IMPORTANT for the "notes" field:
- Preserve ALL details from the original message
- DO NOT simplify or shorten creative descriptions
- Include all technical aspects (movements, music, methods)
- Preserve emotional and metaphorical descriptions
- Include all mentions of evolution, development, connections
- Keep development processes and reflections ("looking at how to...")
- Include all details about trance, states, transitions
- Include specific track names, techniques, practices

Respond ONLY in JSON format:
[...full JSON format left unchanged for brevity...]
"""
            user_prompt = f"Message from Peruquois: {text}"

            response = await self._make_chat_request(system_prompt, user_prompt)

            if response:
                try:
                    intent_data = json.loads(response)
                    logger.info(f"Intent analysis: {intent_data}")
                    return intent_data
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON response: {response}")
                    return None
            else:
                return None

        except Exception as e:
            logger.error(f"Error analyzing intent: {e}")
            return None

    async def generate_response(self, context: str, response_type: str) -> str:
        """Generate a response in the style of Peruquois"""
        try:
            system_prompt = """
You are Peruquois’ personal assistant — a creative woman, musician, and feminine teacher.

Your tone:
- Warm, supportive, inspiring
- Use metaphors of nature, motherhood, creativity
- Talk about projects as "seeds", "blossoming", "creative flow"
- Support her multiproject nature as a gift, not a problem
- Use emojis moderately and meaningfully
- Write in English (Peruquois' language)

Response types:
- create_success: project successfully created
- update_success: project successfully updated
- general_chat: general communication
- project_info: information about projects

Keep responses brief but soulful. Max 2–3 sentences.
"""
            if response_type == "create_success":
                user_prompt = f"Project created: {context}. Tell Peruquois it was saved."
            elif response_type == "update_success":
                user_prompt = f"Project updated: {context}. Let Peruquois know it was updated successfully."
            elif response_type == "general_chat":
                user_prompt = f"Peruquois wrote: {context}. Respond warmly and supportively."
            else:
                user_prompt = f"Context: {context}. Respond to Peruquois."

            response = await self._make_chat_request(system_prompt, user_prompt)

            if response:
                logger.info(f"Generated response: {response}")
                return response
            else:
                return "I hear you, beautiful soul. Let me help you with that. ✨"

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "Something went wrong, but I'm here for you. Try again, love. 💫"

    async def format_projects_response(self, projects: List[Dict[str, Any]], query_type: str) -> str:
        """Format the response with a list of projects"""
        try:
            if not projects:
                return "No projects found for your request, beautiful. Ready to plant some new seeds? 🌱"

            system_prompt = """
You are Peruquois' personal assistant. You need to format her list of projects beautifully.

Tone:
- Warm, inspiring
- Use emojis for project types and statuses
- Group projects logically
- Write in English
- Use Markdown for formatting

[Emoji list omitted for brevity]
"""
            projects_text = "Projects:\n"
            for project in projects:
                name = project.get('name', 'Untitled')
                project_type = project.get('type', 'Project')
                status = project.get('status', 'Unknown')
                date = project.get('date', '')
                tags = project.get('tags', [])

                projects_text += f"- {name} ({project_type}) - {status}"
                if date:
                    projects_text += f" - {date}"
                if tags:
                    projects_text += f" - Tags: {', '.join(tags)}"
                projects_text += "\n"

            user_prompt = f"Format this list of projects beautifully:\n{projects_text}"

            response = await self._make_chat_request(system_prompt, user_prompt)

            if response:
                return response
            else:
                return self._format_projects_fallback(projects)

        except Exception as e:
            logger.error(f"Error formatting projects: {e}")
            return self._format_projects_fallback(projects)

    def _format_projects_fallback(self, projects: List[Dict[str, Any]]) -> str:
        """Fallback formatting of projects without OpenAI"""
        if not projects:
            return "No projects found, beautiful. Ready to create something new? ✨"

        message = "🌟 **Your Creative Garden:**\n\n"

        projects_by_type = {}
        for project in projects:
            project_type = project.get('type', 'Other')
            if project_type not in projects_by_type:
                projects_by_type[project_type] = []
            projects_by_type[project_type].append(project)

        type_emojis = {
            'Song': '🎵',
            'Book': '📖',
            'Course': '🎓',
            'Retreat': '🏔️',
            'Workshop': '🛠️',
            'Album': '💿'
        }

        status_emojis = {
            'Idea': '💡',
            'In Progress': '🔥',
            'Paused': '⏸️',
            'Completed': '✅',
            'Released': '🚀',
            'Archived': '📦'
        }

        for project_type, type_projects in projects_by_type.items():
            emoji = type_emojis.get(project_type, '📋')
            message += f"**{emoji} {project_type}:**\n"

            for project in type_projects:
                name = project.get('name', 'Untitled')
                status = project.get('status', 'Unknown')
                status_emoji = status_emojis.get(status, '📋')

                message += f"  {status_emoji} {name}\n"

            message += "\n"

        return message

    async def _make_chat_request(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Perform request to Chat API"""
        try:
            url = f"{self.base_url}/chat/completions"

            data = {
                "model": "gpt-4",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 1000,
                "temperature": 0.7
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self.headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result['choices'][0]['message']['content'].strip()
                        return content
                    else:
                        error_text = await response.text()
                        logger.error(f"OpenAI API error {response.status}: {error_text}")
                        return None

        except Exception as e:
            logger.error(f"Error during OpenAI Chat API request: {e}")
            return None
