"use client"

import React from "react"
import { AlertCircle, RefreshCw, Search, Sparkles } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ResearchProgress } from "@/components/ResearchProgress"
import { ResearchReport } from "@/components/ResearchReport"
import type { SSEEvent, ResearchTask, ResearchReport as ResearchReportType } from "@/types"

interface ReportViewerProps {
  status: string
  events: SSEEvent[]
  report: ResearchReportType | null
  error: string | null
  subtopics: string[]
  tasks: ResearchTask[]
  onRetry?: () => void
}

export function ReportViewer({
  status,
  events,
  report,
  error,
  subtopics,
  tasks,
  onRetry,
}: ReportViewerProps) {
  // Error state
  if (error || status === "error") {
    return (
      <Card className="w-full border-destructive shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg text-destructive">
            <AlertCircle className="h-5 w-5" />
            Research Error
          </CardTitle>
          <CardDescription>
            Something went wrong during the research process.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-md bg-destructive/10 p-4">
            <p className="text-sm text-destructive">
              {error || "An unknown error occurred. Please try again."}
            </p>
          </div>
          {onRetry && (
            <Button variant="outline" onClick={onRetry} className="gap-2">
              <RefreshCw className="h-4 w-4" />
              Try Again
            </Button>
          )}
        </CardContent>
      </Card>
    )
  }

  // No research started yet
  if (status === "pending" || (!status && !report)) {
    return (
      <div className="flex min-h-[520px] flex-col items-center justify-center rounded-lg border border-dashed bg-card/70 px-6 py-16 text-center shadow-sm">
        <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-lg bg-primary/10">
          <Sparkles className="h-7 w-7 text-primary" />
        </div>
        <h3 className="text-xl font-semibold text-foreground">
          Ready for a research run
        </h3>
        <p className="mt-2 max-w-md text-sm leading-6 text-muted-foreground">
          Enter a topic on the left. Progress, source gathering, final report,
          and downloads will appear here.
        </p>
        <div className="mt-6 flex items-center gap-2 rounded-full border bg-background px-3 py-1 text-xs text-muted-foreground">
          <Search className="h-3.5 w-3.5" />
          Waiting for a topic
        </div>
      </div>
    )
  }

  // Research complete with report
  if (status === "complete" && report) {
    return <ResearchReport report={report} />
  }

  // Research in progress
  return (
    <ResearchProgress
      events={events}
      status={status}
      subtopics={subtopics}
      tasks={tasks}
    />
  )
}
