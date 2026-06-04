"use client"

import { useState, useCallback, useEffect, Suspense } from "react"
import { useSearchParams } from "next/navigation"
import { Activity, CheckCircle2, Clock, Layers3, Search } from "lucide-react"
import { ResearchForm } from "@/components/ResearchForm"
import { ReportViewer } from "@/components/ReportViewer"
import { startResearch, getReport } from "@/lib/api"
import type { SSEEvent, ResearchTask, ResearchReport, ResearchDepth } from "@/types"

function statusLabel(status: string) {
  switch (status) {
    case "decomposing":
      return "Planning"
    case "researching":
      return "Researching"
    case "synthesizing":
      return "Synthesizing"
    case "complete":
      return "Complete"
    case "error":
      return "Needs attention"
    default:
      return "Ready"
  }
}

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
        if (event.data.subtopic) {
          setTasks((prev) =>
            prev.map((task) =>
              task.subtopic === event.data.subtopic ||
              task.id === `task-${event.data.index}`
                ? { ...task, status: "searching" as const }
                : task
            )
          )
        }
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
                    status:
                      event.data.status === "failed" || event.data.status === "error"
                        ? "error" as const
                        : "complete" as const,
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

  const completedTasks = tasks.filter((task) => task.status === "complete").length
  const hasActiveResearch = status !== "pending" || Boolean(report)

  return (
    <div className="min-h-[calc(100vh-121px)] bg-[radial-gradient(circle_at_top_left,hsl(var(--primary)/0.08),transparent_34rem)]">
      <div className="mx-auto grid max-w-7xl gap-6 px-4 py-6 lg:grid-cols-[390px_minmax(0,1fr)] lg:py-8">
        <aside className="space-y-4 lg:sticky lg:top-24 lg:self-start">
          <div className="space-y-3">
            <div className="inline-flex items-center gap-2 rounded-full border bg-background/80 px-3 py-1 text-xs font-medium text-muted-foreground shadow-sm backdrop-blur">
              <Activity className="h-3.5 w-3.5 text-primary" />
              Research workspace
            </div>
            <div>
              <h1 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
                Turn a question into a sourced research brief.
              </h1>
              <p className="mt-3 text-sm leading-6 text-muted-foreground">
                Define the topic, pick a depth, then monitor decomposition,
                source gathering, synthesis, and export from one focused view.
              </p>
            </div>
          </div>

          <ResearchForm onSubmit={handleSubmit} isLoading={isLoading} />

          <div className="grid grid-cols-3 gap-2 rounded-lg border bg-card p-2 shadow-sm">
            <div className="rounded-md bg-muted/60 p-3">
              <Clock className="mb-2 h-4 w-4 text-muted-foreground" />
              <div className="text-xs text-muted-foreground">Status</div>
              <div className="mt-1 truncate text-sm font-semibold">
                {statusLabel(status)}
              </div>
            </div>
            <div className="rounded-md bg-muted/60 p-3">
              <Layers3 className="mb-2 h-4 w-4 text-muted-foreground" />
              <div className="text-xs text-muted-foreground">Topics</div>
              <div className="mt-1 text-sm font-semibold">{subtopics.length}</div>
            </div>
            <div className="rounded-md bg-muted/60 p-3">
              <CheckCircle2 className="mb-2 h-4 w-4 text-muted-foreground" />
              <div className="text-xs text-muted-foreground">Done</div>
              <div className="mt-1 text-sm font-semibold">
                {completedTasks}/{tasks.length || 0}
              </div>
            </div>
          </div>
        </aside>

        <section className="min-w-0">
          {!hasActiveResearch && (
            <div className="mb-4 grid gap-3 sm:grid-cols-3">
              {[
                "Market landscape for AI-native research tools",
                "Competitive analysis of browser automation agents",
                "Risks and opportunities for small language models",
              ].map((example) => (
                <div
                  key={example}
                  className="rounded-lg border bg-card/80 p-4 text-sm text-muted-foreground shadow-sm"
                >
                  <Search className="mb-3 h-4 w-4 text-primary" />
                  {example}
                </div>
              ))}
            </div>
          )}

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
        </section>
      </div>
    </div>
  )
}

export default function HomePage() {
  return (
    <Suspense
      fallback={
        <div className="mx-auto max-w-7xl space-y-8 px-4 py-8">
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
