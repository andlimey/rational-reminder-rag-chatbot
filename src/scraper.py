"""
Web scraping utilities for the Rational Reminder podcast.
"""

import requests
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Optional
import logging
from urllib.parse import urljoin, urlparse

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PodcastScraper:
    """Scraper for Rational Reminder podcast episodes."""
    
    def __init__(self, base_url: str = "https://rationalreminder.ca"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_episode_list(self) -> List[Dict]:
        """
        Extract all episodes from the podcast directory.
        Does not include crypto episodes and special episodes.
        
        Returns:
            List of episode dictionaries with title, url, and episode number
        """
        try:
            url = f"{self.base_url}/podcast-directory"
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            episodes = []
            
            # Find all episode links in the directory
            episode_links = soup.find_all('a', href=re.compile(r'/podcast/\d+'))
                        
            for link in episode_links:
                href = link.get('href')
                if href:
                    # Extract episode number from URL
                    episode_match = re.search(r'/podcast/(\d+)$', href)

                    if episode_match:
                        episode_num = int(episode_match.group(1))
                        title = link.get_text(strip=True)

                        episodes.append({
                            'episode_number': episode_num,
                            'title': title,
                            'url': urljoin(self.base_url, href),
                        })
            
            # Sort by episode number
            episodes.sort(key=lambda x: x['episode_number'])
            logger.info(f"Found {len(episodes)} episodes")
            return episodes
            
        except Exception as e:
            logger.error(f"Error fetching episode list: {e}")
            return []
    
    def get_episode_transcript_and_published_date(self, episode_url: str) -> Optional[Dict]:
        """
        Extract the transcript from a specific episode page.
        
        Args:
            episode_url: URL of the episode
            
        Returns:
            Episode transcript text and published date or None if not found
        """
        try:
            response = self.session.get(episode_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')     

            sqs_html_content_divs = soup.find_all("div", class_="sqs-html-content")
            transcript_paragraphs = []

            for content in sqs_html_content_divs:
                header = content.find('h2')

                if header and "read the transcript" in header.get_text(strip=True).lower():

                    paragraphs = content.find_all('p')

                    for paragraph in paragraphs:
                        transcript_paragraphs.append(paragraph.get_text(separator=" ", strip=True))

                    break

            date_published_meta_tag = soup.find("meta", itemprop="datePublished")

            if date_published_meta_tag and date_published_meta_tag.has_attr("content"):
                published_date = date_published_meta_tag.get("content")
            else:
                logger.warning(f"No published date meta tag found for {episode_url}")
                return None

            return {
                'transcript': transcript_paragraphs,
                'published_date': published_date
            }

        except Exception as e:
            logger.error(f"Error extracting transcript and published date from {episode_url}: {e}")
            return None
