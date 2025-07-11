# 🎙️ RAG Podcast Chatbot

A Streamlit-based RAG (Retrieval-Augmented Generation) chatbot for the [Rational Reminder podcast](https://rationalreminder.ca). This application allows users to select episodes and chat with an AI about the episode content.

## ✨ Features

- **📚 Episode Selection**: Browse and select episodes from the Rational Reminder podcast directory
- **🗄️ Vector Database Storage**: Store episode content in Supabase for efficient retrieval
- **💬 RAG Chat Interface**: Chat with an AI about episode content using LangChain
- **📝 Episode Summaries**: Generate and display AI-powered episode summaries
- **📊 Progress Tracking**: Monitor which episodes have been processed

## 🚀 Quick Start

### Prerequisites

- Python 3.13 or higher
- OpenAI API key
- Supabase account for persistent storage

### Installation

1. **Clone or download the project**

   ```bash
   cd rational-reminder-rag-chatbot
   ```

2. **Configure environment variables**

   Create a `.env` file and add your API keys:

   ```bash
   cp .env.example .env
   ```

   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   SUPABASE_URL=your_supabase_url_here  # Optional
   SUPABASE_KEY=your_supabase_key_here  # Optional
   ```

3. **Create a virtual environment and install dependencies**

   ```bash
   python3 -m venv .venv
   source venv/bin/activate
   pip3 install -r requirements.txt
   ```

4. **Setup Supabase**

   Create a project in Supabase and run the schema in `database_schema.sql` in the SQL Editor.

5. **Run the application**

   ```bash
   streamlit run app.py
   ```

6. **Open your browser**

   The application will open at `http://localhost:8501`

## 📖 Usage

### 1. Scrape the Rational Reminder website

- Run the following:

```bash
python3 scrape_and_update_db.py
```

- This will scrape the Rational Reminder podcast [directory](https://rationalreminder.ca/podcast-directory) and process each episode.
- The script will store the episode's title, URL and transcript to Supabase for future processing.
- If new episodes are released, re-run the scraper to update the database.

### 2. Select an Episode

- Use the sidebar to browse available episodes
- Green checkmarks indicate already processed episodes

### 3. Process an Episode

- Click "Process Episode" for unprocessed episodes
- The app will:
  - Create vector embeddings from the transcript
  - Store everything in the database

### 4. Chat with AI

- Once processed, you can ask questions about the episode
- The AI will search through the episode content to find relevant answers
- Chat history is maintained during your session

### 5. View Summaries

- Processed episodes show AI-generated summaries
- Summaries highlight key topics, insights, and takeaways

## 🏗️ Architecture

```
rag-podcast-chatbot/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── env.example           # Environment variables template
├── README.md             # This file
├── src/
│   ├── __init__.py
│   ├── scraper.py        # Web scraping utilities
│   ├── database.py       # Database operations (Supabase)
│   └── langchain_rag_pipeline.py   # RAG pipeline orchestration
```

### Core Components

- **PodcastScraper**: Extracts episode information and transcripts from the website
- **PodcastDatabase**: Manages episode storage and vector embeddings
- **RAGPipeline**: Orchestrates the entire RAG workflow

## 🔧 Configuration

### Environment Variables

| Variable         | Required | Description                                         |
| ---------------- | -------- | --------------------------------------------------- |
| `OPENAI_API_KEY` | Yes      | Your OpenAI API key                                 |
| `SUPABASE_URL`   | No       | Supabase project URL (uses mock DB if not provided) |
| `SUPABASE_KEY`   | No       | Supabase anonymous key                              |

## 🗄️ Database Setup

1. **Create a Supabase project** at [supabase.com](https://supabase.com)
2. **Enable the pgvector extension** in your database
3. **Create the required tables**:
4. **Add your Supabase credentials** to the `.env` file

## 🐛 Troubleshooting

### Debug Mode

Enable debug logging by modifying the logging level in any module:

```python
logging.basicConfig(level=logging.DEBUG)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- [Rational Reminder Podcast](https://rationalreminder.ca) for the content
- [Streamlit](https://streamlit.io) for the web framework
- [LangChain](https://langchain.com) for the RAG framework
- [OpenAI](https://openai.com) for the AI models
- [Supabase](https://supabase.com) for the database
