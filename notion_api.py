"""
Модуль для работы с Notion API
Обрабатывает все операции с базой данных проектов Перукуа
"""

import asyncio
import aiohttp
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from config import Config

logger = logging.getLogger(__name__)

class NotionAPI:
    """Класс для работы с Notion API"""
    
    def __init__(self):
        self.config = Config()
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.config.NOTION_TOKEN}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """Выполнить HTTP запрос к Notion API"""
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
            logger.error(f"Ошибка при запросе к Notion API: {e}")
            return None
    
    async def create_project(self, project_data: Dict[str, Any]) -> Optional[Dict]:
        """Создать новый проект в Notion"""
        try:
            # Подготавливаем данные для создания страницы
            page_data = {
                "parent": {"database_id": self.config.NOTION_DATABASE_ID},
                "properties": self._prepare_project_properties(project_data)
            }
            
            result = await self._make_request("POST", "pages", page_data)
            
            if result:
                logger.info(f"Создан проект: {project_data.get('name', 'Без названия')}")
                return result
            else:
                logger.error(f"Не удалось создать проект: {project_data}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при создании проекта: {e}")
            return None
    
    async def get_all_projects(self) -> List[Dict[str, Any]]:
        """Получить все проекты из базы данных"""
        try:
            endpoint = f"databases/{self.config.NOTION_DATABASE_ID}/query"
            
            # Запрашиваем все записи
            query_data = {
                "page_size": 100,
                "sorts": [
                    {
                        "property": "Date",
                        "direction": "descending"
                    }
                ]
            }
            
            result = await self._make_request("POST", endpoint, query_data)
            
            if result:
                projects = []
                for page in result.get("results", []):
                    project = self._parse_project_from_page(page)
                    if project:
                        projects.append(project)
                
                logger.info(f"Получено проектов: {len(projects)}")
                return projects
            else:
                logger.error("Не удалось получить проекты")
                return []
                
        except Exception as e:
            logger.error(f"Ошибка при получении проектов: {e}")
            return []
    
    async def get_projects_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Получить проекты по статусу"""
        try:
            endpoint = f"databases/{self.config.NOTION_DATABASE_ID}/query"
            
            query_data = {
                "filter": {
                    "property": "Status",
                    "select": {
                        "equals": status
                    }
                },
                "sorts": [
                    {
                        "property": "Date",
                        "direction": "descending"
                    }
                ]
            }
            
            result = await self._make_request("POST", endpoint, query_data)
            
            if result:
                projects = []
                for page in result.get("results", []):
                    project = self._parse_project_from_page(page)
                    if project:
                        projects.append(project)
                
                logger.info(f"Получено проектов со статусом '{status}': {len(projects)}")
                return projects
            else:
                return []
                
        except Exception as e:
            logger.error(f"Ошибка при получении проектов по статусу: {e}")
            return []
    
    async def get_projects_by_type(self, project_type: str) -> List[Dict[str, Any]]:
        """Получить проекты по типу"""
        try:
            endpoint = f"databases/{self.config.NOTION_DATABASE_ID}/query"
            
            query_data = {
                "filter": {
                    "property": "Type",
                    "select": {
                        "equals": project_type
                    }
                },
                "sorts": [
                    {
                        "property": "Date",
                        "direction": "descending"
                    }
                ]
            }
            
            result = await self._make_request("POST", endpoint, query_data)
            
            if result:
                projects = []
                for page in result.get("results", []):
                    project = self._parse_project_from_page(page)
                    if project:
                        projects.append(project)
                
                logger.info(f"Получено проектов типа '{project_type}': {len(projects)}")
                return projects
            else:
                return []
                
        except Exception as e:
            logger.error(f"Ошибка при получении проектов по типу: {e}")
            return []
    
    async def update_project_status(self, project_name: str, new_status: str) -> bool:
        """Обновить статус проекта по названию"""
        try:
            # Сначала найдём проект по названию
            projects = await self.get_all_projects()
            target_project = None
            
            for project in projects:
                if project.get('name', '').lower() == project_name.lower():
                    target_project = project
                    break
            
            if not target_project:
                logger.warning(f"Проект '{project_name}' не найден")
                return False
            
            # Обновляем статус
            page_id = target_project.get('id')
            if not page_id:
                logger.error("Не удалось получить ID проекта")
                return False
            
            update_data = {
                "properties": {
                    "Status": {
                        "select": {
                            "name": new_status
                        }
                    }
                }
            }
            
            result = await self._make_request("PATCH", f"pages/{page_id}", update_data)
            
            if result:
                logger.info(f"Обновлён статус проекта '{project_name}' на '{new_status}'")
                return True
            else:
                logger.error(f"Не удалось обновить статус проекта '{project_name}'")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка при обновлении статуса проекта: {e}")
            return False
    
    async def find_project_by_name(self, project_name: str) -> Optional[Dict[str, Any]]:
        """Найти проект по названию"""
        try:
            projects = await self.get_all_projects()
            
            for project in projects:
                if project.get('name', '').lower() == project_name.lower():
                    return project
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при поиске проекта: {e}")
            return None
    
    def _prepare_project_properties(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Подготовить свойства проекта для Notion API"""
        properties = {}
        
        # Название проекта (обязательное поле)
        name = project_data.get('name', 'Новый проект')
        properties["Name"] = {
            "title": [
                {
                    "type": "text",
                    "text": {"content": name}
                }
            ]
        }
        
        # Тип проекта
        project_type = project_data.get('type', 'Song')
        properties["Type"] = {
            "select": {"name": project_type}
        }
        
        # Статус проекта
        status = project_data.get('status', 'Idea')
        properties["Status"] = {
            "select": {"name": status}
        }
        
        # Заметки
        notes = project_data.get('notes', '')
        if notes:
            properties["Notes"] = {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": notes}
                    }
                ]
            }
        
        # Теги
        tags = project_data.get('tags', [])
        if tags:
            properties["Tags"] = {
                "multi_select": [{"name": tag} for tag in tags]
            }
        
        # Дата
        date = project_data.get('date')
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        properties["Date"] = {
            "date": {"start": date}
        }
        
        return properties
    
    def _parse_project_from_page(self, page: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Извлечь данные проекта из страницы Notion"""
        try:
            properties = page.get("properties", {})
            
            project = {
                "id": page.get("id", ""),
                "name": self._extract_title(properties.get("Name", {})),
                "type": self._extract_select(properties.get("Type", {})),
                "status": self._extract_select(properties.get("Status", {})),
                "notes": self._extract_rich_text(properties.get("Notes", {})),
                "tags": self._extract_multi_select(properties.get("Tags", {})),
                "date": self._extract_date(properties.get("Date", {}))
            }
            
            return project
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге проекта: {e}")
            return None
    
    def _extract_title(self, title_property: Dict) -> str:
        """Извлечь заголовок из свойства Notion"""
        try:
            title_list = title_property.get("title", [])
            if title_list:
                return title_list[0].get("plain_text", "")
            return ""
        except:
            return ""
    
    def _extract_select(self, select_property: Dict) -> str:
        """Извлечь значение select из свойства Notion"""
        try:
            select_obj = select_property.get("select")
            if select_obj:
                return select_obj.get("name", "")
            return ""
        except:
            return ""
    
    def _extract_rich_text(self, rich_text_property: Dict) -> str:
        """Извлечь rich text из свойства Notion"""
        try:
            rich_text_list = rich_text_property.get("rich_text", [])
            if rich_text_list:
                return rich_text_list[0].get("plain_text", "")
            return ""
        except:
            return ""
    
    def _extract_multi_select(self, multi_select_property: Dict) -> List[str]:
        """Извлечь multi select из свойства Notion"""
        try:
            multi_select_list = multi_select_property.get("multi_select", [])
            return [item.get("name", "") for item in multi_select_list]
        except:
            return []
    
    def _extract_date(self, date_property: Dict) -> str:
        """Извлечь дату из свойства Notion"""
        try:
            date_obj = date_property.get("date")
            if date_obj:
                return date_obj.get("start", "")
            return ""
        except:
            return ""

