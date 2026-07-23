import { api } from "@/lib/api";

export interface DocumentResponse {
  id: string;
  filename: string;
  media_type: string;
  size_bytes: number;
  status: string;
  error_message?: string;
  metadata_json?: Record<string, unknown>;
  user_id: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentListResponse {
  documents: DocumentResponse[];
  total_count: number;
}

export interface DocumentPreviewResponse {
  id: string;
  filename: string;
  content_preview: string;
}

export interface ListDocumentsParams {
  skip?: number;
  limit?: number;
  sort_by?: string;
  sort_order?: string;
  search?: string;
  media_type?: string;
}

export const documentService = {
  uploadDocument: async (file: File): Promise<DocumentResponse> => {
    const formData = new FormData();
    formData.append("file", file);
    const { data } = await api.post<DocumentResponse>("/documents/upload", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return data;
  },

  listDocuments: async (params: ListDocumentsParams): Promise<DocumentListResponse> => {
    const { data } = await api.get<DocumentListResponse>("/documents", { params });
    return data;
  },

  getDocument: async (id: string): Promise<DocumentResponse> => {
    const { data } = await api.get<DocumentResponse>(`/documents/${id}`);
    return data;
  },

  getDocumentPreview: async (id: string): Promise<DocumentPreviewResponse> => {
    const { data } = await api.get<DocumentPreviewResponse>(`/documents/${id}/preview`);
    return data;
  },

  deleteDocument: async (id: string): Promise<void> => {
    await api.delete(`/documents/${id}`);
  },
};
