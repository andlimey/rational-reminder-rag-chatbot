-- Database schema for RAG Podcast Chatbot
-- Run this in your Supabase SQL editor

-- Database schema for RAG Podcast Chatbot
CREATE TABLE IF NOT EXISTS episodes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    episode_number INTEGER UNIQUE NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    summary TEXT,
    transcript TEXT[],
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    published_date TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_episodes_episode_number ON episodes(episode_number);
CREATE INDEX IF NOT EXISTS idx_episode_embeddings_episode_id ON episode_embeddings(episode_id);
CREATE INDEX IF NOT EXISTS idx_episode_embeddings_chunk_index ON episode_embeddings(chunk_index);


-- https://supabase.com/docs/guides/ai/langchain?queryGroups=database-method&database-method=dashboard
-- Enable the pgvector extension to work with embedding vectors
create extension vector;

-- Create a table to store your documents
create table documents (
  id uuid primary key,
  content text, -- corresponds to Document.pageContent
  metadata jsonb, -- corresponds to Document.metadata
  embedding vector(1536) -- 1536 works for OpenAI embeddings, change if needed
);

-- Create a function to search for documents
create function match_documents (
  query_embedding vector(1536),
  match_count int default null,
  filter jsonb DEFAULT '{}'
) returns table (
  id uuid,
  content text,
  metadata jsonb,
  similarity float
)
language plpgsql
as $$
#variable_conflict use_column
begin
  return query
  select
    id,
    content,
    metadata,
    1 - (documents.embedding <=> query_embedding) as similarity
  from documents
  where metadata @> filter
  order by documents.embedding <=> query_embedding
  limit match_count;
end;
$$;