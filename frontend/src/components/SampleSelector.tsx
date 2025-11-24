"use client";

import { useState, useEffect } from "react";
import { FileText, ArrowRight, Loader2, Sparkles, BookOpen } from "lucide-react";
import { cn } from "@/lib/utils";
import { Tooltip } from "@/components/ui/tooltip";

interface SampleSelectorProps {
  onSelect: (filename: string) => Promise<void>;
}

export default function SampleSelector({ onSelect }: SampleSelectorProps) {
  const [samples, setSamples] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [processingFile, setProcessingFile] = useState<string | null>(null);

  useEffect(() => {
    const fetchSamples = async () => {
      try {
        const res = await fetch("http://localhost:8000/api/documents/samples");
        if (res.ok) {
          const data = await res.json();
          setSamples(data.samples || []);
        }
      } catch (err) {
        console.error("Failed to load samples", err);
      }
    };
    fetchSamples();
  }, []);

  const handleSelect = async (filename: string) => {
    if (loading) return;
    setLoading(true);
    setProcessingFile(filename);
    try {
      await onSelect(filename);
    } finally {
      setLoading(false);
      setProcessingFile(null);
    }
  };

  if (samples.length === 0) return null;

  return (
    <div className="w-full max-w-xl mx-auto mt-10 animate-in fade-in slide-in-from-bottom-4 duration-700 delay-200">
      <div className="flex items-center gap-4 mb-6">
        <div className="h-px flex-1 bg-gradient-to-r from-transparent via-border to-transparent"></div>
        <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-widest">
          Or try a sample dataset
        </span>
        <div className="h-px flex-1 bg-gradient-to-r from-transparent via-border to-transparent"></div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {samples.slice(0, 4).map((sample) => (
          <Tooltip key={sample} content="Load this sample document instantly" side="top">
            <button
              onClick={() => handleSelect(sample)}
              disabled={loading}
              className={cn(
                "group relative flex items-center gap-3 p-3.5 rounded-xl border transition-all duration-300 text-left overflow-hidden",
                "bg-secondary/20 border-border/50 hover:bg-secondary/40 hover:border-primary/30 hover:shadow-lg hover:shadow-primary/5",
                loading && "opacity-50 cursor-not-allowed",
                processingFile === sample && "border-primary ring-1 ring-primary/20 bg-primary/5"
              )}
            >
              <div className={cn(
                "p-2.5 rounded-lg bg-background/80 border border-border/50 text-muted-foreground group-hover:text-primary group-hover:border-primary/20 transition-colors",
                processingFile === sample && "text-primary border-primary/30"
              )}>
                {processingFile === sample ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <BookOpen className="w-4 h-4" />
                )}
              </div>
              
              <div className="flex-1 min-w-0 z-10">
                <p className="text-xs font-semibold text-foreground truncate">
                  {sample.replace(/-/g, " ").replace(/\.[^/.]+$/, "")}
                </p>
                <p className="text-[10px] text-muted-foreground mt-0.5 font-mono">
                  {sample.split('.').pop()?.toUpperCase()}
                </p>
              </div>

              <div className="absolute right-3 opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-300">
                <ArrowRight className="w-4 h-4 text-primary" />
              </div>
            </button>
          </Tooltip>
        ))}
      </div>
    </div>
  );
}
