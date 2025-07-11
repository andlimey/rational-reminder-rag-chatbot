"""
LangChain-based RAG pipeline for podcast episodes.
"""

import os
from typing import List, Dict, Optional, Any
import logging
from dotenv import load_dotenv

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import SupabaseVectorStore
from langchain.schema import Document
from langchain.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain.schema.output_parser import StrOutputParser
from supabase import create_client

from .database import get_database

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LangChainRAGPipeline:
    """LangChain-based RAG pipeline for processing and querying podcast episodes."""
    
    def __init__(self):
        """Initialize LangChain RAG pipeline components."""
        self.database = get_database()
        
        # Initialize LangChain components
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY must be set in environment variables")
        
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-ada-002",
            openai_api_key=api_key
        )
        
        self.llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0.7,
            openai_api_key=api_key
        )
        
        # Initialize vector store
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
        
        supabase_client = create_client(supabase_url, supabase_key)

        self.vector_store = SupabaseVectorStore(
            client=supabase_client,
            embedding=self.embeddings,
            table_name="documents",
            query_name="match_documents",
        )
        
        logger.info("Initialized LangChain RAG pipeline")
    
    def get_available_episodes(self) -> List[Dict[str, Any]]:
        """Get all available episodes from the database."""
        try:
            episodes = self.database.get_all_episodes()
            logger.info(f"Retrieved {len(episodes)} episodes from database")
            return episodes
        except Exception as e:
            logger.error(f"Error getting available episodes: {e}")
            return []
    
    def process_episode(self, episode_number: int) -> bool:
        """
        Process an episode using LangChain's document processing.
        
        Args:
            episode_number: Episode number to process
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get episode from database
            episode = self.database.get_episode(episode_number)
            if not episode:
                logger.error(f"Episode {episode_number} not found in database")
                return False
            
            # Check if already processed
            if episode.get('processed'):
                logger.info(f"Episode {episode_number} already processed")
                return True
            
            # Get transcript
            transcript = episode.get('transcript')
            if not transcript:
                logger.error(f"No transcript found for episode {episode_number}")
                return False
            
            # Convert transcript to LangChain Documents
            documents = self._create_documents_from_transcript(episode)
            
            # Add documents to vector store
            self.vector_store.add_documents(documents)
            
            # Mark episode as processed
            episode['processed'] = True
            self.database.save_episode(episode)
            
            logger.info(f"Successfully processed episode {episode_number}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing episode {episode_number}: {e}")
            return False
    
    def _create_documents_from_transcript(
        self, 
        episode: Dict[str, Any], 
    ) -> List[Document]:
        """Convert transcript paragraphs to LangChain Documents."""
        documents = []

        transcript = episode['transcript']
        episode_number = episode['episode_number']
        title = episode['title']
        url = episode['url']
        
        for i, paragraph in enumerate(transcript):
            # Create metadata for each document
            metadata = {
                'episode_number': episode_number,
                'episode_title': title,
                'chunk_index': i,
                'source': url
            }
            
            # Create LangChain Document
            doc = Document(
                page_content=paragraph,
                metadata=metadata
            )
            
            documents.append(doc)
        
        return documents
    
    def answer_question(self, question: str, episode_number: int) -> str:
        """
        Answer a question about a specific episode using LangChain's retrieval chain.
        
        Args:
            question: User's question
            episode_number: Episode number to query
            
        Returns:
            Generated answer
        """
        try:
            # Get episode from database
            episode = self.database.get_episode(episode_number)
            if not episode:
                return f"Episode {episode_number} not found in database. Please process it first."

            prompt = ChatPromptTemplate.from_template("""
            You are a helpful assistant answering questions about podcast episodes from the Rational Reminder podcast.
            
            Episode Title: {title}
            
            Context from the episode:
            {context}
            
            Question: {input}
            
            Please provide a clear and accurate answer based on the context provided.
            If the context doesn't contain enough information to answer the question,
            please say so rather than making up information.
            
            Answer:
            """)

            document_chain = create_stuff_documents_chain(
                llm=self.llm,
                prompt=prompt
            )

            # Filter retriever to specific episode using episode_number in metadata
            retriever = self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={
                    "k": 4,
                    "filter": {"episode_number": episode_number}
                }
            )
            
            # Create episode-specific retrieval chain
            retrieval_chain = create_retrieval_chain(
                retriever,
                document_chain
            )
            
            # Generate answer
            response = retrieval_chain.invoke({
                "title": episode['title'],
                "input": question
            })
            
            return response["answer"]
            
        except Exception as e:
            logger.error(f"Error answering question for episode {episode_number}: {e}")
            return "I encountered an error while processing your question. Please try again."
    
    def get_episode_summary(self, episode_number: int) -> Optional[str]:
        """
        Get or generate summary for an episode using LangChain.
        
        Args:
            episode_number: Episode number
            
        Returns:
            Episode summary or None if not available
        """
        try:
            # Get episode from database
            episode = self.database.get_episode(episode_number)
            if not episode:
                logger.error(f"Episode {episode_number} not found in database")
                return None
            
            # Check if summary already exists
            if episode.get('summary'):
                return episode['summary']
            
            # Create summary chain
            prompt = ChatPromptTemplate.from_template("""
            You are a helpful assistant that creates concise summaries of podcast episodes.
            Please create a comprehensive summary of the following podcast episode: {title}
            Context: {context}

            {input}
            """)
            
            document_chain = create_stuff_documents_chain(
                llm=self.llm,
                prompt=prompt
            )

            # Use existing vectors from database for summary generation
            # Create a retriever that gets all chunks from this episode
            retriever = self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={
                    "k": 300,  # Get more chunks for comprehensive summary
                    "filter": {"episode_number": episode_number}
                }
            )
            
            retrieval_chain = create_retrieval_chain(
                retriever,
                document_chain
            )
            
            # Generate summary using existing documents from vector store
            response = retrieval_chain.invoke({
                "title": episode['title'],
                "input": """
                    Please provide a well-structured summary that includes:
                    1. Main topics discussed
                    2. Key insights and takeaways
                    3. Important guests or references mentioned
                    4. Overall themes and conclusions
                    Summary:
                """, 
            })

            summary = response["answer"]
            
            # Save summary to database
            self.database.update_episode_summary(episode_number, summary)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting summary for episode {episode_number}: {e}")
            return None
    
    def get_processed_episodes(self) -> List[Dict[str, Any]]:
        """Get list of episodes that have been processed."""
        try:
            return self.database.get_all_processed_episodes()
        except Exception as e:
            logger.error(f"Error getting processed episodes: {e}")
            return []

def get_langchain_rag_pipeline() -> LangChainRAGPipeline:
    """Get LangChain RAG pipeline instance."""
    try:
        return LangChainRAGPipeline()
    except ValueError as e:
        logger.error(f"Failed to initialize LangChain RAG pipeline: {e}")
        return None

def test_langchain_pipeline():
    """Test function to verify LangChain RAG pipeline functionality."""
    pipeline = get_langchain_rag_pipeline()
    
    if not pipeline:
        print("Failed to initialize LangChain RAG pipeline")
        return
    
    # Test getting available episodes
    episodes = pipeline.get_available_episodes()
    print(f"Found {len(episodes)} available episodes")
    
    if episodes:
        # Test processing first episode
        first_episode = episodes[0]
        print(f"Testing processing for episode {first_episode['episode_number']}: {first_episode['title']}")
        
        success = pipeline.process_episode(first_episode['episode_number'])
        print(f"Processing successful: {success}")
        
        if success:
            # Test getting summary
            summary = pipeline.get_episode_summary(first_episode['episode_number'])
            print(f"Summary: {summary}" if summary else "No summary available")
            
            # Test answering a question
            answer = pipeline.answer_question("What is this episode about?", first_episode['episode_number'])
            print(f"Answer: {answer}" if answer else "No answer available")

if __name__ == "__main__":
    test_langchain_pipeline() 