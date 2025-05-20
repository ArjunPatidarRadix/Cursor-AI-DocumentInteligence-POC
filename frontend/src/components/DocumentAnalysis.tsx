import {
  Box,
  Paper,
  Typography,
  Tabs,
  Tab,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  List,
  ListItem,
  ListItemText,
  Divider,
} from "@mui/material";
import { useState, useEffect } from "react";
import api from "../services/api";
import type { DocumentAnalysis } from "../services/api";

interface DocumentAnalysisProps {
  documentId: string;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`analysis-tabpanel-${index}`}
      aria-labelledby={`analysis-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const DocumentAnalysis = ({ documentId }: DocumentAnalysisProps) => {
  const [value, setValue] = useState(0);
  const [analysis, setAnalysis] = useState<DocumentAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadAnalysis = async () => {
      try {
        setLoading(true);
        const data = await api.getDocumentAnalysis(documentId);
        setAnalysis(data);
        setError(null);
      } catch (err) {
        setError("Failed to load document analysis");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    loadAnalysis();
  }, [documentId]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setValue(newValue);
  };

  if (loading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography color="error">{error}</Typography>
      </Box>
    );
  }

  if (!analysis) {
    return null;
  }

  return (
    <Box sx={{ width: "100%" }}>
      <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
        <Tabs value={value} onChange={handleTabChange}>
          <Tab label="Summary" />
          <Tab label="Classification" />
          <Tab label="Entities" />
          <Tab label="Tables" />
        </Tabs>
      </Box>

      <TabPanel value={value} index={0}>
        <Paper elevation={1} sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Document Summary
          </Typography>
          <Typography variant="body1" paragraph>
            {analysis.summary.summary}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Original length: {analysis.summary.original_length} characters
            <br />
            Summary length: {analysis.summary.summary_length} characters
            <br />
            Compression ratio:{" "}
            {(analysis.summary.compression_ratio * 100).toFixed(1)}%
          </Typography>
        </Paper>
      </TabPanel>

      <TabPanel value={value} index={1}>
        <Paper elevation={1} sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Document Classification
          </Typography>
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle1">
              Primary Category:{" "}
              <Chip
                label={analysis.classification.category}
                color="primary"
                sx={{ ml: 1 }}
              />
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Confidence:{" "}
              {(analysis.classification.confidence * 100).toFixed(1)}%
            </Typography>
          </Box>
          <Typography variant="subtitle2" gutterBottom>
            All Categories:
          </Typography>
          <List dense>
            {Object.entries(analysis.classification.all_categories).map(
              ([category, confidence]) => (
                <ListItem key={category}>
                  <ListItemText
                    primary={category}
                    secondary={`${(confidence * 100).toFixed(1)}% confidence`}
                  />
                </ListItem>
              )
            )}
          </List>
        </Paper>
      </TabPanel>

      <TabPanel value={value} index={2}>
        <Paper elevation={1} sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Extracted Entities
          </Typography>
          {Object.entries(analysis.entities).map(([type, entities]) => (
            <Box key={type} sx={{ mb: 2 }}>
              <Typography variant="subtitle1" gutterBottom>
                {type}
              </Typography>
              <List dense>
                {entities.map((entity, index) => (
                  <ListItem key={`${entity.text}-${index}`}>
                    <ListItemText
                      primary={entity.text}
                      secondary={`Confidence: ${(
                        entity.confidence * 100
                      ).toFixed(1)}%`}
                    />
                  </ListItem>
                ))}
              </List>
              <Divider />
            </Box>
          ))}
        </Paper>
      </TabPanel>

      <TabPanel value={value} index={3}>
        <Paper elevation={1} sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Extracted Tables
          </Typography>
          {analysis.tables.map((table) => (
            <Box key={table.table_id} sx={{ mb: 3 }}>
              <Typography variant="subtitle1" gutterBottom>
                Table {table.table_id}
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      {table.columns.map((column) => (
                        <TableCell key={column}>{column}</TableCell>
                      ))}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {table.data.map((row, rowIndex) => (
                      <TableRow key={rowIndex}>
                        {table.columns.map((column) => (
                          <TableCell key={`${rowIndex}-${column}`}>
                            {row[column]}
                          </TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
              <Typography variant="caption" color="text.secondary">
                {table.rows} rows × {table.columns_count} columns
              </Typography>
            </Box>
          ))}
        </Paper>
      </TabPanel>
    </Box>
  );
};

export default DocumentAnalysis;
