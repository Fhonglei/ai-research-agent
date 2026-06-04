import { ResearchReport, SSEEvent, ResearchDepth } from '@/types'

export function getApiUrl(): string {
  if (typeof window !== 'undefined') {
    const stored = localStorage.getItem('api_url')
    if (stored) return stored
  }
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
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
          const jsonStr = trimmed.slice(6)
          if (jsonStr === '[DONE]') {
            return
          }
          const event = parseSSEEvent(currentEventType, jsonStr)
          onEvent(event)
          currentEventType = 'message'
          continue
        }

        // Empty line signals the end of an event; reset.
        if (trimmed === '') {
          currentEventType = 'message'
        }
      }
    }

    const remaining = buffer.trim()
    if (remaining.startsWith('data: ')) {
      const jsonStr = remaining.slice(6)
      if (jsonStr && jsonStr !== '[DONE]') {
        const event = parseSSEEvent(currentEventType, jsonStr)
        onEvent(event)
      }
    }
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
      markdown_content: r.markdown_content ?? '',
      status: r.status ?? 'complete',
      created_at: r.created_at ?? '',
    }))
  }
  return []
}
