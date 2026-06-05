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
  ListChecks,
  Radio,
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
      return <CheckCircle2 className="h-4 w-4 text-emerald-600" />
    case "searching":
      return <Search className="h-4 w-4 animate-pulse text-primary" />
    case "summarizing":
      return <FileText className="h-4 w-4 animate-pulse text-amber-600" />
    case "pending":
      return <Clock className="h-4 w-4 text-muted-foreground" />
    case "error":
    case "failed":
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
    case "failed":
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
    case "failed":
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
      return "Breaking the topic into focused research tracks..."
    case "researching": {
      const activeTask = tasks.find(
        (t) => t.status === "searching" || t.status === "summarizing"
      )
      if (activeTask) {
        const action =
          activeTask.status === "searching" ? "Searching" : "Summarizing"
        return `${action}: "${activeTask.subtopic}"...`
      }
      return "Collecting sources and summaries for each track..."
    }
    case "synthesizing":
      return "Synthesizing findings into the final report..."
    case "complete":
      return "Research complete."
    case "error":
      return "Research stopped because an error occurred."
    default:
      return "Preparing research workspace..."
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
  const recentEvents = events.slice(-8)
  const firstRecentEventIndex = events.length - recentEvents.length

  return (
    <Card translate="no" className="notranslate w-full overflow-hidden shadow-sm">
      <CardHeader className="border-b bg-muted/35">
        <CardTitle className="flex items-center gap-2 text-base">
          {isComplete ? (
            <CheckCircle2 className="h-5 w-5 text-emerald-600" />
          ) : (
            <Loader2 className="h-5 w-5 animate-spin text-primary" />
          )}
          Live research progress
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6 p-5">
        {/* Progress Bar */}
        <div className="space-y-3">
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
            <div className="flex items-center justify-between">
              <h4 className="flex items-center gap-2 text-sm font-semibold text-foreground">
                <ListChecks className="h-4 w-4 text-primary" />
                Research tracks
              </h4>
              <Badge variant="outline" className="text-xs">
                {tasks.filter((task) => task.status === "complete").length}/{tasks.length}
              </Badge>
            </div>
            <ul className="space-y-2">
              {subtopics.map((subtopic, idx) => {
                const task = tasks.find((t) => t.subtopic === subtopic)
                const taskStatus = task ? task.status : "pending"

                return (
                  <li
                    key={`${subtopic}-${idx}`}
                    className={cn(
                      "flex items-center gap-3 rounded-md border px-3 py-3 text-sm transition-colors",
                      taskStatus === "searching" || taskStatus === "summarizing"
                        ? "border-primary/30 bg-primary/5"
                        : taskStatus === "complete"
                          ? "border-emerald-200 bg-emerald-50 dark:border-emerald-900 dark:bg-emerald-950"
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
          <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-12 text-center">
            <Brain className="mb-3 h-10 w-10 animate-pulse text-primary/60" />
            <p className="text-sm text-muted-foreground">
              Analyzing the topic and preparing research tracks.
            </p>
          </div>
        )}

        {/* Recent events log */}
        {events.length > 0 && (
          <div className="space-y-2">
            <h4 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              <Radio className="h-3.5 w-3.5" />
              Activity log
            </h4>
            <div className="max-h-52 space-y-2 overflow-y-auto rounded-md border bg-muted/40 p-3 text-xs">
              {recentEvents.map((event, idx) => (
                <div
                  key={`${firstRecentEventIndex + idx}-${event.type}`}
                  className="flex items-start gap-2 rounded bg-background/70 px-2 py-1.5 text-muted-foreground"
                >
                  <span className="mt-1 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-primary" />
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
