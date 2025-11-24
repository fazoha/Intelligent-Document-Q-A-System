"use client";

import { useCallback, useState } from "react";
import { cn } from "@/lib/utils";
import { UploadCloud, FileUp, CheckCircle2, XCircle, Loader2, FileType } from "lucide-react";

interface UploadZoneProps {
  onUploadComplete: () => void;
}

export default function UploadZone({ onUploadComplete }: UploadZoneProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const uploadFile = useCallback(async (file: File) => {
    setError(null);
    setSuccess(null);
    setIsUploading(true);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch("http://localhost:8000/api/documents/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Upload failed");
      }

      const result = await response.json();
      setSuccess(
        `${result.filename}`
      );
      
      onUploadComplete();
      setTimeout(() => setSuccess(null), 4000);
    } catch (err: any) {
      setError(err.message || "Failed to upload file");
    } finally {
      setIsUploading(false);
    }
  }, [onUploadComplete]);

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragOver(false);

      const files = Array.from(e.dataTransfer.files);
      if (files.length > 0) {
        await uploadFile(files[0]);
      }
    },
    [uploadFile]
  );

  const handleFileSelect = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        await uploadFile(files[0]);
      }
    },
    [uploadFile]
  );

  return (
    <div className="w-full max-w-xl mx-auto group">
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={cn(
          "relative cursor-pointer rounded-2xl border-2 border-dashed transition-all duration-300 ease-out p-10 overflow-hidden",
          isDragOver
            ? "border-primary bg-primary/5 scale-[1.01] shadow-lg shadow-primary/10"
            : "border-border/60 hover:border-primary/40 hover:bg-secondary/20",
          isUploading && "opacity-80 pointer-events-none"
        )}
      >
        <input
          type="file"
          id="file-upload"
          className="hidden"
          accept=".pdf,.png,.jpg,.jpeg,.docx"
          onChange={handleFileSelect}
          disabled={isUploading}
        />
        
        <label
          htmlFor="file-upload"
          className="flex flex-col items-center justify-center gap-5 cursor-pointer relative z-10"
        >
          <div className={cn(
            "w-16 h-16 rounded-2xl bg-gradient-to-br from-secondary to-background border border-border flex items-center justify-center shadow-sm transition-transform duration-300 group-hover:scale-110 group-hover:rotate-3",
            isDragOver && "scale-110 rotate-3 border-primary/30"
          )}>
            {isUploading ? (
              <Loader2 className="w-8 h-8 text-primary animate-spin" />
            ) : (
              <UploadCloud className="w-8 h-8 text-muted-foreground group-hover:text-primary transition-colors" />
            )}
          </div>

          <div className="text-center space-y-1.5">
            <p className="text-lg font-semibold text-foreground tracking-tight">
              {isUploading ? "Analyzing Document..." : "Upload Knowledge Source"}
            </p>
            <p className="text-sm text-muted-foreground max-w-xs mx-auto leading-relaxed">
              Drag & drop or click to browse files.<br/>
              <span className="text-xs opacity-70 font-medium">Supports PDF, DOCX, Images (Max 10MB)</span>
            </p>
          </div>
        </label>
        
        {/* Background decorative elements */}
        <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none">
           <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-b from-transparent to-primary/5" />
        </div>

        {/* Status Badges */}
        {(success || error) && (
          <div className="absolute inset-x-0 bottom-4 flex justify-center animate-in slide-in-from-bottom-4 fade-in duration-300 z-20">
            <div className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-full text-xs font-medium shadow-xl backdrop-blur-md",
              success ? "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20" : "bg-destructive/10 text-destructive border border-destructive/20"
            )}>
              {success ? <CheckCircle2 className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
              {success ? <span>Successfully indexed <b>{success}</b></span> : error}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
