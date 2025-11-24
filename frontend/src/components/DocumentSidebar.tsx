"use client";

import { useState } from "react";
import { 
  FileText, 
  Trash2, 
  RefreshCw, 
  Clock, 
  AlertCircle,
  BookOpen,
  Search,
  MoreVertical,
  CheckCircle2
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Tooltip } from "@/components/ui/tooltip";

interface Document {
  doc_id: string;
  filename: string;
  page_count: number;
  chunk_count: number;
  uploaded_at: string;
  status: string;
}

interface DocumentSidebarProps {
  documents: Document[];
  onRefresh: () => void;
  onClearAll: () => void;
}

export default function DocumentSidebar({
  documents,
  onRefresh,
  onClearAll,
}: DocumentSidebarProps) {
  const [showClearConfirm, setShowClearConfirm] = useState(false);

  const formatRelativeTime = (isoString: string) => {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  const handleClearAll = () => {
    if (showClearConfirm) {
      onClearAll();
      setShowClearConfirm(false);
    } else {
      setShowClearConfirm(true);
      setTimeout(() => setShowClearConfirm(false), 3000);
    }
  };

  return (
    <aside className="w-80 bg-secondary/20 border-r border-border flex flex-col h-full transition-all duration-300 ease-in-out backdrop-blur-xl">
      {/* Header */}
      <div className="p-5 border-b border-border/40">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-primary" />
            <h2 className="text-sm font-semibold text-foreground/90 tracking-wide">
              Your Library
            </h2>
          </div>
          <Tooltip content="Refresh document list" side="bottom">
            <button
              onClick={onRefresh}
              className="p-2 hover:bg-secondary/80 rounded-lg transition-colors text-muted-foreground hover:text-foreground"
              aria-label="Refresh library"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </Tooltip>
        </div>
        
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
          <input 
            type="text" 
            placeholder="Filter documents..." 
            className="w-full bg-background/50 border border-border/50 rounded-lg py-2 pl-9 pr-3 text-xs focus:outline-none focus:ring-1 focus:ring-primary/30 transition-all placeholder:text-muted-foreground/70"
            disabled={documents.length === 0}
          />
        </div>
        
        <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
          <span>{documents.length} {documents.length === 1 ? "file" : "files"}</span>
          <span>{documents.reduce((acc, doc) => acc + doc.page_count, 0)} pages total</span>
        </div>
      </div>

      {/* Document List */}
      <div className="flex-1 overflow-y-auto scrollbar-hide p-3 space-y-2">
        {documents.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-center p-6 border-2 border-dashed border-border/40 rounded-xl bg-secondary/5 mx-2">
            <div className="w-12 h-12 rounded-full bg-secondary/30 flex items-center justify-center mb-3">
              <FileText className="w-6 h-6 text-muted-foreground/50" />
            </div>
            <h3 className="text-sm font-medium text-foreground mb-1">Library is empty</h3>
            <p className="text-xs text-muted-foreground max-w-[180px]">
              Upload documents to start building your knowledge base.
            </p>
          </div>
        ) : (
          documents.map((doc) => (
            <div
              key={doc.doc_id}
              className="group relative p-3 rounded-xl border border-transparent hover:border-border/60 hover:bg-secondary/40 transition-all duration-200"
            >
              <div className="flex items-start gap-3">
                <div className={cn(
                  "p-2.5 rounded-lg border mt-0.5 transition-colors",
                  doc.status === "indexed" 
                    ? "bg-primary/10 border-primary/20 text-primary" 
                    : "bg-yellow-500/10 border-yellow-500/20 text-yellow-600"
                )}>
                  <FileText className="w-4 h-4" />
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-medium text-foreground truncate" title={doc.filename}>
                      {doc.filename}
                    </p>
                    <button className="opacity-0 group-hover:opacity-100 p-1 hover:bg-background rounded text-muted-foreground transition-opacity">
                      <MoreVertical className="w-3 h-3" />
                    </button>
                  </div>
                  
                  <div className="flex items-center gap-3 mt-1.5">
                    <Tooltip content={`Processed ${doc.chunk_count} chunks from ${doc.page_count} pages`} side="right">
                      <span className="text-[10px] text-muted-foreground bg-background/50 px-1.5 py-0.5 rounded border border-border/30">
                        {doc.page_count} pg
                      </span>
                    </Tooltip>
                    
                    <span className="text-[10px] text-muted-foreground flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {formatRelativeTime(doc.uploaded_at)}
                    </span>
                  </div>
                  
                  {doc.status !== "indexed" && (
                    <div className="flex items-center gap-1.5 mt-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-yellow-500 animate-pulse" />
                      <span className="text-[10px] text-yellow-500 font-medium uppercase tracking-wide">
                        Processing...
                      </span>
                    </div>
                  )}
                </div>
              </div>
              
              {/* Hover Status Indicator */}
              {doc.status === "indexed" && (
                <div className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity">
                  <Tooltip content="Ready for querying" side="left">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                  </Tooltip>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Footer Actions */}
      {documents.length > 0 && (
        <div className="p-4 border-t border-border/40 bg-secondary/10">
          <Tooltip content="This will permanently delete all documents and reset the index" side="top">
            <button
              onClick={handleClearAll}
              className={cn(
                "w-full px-4 py-2.5 text-xs font-medium rounded-lg transition-all duration-200 flex items-center justify-center gap-2 border",
                showClearConfirm
                  ? "bg-destructive/10 text-destructive border-destructive/30 hover:bg-destructive/20"
                  : "bg-background border-border/50 text-muted-foreground hover:text-foreground hover:border-border"
              )}
            >
              <Trash2 className="w-3.5 h-3.5" />
              {showClearConfirm ? "Are you sure?" : "Clear Library"}
            </button>
          </Tooltip>
        </div>
      )}
    </aside>
  );
}
