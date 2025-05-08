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
  Alert,
} from "@mui/material";
import { useState, useEffect } from "react";
import InsertDriveFileIcon from "@mui/icons-material/InsertDriveFile";
import SearchIcon from "@mui/icons-material/Search";
import SendIcon from "@mui/icons-material/Send";
import api from "../services/api";
import type { Document, QuestionResponse } from "../services/api";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { debounce } from "lodash";

interface DocumentViewerProps {
  file?: File;
}

const DocumentViewer = ({ file }: DocumentViewerProps) => {
  const [aiModel, setAiModel] = useState(
    "HF - roberta-base-squad2 (Open Source)"
  );
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(
    null
  );
  const [documentUrl, setDocumentUrl] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<QuestionResponse | null>(null);
  const [isAsking, setIsAsking] = useState(false);
  const queryClient = useQueryClient();

  // Fetch documents list
  const { data: documents = [], isLoading } = useQuery({
    queryKey: ["documents", searchQuery],
    queryFn: () =>
      searchQuery ? api.searchDocuments(searchQuery) : api.listDocuments(),
  });

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

  const handleQuestionSubmit = async () => {
    if (!selectedDocument || !question.trim()) return;

    setIsAsking(true);
    setAnswer(null);

    try {
      const response = await api.askQuestion(
        selectedDocument.id,
        question.trim()
      );
      setAnswer(response);
    } catch (error) {
      console.error("Failed to get answer:", error);
      setAnswer({
        answer: "Failed to get an answer. Please try again.",
        confidence: 0,
        success: false,
      });
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
                  <SearchIcon fontSize="small" />
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
          ) : documents.length > 0 ? (
            documents.map((doc) => (
              <ListItem key={doc.id} disablePadding>
                <ListItemButton
                  selected={selectedDocument?.id === doc.id}
                  onClick={() => setSelectedDocument(doc)}
                  sx={{
                    borderBottom: "1px solid #f0f0f0",
                    "&.Mui-selected": {
                      backgroundColor: "#f0f7ff",
                    },
                  }}
                >
                  <ListItemIcon sx={{ minWidth: 40 }}>
                    <InsertDriveFileIcon color="primary" />
                  </ListItemIcon>
                  <ListItemText
                    primary={doc.file_name}
                    secondary={api.formatFileSize(doc.file_size)}
                    primaryTypographyProps={{
                      fontSize: "0.875rem",
                      fontWeight: selectedDocument?.id === doc.id ? 600 : 400,
                    }}
                    secondaryTypographyProps={{
                      fontSize: "0.75rem",
                    }}
                  />
                </ListItemButton>
              </ListItem>
            ))
          ) : (
            <Box sx={{ p: 2, textAlign: "center", color: "text.secondary" }}>
              No documents found
            </Box>
          )}
        </List>
      </Box>

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

      {/* Right Panel - AI Assistant */}
      <Box
        sx={{ width: 400, borderLeft: "1px solid #e0e0e0", bgcolor: "#fff" }}
      >
        <Box sx={{ p: 2, borderBottom: "1px solid #e0e0e0" }}>
          <Typography variant="h6" gutterBottom>
            AI Assistant
          </Typography>
          <Select
            value={aiModel}
            onChange={(e) => setAiModel(e.target.value)}
            size="small"
            fullWidth
            disabled
          >
            <MenuItem value="HF - roberta-base-squad2 (Open Source)">
              HF - roberta-base-squad2 (Open Source)
            </MenuItem>
          </Select>
        </Box>

        <Box sx={{ p: 2 }}>
          <Box sx={{ mb: 2 }}>
            <Button
              variant="outlined"
              size="small"
              sx={{ mr: 1, mb: 1 }}
              onClick={() => {
                setQuestion("What is the contract title?");
                handleQuestionSubmit();
              }}
            >
              What is the contract title?
            </Button>
            <Button
              variant="outlined"
              size="small"
              sx={{ mr: 1, mb: 1 }}
              onClick={() => {
                setQuestion("What is the contract type?");
                handleQuestionSubmit();
              }}
            >
              What is the contract type?
            </Button>
          </Box>

          {answer && (
            <Box sx={{ mb: 2 }}>
              <Alert
                severity={answer.success ? "success" : "info"}
                sx={{ mb: 1 }}
              >
                {answer.answer}
                {answer.success && (
                  <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                    Confidence: {(answer.confidence * 100).toFixed(1)}%
                  </Typography>
                )}
              </Alert>
            </Box>
          )}

          <Box sx={{ display: "flex", gap: 1 }}>
            <TextField
              fullWidth
              multiline
              rows={4}
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
  );
};

export default DocumentViewer;
