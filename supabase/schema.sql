-- AI Research Agent - Supabase Schema

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS research_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    topic TEXT NOT NULL,
    depth TEXT NOT NULL DEFAULT 'standard',
    subtopics JSONB DEFAULT '[]',
    markdown_content TEXT NOT NULL DEFAULT '',
    tasks JSONB DEFAULT '[]',
    quality JSONB DEFAULT '{}',
    search_results JSONB DEFAULT '[]',
    format TEXT NOT NULL DEFAULT 'markdown',
    status TEXT NOT NULL DEFAULT 'pending',
    error_message TEXT,
    pdf_url TEXT DEFAULT '',
    pptx_url TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS research_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id UUID REFERENCES research_reports(id) ON DELETE CASCADE,
    subtopic TEXT NOT NULL,
    summary TEXT,
    sources JSONB DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_research_reports_created_at
    ON research_reports(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_research_reports_status
    ON research_reports(status);

CREATE INDEX IF NOT EXISTS idx_research_tasks_report_id
    ON research_tasks(report_id);

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_research_reports_updated_at ON research_reports;
CREATE TRIGGER update_research_reports_updated_at
    BEFORE UPDATE ON research_reports
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_research_tasks_updated_at ON research_tasks;
CREATE TRIGGER update_research_tasks_updated_at
    BEFORE UPDATE ON research_tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Optional: create a public storage bucket named "reports" in Supabase Storage
-- for generated PDF/PPTX files.
