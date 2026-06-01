"use client"

import React, { useState } from "react"
import { Search, Loader2, Zap, Globe, Microscope } from "lucide-react"
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
    <Card className="w-full border-2 transition-all duration-300 hover:border-primary/30">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-xl">
          <Search className="h-5 w-5 text-primary" />
          Start New Research
        </CardTitle>
        <CardDescription>
          Enter a research topic and select the depth of analysis you need.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <Textarea
              placeholder="e.g., Research the AI internship market in 2026"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              disabled={isLoading}
              rows={4}
              className="resize-none text-base"
            />
          </div>

          <div>
            <label className="mb-3 block text-sm font-medium text-foreground">
              Research Depth
            </label>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              {depthOptions.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  disabled={isLoading}
                  onClick={() => setDepth(option.value)}
                  className={cn(
                    "flex flex-col items-center gap-2 rounded-lg border-2 p-4 text-center transition-all duration-200",
                    "hover:border-primary/50 hover:shadow-md",
                    "disabled:cursor-not-allowed disabled:opacity-50",
                    depth === option.value
                      ? "border-primary bg-primary/5 ring-1 ring-primary"
                      : "border-border bg-card"
                  )}
                >
                  <div
                    className={cn(
                      "flex h-8 w-8 items-center justify-center rounded-full",
                      depth === option.value
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted text-muted-foreground"
                    )}
                  >
                    {option.icon}
                  </div>
                  <div>
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
                </button>
              ))}
            </div>
          </div>

          <Button
            type="submit"
            size="lg"
            disabled={isLoading || !topic.trim()}
            className="w-full gap-2 sm:w-auto"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                Researching...
              </>
            ) : (
              <>
                <Search className="h-5 w-5" />
                Start Research
              </>
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
