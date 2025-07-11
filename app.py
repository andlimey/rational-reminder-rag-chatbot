"""
Streamlit application for RAG Podcast Chatbot.
"""

import streamlit as st
import sys
import os
from typing import List, Dict, Any
import logging

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.langchain_rag_pipeline import LangChainRAGPipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="RAG Podcast Chatbot",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .episode-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #1f77b4;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .assistant-message {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
    }
    .status-success {
        color: #4caf50;
        font-weight: bold;
    }
    .status-error {
        color: #f44336;
        font-weight: bold;
    }
    .status-warning {
        color: #ff9800;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_rag_pipeline():
    """Get RAG pipeline instance with caching."""
    return LangChainRAGPipeline()

def main():
    """Main application function."""
    
    # Header
    st.markdown('<h1 class="main-header">🎙️ RAG Podcast Chatbot</h1>', unsafe_allow_html=True)
    st.markdown("### Chat with AI about Rational Reminder podcast episodes")
    
    # Initialize RAG pipeline
    try:
        pipeline = get_rag_pipeline()
    except Exception as e:
        st.error(f"Failed to initialize RAG pipeline: {e}")
        st.info("Please check your environment variables and try again.")
        return
    
    # Sidebar for episode selection
    with st.sidebar:
        st.header("📚 Episode Selection")
        
        # Get available episodes
        with st.spinner("Loading episodes..."):
            episodes = pipeline.get_available_episodes()
        
        if not episodes:
            st.error("No episodes found. Please check your internet connection.")
            return
        
        # Episode selection
        episode_options = {f"Episode {ep['episode_number']}: {ep['title']}": ep['episode_number'] 
                          for ep in episodes}
        
        selected_episode_label = st.selectbox(
            "Choose an episode:",
            options=list(episode_options.keys()),
            index=0
        )
        
        selected_episode_number = episode_options[selected_episode_label]
        selected_episode = next(ep for ep in episodes if ep['episode_number'] == selected_episode_number)
        
        # Display episode info
        st.markdown("### Episode Information")
        st.write(f"**Title:** {selected_episode['title']}")
        st.write(f"**Status:** {'✅ Processed' if selected_episode['processed'] else '⏳ Not Processed'}")
        
        # Process episode button
        if not selected_episode['processed']:
            if st.button("🔄 Process Episode", type="primary"):
                with st.spinner("Processing episode..."):
                    success = pipeline.process_episode(selected_episode_number)
                    if success:
                        st.success("Episode processed successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to process episode. Please try again.")
        
        # Episode summary
        if selected_episode['processed']:
            st.markdown("### 📝 Episode Summary")
            with st.spinner("Generating summary..."):
                summary = pipeline.get_episode_summary(selected_episode_number)
                if summary:
                    st.write(summary)
                else:
                    st.warning("Summary not available")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("💬 Chat with AI")
        
        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if selected_episode['processed']:
            if prompt := st.chat_input("Ask a question about this episode..."):
                # Add user message to chat history
                st.session_state.messages.append({"role": "user", "content": prompt})
                
                # Display user message
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                # Generate response
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        response = pipeline.answer_question(prompt, selected_episode_number)
                        st.markdown(response)
                
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": response})
        else:
            st.info("Please process the episode first to start chatting.")
        
        # Clear chat button
        if st.session_state.messages and st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.rerun()
    
    with col2:
        st.header("📊 Statistics")
        
        # Get processed episodes count
        processed_episodes = pipeline.get_processed_episodes()
        total_processed = len(processed_episodes)
        total_available = len(episodes)
        
        st.metric("Processed Episodes", total_processed, f"{total_processed}/{total_available}")
        
        # Recent processed episodes
        if processed_episodes:
            st.markdown("### Recently Processed")
            for episode in processed_episodes[:5]:  # Show last 5
                st.write(f"• Episode {episode['episode_number']}: {episode['title'][:30]}...")
        
        # Quick actions
        st.header("⚡ Quick Actions")
        
        if st.button("📋 View All Processed"):
            st.session_state.show_processed = True
        
        # Show processed episodes list
        if st.session_state.get("show_processed", False):
            st.markdown("### All Processed Episodes")
            for episode in processed_episodes:
                with st.expander(f"Episode {episode['episode_number']}: {episode['title']}"):
                    st.write(f"**Date:** {episode.get('date', 'Unknown')}")
                    st.write(f"**URL:** {episode.get('url', 'N/A')}")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
            <p>Built with ❤️ using Streamlit, LangChain, and OpenAI</p>
            <p>Data source: <a href='https://rationalreminder.ca' target='_blank'>Rational Reminder Podcast</a></p>
        </div>
        """,
        unsafe_allow_html=True
    )

def show_environment_setup():
    """Show environment setup instructions."""
    st.error("Environment Setup Required")
    st.markdown("""
    ### Required Environment Variables
    
    Create a `.env` file in the project directory with the following variables:
    
    ```
    OPENAI_API_KEY=your_openai_api_key_here
    SUPABASE_URL=your_supabase_url_here
    SUPABASE_KEY=your_supabase_anon_key_here
    ```
    
    ### Setup Instructions
    
    1. **Get OpenAI API Key:**
       - Sign up at [OpenAI](https://platform.openai.com/)
       - Create an API key in your dashboard
       - Add it to the `.env` file
    
    2. **Set up Supabase:**
       - Create a project at [Supabase](https://supabase.com/)
       - Get your project URL and anon key
       - Add them to the `.env` file
    
    3. **Install Dependencies:**
       ```bash
       pip install -r requirements.txt
       ```

    4. **Run the scraper:**
       ```bash
       python scrape_and_update_db.py
       ```
    
    5. **Run the Application:**
       ```bash
       streamlit run app.py
       ```
    """)

if __name__ == "__main__":
    # Check if required environment variables are set
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Check for OpenAI API key (required)
    if not os.getenv("OPENAI_API_KEY"):
        show_environment_setup()
    else:
        main() 