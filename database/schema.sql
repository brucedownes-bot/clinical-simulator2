-- Adaptive Clinical Decision Simulator - Database Schema
-- Run this in Supabase SQL Editor

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Documents table
CREATE TABLE documents (
    id BIGSERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    uploaded_by UUID,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    document_type TEXT CHECK (document_type IN ('guideline', 'protocol', 'textbook')),
    specialty TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

-- Document chunks with embeddings
CREATE TABLE document_chunks (
    id BIGSERIAL PRIMARY KEY,
    document_id BIGINT REFERENCES documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding VECTOR(1536) NOT NULL,
    page_number INTEGER,
    section_header TEXT,
    chunk_type TEXT CHECK (chunk_type IN ('standard', 'exception', 'contraindication', 'special_population')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User mastery tracking
CREATE TABLE user_document_mastery (
    user_id UUID,
    document_id BIGINT REFERENCES documents(id) ON DELETE CASCADE,
    current_level INTEGER DEFAULT 1 CHECK (current_level BETWEEN 1 AND 5),
    questions_answered INTEGER DEFAULT 0,
    questions_correct INTEGER DEFAULT 0,
    avg_score FLOAT DEFAULT 0.0,
    clinical_accuracy_avg FLOAT DEFAULT 0.0,
    risk_assessment_avg FLOAT DEFAULT 0.0,
    communication_avg FLOAT DEFAULT 0.0,
    efficiency_avg FLOAT DEFAULT 0.0,
    last_active TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (user_id, document_id)
);

-- Questions generated
CREATE TABLE questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id BIGINT REFERENCES documents(id) ON DELETE CASCADE,
    user_id UUID,
    vignette TEXT NOT NULL,
    question_text TEXT NOT NULL,
    difficulty_level INTEGER CHECK (difficulty_level BETWEEN 1 AND 5),
    source_chunk_ids BIGINT[] NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    was_answered BOOLEAN DEFAULT FALSE
);

-- User answers
CREATE TABLE answers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id UUID REFERENCES questions(id) ON DELETE CASCADE,
    user_id UUID,
    answer_text TEXT NOT NULL,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    total_score FLOAT CHECK (total_score BETWEEN 0 AND 10),
    clinical_accuracy_score FLOAT CHECK (clinical_accuracy_score BETWEEN 0 AND 4),
    risk_assessment_score FLOAT CHECK (risk_assessment_score BETWEEN 0 AND 3),
    communication_score FLOAT CHECK (communication_score BETWEEN 0 AND 2),
    efficiency_score FLOAT CHECK (efficiency_score BETWEEN 0 AND 1),
    ai_feedback TEXT,
    level_before INTEGER,
    level_after INTEGER,
    level_change INTEGER CHECK (level_change BETWEEN -1 AND 1)
);

-- Indexes for performance
CREATE INDEX idx_chunks_embedding ON document_chunks 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX idx_chunks_document_id ON document_chunks(document_id);
CREATE INDEX idx_questions_user_id ON questions(user_id);
CREATE INDEX idx_answers_user_id ON answers(user_id);
