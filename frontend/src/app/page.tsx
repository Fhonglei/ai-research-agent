"use client"

import { useState, useCallback, useEffect, Suspense } from "react"
import { useSearchParams } from "next/navigation"
import { ResearchForm } from "@/components/ResearchForm"
import { ReportViewer } from "@/components/ReportViewer"
import { startResearch, getReport } from "@/lib/api"
import type { SSEEvent, ResearchTask, ResearchReport, ResearchDepth } from "@/types"

function HomePageInner() {
  const searchParams = useSearchParams()

  const [topic, setTopic] = useState("")
  const [status, setStatus] = useState<string>("pending")
  const [isLoading, setIsLoading] = useState(false)
  const [events, setEvents] = useState<SSEEvent[]>([])
  const [report, setReport] = useState<ResearchReport | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [subtopics, setSubtopics] = useState<string[]>([])
  const [tasks, setTasks] = useState<ResearchTask[]>([])

  // Reset state for new research
  const resetState = useCallback(() => {
    setStatus("pending")
    setIsLoading(false)
    setEvents([])
    setReport(null)
    setError(null)
    setSubtopics([])
    setTasks([])
  }, [])

  // Handle SSE events from backend (event types: decomposing, decomposed,
  // researching, task_complete, synthesizing, generating_files, saving, complete, error)
  const handleEvent = useCallback((event: SSEEvent) => {
    setEvents((prev) => [...prev, event])

    switch (event.type) {
      case "decomposing":
        setStatus("decomposing")
        break

      case "decomposed":
        if (event.data.subtopics) {
          setSubtopics(event.data.subtopics)
          // Initialize tasks from the subtopics list
          setTasks(
            event.data.subtopics.map((st: string, i: number) => ({
              id: `task-${i}`,
              subtopic: st,
              summary: "",
              sources: [],
              status: "pending" as const,
            }))
          )
          setStatus("researching")
        }
        break

      case "researching":
        setStatus("researching")
        break

      case "task_complete":
        if (event.data.task_id || event.data.subtopic) {
          setTasks((prev) =>
            prev.map((t) =>
              t.id === (event.data.task_id || `task-${event.data.index}`) ||
              t.subtopic === event.data.subtopic
                ? {
                    ...t,
                    id: event.data.task_id || t.id,
                    status: event.data.status === "failed" ? "error" as const : "complete" as const,
                  }
                : t
            )
          )
        }
        break

      case "synthesizing":
        setStatus("synthesizing")
        break

      case "generating_files":
        // File generation in progress
        break

      case "saving":
        // Saving to database in progress
        break

      case "complete":
        setStatus("complete")
        if (event.data) {
          setReport({
            id: event.data.report_id || "",
            topic: event.data.topic || topic,
            subtopics: event.data.subtopics || subtopics,
            markdown_content: event.data.markdown_content || "",
            tasks: tasks,
            status: "complete",
            created_at: event.data.created_at || new Date().toISOString(),
          })
        }
        break

      case "error":
        setStatus("error")
        setError(event.message || event.data?.message || "An error occurred during research")
        break

      default:
        break
    }
  }, [topic, subtopics, tasks])

  // Handle form submission
  const handleSubmit = useCallback(
    async (newTopic: string, depth: ResearchDepth) => {
      resetState()
      setTopic(newTopic)
      setIsLoading(true)
      setStatus("decomposing")

      try {
        await startResearch(newTopic, depth, handleEvent)
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to connect to research server"
        )
        setStatus("error")
      } finally {
        setIsLoading(false)
      }
    },
    [handleEvent, resetState]
  )

  // Load report by ID from query params
  useEffect(() => {
    const reportId = searchParams.get("report")
    if (!reportId) return

    let cancelled = false

    async function loadReport() {
      setIsLoading(true)
      setError(null)
      try {
        const data = await getReport(reportId!)
        if (!cancelled) {
          setReport(data)
          setStatus(data.status)
          setTopic(data.topic)
          setSubtopics(data.subtopics)
          setTasks(data.tasks)
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Failed to load report"
          )
          setStatus("error")
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false)
        }
      }
    }

    loadReport()

    return () => {
      cancelled = true
    }
  }, [searchParams])

  return (
    <div className="mx-auto max-w-4xl space-y-8 px-4 py-8">
      {/* Research Form */}
      <ResearchForm onSubmit={handleSubmit} isLoading={isLoading} />

      {/* Report or Progress */}
      <ReportViewer
        status={status}
        events={events}
        report={report}
        error={error}
        subtopics={subtopics}
        tasks={tasks}
        onRetry={() => {
          if (topic) {
            handleSubmit(topic, "standard")
          } else {
            resetState()
          }
        }}
      />
    </div>
  )
}

export default function HomePage() {
  return (
    <Suspense
      fallback={
        <div className="mx-auto max-w-4xl space-y-8 px-4 py-8">
          <div className="flex items-center justify-center py-20">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          </div>
        </div>
      }
    >
      <HomePageInner />
    </Suspense>
  )
}
