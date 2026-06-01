"use client"

import Link from "next/link"
import { Sparkles, History } from "lucide-react"
import { Button } from "@/components/ui/button"

export function Navbar() {
  return (
    <nav className="sticky top-0 z-50 w-full bg-gradient-to-r from-slate-900 to-slate-800 text-white shadow-lg">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Link href="/" className="flex items-center gap-2 transition-opacity hover:opacity-90">
          <Sparkles className="h-6 w-6 text-blue-400" />
          <span className="text-xl font-bold tracking-tight">AI Research Agent</span>
        </Link>

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
    </nav>
  )
}
