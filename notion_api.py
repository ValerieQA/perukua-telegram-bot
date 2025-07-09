"""
Module for working with Notion API
Handles all operations with Peruquois’ project database
"""

import asyncio
import aiohttp
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from config import Config

logger = logging.getLogger(__name__)


class NotionAPI:
    """Class for working with Notion API"""

    def __init__(self):
        self.config = Config()
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.config.NOTION_TOKEN}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }

    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """Perform an HTTP request to the Notion API"""
        url = f"{self.base_url}/{endpoint}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                        method=method,
                        url=url,
                        headers=self.headers,
                        json=data
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"Notion API error {response.status}: {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Error during request to Notion API: {e}")
            return None

    async def create_project(self, project_data: Dict[str, Any]) -> Optional[Dict]:
        """Create a new project in Notion"""
        try:
            page_data = {
                "parent": {"database_id": self.config.NOTION_DATABASE_ID},
                "properties": self._prepare_project_properties(project_data)
            }
            result = await self._make_request("POST", "pages", page_data)
            if result:
                logger.info(f"Project created: {project_data.get('name', 'Untitled')}")
                return result
            else:
                logger.error(f"Failed to create project: {project_data}")
                return None
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            return None

    async def get_all_projects(self) -> List[Dict[str, Any]]:
        """Get all projects from the database"""
        try:
            endpoint = f"databases/{self.config.NOTION_DATABASE_ID}/query"
            query_data = {
                "page_size": 100,
                "sorts": [{"property": "Date", "direction": "descending"}]
            }
            result = await self._make_request("POST", endpoint, query_data)
            if result:
                projects = []
                for page in result.get("results", []):
                    project = self._parse_project_from_page(page)
                    if project:
                        projects.append(project)
                logger.info(f"Projects retrieved: {len(projects)}")
                return projects
            else:
                logger.error("Failed to retrieve projects")
                return []
        except Exception as e:
            logger.error(f"Error getting projects: {e}")
            return []

# … файл продолжается с переводом всех методов ...

