import type { Metadata } from "next"
import { Navbar } from "@/components/Navbar"
import "./globals.css"

export const metadata: Metadata = {
  title: "AI Research Agent",
  description:
    "AI-powered research automation that generates comprehensive reports on any topic.",
  other: {
    google: "notranslate",
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" translate="no" className="notranslate">
      <body translate="no" className="notranslate">
        <div className="flex min-h-screen flex-col">
          <Navbar />
          <main className="flex-1">{children}</main>
          <footer className="border-t bg-background py-5 text-center text-xs text-muted-foreground">
            <div className="mx-auto max-w-7xl px-4">
              AI Research Agent - powered by AI. Use responsibly.
            </div>
          </footer>
        </div>
      </body>
    </html>
  )
}
