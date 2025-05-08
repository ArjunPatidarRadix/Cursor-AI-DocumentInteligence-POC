from transformers import pipeline
from pathlib import Path
import pypdf
from typing import Optional


class QAService:
    def __init__(self):
        # Initialize the question-answering pipeline with a suitable model
        self.qa_pipeline = pipeline(
            "question-answering",
            model="deepset/roberta-base-squad2",
            tokenizer="deepset/roberta-base-squad2",
        )

    def extract_text_from_pdf(self, file_path: Path) -> str:
        """Extract text from a PDF file."""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        text = ""
        try:
            with open(file_path, "rb") as file:
                pdf_reader = pypdf.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")

        return text.strip()

    def extract_text_from_document(self, file_path: Path) -> str:
        """Extract text from a document based on its extension."""
        if file_path.suffix.lower() == ".pdf":
            return self.extract_text_from_pdf(file_path)
        else:
            # For text-based files
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    return file.read().strip()
            except Exception as e:
                raise Exception(f"Error reading file: {str(e)}")

    def answer_question(self, question: str, context: str) -> dict:
        """Answer a question based on the given context."""
        try:
            # Use the QA pipeline to get the answer
            result = self.qa_pipeline(
                question=question,
                context=context,
                max_answer_length=100,
                max_seq_length=512,
                doc_stride=128,
                handle_impossible_answer=True,
            )

            # Check if the model is confident about the answer
            if result["score"] < 0.1:  # Confidence threshold
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
