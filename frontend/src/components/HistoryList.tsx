"use client"

import React, { useEffect, useState } from "react"
import Link from "next/link"
import {
  FileText,
  Plus,
  Clock,
  CheckCircle2,
  AlertCircle,
  Search,
  ChevronRight,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { getHistory } from "@/lib/api"
import type { ResearchReport } from "@/types"

export function HistoryList() {
  const [reports, setReports] = useState<ResearchReport[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function fetchHistory() {
      setIsLoading(true)
      setError(null)
      try {
        const data = await getHistory()
        if (!cancelled) {
          setReports(data)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load history")
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false)
        }
      }
    }

    fetchHistory()

    return () => {
      cancelled = true
    }
  }, [])

  function getStatusBadge(status: string) {
    switch (status) {
      case "complete":
        return (
          <Badge variant="default" className="gap-1">
            <CheckCircle2 className="h-3 w-3" />
            Complete
          </Badge>
        )
      case "error":
        return (
          <Badge variant="destructive" className="gap-1">
            <AlertCircle className="h-3 w-3" />
            Error
          </Badge>
        )
      default:
        return (
          <Badge variant="secondary" className="gap-1">
            <Clock className="h-3 w-3" />
            In Progress
          </Badge>
        )
    }
  }

  function formatDate(dateStr: string): string {
    if (!dateStr) return "Unknown date"
    const date = new Date(dateStr)
    if (Number.isNaN(date.getTime())) return "Unknown date"
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return "Just now"
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    })
  }

  // Loading skeleton
  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-foreground">Research History</h2>
          <Skeleton className="h-10 w-32" />
        </div>
        <div className="space-y-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={i}>
              <CardContent className="p-6">
                <div className="space-y-3">
                  <Skeleton className="h-6 w-3/4" />
                  <Skeleton className="h-4 w-1/2" />
                  <div className="flex gap-2">
                    <Skeleton className="h-5 w-20" />
                    <Skeleton className="h-5 w-16" />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-foreground">Research History</h2>
          <Link href="/">
            <Button variant="outline" size="sm" className="gap-2">
              <Plus className="h-4 w-4" />
              New Research
            </Button>
          </Link>
        </div>
        <Card className="border-destructive">
          <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
            <AlertCircle className="h-10 w-10 text-destructive" />
            <p className="text-sm text-muted-foreground">{error}</p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => window.location.reload()}
            >
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Empty state
  if (reports.length === 0) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-foreground">Research History</h2>
          <Link href="/">
            <Button variant="outline" size="sm" className="gap-2">
              <Plus className="h-4 w-4" />
              New Research
            </Button>
          </Link>
        </div>
        <Card>
          <CardContent className="flex flex-col items-center gap-4 py-16 text-center">
            <div className="rounded-full bg-muted p-4">
              <Search className="h-8 w-8 text-muted-foreground" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-foreground">
                No Research Yet
              </h3>
              <p className="mt-2 max-w-sm text-sm text-muted-foreground">
                Your research history will appear here. Start your first research
                to see results.
              </p>
            </div>
            <Link href="/">
              <Button className="gap-2">
                <Plus className="h-4 w-4" />
                Start First Research
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    )
  }

  // History list
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-foreground">
          Research History
          <span className="ml-2 text-sm font-normal text-muted-foreground">
            ({reports.length})
          </span>
        </h2>
        <Link href="/">
          <Button variant="default" size="sm" className="gap-2">
            <Plus className="h-4 w-4" />
            New Research
          </Button>
        </Link>
      </div>

      <div className="space-y-3">
        {reports.map((report) => (
          <Link
            key={report.id}
            href={`/?report=${report.id}`}
            className="block transition-transform duration-150 hover:scale-[1.01]"
          >
            <Card className="cursor-pointer border-2 transition-colors hover:border-primary/30 hover:shadow-md">
              <CardContent className="flex items-center justify-between p-5">
                <div className="min-w-0 flex-1 space-y-1.5">
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 flex-shrink-0 text-primary" />
                    <h3 className="truncate text-base font-semibold text-foreground">
                      {report.topic}
                    </h3>
                  </div>
                  <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {formatDate(report.created_at)}
                    </span>
                    <span>
                      {report.subtopics.length}{" "}
                      {report.subtopics.length === 1 ? "subtopic" : "subtopics"}
                    </span>
                    {getStatusBadge(report.status)}
                  </div>
                </div>
                <ChevronRight className="ml-4 h-5 w-5 flex-shrink-0 text-muted-foreground" />
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}
