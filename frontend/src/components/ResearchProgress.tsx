"use client"

import React from "react"
import {
  Loader2,
  CheckCircle2,
  Search,
  Clock,
  AlertCircle,
  FileText,
  Brain,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import type { SSEEvent, ResearchTask } from "@/types"

interface ResearchProgressProps {
  events: SSEEvent[]
  status: string
  subtopics: string[]
  tasks: ResearchTask[]
}

function getStatusIcon(status: string) {
  switch (status) {
    case "complete":
      return <CheckCircle2 className="h-4 w-4 text-green-500" />
    case "searching":
      return <Search className="h-4 w-4 animate-pulse text-blue-500" />
    case "summarizing":
      return <FileText className="h-4 w-4 animate-pulse text-purple-500" />
    case "pending":
      return <Clock className="h-4 w-4 text-muted-foreground" />
    case "error":
      return <AlertCircle className="h-4 w-4 text-destructive" />
    default:
      return <Clock className="h-4 w-4 text-muted-foreground" />
  }
}

function getStatusBadgeVariant(status: string): "default" | "secondary" | "destructive" | "outline" {
  switch (status) {
    case "complete":
      return "default"
    case "searching":
    case "summarizing":
      return "secondary"
    case "error":
      return "destructive"
    default:
      return "outline"
  }
}

function getStatusLabel(status: string): string {
  switch (status) {
    case "pending":
      return "Pending"
    case "searching":
      return "Searching"
    case "summarizing":
      return "Summarizing"
    case "complete":
      return "Complete"
    case "error":
      return "Error"
    default:
      return "Unknown"
  }
}

function getProgressPercentage(status: string, tasks: ResearchTask[]): number {
  if (status === "complete") return 100
  if (status === "decomposing") return 10
  if (status === "error") return 0

  if (tasks.length === 0) return 20

  const completedTasks = tasks.filter((t) => t.status === "complete").length
  const searchingTasks = tasks.filter(
    (t) => t.status === "searching" || t.status === "summarizing"
  ).length

  // Weight completed tasks at 60% of progress, searching at 20%
  const completedPercent = (completedTasks / tasks.length) * 60
  const searchingPercent = (searchingTasks / tasks.length) * 20
  const basePercent = status === "synthesizing" ? 85 : 20

  return Math.min(Math.round(basePercent + completedPercent + searchingPercent), 95)
}

function getStatusMessage(status: string, subtopics: string[], tasks: ResearchTask[]): string {
  switch (status) {
    case "decomposing":
      return "Decomposing topic into subtopics..."
    case "researching": {
      const activeTask = tasks.find(
        (t) => t.status === "searching" || t.status === "summarizing"
      )
      if (activeTask) {
        const action =
          activeTask.status === "searching" ? "Searching" : "Summarizing"
        return `${action}: "${activeTask.subtopic}"...`
      }
      return "Researching subtopics..."
    }
    case "synthesizing":
      return "Synthesizing research into final report..."
    case "complete":
      return "Research complete!"
    case "error":
      return "An error occurred during research."
    default:
      return "Preparing..."
  }
}

export function ResearchProgress({
  events,
  status,
  subtopics,
  tasks,
}: ResearchProgressProps) {
  const progress = getProgressPercentage(status, tasks)
  const statusMessage = getStatusMessage(status, subtopics, tasks)
  const isComplete = status === "complete"

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          {isComplete ? (
            <CheckCircle2 className="h-5 w-5 text-green-500" />
          ) : (
            <Loader2 className="h-5 w-5 animate-spin text-primary" />
          )}
          Research Progress
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="font-medium text-foreground">{statusMessage}</span>
            <span className="text-muted-foreground">{progress}%</span>
          </div>
          <Progress
            value={progress}
            className={cn(isComplete && "[&>div]:bg-green-500")}
          />
        </div>

        {/* Subtopics List */}
        {subtopics.length > 0 && (
          <div className="space-y-3">
            <h4 className="text-sm font-semibold text-foreground">Subtopics</h4>
            <ul className="space-y-2">
              {subtopics.map((subtopic, idx) => {
                const task = tasks.find((t) => t.subtopic === subtopic)
                const taskStatus = task ? task.status : "pending"

                return (
                  <li
                    key={idx}
                    className={cn(
                      "flex items-center gap-3 rounded-md border px-3 py-2 text-sm transition-colors",
                      taskStatus === "searching" || taskStatus === "summarizing"
                        ? "border-blue-200 bg-blue-50 dark:border-blue-900 dark:bg-blue-950"
                        : taskStatus === "complete"
                          ? "border-green-200 bg-green-50 dark:border-green-900 dark:bg-green-950"
                          : "border-border bg-card"
                    )}
                  >
                    <div className="flex-shrink-0">
                      {getStatusIcon(taskStatus)}
                    </div>
                    <span className="flex-1 font-medium text-foreground">
                      {subtopic}
                    </span>
                    <Badge variant={getStatusBadgeVariant(taskStatus)} className="text-xs">
                      {getStatusLabel(taskStatus)}
                    </Badge>
                  </li>
                )
              })}
            </ul>
          </div>
        )}

        {/* Empty state when no subtopics yet */}
        {subtopics.length === 0 && status !== "complete" && (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <Brain className="mb-3 h-10 w-10 animate-pulse text-primary/50" />
            <p className="text-sm text-muted-foreground">
              Analyzing your topic and breaking it down...
            </p>
          </div>
        )}

        {/* Recent events log */}
        {events.length > 0 && (
          <div className="space-y-1">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Activity Log
            </h4>
            <div className="max-h-40 space-y-1 overflow-y-auto rounded-md bg-muted/50 p-3 text-xs">
              {events.slice(-8).map((event, idx) => (
                <div
                  key={idx}
                  className="flex items-start gap-2 text-muted-foreground"
                >
                  <span className="mt-0.5 flex-shrink-0 text-primary">&#9679;</span>
                  <span>{event.message}</span>
                </div>
              ))}
              {events.length === 0 && (
                <p className="text-muted-foreground">Waiting for events...</p>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
