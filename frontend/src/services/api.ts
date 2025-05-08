import axios from "axios";

const API_BASE_URL = "http://localhost:8000/api/v1";

export interface Document {
  id: string;
  file_name: string;
  file_size: number;
  uploaded_at: string;
}

export interface QuestionResponse {
  answer: string;
  confidence: number;
  success: boolean;
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
    question: string
  ): Promise<QuestionResponse> => {
    const response = await axios.post(
      `${API_BASE_URL}/documents/${documentId}/ask`,
      { question }
    );
    return response.data;
  },

  formatFileSize: (bytes: number): string => {
    const sizes = ["Bytes", "KB", "MB", "GB"];
    if (bytes === 0) return "0 Byte";
    const i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)).toString());
    return Math.round(bytes / Math.pow(1024, i)) + " " + sizes[i];
  },
};

export default api;
