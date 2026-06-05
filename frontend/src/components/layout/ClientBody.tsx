"use client"

import { useEffect, useState } from "react"
import { Navbar } from "@/components/Navbar"

export function ClientBody({ children }: { children: React.ReactNode }) {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return (
      <div className="flex min-h-screen flex-col">
        <div className="flex items-center justify-center py-20">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />
      <main className="flex-1">{children}</main>
      <footer className="border-t bg-background py-5 text-center text-xs text-muted-foreground">
        <div className="mx-auto max-w-7xl px-4">
          AI Research Agent - powered by AI. Use responsibly.
        </div>
      </footer>
    </div>
  )
}
