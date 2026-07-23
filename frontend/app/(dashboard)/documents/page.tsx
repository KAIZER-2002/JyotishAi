"use client";

import { useState, useRef, DragEvent, ChangeEvent } from "react";
import { useDocuments, useDocumentPreview } from "@/hooks/useDocuments";
import { ListDocumentsParams } from "@/services/document";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  FileText,
  UploadCloud,
  Search,
  Trash2,
  Eye,
  Loader2,
  Inbox,
  AlertTriangle,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Info,
  RefreshCw,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";

// Supported extensions constant
const SUPPORTED_EXTENSIONS = [".pdf", ".docx", ".txt", ".md", ".markdown"];

interface UploadJob {
  id: string;
  file: File;
  progress: number; // 0 to 100
  status: "queued" | "uploading" | "completed" | "failed";
  error?: string;
}

export default function DocumentsPage() {
  // Query Filters & Pagination State
  const [search, setSearch] = useState("");
  const [mediaType, setMediaType] = useState<string>("all");
  const [sortBy, setSortBy] = useState<string>("created_at");
  const [sortOrder, setSortOrder] = useState<string>("desc");
  const [page, setPage] = useState(0);
  const limit = 8;

  // Active documents query
  const queryParams: ListDocumentsParams = {
    skip: page * limit,
    limit,
    sort_by: sortBy,
    sort_order: sortOrder,
    search: search || undefined,
    media_type: mediaType !== "all" ? mediaType : undefined,
  };

  const {
    documents,
    totalCount,
    isLoading,
    uploadDocument,
    deleteDocument,
  } = useDocuments(queryParams);

  // Upload Jobs State (Tracks active / history of uploads in current session)
  const [uploadJobs, setUploadJobs] = useState<UploadJob[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Preview & Metadata Dialog State
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);

  // Retrieve preview content query
  const { data: previewData, isLoading: isPreviewLoading } = useDocumentPreview(
    isPreviewOpen ? selectedDocId : null
  );

  const selectedDoc = documents.find((d) => d.id === selectedDocId);

  // ── Handlers ──────────────────────────────────────────────────────────────

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files) {
      handleFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      handleFiles(Array.from(e.target.files));
    }
  };

  const handleFiles = (files: File[]) => {
    const MAX_SIZE = 10 * 1024 * 1024; // 10MB
    const validFiles = files.filter((file) => {
      const ext = "." + file.name.split(".").pop()?.toLowerCase();
      const isValidExt = SUPPORTED_EXTENSIONS.includes(ext);
      if (!isValidExt) {
        toast.error(`"${file.name}" is not a supported file type.`);
        return false;
      }
      if (file.size > MAX_SIZE) {
        toast.error(`"${file.name}" exceeds the 10MB size limit.`);
        return false;
      }
      return true;
    });

    validFiles.forEach((file) => {
      const job: UploadJob = {
        id: uuidv4(),
        file,
        progress: 0,
        status: "queued",
      };
      setUploadJobs((prev) => [job, ...prev]);
      startUpload(job);
    });
  };

  const startUpload = async (job: UploadJob) => {
    setUploadJobs((prev) =>
      prev.map((j) => (j.id === job.id ? { ...j, status: "uploading", progress: 10 } : j))
    );

    // Simulate progress updates up to 80% to give user immediate visual feedback
    const progressInterval = setInterval(() => {
      setUploadJobs((prev) =>
        prev.map((j) => {
          if (j.id === job.id && j.status === "uploading" && j.progress < 80) {
            return { ...j, progress: j.progress + 15 };
          }
          return j;
        })
      );
    }, 200);

    try {
      await uploadDocument(job.file);
      clearInterval(progressInterval);
      setUploadJobs((prev) =>
        prev.map((j) => (j.id === job.id ? { ...j, status: "completed", progress: 100 } : j))
      );
      toast.success(`"${job.file.name}" uploaded successfully.`);
    } catch (err: unknown) {
      clearInterval(progressInterval);
      const errMsg = (err as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail || (err as Error).message || "Upload failed.";
      setUploadJobs((prev) =>
        prev.map((j) => (j.id === job.id ? { ...j, status: "failed", error: errMsg } : j))
      );
    }
  };

  const handleRetryUpload = (jobId: string) => {
    const job = uploadJobs.find((j) => j.id === jobId);
    if (job) {
      startUpload(job);
    }
  };

  const handleClearUploads = () => {
    setUploadJobs([]);
  };

  const handleDelete = async (docId: string, filename: string) => {
    const confirm = window.confirm(`Are you sure you want to delete "${filename}" from the Knowledge Base?`);
    if (!confirm) return;

    try {
      await deleteDocument(docId);
    } catch {
      // Error is handled inside hook toast
    }
  };

  const handleOpenPreview = (docId: string) => {
    setSelectedDocId(docId);
    setIsPreviewOpen(true);
  };

  // Helper function to format file sizes
  const formatBytes = (bytes: number, decimals = 2) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + " " + sizes[i];
  };

  // Unique ID generator for uploads list
  function uuidv4() {
    return "10000000-1000-4000-8000-100000000000".replace(/[018]/g, (c: string) =>
      (parseInt(c, 10) ^ (crypto.getRandomValues(new Uint8Array(1))[0] & (15 >> (parseInt(c, 10) / 4)))).toString(16)
    );
  }

  return (
    <div className="space-y-8 py-6 max-w-6xl mx-auto px-4">
      {/* Page Header */}
      <div className="space-y-1.5">
        <h1 className="text-3xl font-extrabold tracking-tight text-foreground bg-clip-text">
          Knowledge Base
        </h1>
        <p className="text-sm text-muted-foreground max-w-2xl leading-relaxed">
          Upload and manage your PDF, DOCX, TXT, and Markdown files. Extracted texts are chunked and embedded in Chroma DB to enrich AI Chat consultations.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* LEFT COLUMN: Upload Panel */}
        <div className="space-y-6 lg:col-span-1">
          <Card className="glass-card border-white/10 bg-sidebar/5 backdrop-blur-sm shadow-xl">
            <CardHeader>
              <CardTitle className="text-lg font-bold flex items-center gap-2">
                <UploadCloud className="size-5 text-primary" /> Upload Documents
              </CardTitle>
              <CardDescription>
                Max file size: 10MB. Supports PDF, DOCX, TXT, MD.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Drag and Drop Zone */}
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`relative flex flex-col items-center justify-center border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-300 min-h-[160px] ${
                  isDragging
                    ? "border-primary bg-primary/10 scale-[0.98]"
                    : "border-white/10 bg-white/[0.01] hover:bg-white/[0.03] hover:border-white/20"
                }`}
              >
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  multiple
                  accept=".pdf,.docx,.txt,.md,.markdown"
                  className="hidden"
                />
                <UploadCloud className={`size-10 mb-3 transition-colors ${isDragging ? "text-primary" : "text-muted-foreground"}`} />
                <p className="text-sm font-semibold text-foreground">
                  Drag & drop files here
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  or click to browse filesystem
                </p>
              </div>

              {/* Upload Jobs Progress Queue */}
              {uploadJobs.length > 0 && (
                <div className="space-y-3 pt-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-muted-foreground">Upload Queue</span>
                    <Button variant="ghost" size="sm" onClick={handleClearUploads} className="h-6 px-2 text-[10px] text-muted-foreground hover:text-foreground">
                      Clear list
                    </Button>
                  </div>
                  <div className="max-h-[220px] overflow-y-auto space-y-2 pr-1 custom-scrollbar">
                    <AnimatePresence initial={false}>
                      {uploadJobs.map((job) => (
                        <motion.div
                          key={job.id}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, scale: 0.95 }}
                          className="p-2.5 rounded-lg border border-white/5 bg-white/[0.02] space-y-1.5"
                        >
                          <div className="flex items-center justify-between gap-2">
                            <span className="text-xs font-medium text-foreground truncate flex-1" title={job.file.name}>
                              {job.file.name}
                            </span>
                            <span className="text-[10px] text-muted-foreground shrink-0">
                              {formatBytes(job.file.size)}
                            </span>
                          </div>

                          {/* Progress bar / State label */}
                          <div className="flex items-center gap-2">
                            <div className="flex-1 bg-white/5 h-1.5 rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full transition-all duration-300 ${
                                  job.status === "failed"
                                    ? "bg-destructive"
                                    : job.status === "completed"
                                    ? "bg-success"
                                    : "bg-primary animate-pulse"
                                }`}
                                style={{ width: `${job.progress}%` }}
                              />
                            </div>
                            <span className="text-[10px] font-bold shrink-0 min-w-[28px] text-right">
                              {job.status === "failed" ? (
                                <span className="text-destructive">Failed</span>
                              ) : job.status === "completed" ? (
                                <span className="text-success">Done</span>
                              ) : (
                                `${job.progress}%`
                              )}
                            </span>
                          </div>

                          {/* Error block with retry capability */}
                          {job.status === "failed" && (
                            <div className="flex items-center justify-between text-[10px] text-destructive bg-destructive/10 p-1 px-2 rounded mt-1 gap-2">
                              <span className="truncate flex-1">{job.error || "Upload failed"}</span>
                              <Button
                                size="icon"
                                variant="ghost"
                                onClick={() => handleRetryUpload(job.id)}
                                className="size-5 hover:bg-destructive/20 text-destructive"
                              >
                                <RefreshCw className="size-3" />
                              </Button>
                            </div>
                          )}
                        </motion.div>
                      ))}
                    </AnimatePresence>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* RIGHT COLUMN: Document list, sorting, search, pagination */}
        <div className="space-y-6 lg:col-span-2">
          <Card className="glass-card border-white/10 bg-sidebar/5 backdrop-blur-sm shadow-xl">
            {/* Filtering & Listing Controls */}
            <CardHeader className="space-y-4 pb-4 border-b border-white/5">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg font-bold">Document Inventory</CardTitle>
                  <CardDescription>Browse, review metadata, and preview parsed texts.</CardDescription>
                </div>
              </div>

              {/* Filters grid */}
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                {/* Search bar */}
                <div className="sm:col-span-2 relative">
                  <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input
                    type="search"
                    placeholder="Search documents..."
                    value={search}
                    onChange={(e) => {
                      setSearch(e.target.value);
                      setPage(0);
                    }}
                    className="pl-9 bg-background/30 border-white/5 text-sm h-9"
                  />
                </div>

                {/* Filter MediaType */}
                <Select
                  value={mediaType}
                  onValueChange={(val) => {
                    setMediaType(val);
                    setPage(0);
                  }}
                >
                  <SelectTrigger className="bg-background/30 border-white/5 text-sm h-9">
                    <SelectValue placeholder="Format Filter" />
                  </SelectTrigger>
                  <SelectContent className="bg-sidebar border-white/10">
                    <SelectItem value="all">All Formats</SelectItem>
                    <SelectItem value="application/pdf">PDF</SelectItem>
                    <SelectItem value="application/vnd.openxmlformats-officedocument.wordprocessingml.document">DOCX</SelectItem>
                    <SelectItem value="text/plain">TXT</SelectItem>
                    <SelectItem value="text/markdown">Markdown</SelectItem>
                  </SelectContent>
                </Select>

                {/* Sort control */}
                <Select
                  value={`${sortBy}-${sortOrder}`}
                  onValueChange={(val) => {
                    const [field, order] = val.split("-");
                    setSortBy(field);
                    setSortOrder(order);
                    setPage(0);
                  }}
                >
                  <SelectTrigger className="bg-background/30 border-white/5 text-sm h-9">
                    <SelectValue placeholder="Sort order" />
                  </SelectTrigger>
                  <SelectContent className="bg-sidebar border-white/10">
                    <SelectItem value="created_at-desc">Newest First</SelectItem>
                    <SelectItem value="created_at-asc">Oldest First</SelectItem>
                    <SelectItem value="filename-asc">Name A-Z</SelectItem>
                    <SelectItem value="filename-desc">Name Z-A</SelectItem>
                    <SelectItem value="size_bytes-desc">Size (Large)</SelectItem>
                    <SelectItem value="size_bytes-asc">Size (Small)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardHeader>

            <CardContent className="p-0">
              {isLoading ? (
                // Skeleton loading state
                <div className="p-6 space-y-4">
                  {[...Array(4)].map((_, i) => (
                    <div key={i} className="flex items-center justify-between p-4 rounded-xl border border-white/5">
                      <div className="space-y-2 flex-1">
                        <Skeleton className="h-4 w-1/3" />
                        <Skeleton className="h-3 w-1/4" />
                      </div>
                      <div className="flex gap-2">
                        <Skeleton className="h-8 w-16" />
                        <Skeleton className="h-8 w-16" />
                      </div>
                    </div>
                  ))}
                </div>
              ) : documents.length === 0 ? (
                // Empty state
                <div className="flex flex-col items-center justify-center py-20 text-center px-4">
                  <Inbox className="size-12 text-muted-foreground/40 mb-3" />
                  <h3 className="text-md font-bold text-foreground">No documents found</h3>
                  <p className="text-xs text-muted-foreground mt-1 max-w-xs leading-relaxed">
                    {search || mediaType !== "all"
                      ? "No records match your active query filters."
                      : "Your Knowledge Base is empty. Drag a script or report to get started."}
                  </p>
                </div>
              ) : (
                // Documents Table
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader className="bg-white/[0.01] hover:bg-transparent border-white/5">
                      <TableRow className="border-white/5 hover:bg-transparent">
                        <TableHead className="px-6 py-3 font-semibold text-xs text-muted-foreground">Document Details</TableHead>
                        <TableHead className="px-4 py-3 font-semibold text-xs text-muted-foreground">Size</TableHead>
                        <TableHead className="px-4 py-3 font-semibold text-xs text-muted-foreground">Status</TableHead>
                        <TableHead className="px-6 py-3 font-semibold text-xs text-muted-foreground text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {documents.map((doc) => {
                        const isProcessing = doc.status === "processing" || doc.status === "pending";
                        const isFailed = doc.status === "failed";
                        const isDone = doc.status === "completed";

                        return (
                          <TableRow key={doc.id} className="border-white/5 hover:bg-white/[0.01] transition-colors">
                            {/* Title & extension info */}
                            <TableCell className="px-6 py-4">
                              <div className="flex items-center gap-3 max-w-[240px] sm:max-w-[320px]">
                                <FileText className="size-8 text-primary/80 shrink-0" />
                                <div className="truncate space-y-0.5">
                                  <p className="text-sm font-semibold text-foreground truncate" title={doc.filename}>
                                    {doc.filename}
                                  </p>
                                  <p className="text-[10px] text-muted-foreground">
                                    {new Date(doc.created_at).toLocaleString(undefined, {
                                      dateStyle: "medium",
                                      timeStyle: "short",
                                    })}
                                  </p>
                                </div>
                              </div>
                            </TableCell>

                            {/* Bytes size */}
                            <TableCell className="px-4 py-4 text-xs font-medium">
                              {formatBytes(doc.size_bytes)}
                            </TableCell>

                            {/* Ingestion statuses */}
                            <TableCell className="px-4 py-4">
                              <div className="flex items-center gap-1.5">
                                {isProcessing && (
                                  <Badge variant="secondary" className="gap-1 bg-yellow-500/10 text-yellow-500 border-yellow-500/20 text-[10px] font-bold px-2 py-0.5">
                                    <Loader2 className="size-3 animate-spin" />
                                    <span>Processing</span>
                                  </Badge>
                                )}
                                {isDone && (
                                  <Badge variant="secondary" className="gap-1 bg-success/15 text-success border-success/20 text-[10px] font-bold px-2 py-0.5">
                                    <CheckCircle2 className="size-3" />
                                    <span>Completed</span>
                                  </Badge>
                                )}
                                {isFailed && (
                                  <Badge
                                    variant="secondary"
                                    className="gap-1 bg-destructive/15 text-destructive border-destructive/20 text-[10px] font-bold px-2 py-0.5 cursor-pointer"
                                    title={doc.error_message || "Ingestion error"}
                                  >
                                    <AlertTriangle className="size-3" />
                                    <span>Failed</span>
                                  </Badge>
                                )}
                              </div>
                            </TableCell>

                            {/* Document actions: preview/delete */}
                            <TableCell className="px-6 py-4 text-right">
                              <div className="flex items-center justify-end gap-2">
                                <Button
                                  variant="secondary"
                                  size="sm"
                                  disabled={isProcessing}
                                  onClick={() => handleOpenPreview(doc.id)}
                                  className="h-8 px-2.5 gap-1 text-xs hover:bg-primary hover:text-primary-foreground transition-all"
                                  title="View document preview"
                                >
                                  <Eye className="size-3.5" />
                                  <span className="hidden sm:inline">Preview</span>
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  onClick={() => handleDelete(doc.id, doc.filename)}
                                  className="size-8 text-muted-foreground hover:bg-destructive/10 hover:text-destructive shrink-0"
                                  title="Delete document"
                                >
                                  <Trash2 className="size-3.5" />
                                </Button>
                              </div>
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </div>
              )}

              {/* Pagination controls footer */}
              {totalCount > limit && (
                <div className="flex items-center justify-between p-4 px-6 border-t border-white/5 bg-white/[0.005]">
                  <span className="text-xs text-muted-foreground">
                    Showing documents {page * limit + 1} to {Math.min((page + 1) * limit, totalCount)} of {totalCount}
                  </span>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={page === 0}
                      onClick={() => setPage((p) => p - 1)}
                      className="h-8 gap-1 rounded-lg text-xs"
                    >
                      <ChevronLeft className="size-4" /> Prev
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={(page + 1) * limit >= totalCount}
                      onClick={() => setPage((p) => p + 1)}
                      className="h-8 gap-1 rounded-lg text-xs"
                    >
                      Next <ChevronRight className="size-4" />
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* METADATA & PREVIEW DIALOG */}
      <Dialog open={isPreviewOpen} onOpenChange={setIsPreviewOpen}>
        <DialogContent className="bg-sidebar border-white/10 max-w-2xl text-foreground backdrop-blur-xl">
          <DialogHeader>
            <DialogTitle className="text-lg font-bold truncate pr-6 flex items-center gap-2">
              <FileText className="size-5 text-primary" /> {selectedDoc?.filename}
            </DialogTitle>
            <DialogDescription className="text-xs text-muted-foreground">
              Document ID: {selectedDoc?.id}
            </DialogDescription>
          </DialogHeader>

          {/* Metadata attributes summary */}
          {selectedDoc && (
            <div className="grid grid-cols-2 gap-4 bg-white/[0.02] border border-white/5 rounded-xl p-3 text-xs leading-relaxed mt-2">
              <div>
                <span className="text-muted-foreground">Format MIME:</span>{" "}
                <span className="font-semibold text-foreground truncate block">{selectedDoc.media_type}</span>
              </div>
              <div>
                <span className="text-muted-foreground">File Size:</span>{" "}
                <span className="font-semibold text-foreground block">{formatBytes(selectedDoc.size_bytes)}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Chunking:</span>{" "}
                <span className="font-semibold text-foreground block">
                  {selectedDoc.metadata_json?.heading_count !== undefined
                    ? `${selectedDoc.metadata_json.heading_count} Headings`
                    : selectedDoc.metadata_json?.paragraph_count !== undefined
                    ? `${selectedDoc.metadata_json.paragraph_count} Paragraphs`
                    : "Standard Chunks"}
                </span>
              </div>
              <div>
                <span className="text-muted-foreground">Ingested:</span>{" "}
                <span className="font-semibold text-foreground block">
                  {new Date(selectedDoc.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          )}

          {/* Truncated Text Viewport */}
          <div className="space-y-1.5 pt-2">
            <span className="text-xs font-semibold text-muted-foreground flex items-center gap-1">
              <Info className="size-3.5 text-primary" /> Parsed Text Content (Truncated)
            </span>
            <div className="relative border border-white/5 rounded-xl bg-background/50 h-[260px] overflow-y-auto p-4 text-xs font-mono whitespace-pre-wrap leading-relaxed select-text custom-scrollbar">
              {isPreviewLoading ? (
                <div className="absolute inset-0 flex items-center justify-center">
                  <Loader2 className="size-6 text-primary animate-spin" />
                </div>
              ) : (
                previewData?.content_preview || "[No extractable text present]"
              )}
            </div>
          </div>

          <DialogFooter className="mt-4">
            <Button variant="secondary" onClick={() => setIsPreviewOpen(false)} className="rounded-lg h-9">
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
