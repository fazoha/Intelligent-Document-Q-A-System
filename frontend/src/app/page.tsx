"use client";

import { useEffect, useState } from "react";
import UploadZone from "@/components/UploadZone";
import SampleSelector from "@/components/SampleSelector";
import QuestionInput from "@/components/QuestionInput";
import AnswerDisplay from "@/components/AnswerDisplay";
import DocumentSidebar from "@/components/DocumentSidebar";
import { Sparkles, MessageSquarePlus, Layers, Command } from "lucide-react";
import { Tooltip } from "@/components/ui/tooltip";

interface Document {
  doc_id: string;
  filename: string;
  page_count: number;
  chunk_count: number;
  uploaded_at: string;
  status: string;
}

interface Citation {
  chunk_id: string;
  text: string;
  page: number;
  bbox: number[];
  doc_name: string;
  block_type: string;
}

interface QueryResponse {
  answer: string;
  citations: Citation[];
  query_time_ms: number;
  retrieved_chunks: number;
}

export default function HomePage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isQuerying, setIsQuerying] = useState(false);
  const [answer, setAnswer] = useState("");
  const [citations, setCitations] = useState<Citation[]>([]);
  const [queryTime, setQueryTime] = useState<number | undefined>();

  // Fetch documents on mount
  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/documents");
      const data = await response.json();
      setDocuments(data.documents || []);
    } catch (error) {
      console.error("Error fetching documents:", error);
    }
  };

  const handleSampleSelect = async (filename: string) => {
    try {
      const response = await fetch("http://localhost:8000/api/documents/samples/load", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ filename }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to load sample");
      }

      await fetchDocuments();
    } catch (error) {
      console.error("Error loading sample:", error);
    }
  };

  const handleQuery = async (query: string) => {
    setIsQuerying(true);
    setAnswer("");
    setCitations([]);
    setQueryTime(undefined);

    try {
      const response = await fetch("http://localhost:8000/api/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Query failed");
      }

      const data: QueryResponse = await response.json();
      setAnswer(data.answer);
      setCitations(data.citations);
      setQueryTime(data.query_time_ms);
    } catch (error: any) {
      setAnswer(`Error: ${error.message}`);
      setCitations([]);
    } finally {
      setIsQuerying(false);
    }
  };

  const handleClearAll = async () => {
    try {
      const response = await fetch(
        "http://localhost:8000/api/documents/clear",
        {
          method: "DELETE",
        }
      );

      if (response.ok) {
        setDocuments([]);
        setAnswer("");
        setCitations([]);
        setQueryTime(undefined);
      }
    } catch (error) {
      console.error("Error clearing documents:", error);
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-background text-foreground font-sans antialiased selection:bg-primary/20 selection:text-primary">
      {/* Sidebar */}
      <DocumentSidebar
        documents={documents}
        onRefresh={fetchDocuments}
        onClearAll={handleClearAll}
      />

      {/* Main Content */}
      <main className="flex-1 flex flex-col relative min-w-0 bg-gradient-to-b from-background to-secondary/5">
        {/* Header - Minimalist */}
        <header className="absolute top-0 left-0 right-0 h-20 flex items-center px-8 z-20 justify-between pointer-events-none">
          <div className="flex items-center gap-3 pointer-events-auto">
            <div className="w-9 h-9 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center backdrop-blur-sm">
              <Layers className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h1 className="font-bold text-lg tracking-tight flex items-center gap-2">
                DocuSphere
                <span className="px-2 py-0.5 rounded-full bg-primary/10 text-[10px] font-medium text-primary uppercase tracking-wide">Beta</span>
              </h1>
              <p className="text-[10px] text-muted-foreground font-medium tracking-wide uppercase">Enterprise Intelligence</p>
            </div>
          </div>
          
          {documents.length > 0 && (
             <Tooltip content="Start a fresh conversation" side="bottom">
               <button 
                 onClick={() => {
                   setAnswer(""); 
                   setCitations([]);
                 }}
                 className="pointer-events-auto text-xs font-medium text-muted-foreground hover:text-foreground flex items-center gap-2 px-4 py-2 rounded-full border border-border/50 bg-background/50 backdrop-blur-sm hover:bg-secondary transition-all duration-200 shadow-sm hover:shadow"
               >
                 <MessageSquarePlus className="w-4 h-4" />
                 New Chat
               </button>
             </Tooltip>
          )}
        </header>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto scroll-smooth pt-24 pb-56 px-4">
          <div className="max-w-4xl mx-auto w-full">
            
            {documents.length === 0 ? (
              <div className="flex flex-col items-center justify-center min-h-[70vh] space-y-10 animate-in fade-in duration-700 slide-in-from-bottom-4">
                <div className="text-center space-y-4 max-w-2xl mx-auto">
                  <h2 className="text-4xl font-bold tracking-tight text-foreground sm:text-5xl">
                    Turn documents into <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-purple-400">intelligence</span>
                  </h2>
                  <p className="text-muted-foreground text-lg leading-relaxed max-w-lg mx-auto">
                    Upload your policies, contracts, or reports and get instant, cited answers from our advanced AI engine.
                  </p>
                </div>
                
                <div className="w-full max-w-2xl space-y-10">
                  <UploadZone onUploadComplete={fetchDocuments} />
                  <SampleSelector onSelect={handleSampleSelect} />
                </div>
              </div>
            ) : (
              <div className="space-y-10 min-h-[calc(100vh-16rem)]">
                {!answer && !isQuerying ? (
                  <div className="flex flex-col items-center justify-center h-[50vh] text-center space-y-8 opacity-0 animate-in fade-in duration-1000 fill-mode-forwards">
                    <div className="relative">
                      <div className="absolute inset-0 bg-primary/20 blur-3xl rounded-full opacity-50" />
                      <div className="relative w-20 h-20 rounded-3xl bg-gradient-to-tr from-secondary to-background border border-border/50 flex items-center justify-center shadow-2xl transform rotate-6 transition-transform hover:rotate-0 duration-500">
                        <Sparkles className="w-10 h-10 text-primary" />
                      </div>
                    </div>
                    
                    <div className="space-y-3 max-w-lg">
                      <h3 className="text-2xl font-semibold tracking-tight">Ready to analyze</h3>
                      <p className="text-muted-foreground leading-relaxed">
                        I've indexed <span className="text-foreground font-medium">{documents.length} documents</span>. 
                        <br/>Ask me anything about the content.
                      </p>
                      
                      <div className="pt-4 flex flex-wrap gap-2 justify-center">
                        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-secondary/50 border border-border/50 text-muted-foreground">
                          <Command className="w-3 h-3" />
                          Specific Questions
                        </span>
                        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-secondary/50 border border-border/50 text-muted-foreground">
                          <Layers className="w-3 h-3" />
                          Summaries
                        </span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <AnswerDisplay
                    answer={answer}
                    citations={citations}
                    queryTime={queryTime}
                  />
                )}
                
                {/* Loading State Placeholder */}
                {isQuerying && !answer && (
                  <div className="flex flex-col items-center justify-center py-12 space-y-6 animate-pulse">
                    <div className="flex gap-2">
                      <div className="w-2.5 h-2.5 bg-primary rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                      <div className="w-2.5 h-2.5 bg-primary rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                      <div className="w-2.5 h-2.5 bg-primary rounded-full animate-bounce"></div>
                    </div>
                    <p className="text-sm text-muted-foreground font-medium tracking-wide uppercase">Synthesizing Answer...</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Floating Input Area */}
        {documents.length > 0 && (
          <div className="absolute bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-transparent via-background/80 to-background pt-12 pb-8 z-20 pointer-events-none">
            <div className="pointer-events-auto">
              <QuestionInput onSubmit={handleQuery} isLoading={isQuerying} />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
