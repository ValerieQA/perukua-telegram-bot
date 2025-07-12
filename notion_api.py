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


    async def get_active_projects(self) -> List[Dict[str, Any]]:
        """Get only active projects (not archived)"""
        try:
            endpoint = f"databases/{self.config.NOTION_DATABASE_ID}/query"
            query_data = {
                "page_size": 100,
                "filter": {
                    "property": "Status",
                    "select": {
                        "does_not_equal": "Archived"
                    }
                },
                "sorts": [{"property": "Date", "direction": "descending"}]
            }
            result = await self._make_request("POST", endpoint, query_data)
            if result:
                projects = []
                for page in result.get("results", []):
                    project = self._parse_project_from_page(page)
                    if project:
                        projects.append(project)
                logger.info(f"Active projects retrieved: {len(projects)}")
                return projects
            else:
                logger.error("Failed to retrieve active projects")
                return []
        except Exception as e:
            logger.error(f"Error getting active projects: {e}")
            return []

    async def update_project_status(self, project_id: str, new_status: str) -> bool:
        """Update project status"""
        try:
            endpoint = f"pages/{project_id}"
            update_data = {
                "properties": {
                    "Status": {
                        "select": {"name": new_status}
                    }
                }
            }
            result = await self._make_request("PATCH", endpoint, update_data)
            if result:
                logger.info(f"Project status updated to: {new_status}")
                return True
            else:
                logger.error(f"Failed to update project status")
                return False
        except Exception as e:
            logger.error(f"Error updating project status: {e}")
            return False

    async def find_project_by_name(self, project_name: str) -> Optional[Dict[str, Any]]:
        """Find project by exact name match"""
        try:
            projects = await self.get_all_projects()
            for project in projects:
                if project.get("name", "").lower() == project_name.lower():
                    return project
            return None
        except Exception as e:
            logger.error(f"Error finding project by name: {e}")
            return None

    async def find_project_by_keywords(self, keywords: str) -> Optional[Dict[str, Any]]:
        """Find project by keywords in name, type, or notes"""
        try:
            projects = await self.get_all_projects()
            keywords_lower = keywords.lower()
            
            # First try exact name match
            for project in projects:
                if project.get("name", "").lower() == keywords_lower:
                    return project
            
            # Then try partial matches in name
            for project in projects:
                if keywords_lower in project.get("name", "").lower():
                    return project
            
            # Then try matches in type
            for project in projects:
                if keywords_lower in project.get("type", "").lower():
                    return project
            
            # Finally try matches in notes
            for project in projects:
                if keywords_lower in project.get("notes", "").lower():
                    return project
            
            return None
        except Exception as e:
            logger.error(f"Error finding project by keywords: {e}")
            return None

    async def add_notes_to_project(self, project_identifier: str, additional_notes: str, note_type: str = "update") -> bool:
        """Add notes to existing project"""
        try:
            # Find project by keywords
            project = await self.find_project_by_keywords(project_identifier)
            if not project:
                logger.error(f"Project not found: {project_identifier}")
                return False
            
            # Get current notes
            current_notes = project.get("notes", "")
            
            # Append new notes
            if current_notes:
                updated_notes = f"{current_notes}\n\n{additional_notes}"
            else:
                updated_notes = additional_notes
            
            # Update project
            endpoint = f"pages/{project['id']}"
            update_data = {
                "properties": {
                    "Notes": {
                        "rich_text": [{"text": {"content": updated_notes}}]
                    }
                }
            }
            
            result = await self._make_request("PATCH", endpoint, update_data)
            if result:
                logger.info(f"Notes added to project: {project['name']}")
                return True
            else:
                logger.error(f"Failed to add notes to project")
                return False
                
        except Exception as e:
            logger.error(f"Error adding notes to project: {e}")
            return False

    async def update_project_info(self, project_identifier: str, updates: Dict[str, str]) -> bool:
        """Update project information (name, type, etc.)"""
        try:
            # Find project by keywords
            project = await self.find_project_by_keywords(project_identifier)
            if not project:
                logger.error(f"Project not found: {project_identifier}")
                return False
            
            # Prepare update data
            properties = {}
            
            if "name" in updates:
                properties["Name"] = {
                    "title": [{"text": {"content": updates["name"]}}]
                }
            
            if "type" in updates:
                properties["Type"] = {
                    "select": {"name": updates["type"]}
                }
            
            if "status" in updates:
                properties["Status"] = {
                    "select": {"name": updates["status"]}
                }
            
            # Update project
            endpoint = f"pages/{project['id']}"
            update_data = {"properties": properties}
            
            result = await self._make_request("PATCH", endpoint, update_data)
            if result:
                logger.info(f"Project info updated: {project['name']}")
                return True
            else:
                logger.error(f"Failed to update project info")
                return False
                
        except Exception as e:
            logger.error(f"Error updating project info: {e}")
            return False

    async def archive_project(self, project_identifier: str, reason: str = "") -> bool:
        """Archive project by setting status to Archived"""
        try:
            # Find project by keywords
            project = await self.find_project_by_keywords(project_identifier)
            if not project:
                logger.error(f"Project not found: {project_identifier}")
                return False
            
            # Update status to Archived
            success = await self.update_project_status(project['id'], "Archived")
            
            # Optionally add archive reason to notes
            if success and reason:
                current_notes = project.get("notes", "")
                archive_note = f"Archived: {reason}"
                if current_notes:
                    updated_notes = f"{current_notes}\n\n{archive_note}"
                else:
                    updated_notes = archive_note
                
                await self.add_notes_to_project(project_identifier, archive_note)
            
            return success
                
        except Exception as e:
            logger.error(f"Error archiving project: {e}")
            return False

    async def get_project_details(self, project_identifier: str) -> Optional[Dict[str, Any]]:
        """Get detailed project information"""
        try:
            project = await self.find_project_by_keywords(project_identifier)
            return project
        except Exception as e:
            logger.error(f"Error getting project details: {e}")
            return None

    def _prepare_project_properties(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare project properties for Notion API (works with existing columns only)"""
        properties = {}
        
        # Project name (required field)
        if "name" in project_data:
            properties["Name"] = {
                "title": [{"text": {"content": project_data["name"]}}]
            }
        
        # Project type
        if "type" in project_data:
            properties["Type"] = {
                "select": {"name": project_data["type"]}
            }
        
        # Project status
        if "status" in project_data:
            properties["Status"] = {
                "select": {"name": project_data["status"]}
            }
        
        # Notes - use existing Notes column
        if "notes" in project_data:
            properties["Notes"] = {
                "rich_text": [{"text": {"content": project_data["notes"]}}]
            }
        
        # Tags
        if "tags" in project_data and project_data["tags"]:
            tag_objects = []
            for tag in project_data["tags"]:
                tag_objects.append({"name": tag})
            properties["Tags"] = {"multi_select": tag_objects}
        
        return properties

    def _parse_project_from_page(self, page: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse project data from Notion page"""
        try:
            properties = page.get("properties", {})
            
            project = {
                "id": page.get("id"),
                "name": self._extract_title(properties.get("Name", {})),
                "type": self._extract_select(properties.get("Type", {})),
                "status": self._extract_select(properties.get("Status", {})),
                "notes": self._extract_rich_text(properties.get("Notes", {})),
                "tags": self._extract_multi_select(properties.get("Tags", {})),
                "created_time": page.get("created_time"),
                "last_edited_time": page.get("last_edited_time")
            }
            
            return project
            
        except Exception as e:
            logger.error(f"Error parsing project from page: {e}")
            return None

    def _extract_title(self, title_property: Dict[str, Any]) -> str:
        """Extract title from Notion title property"""
        try:
            title_list = title_property.get("title", [])
            if title_list:
                return title_list[0].get("text", {}).get("content", "")
            return ""
        except Exception:
            return ""

    def _extract_select(self, select_property: Dict[str, Any]) -> str:
        """Extract value from Notion select property"""
        try:
            select_obj = select_property.get("select")
            if select_obj:
                return select_obj.get("name", "")
            return ""
        except Exception:
            return ""

    def _extract_rich_text(self, rich_text_property: Dict[str, Any]) -> str:
        """Extract text from Notion rich text property"""
        try:
            rich_text_list = rich_text_property.get("rich_text", [])
            text_parts = []
            for text_obj in rich_text_list:
                text_parts.append(text_obj.get("text", {}).get("content", ""))
            return "".join(text_parts)
        except Exception:
            return ""

    def _extract_multi_select(self, multi_select_property: Dict[str, Any]) -> List[str]:
        """Extract values from Notion multi-select property"""
        try:
            multi_select_list = multi_select_property.get("multi_select", [])
            return [item.get("name", "") for item in multi_select_list]
        except Exception:
            return []

    def _get_status_emoji(self, status: str) -> str:
        """Get emoji for project status"""
        status_emojis = {
            "Idea": "💡",
            "Planning": "📋", 
            "In Progress": "🔄",
            "On Hold": "⏸️",
            "Completed": "✅",
            "Archived": "📦"
        }
        return status_emojis.get(status, "📄")


    # ========================================
    # DYNAMIC COLUMN CREATION METHODS
    # ========================================
    
    async def get_database_schema(self) -> Optional[Dict[str, Any]]:
        """Get current database schema/properties"""
        try:
            endpoint = f"databases/{self.config.NOTION_DATABASE_ID}"
            result = await self._make_request("GET", endpoint)
            
            if result:
                properties = result.get("properties", {})
                logger.info(f"Retrieved database schema with {len(properties)} properties")
                return properties
            else:
                logger.error("Failed to retrieve database schema")
                return None
                
        except Exception as e:
            logger.error(f"Error getting database schema: {e}")
            return None
    
    async def property_exists(self, property_name: str) -> bool:
        """Check if property already exists in database"""
        try:
            schema = await self.get_database_schema()
            if schema:
                return property_name in schema
            return False
        except Exception as e:
            logger.error(f"Error checking property existence: {e}")
            return False
    
    async def create_optimal_property(self, property_name: str, property_type: str, options: List[str] = None) -> bool:
        """Create optimal property based on type and content"""
        try:
            if await self.property_exists(property_name):
                logger.info(f"Property '{property_name}' already exists")
                return True
            
            endpoint = f"databases/{self.config.NOTION_DATABASE_ID}"
            
            # Determine optimal property configuration
            if property_type == "text" or property_type == "rich_text":
                property_config = {"rich_text": {}}
            
            elif property_type == "select":
                if not options:
                    options = ["Option 1", "Option 2", "Option 3"]
                
                colors = ["default", "gray", "brown", "orange", "yellow", "green", "blue", "purple", "pink", "red"]
                select_options = []
                for i, option in enumerate(options):
                    select_options.append({
                        "name": option,
                        "color": colors[i % len(colors)]
                    })
                property_config = {"select": {"options": select_options}}
            
            elif property_type == "multi_select":
                if not options:
                    options = ["Tag 1", "Tag 2", "Tag 3"]
                
                colors = ["default", "gray", "brown", "orange", "yellow", "green", "blue", "purple", "pink", "red"]
                select_options = []
                for i, option in enumerate(options):
                    select_options.append({
                        "name": option,
                        "color": colors[i % len(colors)]
                    })
                property_config = {"multi_select": {"options": select_options}}
            
            elif property_type == "number":
                property_config = {"number": {"format": "number"}}
            
            elif property_type == "date":
                property_config = {"date": {}}
            
            elif property_type == "checkbox":
                property_config = {"checkbox": {}}
            
            elif property_type == "url":
                property_config = {"url": {}}
            
            else:
                # Default to rich text
                property_config = {"rich_text": {}}
            
            update_data = {
                "properties": {
                    property_name: property_config
                }
            }
            
            result = await self._make_request("PATCH", endpoint, update_data)
            if result:
                logger.info(f"Created optimal property: {property_name} ({property_type})")
                return True
            else:
                logger.error(f"Failed to create property: {property_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating optimal property: {e}")
            return False
    
    async def analyze_and_create_optimal_columns(self, request_analysis: Dict[str, Any]) -> Dict[str, bool]:
        """Analyze request and create optimal columns automatically"""
        try:
            created_columns = {}
            
            # Extract potential column needs from request analysis
            project_type = request_analysis.get("project_type", "").lower()
            content = request_analysis.get("content", "").lower()
            action = request_analysis.get("action", "").lower()
            
            # Analyze what columns would be optimal for this type of request
            optimal_columns = self._determine_optimal_columns(project_type, content, action)
            
            # Create each optimal column
            for column_name, column_config in optimal_columns.items():
                success = await self.create_optimal_property(
                    column_name, 
                    column_config["type"], 
                    column_config.get("options")
                )
                created_columns[column_name] = success
                
                if success:
                    logger.info(f"✅ Created optimal column: {column_name}")
                else:
                    logger.warning(f"❌ Failed to create column: {column_name}")
            
            return created_columns
            
        except Exception as e:
            logger.error(f"Error analyzing and creating optimal columns: {e}")
            return {}
    
    def _determine_optimal_columns(self, project_type: str, content: str, action: str) -> Dict[str, Dict[str, Any]]:
        """Determine what columns would be optimal for this request"""
        optimal_columns = {}
        
        # Always useful columns for detailed tracking
        optimal_columns["Original Transcription"] = {
            "type": "rich_text"
        }
        optimal_columns["Processed Notes"] = {
            "type": "rich_text"
        }
        
        # Project type specific columns
        if "song" in project_type or "music" in content:
            optimal_columns["Key Signature"] = {
                "type": "select",
                "options": ["C Major", "G Major", "D Major", "A Major", "E Major", "B Major", "F# Major", "C# Major", "F Major", "Bb Major", "Eb Major", "Ab Major", "Db Major", "Gb Major", "Cb Major"]
            }
            optimal_columns["Tempo"] = {
                "type": "number"
            }
            optimal_columns["Duration"] = {
                "type": "rich_text"
            }
            optimal_columns["Instruments"] = {
                "type": "multi_select",
                "options": ["Piano", "Guitar", "Vocals", "Drums", "Bass", "Strings", "Synth", "Flute", "Violin"]
            }
            optimal_columns["Mood"] = {
                "type": "select",
                "options": ["Peaceful", "Energetic", "Melancholic", "Joyful", "Mysterious", "Romantic", "Powerful", "Dreamy"]
            }
        
        elif "workshop" in project_type or "course" in project_type or "class" in content:
            optimal_columns["Duration"] = {
                "type": "rich_text"
            }
            optimal_columns["Participants"] = {
                "type": "number"
            }
            optimal_columns["Location"] = {
                "type": "rich_text"
            }
            optimal_columns["Materials Needed"] = {
                "type": "multi_select",
                "options": ["Mats", "Music", "Props", "Handouts", "Projector", "Microphone", "Candles", "Crystals"]
            }
            optimal_columns["Energy Level"] = {
                "type": "select",
                "options": ["Gentle", "Moderate", "High Energy", "Mixed", "Restorative"]
            }
            optimal_columns["Focus Area"] = {
                "type": "select",
                "options": ["Movement", "Breathing", "Meditation", "Expression", "Healing", "Connection", "Creativity"]
            }
        
        elif "retreat" in project_type or "event" in content:
            optimal_columns["Start Date"] = {
                "type": "date"
            }
            optimal_columns["End Date"] = {
                "type": "date"
            }
            optimal_columns["Location"] = {
                "type": "rich_text"
            }
            optimal_columns["Capacity"] = {
                "type": "number"
            }
            optimal_columns["Price"] = {
                "type": "number"
            }
            optimal_columns["Accommodation"] = {
                "type": "select",
                "options": ["Included", "Not Included", "Optional", "Camping", "Hotel", "Shared Rooms"]
            }
            optimal_columns["Meals"] = {
                "type": "select",
                "options": ["All Included", "Breakfast Only", "Not Included", "Vegetarian", "Vegan", "Raw Food"]
            }
        
        elif "dance" in content or "movement" in content:
            optimal_columns["Dance Style"] = {
                "type": "multi_select",
                "options": ["Feminine Movement", "Ecstatic Dance", "Contact Improv", "Contemporary", "Tribal", "Belly Dance", "Sacred Dance"]
            }
            optimal_columns["Music Style"] = {
                "type": "multi_select",
                "options": ["Ambient", "World Music", "Electronic", "Acoustic", "Tribal", "Classical", "Nature Sounds"]
            }
            optimal_columns["Space Requirements"] = {
                "type": "rich_text"
            }
            optimal_columns["Props Needed"] = {
                "type": "multi_select",
                "options": ["Scarves", "Fans", "Ribbons", "Mirrors", "Candles", "Crystals", "Flowers", "Feathers"]
            }
        
        # Content-based columns
        if "breathing" in content or "breath" in content:
            optimal_columns["Breathing Technique"] = {
                "type": "multi_select",
                "options": ["Deep Breathing", "Pranayama", "Circular Breathing", "Box Breathing", "Wim Hof", "Holotropic"]
            }
        
        if "energy" in content or "chakra" in content:
            optimal_columns["Energy Focus"] = {
                "type": "multi_select",
                "options": ["Root Chakra", "Sacral Chakra", "Solar Plexus", "Heart Chakra", "Throat Chakra", "Third Eye", "Crown Chakra", "Aura Cleansing"]
            }
        
        if "moon" in content or "lunar" in content:
            optimal_columns["Moon Phase"] = {
                "type": "select",
                "options": ["New Moon", "Waxing Crescent", "First Quarter", "Waxing Gibbous", "Full Moon", "Waning Gibbous", "Last Quarter", "Waning Crescent"]
            }
        
        if "crystal" in content or "healing" in content:
            optimal_columns["Crystals Used"] = {
                "type": "multi_select",
                "options": ["Amethyst", "Rose Quartz", "Clear Quartz", "Citrine", "Black Tourmaline", "Selenite", "Labradorite", "Moonstone"]
            }
        
        # Action-based columns
        if "collaboration" in action or "partner" in content:
            optimal_columns["Collaborators"] = {
                "type": "multi_select",
                "options": ["Musicians", "Dancers", "Healers", "Artists", "Teachers", "Photographers", "Videographers"]
            }
        
        if "publish" in action or "share" in content:
            optimal_columns["Publishing Platform"] = {
                "type": "multi_select",
                "options": ["Instagram", "YouTube", "Website", "Spotify", "SoundCloud", "Facebook", "TikTok", "Newsletter"]
            }
            optimal_columns["Ready to Publish"] = {
                "type": "checkbox"
            }
        
        # Universal useful columns
        optimal_columns["Priority Level"] = {
            "type": "select",
            "options": ["Low", "Medium", "High", "Urgent"]
        }
        optimal_columns["Inspiration Source"] = {
            "type": "rich_text"
        }
        optimal_columns["Next Steps"] = {
            "type": "rich_text"
        }
        optimal_columns["Resources Needed"] = {
            "type": "multi_select",
            "options": ["Time", "Money", "Equipment", "Space", "People", "Research", "Practice", "Inspiration"]
        }
        
        return optimal_columns
    
    async def create_project_with_optimal_columns(self, project_data: Dict[str, Any], request_analysis: Dict[str, Any]) -> Optional[Dict]:
        """Create project and optimal columns in one operation"""
        try:
            # First, analyze and create optimal columns
            logger.info("Analyzing request for optimal columns...")
            created_columns = await self.analyze_and_create_optimal_columns(request_analysis)
            
            if created_columns:
                logger.info(f"Created {len(created_columns)} optimal columns")
                
                # Wait a moment for Notion to process the schema changes
                import asyncio
                await asyncio.sleep(2)
            
            # Then create the project with all available data
            logger.info("Creating project with enhanced data...")
            project = await self.create_project(project_data)
            
            return project
            
        except Exception as e:
            logger.error(f"Error creating project with optimal columns: {e}")
            return None

