"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2, Maximize2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface QuestionInputProps {
  onSubmit: (query: string) => void;
  isLoading: boolean;
}

export default function QuestionInput({
  onSubmit,
  isLoading,
}: QuestionInputProps) {
  const [query, setQuery] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [query]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSubmit(query.trim());
      setQuery("");
      // Reset height
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto relative">
      <form 
        onSubmit={handleSubmit}
        className={cn(
          "relative flex items-end gap-2 bg-secondary/80 border border-border/50 rounded-2xl p-2 shadow-2xl backdrop-blur-xl transition-all duration-300",
          isFocused ? "ring-2 ring-primary/20 bg-secondary/95 border-primary/30" : "hover:bg-secondary/90"
        )}
      >
        <textarea
          ref={textareaRef}
          id="question"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder="Ask a question about your documents..."
          rows={1}
          disabled={isLoading}
          className="flex-1 bg-transparent border-0 text-foreground placeholder:text-muted-foreground focus:ring-0 resize-none py-3 px-4 max-h-48 scrollbar-hide text-base"
          style={{ minHeight: "52px" }}
        />
        
        <button
          type="submit"
          disabled={!query.trim() || isLoading}
          className={cn(
            "p-3 rounded-xl transition-all duration-200 flex-shrink-0 mb-1 mr-1",
            query.trim() && !isLoading 
              ? "bg-primary text-primary-foreground hover:bg-primary/90 shadow-lg shadow-primary/20" 
              : "bg-muted text-muted-foreground hover:bg-muted/80"
          )}
        >
          {isLoading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Send className="w-5 h-5" />
          )}
        </button>
      </form>
      
      <div className="flex justify-center gap-6 mt-4 text-[10px] font-medium text-muted-foreground/70 uppercase tracking-widest">
        <span className="flex items-center gap-1.5">
          <kbd className="font-sans px-1.5 py-0.5 bg-secondary border border-border rounded text-foreground">Enter</kbd> Send
        </span>
        <span className="flex items-center gap-1.5">
          <kbd className="font-sans px-1.5 py-0.5 bg-secondary border border-border rounded text-foreground">Shift + Enter</kbd> New Line
        </span>
      </div>
    </div>
  );
}
