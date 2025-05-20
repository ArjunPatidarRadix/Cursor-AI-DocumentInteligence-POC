import { useState } from "react";
import {
  ThemeProvider,
  CssBaseline,
  AppBar,
  Toolbar,
  Typography,
  Box,
  Button,
  Tabs,
  Tab,
  Stack,
} from "@mui/material";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import theme from "./utils/theme";
import Home from "./pages/Home";
import AISearch from "./pages/AISearch";

const queryClient = new QueryClient();

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <Box
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      sx={{ height: "calc(100% - 48px)" }}
      {...other}
    >
      {value === index && children}
    </Box>
  );
}

function App() {
  const [selectedFile, setSelectedFile] = useState<File>();
  const [currentTab, setCurrentTab] = useState(0);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      // Switch to Home tab when a file is selected
      setCurrentTab(0);
    }
  };

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
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
              <Stack
                direction="row"
                alignItems="center"
                spacing={4}
                sx={{ flexGrow: 1 }}
              >
                <Typography variant="h6">Radix AI</Typography>
                <Tabs
                  value={currentTab}
                  onChange={handleTabChange}
                  sx={{
                    minHeight: "48px",
                    "& .MuiTab-root": {
                      color: "white",
                      opacity: 0.7,
                      minHeight: "48px",
                      "&.Mui-selected": {
                        color: "white",
                        opacity: 1,
                      },
                    },
                    "& .MuiTabs-indicator": {
                      backgroundColor: "white",
                    },
                  }}
                >
                  <Tab label="Home" />
                  <Tab label="AI Search" />
                </Tabs>
              </Stack>
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
                    accept=".pdf,.doc,.docx,.txt"
                  />
                </Button>
              </Box>
            </Toolbar>
          </AppBar>

          <TabPanel value={currentTab} index={0}>
            <Home selectedFile={selectedFile} />
          </TabPanel>
          <TabPanel value={currentTab} index={1}>
            <AISearch />
          </TabPanel>
        </Box>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
