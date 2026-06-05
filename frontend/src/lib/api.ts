import { ResearchReport, SSEEvent, ResearchDepth } from '@/types'

const DEFAULT_API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export function getApiUrl(): string {
  if (typeof window !== 'undefined') {
    const stored = localStorage.getItem('api_url')
    if (stored) {
      try {
        const storedUrl = new URL(stored)
        const currentUrl = new URL(window.location.href)
        const pointsToFrontend =
          storedUrl.hostname === currentUrl.hostname &&
          storedUrl.port === currentUrl.port

        if (!pointsToFrontend) {
          return storedUrl.toString().replace(/\/$/, '')
        }

        localStorage.removeItem('api_url')
      } catch {
        localStorage.removeItem('api_url')
      }
    }
  }
  return DEFAULT_API_URL
}

export async function getHealth(): Promise<{
  status: string
  version: string
  provider: string
  model: string
  llm_configured: boolean
  tavily_configured: boolean
  supabase_configured: boolean
}> {
  const apiUrl = getApiUrl()
  const response = await fetch(`${apiUrl}/api/health`)
  if (!response.ok) {
    const errorText = await response.text().catch(() => 'Unknown error')
    throw new Error(`Health check failed: ${response.status} ${errorText}`)
  }
  return response.json()
}

/**
 * Parse Server-Sent Events stream. The wire format is:
 *   event: <event_type>
 *   data: <json_payload>
 */
function parseSSEEvent(eventType: string, dataStr: string): SSEEvent {
  try {
    const payload = JSON.parse(dataStr)
    return {
      type: eventType || payload.type || 'unknown',
      message: payload.message || '',
      data: payload,
    }
  } catch {
    return {
      type: eventType || 'parse_error',
      message: dataStr,
      data: {},
    }
  }
}

export async function startResearch(
  topic: string,
  depth: ResearchDepth,
  onEvent: (event: SSEEvent) => void
): Promise<void> {
  const apiUrl = getApiUrl()
  const response = await fetch(`${apiUrl}/api/research`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ topic, depth }),
  })

  if (!response.ok) {
    const errorText = await response.text().catch(() => 'Unknown error')
    throw new Error(`Research request failed: ${response.status} ${errorText}`)
  }

  if (!response.body) {
    throw new Error('Response body is not readable')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let currentEventType = 'message'
  let currentDataLines: string[] = []

  const flushEvent = () => {
    if (currentDataLines.length === 0) return
    const jsonStr = currentDataLines.join('\n')
    currentDataLines = []
    if (jsonStr === '[DONE]') return
    const event = parseSSEEvent(currentEventType, jsonStr)
    onEvent(event)
    currentEventType = 'message'
  }

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        const trimmed = line.trim()

        if (trimmed.startsWith('event: ')) {
          currentEventType = trimmed.slice(7).trim()
          continue
        }

        if (trimmed.startsWith('data: ')) {
          currentDataLines.push(trimmed.slice(6))
          continue
        }

        // Empty line signals end of an event — flush accumulated data
        if (trimmed === '') {
          flushEvent()
        }
      }
    }

    // Flush any remaining data in buffer
    if (buffer.trim()) {
      buffer.split('\n').forEach((line) => {
        const trimmed = line.trim()
        if (trimmed.startsWith('data: ')) {
          currentDataLines.push(trimmed.slice(6))
        }
      })
    }
    flushEvent()
  } finally {
    reader.releaseLock()
  }
}

export async function getReport(reportId: string): Promise<ResearchReport> {
  const apiUrl = getApiUrl()
  const response = await fetch(`${apiUrl}/api/report/${reportId}`)

  if (!response.ok) {
    const errorText = await response.text().catch(() => 'Unknown error')
    throw new Error(`Failed to fetch report: ${response.status} ${errorText}`)
  }

  return response.json()
}

export function getDownloadUrl(reportId: string, format: 'pdf' | 'pptx'): string {
  const apiUrl = getApiUrl()
  return `${apiUrl}/api/report/${reportId}/download?format=${format}`
}

export async function getHistory(): Promise<ResearchReport[]> {
  const apiUrl = getApiUrl()
  const response = await fetch(`${apiUrl}/api/history`)

  if (!response.ok) {
    const errorText = await response.text().catch(() => 'Unknown error')
    throw new Error(`Failed to fetch history: ${response.status} ${errorText}`)
  }

  const body = await response.json()
  if (Array.isArray(body)) {
    return body
  }
  if (body && Array.isArray(body.reports)) {
    return body.reports.map((r: ResearchReport) => ({
      ...r,
      subtopics: r.subtopics ?? [],
      tasks: r.tasks ?? [],
      depth: r.depth ?? 'standard',
      markdown_content: r.markdown_content ?? '',
      status: r.status ?? 'complete',
      created_at: r.created_at ?? '',
    }))
  }
  return []
}
