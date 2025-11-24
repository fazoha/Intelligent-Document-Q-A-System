"use client";

import Link from "next/link";

import { Demo } from "@/components/ui/demo";

export default function ChatPage() {
  return (
    <div className="min-h-screen bg-slate-950 pb-16 pt-12 text-white">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-4 text-white sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="accent-pill mb-4 w-fit border border-emerald-300/40 bg-emerald-400/10 text-emerald-200">
              Labs Preview
            </p>
            <h1 className="text-4xl font-semibold leading-tight sm:text-5xl">
              Chat with the AI Copilot
            </h1>
            <p className="mt-3 max-w-3xl text-lg text-slate-300">
              Prototype ideas, generate copy, and shape flows directly in your browser.
            </p>
          </div>
          <Link
            href="/"
            className="inline-flex items-center justify-center rounded-2xl border border-white/10 bg-white/5 px-5 py-2 text-sm font-medium text-white transition hover:border-emerald-300/40 hover:bg-emerald-300/10"
          >
            ← Back to workspace
          </Link>
        </div>

        <Demo />
      </div>
    </div>
  );
}

