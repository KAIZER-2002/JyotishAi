import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { documentService, ListDocumentsParams, DocumentResponse, DocumentPreviewResponse } from "@/services/document";
import { toast } from "sonner";

export const DOCUMENTS_QUERY_KEY = ["documents"] as const;

export function useDocuments(params: ListDocumentsParams = {}) {
  const queryClient = useQueryClient();

  const {
    data,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: [...DOCUMENTS_QUERY_KEY, params],
    queryFn: () => documentService.listDocuments(params),
    staleTime: 5000,
    refetchInterval: (query) => {
      // Smart polling: if any documents are pending or processing, refetch every 2 seconds.
      const hasProcessing = query.state.data?.documents.some(
        (doc: DocumentResponse) => doc.status === "processing" || doc.status === "pending"
      );
      return hasProcessing ? 2000 : false;
    },
  });

  const uploadMutation = useMutation<DocumentResponse, Error, File>({
    mutationFn: (file) => documentService.uploadDocument(file),
    onSuccess: (newDoc) => {
      queryClient.invalidateQueries({ queryKey: DOCUMENTS_QUERY_KEY });
      toast.success(`File "${newDoc.filename}" uploaded successfully.`);
    },
    onError: (err) => {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || err.message || "Failed to upload file.";
      toast.error(msg);
    },
  });

  const deleteMutation = useMutation<void, Error, string>({
    mutationFn: (id) => documentService.deleteDocument(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: DOCUMENTS_QUERY_KEY });
      toast.success("Document deleted successfully.");
    },
    onError: (err) => {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || err.message || "Failed to delete document.";
      toast.error(msg);
    },
  });

  return {
    documents: data?.documents || [],
    totalCount: data?.total_count || 0,
    isLoading,
    isError,
    error,
    refetch,
    uploadDocument: uploadMutation.mutateAsync,
    isUploading: uploadMutation.isPending,
    deleteDocument: deleteMutation.mutateAsync,
    isDeleting: deleteMutation.isPending,
  };
}

export function useDocumentPreview(id: string | null) {
  return useQuery<DocumentPreviewResponse | null, Error>({
    queryKey: [...DOCUMENTS_QUERY_KEY, "preview", id],
    queryFn: () => (id ? documentService.getDocumentPreview(id) : Promise.resolve(null)),
    enabled: !!id,
    staleTime: 5 * 60 * 1000,
  });
}
