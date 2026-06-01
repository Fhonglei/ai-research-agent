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
  status: 'pending' | 'searching' | 'summarizing' | 'complete' | 'error'
}

export interface ResearchReport {
  id: string
  topic: string
  subtopics: string[]
  markdown_content: string
  tasks: ResearchTask[]
  status: 'pending' | 'decomposing' | 'researching' | 'synthesizing' | 'complete' | 'error'
  error_message?: string
  created_at: string
}

export interface SSEEvent {
  type: string
  message: string
  data: Record<string, any>
}

export type ResearchDepth = 'quick' | 'standard' | 'deep'
