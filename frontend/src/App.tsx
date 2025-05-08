import { useState } from "react";
import {
  ThemeProvider,
  CssBaseline,
  AppBar,
  Toolbar,
  Typography,
  Box,
  Button,
} from "@mui/material";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import theme from "./utils/theme";
import DocumentViewer from "./components/DocumentViewer";

const queryClient = new QueryClient();

function App() {
  const [selectedFile, setSelectedFile] = useState<File>();

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            height: "100vh",
            width: "100vw",
            overflow: "hidden",
          }}
        >
          <AppBar
            position="static"
            sx={{
              zIndex: 1200,
              boxShadow: "none",
              borderBottom: "1px solid rgba(0,0,0,0.12)",
            }}
          >
            <Toolbar variant="dense">
              <Typography variant="h6" sx={{ flexGrow: 1 }}>
                Radix AI
              </Typography>
              <Box sx={{ display: "flex", gap: 2 }}>
                <Button
                  variant="contained"
                  component="label"
                  color="inherit"
                  size="small"
                >
                  Browse
                  <input
                    type="file"
                    hidden
                    onChange={handleFileSelect}
                    accept=".pdf,.doc,.docx"
                  />
                </Button>
              </Box>
            </Toolbar>
          </AppBar>
          <Box sx={{ flex: 1, overflow: "hidden" }}>
            <DocumentViewer file={selectedFile} />
          </Box>
        </Box>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
