export interface Source {
  url: string
  title: string
  snippet: string
  content?: string
}

export interface ResearchTask {
  id: string
  subtopic: string
  summary: string
  sources: Source[]
  status: 'pending' | 'searching' | 'summarizing' | 'complete' | 'failed' | 'error'
}

export interface ResearchQuality {
  source_count: number
  unique_domain_count: number
  citation_count: number
  citation_coverage: number
  success_rate: number
  confidence_score: number
  warnings: string[]
}

export interface ResearchReport {
  id: string
  topic: string
  subtopics: string[]
  markdown_content: string
  tasks: ResearchTask[]
  quality?: ResearchQuality | null
  depth: string
  status: 'pending' | 'in_progress' | 'decomposing' | 'researching' | 'synthesizing' | 'complete' | 'failed' | 'error'
  error_message?: string
  created_at: string
  pdf_available?: boolean
  pptx_available?: boolean
}

export interface SSEEvent {
  type: string
  message: string
  data: Record<string, any>
}

export type ResearchDepth = 'quick' | 'standard' | 'deep'
