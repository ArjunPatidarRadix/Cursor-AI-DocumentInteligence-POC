import axios from "axios";

const API_BASE_URL = "http://localhost:8000/api/v1";

export interface Document {
  id: string;
  file_name: string;
  file_size: number;
  uploaded_at: Date;
  indexing_status: string;
  indexing_error?: string;
}

export interface DocumentAnalysis {
  classification: {
    category: string;
    confidence: number;
    all_categories: Record<string, number>;
  };
  entities: Record<
    string,
    Array<{
      text: string;
      start: number;
      end: number;
      confidence: number;
    }>
  >;
  summary: {
    summary: string;
    original_length: number;
    summary_length: number;
    compression_ratio: number;
  };
  tables: Array<{
    table_id: number;
    data: Record<string, any>[];
    columns: string[];
    rows: number;
    columns_count: number;
  }>;
}

export interface QuestionResponse {
  answer: string;
  confidence: number;
  success: boolean;
  model_name: string;
}

export interface ModelInfo {
  id: string;
  name: string;
  description: string;
  is_default: boolean;
}

interface ChatMessage {
  id: string;
  document_id: string;
  type: string;
  content: string;
  timestamp: string;
  confidence?: number;
  success?: boolean;
  model_name?: string;
}

export interface SearchResult {
  answer: string;
  confidence: number;
  sources: Array<{
    id: string;
    file_name: string;
    similarity: number;
  }>;
}

const api = {
  uploadDocument: async (file: File): Promise<Document> => {
    const formData = new FormData();
    formData.append("file", file);

    const response = await axios.post(
      `${API_BASE_URL}/documents/upload`,
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );
    return response.data;
  },

  listDocuments: async (): Promise<Document[]> => {
    const response = await axios.get(`${API_BASE_URL}/documents/list`);
    return response.data;
  },

  getDocumentContent: async (documentId: string): Promise<string> => {
    return `${API_BASE_URL}/documents/${documentId}/content`;
  },

  searchDocuments: async (query: string): Promise<Document[]> => {
    const response = await axios.get(`${API_BASE_URL}/documents/search`, {
      params: { query },
    });
    return response.data;
  },

  askQuestion: async (
    documentId: string,
    question: string,
    modelId: string
  ): Promise<QuestionResponse> => {
    const response = await axios.post(
      `${API_BASE_URL}/documents/${documentId}/ask`,
      { question, model_id: modelId }
    );
    return response.data;
  },

  listModels: async (): Promise<ModelInfo[]> => {
    const response = await axios.get(`${API_BASE_URL}/documents/models`);
    return response.data;
  },

  formatFileSize: (bytes: number): string => {
    const sizes = ["Bytes", "KB", "MB", "GB"];
    if (bytes === 0) return "0 Byte";
    const i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)).toString());
    return Math.round(bytes / Math.pow(1024, i)) + " " + sizes[i];
  },

  getChatHistory: async (documentId: string): Promise<ChatMessage[]> => {
    const response = await axios.get(
      `${API_BASE_URL}/documents/${documentId}/chat-history`
    );
    return response.data;
  },

  ragSearch: async (query: string, modelId?: string): Promise<SearchResult> => {
    const response = await axios.post(`${API_BASE_URL}/documents/rag-search`, {
      query,
      model_id: modelId,
    });
    return response.data;
  },

  getDocumentAnalysis: async (
    documentId: string
  ): Promise<DocumentAnalysis> => {
    const response = await axios.get(
      `${API_BASE_URL}/documents/${documentId}/analysis`
    );
    return response.data;
  },

  getDocumentEntities: async (
    documentId: string
  ): Promise<DocumentAnalysis["entities"]> => {
    const response = await axios.get(
      `${API_BASE_URL}/documents/${documentId}/entities`
    );
    return response.data;
  },

  getDocumentSummary: async (
    documentId: string
  ): Promise<DocumentAnalysis["summary"]> => {
    const response = await axios.get(
      `${API_BASE_URL}/documents/${documentId}/summary`
    );
    return response.data;
  },

  getDocumentTables: async (
    documentId: string
  ): Promise<DocumentAnalysis["tables"]> => {
    const response = await axios.get(
      `${API_BASE_URL}/documents/${documentId}/tables`
    );
    return response.data;
  },

  getDocumentClassification: async (
    documentId: string
  ): Promise<DocumentAnalysis["classification"]> => {
    const response = await axios.get(
      `${API_BASE_URL}/documents/${documentId}/classification`
    );
    return response.data;
  },
};

export default api;
