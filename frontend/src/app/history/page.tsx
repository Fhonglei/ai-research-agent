"use client"

import React from "react"
import Link from "next/link"
import { ArrowLeft } from "lucide-react"
import { Button } from "@/components/ui/button"
import { HistoryList } from "@/components/HistoryList"

export default function HistoryPage() {
  return (
    <div className="mx-auto max-w-4xl space-y-6 px-4 py-8">
      {/* Back button */}
      <Link href="/">
        <Button variant="ghost" size="sm" className="gap-2">
          <ArrowLeft className="h-4 w-4" />
          Back to Research
        </Button>
      </Link>

      {/* History List */}
      <HistoryList />
    </div>
  )
}
