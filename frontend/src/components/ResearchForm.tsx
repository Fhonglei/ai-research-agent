"use client"

import React, { useState } from "react"
import { Search, Loader2, Zap, Globe, Microscope, ArrowRight } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import type { ResearchDepth } from "@/types"

const depthOptions: { value: ResearchDepth; label: string; description: string; icon: React.ReactNode }[] = [
  {
    value: "quick",
    label: "Quick",
    description: "Fast overview in 2-3 minutes",
    icon: <Zap className="h-4 w-4" />,
  },
  {
    value: "standard",
    label: "Standard",
    description: "Balanced research in 5-7 minutes",
    icon: <Globe className="h-4 w-4" />,
  },
  {
    value: "deep",
    label: "Deep",
    description: "Thorough analysis in 10-15 minutes",
    icon: <Microscope className="h-4 w-4" />,
  },
]

interface ResearchFormProps {
  onSubmit: (topic: string, depth: ResearchDepth) => void
  isLoading: boolean
}

export function ResearchForm({ onSubmit, isLoading }: ResearchFormProps) {
  const [topic, setTopic] = useState("")
  const [depth, setDepth] = useState<ResearchDepth>("standard")

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const trimmedTopic = topic.trim()
    if (!trimmedTopic) return
    onSubmit(trimmedTopic, depth)
  }

  return (
    <Card className="w-full overflow-hidden border shadow-sm">
      <CardHeader className="border-b bg-muted/35">
        <CardTitle className="flex items-center gap-2 text-base">
          <span className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <Search className="h-4 w-4" />
          </span>
          New research
        </CardTitle>
        <CardDescription className="text-xs">
          Describe the question clearly; the agent will break it into research tasks.
        </CardDescription>
      </CardHeader>
      <CardContent className="p-4">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Topic
            </label>
            <Textarea
              placeholder="e.g. Research the AI productivity tools market in 2026, including demand, use cases, and key companies."
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              disabled={isLoading}
              rows={6}
              className="resize-none border-0 bg-muted/60 text-base shadow-none ring-1 ring-border focus-visible:ring-2 focus-visible:ring-primary"
            />
          </div>

          <div>
            <label className="mb-3 block text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Depth
            </label>
            <div className="grid grid-cols-1 gap-2">
              {depthOptions.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  disabled={isLoading}
                  onClick={() => setDepth(option.value)}
                  className={cn(
                    "flex items-center gap-3 rounded-md border p-3 text-left transition-all duration-200",
                    "hover:border-primary/50 hover:bg-primary/5",
                    "disabled:cursor-not-allowed disabled:opacity-50",
                    depth === option.value
                      ? "border-primary bg-primary/10 ring-1 ring-primary"
                      : "border-border bg-background"
                  )}
                >
                  <div
                    className={cn(
                      "flex h-9 w-9 shrink-0 items-center justify-center rounded-md",
                      depth === option.value
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted text-muted-foreground"
                    )}
                  >
                    {option.icon}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div
                      className={cn(
                        "text-sm font-semibold",
                        depth === option.value ? "text-primary" : "text-foreground"
                      )}
                    >
                      {option.label}
                    </div>
                    <div className="mt-0.5 text-xs text-muted-foreground">
                      {option.description}
                    </div>
                  </div>
                  {depth === option.value && (
                    <div className="h-2 w-2 rounded-full bg-primary" />
                  )}
                </button>
              ))}
            </div>
          </div>

          <Button
            type="submit"
            size="lg"
            disabled={isLoading || !topic.trim()}
            className="h-11 w-full gap-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                Running research
              </>
            ) : (
              <>
                <Search className="h-5 w-5" />
                Start research
                <ArrowRight className="h-4 w-4" />
              </>
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
