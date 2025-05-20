import { useState, useEffect } from "react";
import {
  Box,
  Typography,
  Paper,
  TextField,
  Button,
  CircularProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Select,
  MenuItem,
  Tooltip,
} from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import InsertDriveFileIcon from "@mui/icons-material/InsertDriveFile";
import api, { type SearchResult, type ModelInfo } from "../services/api";
import { useQuery } from "@tanstack/react-query";

const AISearch = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [isSearching, setIsSearching] = useState(false);
  const [searchResult, setSearchResult] = useState<SearchResult | null>(null);

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

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    try {
      const response = await api.ragSearch(searchQuery.trim(), selectedModel);
      setSearchResult(response);
    } catch (error) {
      console.error("Search failed:", error);
      // Handle error appropriately
    } finally {
      setIsSearching(false);
    }
  };

  const handleSearchKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSearch();
    }
  };

  return (
    <Box sx={{ height: "100%", p: 4 }}>
      <Paper
        sx={{
          height: "100%",
          display: "flex",
          flexDirection: "column",
          p: 4,
          gap: 2,
        }}
      >
        <Typography variant="h5" gutterBottom>
          AI Search
        </Typography>
        <Typography variant="body1" color="text.secondary" gutterBottom>
          Search across all your documents using advanced RAG (Retrieval
          Augmented Generation) technology.
        </Typography>

        <Select
          value={selectedModel}
          onChange={(e) => setSelectedModel(e.target.value)}
          size="small"
          fullWidth
          sx={{ mb: 2 }}
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

        <Box sx={{ display: "flex", gap: 1 }}>
          <TextField
            fullWidth
            multiline
            rows={2}
            placeholder="Enter your search query..."
            variant="outlined"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={handleSearchKeyPress}
            disabled={isSearching}
          />
          <Button
            variant="contained"
            onClick={handleSearch}
            disabled={!searchQuery.trim() || isSearching}
            sx={{ minWidth: "auto", alignSelf: "flex-end" }}
          >
            {isSearching ? (
              <CircularProgress size={24} color="inherit" />
            ) : (
              <SearchIcon />
            )}
          </Button>
        </Box>

        {searchResult && (
          <Box sx={{ flex: 1, overflow: "auto", mt: 2 }}>
            <Paper elevation={1} sx={{ p: 2, mb: 2 }}>
              <Typography variant="h6" gutterBottom>
                Answer
              </Typography>
              <Typography variant="body1">{searchResult.answer}</Typography>
              <Typography
                variant="caption"
                sx={{ display: "block", mt: 1, color: "text.secondary" }}
              >
                Confidence: {(searchResult.confidence * 100).toFixed(1)}%
              </Typography>
            </Paper>

            <Typography variant="h6" gutterBottom>
              Source Documents
            </Typography>
            <List>
              {searchResult.sources.map((source) => (
                <ListItem key={source.id}>
                  <ListItemIcon>
                    <InsertDriveFileIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary={source.file_name}
                    secondary={`Relevance: ${(source.similarity * 100).toFixed(
                      1
                    )}%`}
                  />
                </ListItem>
              ))}
            </List>
          </Box>
        )}
      </Paper>
    </Box>
  );
};

export default AISearch;
