import {
  Box,
  Paper,
  Typography,
  Select,
  MenuItem,
  TextField,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemButton,
  CircularProgress,
  InputAdornment,
  Divider,
  Tooltip,
} from "@mui/material";
import { useState, useEffect } from "react";
import InsertDriveFileIcon from "@mui/icons-material/InsertDriveFile";
import SearchIcon from "@mui/icons-material/Search";
import SendIcon from "@mui/icons-material/Send";
import PersonIcon from "@mui/icons-material/Person";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import api from "../services/api";
import type { Document, ModelInfo } from "../services/api";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { debounce } from "lodash";
import DocumentAnalysis from "./DocumentAnalysis";

interface ChatMessage {
  id: string;
  type: "question" | "answer";
  content: string;
  confidence?: number;
  success?: boolean;
  timestamp: Date;
  model_name?: string;
}

interface DocumentViewerProps {
  file?: File;
}

const getStatusColor = (status: string) => {
  switch (status) {
    case "completed":
      return "success.main";
    case "failed":
      return "error.main";
    case "pending":
      return "warning.main";
    case "processing":
      return "warning.main";
    default:
      return "text.primary";
  }
};

const DocumentViewer = ({ file }: DocumentViewerProps) => {
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(
    null
  );
  const [documentUrl, setDocumentUrl] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [question, setQuestion] = useState("");
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [isAsking, setIsAsking] = useState(false);
  const queryClient = useQueryClient();

  // Fetch documents list
  const { data: documents = [], isLoading } = useQuery({
    queryKey: ["documents", searchQuery],
    queryFn: () =>
      searchQuery ? api.searchDocuments(searchQuery) : api.listDocuments(),
  });

  // Fetch available models
  const { data: models = [] } = useQuery<ModelInfo[]>({
    queryKey: ["models"],
    queryFn: api.listModels,
  });

  // Set default model when models are loaded
  useEffect(() => {
    if (models.length > 0 && !selectedModel) {
      const defaultModel = models.find((m) => m.is_default);
      if (defaultModel) {
        setSelectedModel(defaultModel.id);
      }
    }
  }, [models, selectedModel]);

  // Debounced search handler
  const debouncedSearch = debounce((value: string) => {
    setSearchQuery(value);
  }, 300);

  // Handle search input change
  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    debouncedSearch(event.target.value);
  };

  // Load document content when selected
  useEffect(() => {
    const loadDocumentContent = async () => {
      if (selectedDocument) {
        try {
          const url = await api.getDocumentContent(selectedDocument.id);
          setDocumentUrl(url);
        } catch (error) {
          console.error("Failed to load document content:", error);
        }
      } else {
        setDocumentUrl(null);
      }
    };

    loadDocumentContent();
  }, [selectedDocument]);

  // Upload file when it changes
  useEffect(() => {
    const uploadFile = async () => {
      if (file) {
        try {
          const uploaded = await api.uploadDocument(file);
          queryClient.invalidateQueries({ queryKey: ["documents"] });
          setSelectedDocument(uploaded);
        } catch (error) {
          console.error("Upload failed:", error);
        }
      }
    };

    uploadFile();
  }, [file, queryClient]);

  // Load chat history when document changes
  useEffect(() => {
    const loadChatHistory = async () => {
      if (selectedDocument) {
        try {
          const history = await api.getChatHistory(selectedDocument.id);
          setChatMessages(
            history.map((msg) => ({
              id: msg.id,
              type: msg.type as "question" | "answer",
              content: msg.content,
              timestamp: new Date(msg.timestamp),
              confidence: msg.confidence,
              success: msg.success,
              model_name: msg.model_name,
            }))
          );
        } catch (error) {
          console.error("Failed to load chat history:", error);
          setChatMessages([]);
        }
      } else {
        setChatMessages([]);
      }
    };

    loadChatHistory();
  }, [selectedDocument]);

  // Update document selection handler
  const handleDocumentSelect = async (document: Document) => {
    setSelectedDocument(document);
    // Chat history will be loaded by the useEffect above
  };

  const handleQuestionSubmit = async () => {
    if (!selectedDocument || !question.trim() || !selectedModel) return;

    // Add user's question to chat
    const questionMessage: ChatMessage = {
      id: Date.now().toString(),
      type: "question",
      content: question.trim(),
      timestamp: new Date(),
      model_name: selectedModel,
    };
    setChatMessages((prev) => [...prev, questionMessage]);

    setIsAsking(true);
    setQuestion(""); // Clear input after sending

    try {
      const response = await api.askQuestion(
        selectedDocument.id,
        question.trim(),
        selectedModel
      );

      // Add AI's answer to chat
      const answerMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: "answer",
        content: response.answer,
        confidence: response.confidence,
        success: response.success,
        timestamp: new Date(),
        model_name: response.model_name,
      };
      setChatMessages((prev) => [...prev, answerMessage]);
    } catch (error) {
      console.error("Failed to get answer:", error);
      // Add error message to chat
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: "answer",
        content: "Failed to get an answer. Please try again.",
        success: false,
        timestamp: new Date(),
        model_name: selectedModel,
      };
      setChatMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsAsking(false);
    }
  };

  const handleQuestionKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleQuestionSubmit();
    }
  };

  return (
    <Box
      sx={{
        display: "flex",
        height: "calc(100vh - 64px)",
        width: "100vw",
        overflow: "hidden",
      }}
    >
      {/* Left Panel - Document List */}
      <Box
        sx={{
          width: 250,
          borderRight: "1px solid #e0e0e0",
          bgcolor: "#fff",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <Box sx={{ p: 2, borderBottom: "1px solid #e0e0e0" }}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Select Files
          </Typography>
          <TextField
            size="small"
            fullWidth
            placeholder="Search documents..."
            onChange={handleSearchChange}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
          />
        </Box>
        <List sx={{ flex: 1, overflow: "auto" }}>
          {isLoading ? (
            <Box sx={{ display: "flex", justifyContent: "center", p: 2 }}>
              <CircularProgress size={24} />
            </Box>
          ) : (
            documents.map((doc) => (
              <ListItem key={doc.id} disablePadding>
                <ListItemButton
                  selected={selectedDocument?.id === doc.id}
                  onClick={() => handleDocumentSelect(doc)}
                >
                  <ListItemIcon>
                    <InsertDriveFileIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Box sx={{ display: "flex", alignItems: "center" }}>
                        <Typography
                          variant="body2"
                          sx={{
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            whiteSpace: "nowrap",
                            flex: 1,
                          }}
                        >
                          {doc.file_name}
                        </Typography>
                        <Tooltip title={doc.indexing_status}>
                          <Box
                            sx={{
                              width: 8,
                              height: 8,
                              borderRadius: "50%",
                              bgcolor: getStatusColor(doc.indexing_status),
                              ml: 1,
                            }}
                          />
                        </Tooltip>
                      </Box>
                    }
                    secondary={api.formatFileSize(doc.file_size)}
                  />
                </ListItemButton>
              </ListItem>
            ))
          )}
        </List>
      </Box>

      {/* Middle and Right Panels */}
      <Box sx={{ flex: 1, display: "flex" }}>
        {/* Middle Panel - Document Viewer */}
        <Box sx={{ flex: 2, display: "flex", flexDirection: "column" }}>
          <Box sx={{ p: 2, borderBottom: "1px solid #e0e0e0" }}>
            <Typography variant="h6" gutterBottom>
              Document Viewer
            </Typography>
          </Box>
          <Box sx={{ flex: 1, p: 2, overflow: "auto" }}>
            <Paper
              sx={{
                height: "100%",
                bgcolor: "#fff",
                overflow: "auto",
              }}
            >
              {selectedDocument && documentUrl ? (
                <iframe
                  src={documentUrl}
                  style={{
                    width: "100%",
                    height: "100%",
                    border: "none",
                    backgroundColor: "#fff",
                  }}
                  title="document-viewer"
                />
              ) : (
                <Box
                  sx={{
                    height: "100%",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: "text.secondary",
                  }}
                >
                  No document selected
                </Box>
              )}
            </Paper>
          </Box>
        </Box>

        {/* Right Panel - AI Assistant and Analysis */}
        <Box
          sx={{
            width: 400,
            borderLeft: "1px solid #e0e0e0",
            bgcolor: "#fff",
            display: "flex",
            flexDirection: "column",
            height: "100%",
            overflow: "hidden",
          }}
        >
          {/* Header */}
          <Box sx={{ p: 2, borderBottom: "1px solid #e0e0e0", flexShrink: 0 }}>
            <Typography variant="h6" gutterBottom>
              AI Assistant
            </Typography>
            <Select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              size="small"
              fullWidth
            >
              {models.map((model) => (
                <MenuItem key={model.id} value={model.id}>
                  <Tooltip title={model.description} placement="right">
                    <Box>
                      <Typography variant="body2">{model.name}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {model.description}
                      </Typography>
                    </Box>
                  </Tooltip>
                </MenuItem>
              ))}
            </Select>
          </Box>

          {/* Chat Container */}
          <Box
            sx={{
              display: "flex",
              flexDirection: "column",
              flex: 1,
              minHeight: 0,
              overflow: "hidden",
              position: "relative",
            }}
          >
            {/* Chat Messages */}
            <Box
              sx={{
                position: "absolute",
                top: 0,
                left: 0,
                right: 0,
                bottom: 100,
                overflow: "auto",
                p: 2,
                display: "flex",
                flexDirection: "column",
                gap: 2,
                "&::-webkit-scrollbar": {
                  width: "8px",
                },
                "&::-webkit-scrollbar-track": {
                  background: "#f1f1f1",
                },
                "&::-webkit-scrollbar-thumb": {
                  background: "#888",
                  borderRadius: "4px",
                },
                "&::-webkit-scrollbar-thumb:hover": {
                  background: "#555",
                },
              }}
            >
              {selectedDocument && (
                <DocumentAnalysis documentId={selectedDocument.id} />
              )}
              {chatMessages.map((message) => (
                <Box
                  key={message.id}
                  sx={{
                    display: "flex",
                    flexDirection:
                      message.type === "question" ? "row" : "row-reverse",
                  }}
                >
                  <Box
                    sx={{
                      display: "flex",
                      alignItems: "flex-start",
                      gap: 1,
                      maxWidth: "80%",
                    }}
                  >
                    {message.type === "question" ? (
                      <PersonIcon color="primary" />
                    ) : (
                      <SmartToyIcon color="secondary" />
                    )}
                    <Paper
                      elevation={1}
                      sx={{
                        p: 1.5,
                        bgcolor:
                          message.type === "question" ? "#f5f5f5" : "#e3f2fd",
                        borderRadius: 2,
                      }}
                    >
                      <Typography variant="body2">{message.content}</Typography>
                      {message.type === "answer" && message.success && (
                        <>
                          <Typography
                            variant="caption"
                            sx={{
                              display: "block",
                              mt: 0.5,
                              color: "text.secondary",
                            }}
                          >
                            Confidence: {(message.confidence! * 100).toFixed(1)}
                            %
                          </Typography>
                          <Typography
                            variant="caption"
                            sx={{
                              display: "block",
                              color: "text.secondary",
                            }}
                          >
                            Model: {message.model_name}
                          </Typography>
                        </>
                      )}
                    </Paper>
                  </Box>
                </Box>
              ))}
              {isAsking && (
                <Box sx={{ display: "flex", justifyContent: "flex-end" }}>
                  <CircularProgress size={20} />
                </Box>
              )}
            </Box>

            {/* Question Input */}
            <Box
              sx={{
                p: 2,
                borderTop: "1px solid #e0e0e0",
                bgcolor: "#fff",
                position: "absolute",
                bottom: 0,
                left: 0,
                right: 0,
                zIndex: 1,
              }}
            >
              <Box sx={{ display: "flex", gap: 1 }}>
                <TextField
                  fullWidth
                  multiline
                  rows={2}
                  placeholder="Ask a question about the document..."
                  variant="outlined"
                  size="small"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  onKeyPress={handleQuestionKeyPress}
                  disabled={!selectedDocument || isAsking}
                />
                <Button
                  variant="contained"
                  onClick={handleQuestionSubmit}
                  disabled={!selectedDocument || !question.trim() || isAsking}
                  sx={{ minWidth: "auto", alignSelf: "flex-end" }}
                >
                  {isAsking ? (
                    <CircularProgress size={24} color="inherit" />
                  ) : (
                    <SendIcon />
                  )}
                </Button>
              </Box>
            </Box>
          </Box>
        </Box>
      </Box>
    </Box>
  );
};

export default DocumentViewer;
