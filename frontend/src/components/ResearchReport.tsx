"use client"

import React, { useState } from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import {
  FileText,
  Link2,
  Download,
  FileDown,
  FileType,
  Presentation,
  CheckCircle2,
  ExternalLink,
  Copy,
  Check,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { getDownloadUrl } from "@/lib/api"
import type { ResearchReport as ResearchReportType } from "@/types"

interface ResearchReportProps {
  report: ResearchReportType
}

export function ResearchReport({ report }: ResearchReportProps) {
  const [copied, setCopied] = useState(false)

  const handleCopyMarkdown = async () => {
    try {
      await navigator.clipboard.writeText(report.markdown_content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      const textArea = document.createElement("textarea")
      textArea.value = report.markdown_content
      document.body.appendChild(textArea)
      textArea.select()
      document.execCommand("copy")
      document.body.removeChild(textArea)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const handleDownloadMarkdown = () => {
    const blob = new Blob([report.markdown_content], { type: "text/markdown" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `${report.topic.replace(/[^a-zA-Z0-9]/g, "_")}.md`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const allSources = report.tasks
    .filter((task) => task.sources.length > 0)
    .flatMap((task) =>
      task.sources.map((source) => ({
        ...source,
        subtopic: task.subtopic,
      }))
    )

  const uniqueSources = allSources.filter(
    (source, index, self) => index === self.findIndex((s) => s.url === source.url)
  )

  return (
    <div className="space-y-5">
      <Card className="overflow-hidden shadow-sm">
        <CardHeader>
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div className="min-w-0">
              <CardTitle className="text-2xl leading-tight">{report.topic}</CardTitle>
              <CardDescription className="mt-2">
                {report.subtopics.length} research tracks -{" "}
                {new Date(report.created_at).toLocaleDateString("en-US", {
                  year: "numeric",
                  month: "long",
                  day: "numeric",
                })}
              </CardDescription>
            </div>
            <Badge variant="default" className="w-fit gap-1">
              <CheckCircle2 className="h-3 w-3" />
              Complete
            </Badge>
          </div>
        </CardHeader>
      </Card>

      <Tabs defaultValue="report" className="w-full">
        <TabsList className="grid h-11 w-full grid-cols-3 rounded-lg bg-muted/80 p-1">
          <TabsTrigger value="report" className="gap-2">
            <FileText className="h-4 w-4" />
            Report
          </TabsTrigger>
          <TabsTrigger value="sources" className="gap-2">
            <Link2 className="h-4 w-4" />
            Sources
            {uniqueSources.length > 0 && (
              <span className="ml-1 rounded-full bg-muted-foreground/20 px-1.5 text-xs">
                {uniqueSources.length}
              </span>
            )}
          </TabsTrigger>
          <TabsTrigger value="download" className="gap-2">
            <Download className="h-4 w-4" />
            Download
          </TabsTrigger>
        </TabsList>

        <TabsContent value="report">
          <Card className="shadow-sm">
            <CardContent className="p-5 sm:p-7">
              <div className="report-content prose prose-slate max-w-none dark:prose-invert">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {report.markdown_content}
                </ReactMarkdown>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="sources">
          <Card className="shadow-sm">
            <CardHeader className="border-b bg-muted/35">
              <CardTitle className="text-lg">Sources</CardTitle>
              <CardDescription>
                References used in this report, grouped by research track.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-5">
              {uniqueSources.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <Link2 className="mb-3 h-10 w-10 text-muted-foreground/50" />
                  <p className="text-sm text-muted-foreground">
                    No sources available for this report.
                  </p>
                </div>
              ) : (
                <div className="space-y-6">
                  {report.tasks
                    .filter((task) => task.sources.length > 0)
                    .map((task) => (
                      <div key={task.id} className="space-y-2">
                        <h3 className="text-sm font-semibold text-foreground">
                          {task.subtopic}
                        </h3>
                        <div className="space-y-2">
                          {task.sources.map((source, idx) => (
                            <a
                              key={idx}
                              href={source.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex items-start gap-3 rounded-md border bg-background p-3 transition-colors hover:border-primary/40 hover:bg-primary/5"
                            >
                              <ExternalLink className="mt-0.5 h-4 w-4 flex-shrink-0 text-muted-foreground" />
                              <div className="min-w-0">
                                <p className="truncate text-sm font-medium text-primary">
                                  {source.title || source.url}
                                </p>
                                {source.snippet && (
                                  <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">
                                    {source.snippet}
                                  </p>
                                )}
                              </div>
                            </a>
                          ))}
                        </div>
                      </div>
                    ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="download">
          <Card className="shadow-sm">
            <CardHeader className="border-b bg-muted/35">
              <CardTitle className="text-lg">Download Report</CardTitle>
              <CardDescription>
                Download this research report in your preferred format.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-5">
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                <div className="flex flex-col items-center gap-3 rounded-lg border bg-background p-5 text-center transition-colors hover:border-primary/40">
                  <FileType className="h-10 w-10 text-blue-500" />
                  <div>
                    <h3 className="font-semibold text-foreground">Markdown</h3>
                    <p className="mt-1 text-xs text-muted-foreground">
                      Raw markdown text file
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleCopyMarkdown}
                      className="gap-1"
                    >
                      {copied ? (
                        <>
                          <Check className="h-4 w-4" />
                          Copied
                        </>
                      ) : (
                        <>
                          <Copy className="h-4 w-4" />
                          Copy
                        </>
                      )}
                    </Button>
                    <Button
                      variant="default"
                      size="sm"
                      onClick={handleDownloadMarkdown}
                      className="gap-1"
                    >
                      <FileDown className="h-4 w-4" />
                      Download
                    </Button>
                  </div>
                </div>

                {[
                  {
                    label: "PDF",
                    description: "Formatted PDF document",
                    format: "pdf" as const,
                    icon: <FileText className="h-10 w-10 text-red-500" />,
                  },
                  {
                    label: "PowerPoint",
                    description: "Presentation slides",
                    format: "pptx" as const,
                    icon: <Presentation className="h-10 w-10 text-orange-500" />,
                  },
                ].map((option) => (
                  <div
                    key={option.format}
                    className="flex flex-col items-center gap-3 rounded-lg border bg-background p-5 text-center transition-colors hover:border-primary/40"
                  >
                    {option.icon}
                    <div>
                      <h3 className="font-semibold text-foreground">{option.label}</h3>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {option.description}
                      </p>
                    </div>
                    <a
                      href={getDownloadUrl(report.id, option.format)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex h-9 items-center justify-center gap-1 whitespace-nowrap rounded-md bg-primary px-3 text-sm font-medium text-primary-foreground ring-offset-background transition-colors hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                    >
                      <FileDown className="h-4 w-4" />
                      Download
                    </a>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
