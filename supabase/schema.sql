-- ============================================
-- AI Research Agent — Supabase Schema
-- ============================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Research reports table
CREATE TABLE research_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    topic TEXT NOT NULL,
    subtopics JSONB DEFAULT '[]',
    markdown_content TEXT NOT NULL DEFAULT '',
    search_results JSONB DEFAULT '[]',
    format TEXT NOT NULL DEFAULT 'markdown',
    status TEXT NOT NULL DEFAULT 'pending',
    -- status: pending, decomposing, researching, synthesizing, complete, error
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Research tasks (individual subtopics)
CREATE TABLE research_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id UUID REFERENCES research_reports(id) ON DELETE CASCADE,
    subtopic TEXT NOT NULL,
    summary TEXT,
    sources JSONB DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'pending',
    -- status: pending, searching, summarizing, complete, error
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for faster queries
CREATE INDEX idx_research_reports_created_at ON research_reports(created_at DESC);
CREATE INDEX idx_research_tasks_report_id ON research_tasks(report_id);

-- Updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_research_reports_updated_at
    BEFORE UPDATE ON research_reports
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_research_tasks_updated_at
    BEFORE UPDATE ON research_tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
