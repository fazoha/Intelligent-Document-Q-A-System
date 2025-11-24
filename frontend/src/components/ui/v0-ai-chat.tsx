"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  ArrowUpIcon,
  CircleUserRound,
  FileUp,
  Figma,
  ImageIcon,
  MonitorIcon,
  Paperclip,
  PlusIcon,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { Textarea } from "@/components/ui/textarea";

interface UseAutoResizeTextareaProps {
  minHeight: number;
  maxHeight?: number;
}

function useAutoResizeTextarea({
  minHeight,
  maxHeight,
}: UseAutoResizeTextareaProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const adjustHeight = useCallback(
    (reset?: boolean) => {
      const textarea = textareaRef.current;
      if (!textarea) return;

      if (reset) {
        textarea.style.height = `${minHeight}px`;
        return;
      }

      textarea.style.height = `${minHeight}px`;
      const newHeight = Math.max(
        minHeight,
        Math.min(textarea.scrollHeight, maxHeight ?? Number.POSITIVE_INFINITY)
      );
      textarea.style.height = `${newHeight}px`;
    },
    [minHeight, maxHeight]
  );

  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = `${minHeight}px`;
    }
  }, [minHeight]);

  useEffect(() => {
    const handleResize = () => adjustHeight();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [adjustHeight]);

  return { textareaRef, adjustHeight };
}

export function VercelV0Chat() {
  const [value, setValue] = useState("");
  const { textareaRef, adjustHeight } = useAutoResizeTextarea({
    minHeight: 60,
    maxHeight: 200,
  });

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (value.trim()) {
        setValue("");
        adjustHeight(true);
      }
    }
  };

  return (
    <section className="mx-auto flex w-full max-w-5xl flex-col items-center gap-8 px-4 py-12 text-slate-50">
      <div className="text-center">
        <p className="accent-pill mx-auto mb-4 w-fit border border-emerald-300/40 bg-emerald-400/10 text-emerald-200">
          AI Copilot
        </p>
        <h1 className="text-balance text-4xl font-semibold leading-tight tracking-tight text-white sm:text-5xl">
          What can I help you ship?
        </h1>
        <p className="mt-3 text-base text-slate-400">
          Brainstorm, scope, and build faster with an inline design-to-code
          assistant.
        </p>
      </div>

      <div className="w-full space-y-5">
        <div className="rounded-3xl border border-white/10 bg-[#0d101a] shadow-[0_35px_120px_rgba(2,6,23,0.65)]">
          <div className="border-b border-white/5 px-4 py-5 sm:px-6">
            <div className="overflow-y-auto">
              <Textarea
                ref={textareaRef}
                value={value}
                onChange={(e) => {
                  setValue(e.target.value);
                  adjustHeight();
                }}
                onKeyDown={handleKeyDown}
                placeholder="Ask the copilot anything about your workspace..."
                className={cn(
                  "min-h-[60px] w-full resize-none border-0 bg-transparent px-0 py-0 text-base text-white placeholder:text-slate-500 focus-visible:ring-0",
                  "sm:text-lg"
                )}
                style={{ overflow: "hidden" }}
              />
            </div>
          </div>

          <div className="flex flex-col gap-3 px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
            <div className="flex items-center gap-2 text-slate-300">
              <button
                type="button"
                className="group flex items-center gap-2 rounded-xl border border-white/5 px-3 py-2 transition hover:border-emerald-300/40 hover:bg-emerald-300/10"
              >
                <Paperclip className="h-4 w-4 text-white" />
                <span className="text-xs text-slate-400 group-hover:text-emerald-100">
                  Attach
                </span>
              </button>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                className="flex items-center gap-2 rounded-2xl border border-dashed border-white/15 px-3 py-1.5 text-sm text-slate-300 transition hover:border-emerald-300/40 hover:bg-emerald-300/5"
              >
                <PlusIcon className="h-4 w-4" />
                Project
              </button>
              <button
                type="button"
                className={cn(
                  "flex items-center gap-2 rounded-2xl border px-3 py-1.5 text-sm transition",
                  value.trim()
                    ? "border-white bg-white text-slate-900 hover:bg-emerald-100"
                    : "border-white/15 text-slate-500"
                )}
              >
                <ArrowUpIcon
                  className={cn(
                    "h-4 w-4",
                    value.trim() ? "text-slate-900" : "text-slate-500"
                  )}
                />
                Send
              </button>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-center gap-3 text-sm text-slate-300">
          <ActionButton
            icon={<ImageIcon className="h-4 w-4" />}
            label="Clone screenshot"
          />
          <ActionButton icon={<Figma className="h-4 w-4" />} label="Import from Figma" />
          <ActionButton icon={<FileUp className="h-4 w-4" />} label="Upload project" />
          <ActionButton
            icon={<MonitorIcon className="h-4 w-4" />}
            label="Landing page"
          />
          <ActionButton
            icon={<CircleUserRound className="h-4 w-4" />}
            label="Sign-up form"
          />
        </div>
      </div>
    </section>
  );
}

interface ActionButtonProps {
  icon: React.ReactNode;
  label: string;
}

function ActionButton({ icon, label }: ActionButtonProps) {
  return (
    <button
      type="button"
      className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-xs font-medium text-slate-200 transition hover:border-emerald-300/50 hover:bg-emerald-300/10"
    >
      {icon}
      <span>{label}</span>
    </button>
  );
}

