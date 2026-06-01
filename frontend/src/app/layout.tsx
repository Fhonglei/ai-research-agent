import type { Metadata } from "next"
import { Inter } from "next/font/google"
import { Navbar } from "@/components/Navbar"
import "./globals.css"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "AI Research Agent",
  description:
    "AI-powered research automation — generate comprehensive research reports on any topic.",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="flex min-h-screen flex-col">
          <Navbar />
          <main className="flex-1">{children}</main>
          <footer className="border-t py-6 text-center text-xs text-muted-foreground">
            <div className="mx-auto max-w-6xl px-4">
              AI Research Agent &mdash; Powered by AI. Use responsibly.
            </div>
          </footer>
        </div>
      </body>
    </html>
  )
}
