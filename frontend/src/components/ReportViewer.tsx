"use client"

import React from "react"
import { AlertCircle, RefreshCw } from "lucide-react"
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
      <Card className="w-full border-destructive">
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
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="mb-4 rounded-full bg-muted p-4">
          <AlertCircle className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold text-foreground">
          No Research Yet
        </h3>
        <p className="mt-2 max-w-sm text-sm text-muted-foreground">
          Enter a topic above and click Start Research to begin your AI-powered
          research.
        </p>
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
