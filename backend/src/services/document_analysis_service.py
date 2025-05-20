from typing import Dict, List, Any, Optional
from pathlib import Path
import spacy
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
import pandas as pd
import camelot
from ..config.settings import get_settings
from ..database.models import DocumentModel
import re
import asyncio
from functools import lru_cache
import logging
import os

settings = get_settings()
logger = logging.getLogger(__name__)

class DocumentAnalysisService:
    def __init__(self):
        try:
            # Initialize NLP models
            self.nlp = spacy.load("en_core_web_lg")
            
            # Initialize classification model and tokenizer
            model_name = "facebook/bart-large-mnli"
            self.classifier_tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.classifier_model = AutoModelForSequenceClassification.from_pretrained(model_name)
            
            # Initialize classification pipeline
            self.classifier = pipeline(
                "zero-shot-classification",
                model=self.classifier_model,
                tokenizer=self.classifier_tokenizer,
                device=-1  # Use CPU
            )
            
            # Initialize summarization pipeline
            self.summarizer = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                device=-1
            )
            
            # Document categories for classification
            self.document_categories = [
                "legal", "financial", "technical", "medical", "academic",
                "business", "personal", "government", "news", "other"
            ]
            
            # Ensure Java is properly configured for tabula-py
            os.environ["JAVA_HOME"] = "/usr/lib/jvm/java-11-openjdk-amd64"
            
            logger.info("DocumentAnalysisService initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing DocumentAnalysisService: {str(e)}")
            raise

    @lru_cache(maxsize=100)
    def _cached_classify(self, text: str) -> Dict[str, Any]:
        """Cached version of document classification."""
        return self.classify_document(text)

    @lru_cache(maxsize=100)
    def _cached_extract_entities(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """Cached version of entity extraction."""
        return self.extract_entities(text)

    async def analyze_document(self, document: DocumentModel) -> Dict[str, Any]:
        """Perform comprehensive document analysis."""
        try:
            # Get document text
            doc_text = document.file_text_content
            
            # Run analysis tasks concurrently
            tasks = [
                asyncio.to_thread(self._cached_classify, doc_text),
                asyncio.to_thread(self._cached_extract_entities, doc_text),
                asyncio.to_thread(self.generate_summary, doc_text),
                asyncio.to_thread(self.extract_tables, document.file_path)
            ]
            
            classification, entities, summary, tables = await asyncio.gather(*tasks)
            
            # Update document with analysis results
            document.file_extracted_details = {
                "classification": classification,
                "entities": entities,
                "summary": summary,
                "tables": tables
            }
            await document.save()
            
            logger.info(f"Document analysis completed for {document.file_name}")
            return document.file_extracted_details
            
        except Exception as e:
            logger.error(f"Error analyzing document {document.file_name}: {str(e)}")
            raise Exception(f"Error analyzing document: {str(e)}")

    def classify_document(self, text: str) -> Dict[str, Any]:
        """Classify document into predefined categories."""
        try:
            # Prepare text for classification
            text = text[:512]  # Limit text length for classification
            
            # Get classification results
            results = self.classifier(
                text,
                candidate_labels=self.document_categories,
                hypothesis_template="This document is about {}."
            )
            
            # Format results
            return {
                "category": results["labels"][0],
                "confidence": results["scores"][0],
                "all_categories": dict(zip(results["labels"], results["scores"]))
            }
            
        except Exception as e:
            logger.error(f"Error classifying document: {str(e)}")
            raise Exception(f"Error classifying document: {str(e)}")

    def extract_entities(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """Extract named entities from document."""
        try:
            # Process text with spaCy
            doc = self.nlp(text)
            
            # Group entities by type
            entities = {}
            for ent in doc.ents:
                if ent.label_ not in entities:
                    entities[ent.label_] = []
                
                entities[ent.label_].append({
                    "text": ent.text,
                    "start": ent.start_char,
                    "end": ent.end_char,
                    "confidence": 0.95  # spaCy doesn't provide confidence scores
                })
            
            return entities
            
        except Exception as e:
            logger.error(f"Error extracting entities: {str(e)}")
            raise Exception(f"Error extracting entities: {str(e)}")

    def generate_summary(self, text: str) -> Dict[str, Any]:
        """Generate document summary."""
        try:
            # Split text into chunks if too long
            max_chunk_length = 1024
            chunks = [text[i:i + max_chunk_length] 
                     for i in range(0, len(text), max_chunk_length)]
            
            # Generate summary for each chunk
            summaries = []
            for chunk in chunks:
                # Calculate appropriate max_length based on input length
                max_length = max(30, min(130, len(chunk) // 2))
                min_length = max(10, min(30, len(chunk) // 4))
                
                summary = self.summarizer(
                    chunk,
                    max_length=max_length,
                    min_length=min_length,
                    do_sample=False
                )
                summaries.append(summary[0]["summary_text"])
            
            # Combine summaries
            combined_summary = " ".join(summaries)
            
            return {
                "summary": combined_summary,
                "original_length": len(text),
                "summary_length": len(combined_summary),
                "compression_ratio": len(combined_summary) / len(text)
            }
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            raise Exception(f"Error generating summary: {str(e)}")

    def extract_tables(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract tables from document."""
        try:
            # Check if file is PDF
            if not file_path.lower().endswith('.pdf'):
                return []
            
            # Extract tables using camelot-py
            try:
                # Try lattice mode first (better for tables with borders)
                tables = camelot.read_pdf(
                    file_path,
                    pages='all',
                    flavor='lattice'
                )
                
                # If no tables found, try stream mode (better for tables without borders)
                if len(tables) == 0:
                    tables = camelot.read_pdf(
                        file_path,
                        pages='all',
                        flavor='stream'
                    )
                
            except Exception as e:
                logger.error(f"Error reading PDF with camelot: {str(e)}")
                return []
            
            # Convert tables to list of dictionaries
            extracted_tables = []
            for i, table in enumerate(tables):
                if table.df is not None and not table.df.empty:
                    # Clean up the table data
                    df = table.df.fillna('')  # Replace NaN with empty string
                    # Use map instead of applymap
                    df = df.map(lambda x: str(x).strip())  # Clean up cell values
                    
                    # Convert DataFrame to dictionary with string keys
                    table_data = []
                    for _, row in df.iterrows():
                        row_dict = {}
                        for col in df.columns:
                            row_dict[str(col)] = str(row[col])
                        table_data.append(row_dict)
                    
                    extracted_tables.append({
                        "table_id": str(i + 1),  # Convert to string
                        "data": table_data,
                        "columns": [str(col) for col in df.columns],
                        "rows": len(df),
                        "columns_count": len(df.columns),
                        "accuracy": float(table.accuracy)  # Convert to float
                    })
            
            return extracted_tables
            
        except Exception as e:
            logger.error(f"Error extracting tables: {str(e)}")
            return []  # Return empty list instead of raising exception

# Create singleton instance
document_analysis_service = DocumentAnalysisService() 