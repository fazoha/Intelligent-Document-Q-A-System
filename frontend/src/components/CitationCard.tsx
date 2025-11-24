"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { Copy, Check, ChevronDown, Quote, FileText, ExternalLink } from "lucide-react";

interface Citation {
  chunk_id: string;
  text: string;
  page: number;
  bbox: number[];
  doc_name: string;
  block_type: string;
}

interface CitationCardProps {
  citation: Citation;
  index?: number;
}

export default function CitationCard({ citation, index }: CitationCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isCopied, setIsCopied] = useState(false);

  const handleCopy = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(citation.text);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  return (
    <div 
      className={cn(
        "group border rounded-xl transition-all duration-200 overflow-hidden",
        isExpanded 
          ? "bg-card border-primary/30 shadow-lg ring-1 ring-primary/10" 
          : "bg-card/40 border-border/60 hover:border-border hover:bg-card/60"
      )}
    >
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3.5 flex items-start gap-4 text-left relative"
      >
        {/* Number Badge */}
        {index !== undefined && (
          <div className={cn(
            "flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold transition-colors mt-0.5",
            isExpanded 
              ? "bg-primary text-primary-foreground" 
              : "bg-secondary text-muted-foreground group-hover:bg-primary/10 group-hover:text-primary"
          )}>
            {index}
          </div>
        )}

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
             <FileText className="w-3.5 h-3.5 text-muted-foreground" />
             <h4 className="text-sm font-medium text-foreground truncate max-w-[200px] sm:max-w-md" title={citation.doc_name}>
               {citation.doc_name}
             </h4>
             <span className="text-xs text-muted-foreground">•</span>
             <span className="text-xs text-muted-foreground bg-secondary/50 px-1.5 py-0.5 rounded">
               Page {citation.page}
             </span>
          </div>
          
          <p className="text-xs text-muted-foreground line-clamp-1 font-mono opacity-80">
            {citation.text}
          </p>
        </div>
        
        <ChevronDown className={cn(
          "w-4 h-4 text-muted-foreground transition-transform duration-200 mt-1",
          isExpanded && "rotate-180 text-primary"
        )} />
      </button>

      {/* Content */}
      {isExpanded && (
        <div className="px-4 pb-4 pt-0 animate-in slide-in-from-top-2 duration-200">
          <div className="relative p-4 mt-2 rounded-lg bg-secondary/30 border border-border/50 group-hover:border-border transition-colors">
            <Quote className="absolute top-3 left-3 w-4 h-4 text-primary/20" />
            <p className="text-sm text-foreground/90 leading-relaxed pl-6 italic">
              "{citation.text}"
            </p>
          </div>
          
          <div className="flex items-center justify-between mt-3">
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-medium px-2 py-1 rounded-full bg-secondary text-secondary-foreground uppercase tracking-wider border border-border/50">
                {citation.block_type}
              </span>
            </div>

            <button
              onClick={handleCopy}
              className="flex items-center gap-2 text-xs font-medium text-foreground bg-secondary border border-border/50 hover:bg-secondary/80 hover:border-primary/30 transition-all px-3 py-1.5 rounded-md shadow-sm z-10"
            >
              {isCopied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-500" />
                  Copied
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  Copy Quote
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
