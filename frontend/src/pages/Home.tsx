import { Box } from "@mui/material";
import DocumentViewer from "../components/DocumentViewer";

interface HomeProps {
  selectedFile?: File;
}

const Home = ({ selectedFile }: HomeProps) => {
  return (
    <Box sx={{ height: "100%", overflow: "hidden" }}>
      <DocumentViewer file={selectedFile} />
    </Box>
  );
};

export default Home;
