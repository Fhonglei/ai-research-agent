"use client"

import { useState } from "react"
import Link from "next/link"
import { Sparkles, History, Settings, Check, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { getApiUrl } from "@/lib/api"

export function Navbar() {
  const [showSettings, setShowSettings] = useState(false)
  const [apiUrl, setApiUrl] = useState(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("api_url") || getApiUrl()
    }
    return getApiUrl()
  })
  const [saved, setSaved] = useState(false)

  const handleSave = () => {
    localStorage.setItem("api_url", apiUrl)
    setSaved(true)
    setTimeout(() => {
      setSaved(false)
      setShowSettings(false)
    }, 1500)
  }

  return (
    <nav className="sticky top-0 z-50 w-full bg-gradient-to-r from-slate-900 to-slate-800 text-white shadow-lg">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Link href="/" className="flex items-center gap-2 transition-opacity hover:opacity-90">
          <Sparkles className="h-6 w-6 text-blue-400" />
          <span className="text-xl font-bold tracking-tight">AI Research Agent</span>
        </Link>

        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowSettings(!showSettings)}
            className="flex items-center gap-2 text-slate-200 hover:bg-slate-700 hover:text-white"
          >
            <Settings className="h-4 w-4" />
            <span className="hidden sm:inline">API</span>
          </Button>

          <Link href="/history">
            <Button
              variant="ghost"
              size="sm"
              className="flex items-center gap-2 text-slate-200 hover:bg-slate-700 hover:text-white"
            >
              <History className="h-4 w-4" />
              <span className="hidden sm:inline">History</span>
            </Button>
          </Link>
        </div>
      </div>

      {showSettings && (
        <div className="border-t border-slate-700 bg-slate-800/50 px-4 py-3">
          <div className="mx-auto flex max-w-6xl items-center gap-2">
            <span className="shrink-0 text-sm text-slate-300">Backend URL:</span>
            <Input
              value={apiUrl}
              onChange={(e) => setApiUrl(e.target.value)}
              placeholder="http://localhost:8000"
              className="h-8 bg-slate-700 text-white border-slate-600 text-sm"
            />
            <Button
              size="sm"
              onClick={handleSave}
              className="h-8 gap-1 bg-green-600 hover:bg-green-700"
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
