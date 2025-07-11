from src.scraper import PodcastScraper
from src.database import get_database
import sys
from typing import List

def update_all_episodes():
    scraper = PodcastScraper()
    db = get_database()

    # Step 1: Scrape and store episode metadata (URLs, titles, episode_numbers)
    episodes = scraper.get_episode_list()
    print(f"Found {len(episodes)} episodes.")
    for episode in episodes:
        db.save_episode(episode)
        print(f"Saved metadata for episode {episode['episode_number']} - {episode['title']}")

    # Step 2: Retrieve episodes from DB and fetch/store transcript and published date
    db_episodes = db.get_all_episodes()
    for episode in db_episodes:
        if episode.get('url'):
            details = scraper.get_episode_transcript_and_published_date(episode['url'])
            if details:
                episode['transcript'] = details['transcript']
                episode['published_date'] = details['published_date']
                db.save_episode(episode)
                print(f"Updated transcript/date for episode {episode['episode_number']} - {episode['title']}")
            else:
                print(f"Could not fetch transcript/date for episode {episode['episode_number']} - {episode['title']}")

def update_specific_episodes(episode_numbers: List[int]):
    scraper = PodcastScraper()
    db = get_database()

    # Get the latest episode list from the website
    episodes = scraper.get_episode_list()
    episode_map = {ep['episode_number']: ep for ep in episodes}

    for ep_num in episode_numbers:
        if ep_num not in episode_map:
            print(f"Episode {ep_num} does not exist in the current episode list. Skipping.")
            continue
        episode = db.get_episode(ep_num) or episode_map[ep_num]
        if episode.get('transcript') and episode.get('published_date'):
            print(f"Episode {ep_num} already has transcript and published date. Skipping.")
            continue
        details = scraper.get_episode_transcript_and_published_date(episode_map[ep_num]['url'])
        if details:
            episode['transcript'] = details['transcript']
            episode['published_date'] = details['published_date']
            db.save_episode(episode)
            print(f"Updated transcript/date for episode {ep_num} - {episode['title']}")
        else:
            print(f"Could not fetch transcript/date for episode {ep_num} - {episode['title']}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Example: python scrape_and_update_db.py 1 2 3
        episode_numbers = [int(arg) for arg in sys.argv[1:]]
        update_specific_episodes(episode_numbers)
    else:
        update_all_episodes() 