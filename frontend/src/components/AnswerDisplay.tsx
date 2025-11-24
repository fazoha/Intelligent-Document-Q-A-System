"use client";

import { useRef } from "react";
import CitationCard from "./CitationCard";
import { Sparkles, Clock, BookOpen, FileText } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Tooltip } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

interface Citation {
  chunk_id: string;
  text: string;
  page: number;
  bbox: number[];
  doc_name: string;
  block_type: string;
}

interface AnswerDisplayProps {
  answer: string;
  citations: Citation[];
  queryTime?: number;
}

export default function AnswerDisplay({
  answer,
  citations,
  queryTime,
}: AnswerDisplayProps) {
  const citationRefs = useRef<(HTMLDivElement | null)[]>([]);

  if (!answer) return null;

  // 1. Normalize formatting artifacts that GPT might emit (e.g., stray "- ." bullets, extra blank lines)
  const normalizedAnswer = answer
    .replace(/\r\n/g, "\n")
    .replace(/^\s*[-*]\s*\.\s*$/gm, "") // Drop bullets that only contain a dot
    .replace(/\n{3,}/g, "\n\n"); // Collapse excessive blank lines

  // 2. Pre-process the answer to handle citations more gracefully
  // Remove spaces before citations so they hug the preceding word
  const processedAnswer = normalizedAnswer
    .replace(/\s+\[chunk_(\d+)\]/g, "[chunk_$1]")
    .replace(/\[chunk_(\d+)\]/g, (match, id) => {
      const index = parseInt(id, 10);
      return `[^${index + 1}](#citation-${index})`;
    });

  const scrollToCitation = (index: number) => {
    const el = citationRefs.current[index];
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "center" });
      // Add a temporary highlight effect
      el.classList.add("ring-2", "ring-primary", "bg-primary/5");
      setTimeout(() => el.classList.remove("ring-2", "ring-primary", "bg-primary/5"), 2000);
    }
  };

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 space-y-8 pb-8">
      {/* Answer Header */}
      <div className="flex items-center justify-between text-primary/80 px-1">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4" />
          <h3 className="text-xs font-bold uppercase tracking-widest">AI Synthesis</h3>
        </div>
        {queryTime && (
          <span className="text-[10px] text-muted-foreground flex items-center gap-1 font-mono bg-secondary/50 px-2 py-1 rounded-full">
            <Clock className="w-3 h-3" />
            {(queryTime / 1000).toFixed(2)}s
          </span>
        )}
      </div>

      {/* Main Answer Content */}
      <div className="bg-secondary/10 border border-border/40 rounded-2xl p-8 backdrop-blur-sm shadow-sm">
        <div className="prose prose-sm prose-invert max-w-none prose-p:leading-relaxed prose-headings:font-semibold prose-headings:tracking-tight prose-li:marker:text-primary/50">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              // Override the link component to render citations
              a: ({ href, children, ...props }) => {
                // Check if this is one of our citation links
                if (href?.startsWith("#citation-")) {
                  const index = parseInt(href.replace("#citation-", ""), 10);
                  const citation = citations[index];
                  
                  return (
                    <Tooltip
                      side="top"
                      className="max-w-xs bg-popover text-popover-foreground p-0 border border-border shadow-xl z-50"
                      content={
                        citation ? (
                          <div className="p-3 space-y-2">
                            <div className="flex items-center gap-2 text-[10px] text-muted-foreground uppercase tracking-wider border-b border-border/50 pb-2">
                              <FileText className="w-3 h-3" />
                              <span className="truncate max-w-[150px]">{citation.doc_name}</span>
                              <span className="ml-auto">Page {citation.page}</span>
                            </div>
                            <p className="text-xs leading-snug line-clamp-4 italic text-muted-foreground">
                              "{citation.text}"
                            </p>
                            <div className="pt-1 text-[10px] text-primary font-medium">
                              Click to view full context ↓
                            </div>
                          </div>
                        ) : (
                          <span className="p-2 text-xs">Citation not found</span>
                        )
                      }
                    >
                      <sup className="ml-0.5 align-super">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.preventDefault();
                            scrollToCitation(index);
                          }}
                          className={cn(
                            "inline-flex items-center justify-center h-4 min-w-[0.95rem] px-0.5 text-[9px] font-bold rounded-full transition-all duration-200 leading-none",
                            "bg-primary/10 text-primary hover:bg-primary hover:text-primary-foreground hover:scale-110 cursor-pointer border border-primary/20"
                          )}
                        >
                          {children}
                        </button>
                      </sup>
                    </Tooltip>
                  );
                }
                // Normal link
                return (
                  <a 
                    href={href} 
                    className="text-primary underline underline-offset-4 hover:text-primary/80 transition-colors"
                    target="_blank"
                    rel="noopener noreferrer" 
                    {...props}
                  >
                    {children}
                  </a>
                );
              },
            }}
          >
            {processedAnswer}
          </ReactMarkdown>
        </div>
      </div>

      {/* Citations List */}
      {citations.length > 0 && (
        <div className="space-y-4 pt-4 border-t border-border/40">
          <div className="flex items-center gap-2 text-sm font-semibold text-muted-foreground uppercase tracking-wider px-1">
            <BookOpen className="w-4 h-4" />
            <h3>Sources & Citations</h3>
            <span className="ml-auto text-xs font-normal bg-secondary/50 px-2 py-0.5 rounded-full">
              {citations.length} References
            </span>
          </div>
          
          <div className="grid grid-cols-1 gap-4">
            {citations.map((citation, idx) => (
              <div 
                key={idx} 
                ref={(el) => { citationRefs.current[idx] = el; }}
                id={`citation-${idx}`} // Add ID for anchor linking safety
                className="scroll-mt-32 transition-all duration-500 rounded-xl"
              >
                <CitationCard citation={citation} index={idx + 1} />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
