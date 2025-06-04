from transformers import pipeline
from pathlib import Path
import pypdf
from typing import Optional, Dict
from ..database.models import ModelType
import logging

logger = logging.getLogger(__name__)


class QAService:
    def __init__(self):
        # Initialize model pipelines
        self.qa_pipelines: Dict[str, any] = {}
        self.default_model = "roberta-base-squad2"
        
        # Initialize the default pipeline
        self._load_pipeline(self.default_model)

    def _load_pipeline(self, model_id: str):
        """Load a model pipeline if not already loaded"""
        if model_id not in self.qa_pipelines:
            # Map short model IDs to full HuggingFace model IDs
            model_map = {
                "roberta-base-squad2": "deepset/roberta-base-squad2",
                "distilbert-base-cased-distilled-squad": "distilbert-base-cased-distilled-squad",
                "bert-large-uncased-whole-word-masking-finetuned-squad": "bert-large-uncased-whole-word-masking-finetuned-squad",
                "deepset/tinyroberta-squad2": "deepset/tinyroberta-squad2",
                "distilbert-base-uncased-distilled-squad": "distilbert-base-uncased-distilled-squad",
                "deepset/minilm-uncased-squad2": "deepset/minilm-uncased-squad2"
            }
            
            full_model_id = model_map.get(model_id, model_id)
            self.qa_pipelines[model_id] = pipeline(
                "question-answering",
                model=full_model_id,
                tokenizer=full_model_id,
            )

    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from a PDF file."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        text = ""
        try:
            with open(file_path, "rb") as file:
                pdf_reader = pypdf.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise Exception(f"Error extracting text from PDF: {str(e)}")

        return text.strip()

    def extract_text_from_document(self, file_path: str) -> str:
        """Extract text from a document based on its extension."""
        file_path = Path(file_path)
        if file_path.suffix.lower() == ".pdf":
            return self.extract_text_from_pdf(str(file_path))
        else:
            # For text-based files
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    return file.read().strip()
            except Exception as e:
                logger.error(f"Error reading file: {str(e)}")
                raise Exception(f"Error reading file: {str(e)}")

    def answer_question(self, question: str, context: str, model_id: Optional[ModelType] = None) -> dict:
        """Answer a question based on the given context using the specified model."""
        try:
            # Use specified model or default
            model_id = model_id or self.default_model
            
            # Load the model pipeline if not already loaded
            self._load_pipeline(model_id)
            
            # Get the pipeline for the specified model
            print(f"Using model: {model_id}")
            qa_pipeline = self.qa_pipelines[model_id]
            
            # Use the QA pipeline to get the answer
            result = qa_pipeline(
                question=question,
                context=context,
                # max_answer_length=100,
                # max_seq_length=512,
                # doc_stride=128,
                # handle_impossible_answer=True,
            )

            # Check if the model is confident about the answer
            if result["score"] < 0:  # Confidence threshold
                return {
                    "answer": "I'm not confident about the answer to this question based on the provided document.",
                    "confidence": result["score"],
                    "success": False,
                }

            return {
                "answer": result["answer"],
                "confidence": result["score"],
                "success": True,
            }
        except Exception as e:
            return {
                "answer": f"Error processing question: {str(e)}",
                "confidence": 0.0,
                "success": False,
            }


# Create a singleton instance
qa_service = QAService()
