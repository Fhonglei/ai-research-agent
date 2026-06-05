"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Sparkles, History, Settings, Check, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { getApiUrl } from "@/lib/api"

export function Navbar() {
  const [showSettings, setShowSettings] = useState(false)
  const [apiUrl, setApiUrl] = useState("http://localhost:8000")
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    setApiUrl(getApiUrl())
  }, [])

  const handleSave = () => {
    localStorage.setItem("api_url", apiUrl)
    setSaved(true)
    setTimeout(() => {
      setSaved(false)
      setShowSettings(false)
    }, 1500)
  }

  return (
    <nav className="sticky top-0 z-50 w-full border-b bg-background/85 shadow-sm backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
        <Link href="/" className="flex items-center gap-2 transition-opacity hover:opacity-90">
          <span className="flex h-9 w-9 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <Sparkles className="h-5 w-5" />
          </span>
          <span className="text-lg font-semibold tracking-tight">AI Research Agent</span>
        </Link>

        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowSettings(!showSettings)}
            className="flex items-center gap-2"
          >
            <Settings className="h-4 w-4" />
            <span className="hidden sm:inline">API</span>
          </Button>

          <Link
            href="/history"
            className="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 hover:bg-accent hover:text-accent-foreground h-9 px-3"
          >
            <History className="h-4 w-4" />
            <span className="hidden sm:inline">History</span>
          </Link>
        </div>
      </div>

      {showSettings && (
        <div className="border-t bg-muted/50 px-4 py-3">
          <div className="mx-auto flex max-w-7xl items-center gap-2">
            <span className="shrink-0 text-sm text-muted-foreground">Backend URL:</span>
            <Input
              value={apiUrl}
              onChange={(e) => setApiUrl(e.target.value)}
              placeholder="http://localhost:8000"
              className="h-8 text-sm"
            />
            <Button
              size="sm"
              onClick={handleSave}
              className="h-8 gap-1"
            >
              {saved ? <Check className="h-3 w-3" /> : <X className="h-3 w-3" />}
              {saved ? "Saved!" : "Save"}
            </Button>
          </div>
        </div>
      )}
    </nav>
  )
}
