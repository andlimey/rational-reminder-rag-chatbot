"""
Database operations for storing episode data and vector embeddings in Supabase.
"""

import os
from typing import List, Dict, Optional, Any
import logging
from supabase import create_client, Client
from dotenv import load_dotenv
import json
from datetime import datetime
from dateutil import parser

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PodcastDatabase:
    """Database operations for podcast episodes and embeddings."""
    
    def __init__(self):
        """Initialize Supabase client."""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
    
    def save_episode(self, episode_data: Dict[str, Any]) -> Optional[str]:
        """
        Save episode metadata to the database.
        
        Args:
            episode_data: Dictionary containing episode information
            
        Returns:
            Episode ID if successful, None otherwise
        """
        try:
            # Prepare data for insertion
            published_date = episode_data.get('published_date')

            data = {
                'episode_number': episode_data.get('episode_number'),
                'title': episode_data.get('title'),
                'published_date': parser.isoparse(published_date).isoformat() if published_date is not None else None,
                'url': episode_data.get('url'), 
                'transcript': episode_data.get('transcript'),
                'processed': episode_data.get('processed') or False,
                'updated_at': datetime.utcnow().isoformat()
            }

            # Check if episode already exists
            existing = self.supabase.table("episodes").select("id").eq("episode_number", episode_data['episode_number']).execute()
            
            if existing.data:
                # Update existing episode
                episode_id = existing.data[0]['id']
                result = self.supabase.table("episodes").update(data).eq("id", episode_id).execute()
                logger.info(f"Updated episode {episode_data['episode_number']}")
            else:
                # Insert new episode
                result = self.supabase.table("episodes").insert(data).execute()
                episode_id = result.data[0]['id'] if result.data else None
                logger.info(f"Inserted new episode {episode_data['episode_number']}")
            
            return episode_id
            
        except Exception as e:
            logger.error(f"Error saving episode: {e}")
            return None

    def update_episode_summary(self, episode_number: int, summary: str) -> bool:
        """
        Update the summary for an episode.
        """
        try:
            self.supabase.table("episodes").update({"summary": summary}).eq("episode_number", episode_number).execute()
            return True
        except Exception as e:
            logger.error(f"Error updating episode summary: {e}")
            return False
    
    def get_episode(self, episode_number: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve episode data by episode number.
        
        Args:
            episode_number: Episode number to retrieve
            
        Returns:
            Episode data dictionary or None if not found
        """
        try:
            result = self.supabase.table("episodes").select("*").eq("episode_number", episode_number).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving episode {episode_number}: {e}")
            return None
    
    def get_all_episodes(self) -> List[Dict[str, Any]]:
        """
        Retrieve all episodes from the database.
        
        Returns:
            List of episode dictionaries
        """
        try:
            result = self.supabase.table("episodes").select("*").order("episode_number", desc=True).execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error retrieving all episodes: {e}")
            return []

    def get_all_processed_episodes(self) -> List[Dict[str, Any]]:
        """
        Retrieve all processed episodes from the database.
        
        Returns:
            List of episode dictionaries
        """
        try:
            result = self.supabase.table("episodes").select("*").eq("processed", True).order("episode_number", desc=True).execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error retrieving all processed episodes: {e}")
            return []

def get_database() -> PodcastDatabase:
    try:
        return PodcastDatabase()
    except ValueError:
        logger.warning("Supabase credentials not found")
