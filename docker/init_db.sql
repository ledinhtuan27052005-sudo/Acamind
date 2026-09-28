-- Bật pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Bảng users
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Bảng documents (metadata PDF)
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000) NOT NULL,
    title VARCHAR(1000),
    authors TEXT,
    year INTEGER,
    total_pages INTEGER,
    status VARCHAR(50) DEFAULT 'processing',
    category VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Bảng chunks (văn bản + vector embedding)
CREATE TABLE IF NOT EXISTS chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding vector(768),
    page_number INTEGER,
    chunk_index INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index HNSW để tìm kiếm vector nhanh (O log n thay vì O n)
CREATE INDEX IF NOT EXISTS chunks_embedding_idx
ON chunks USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Bảng user profiles (onboarding quiz)
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    user_type VARCHAR(50) DEFAULT 'patient',
    onboarding_done BOOLEAN DEFAULT FALSE,
    answers JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Bảng khai báo triệu chứng 3D
CREATE TABLE IF NOT EXISTS body_symptoms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    region_id VARCHAR(100) NOT NULL,
    region_name VARCHAR(255),
    description TEXT NOT NULL,
    pain_level INTEGER CHECK (pain_level BETWEEN 1 AND 10),
    duration VARCHAR(255),
    reported_at TIMESTAMP DEFAULT NOW()
);

-- Bảng quiz
CREATE TABLE IF NOT EXISTS quiz_sets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    title VARCHAR(500),
    question_type VARCHAR(50) DEFAULT 'mixed',
    difficulty VARCHAR(20) DEFAULT 'medium',
    language VARCHAR(10) DEFAULT 'vi',
    total_questions INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS quiz_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quiz_set_id UUID REFERENCES quiz_sets(id) ON DELETE CASCADE,
    question_index INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    question_type VARCHAR(20) DEFAULT 'mcq',
    options JSONB,
    correct_answer VARCHAR(500) NOT NULL,
    explanation TEXT,
    source_text TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS quiz_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quiz_set_id UUID REFERENCES quiz_sets(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    started_at TIMESTAMP DEFAULT NOW(),
    submitted_at TIMESTAMP,
    deadline TIMESTAMP,
    status VARCHAR(20) DEFAULT 'in_progress',
    score NUMERIC(5,2),
    total_correct INTEGER DEFAULT 0,
    time_spent_seconds INTEGER
);

CREATE TABLE IF NOT EXISTS quiz_answers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    attempt_id UUID REFERENCES quiz_attempts(id) ON DELETE CASCADE,
    question_id UUID REFERENCES quiz_questions(id) ON DELETE CASCADE,
    user_answer VARCHAR(500),
    is_correct BOOLEAN,
    is_flagged BOOLEAN DEFAULT FALSE,
    answered_at TIMESTAMP
);

-- Lịch sử chat (tự động lưu khi user hỏi đáp)
CREATE TABLE IF NOT EXISTS chat_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    answer TEXT NOT NULL,
    document_ids JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW()
);

-- AI insights (phân tích sức khỏe từ triệu chứng)
CREATE TABLE IF NOT EXISTS ai_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    insight_type VARCHAR(50) DEFAULT 'health_summary',
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);
