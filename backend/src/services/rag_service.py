from typing import List, Dict, Any
from pathlib import Path
from sentence_transformers import SentenceTransformer
from transformers import pipeline
import chromadb
from chromadb.config import Settings
from ..config.settings import get_settings
from ..database.models import DocumentModel
from .qa_service import qa_service
import tiktoken
import re

settings = get_settings()

class RAGService:
    def __init__(self):
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=settings.CHROMA_DB_DIR,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Create or get collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="document_chunks",
            metadata={"hnsw:space": "cosine"}
        )

        # Initialize tokenizer for text chunking
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def _chunk_text(self, text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks of specified token size."""
        # Encode text into tokens
        tokens = self.tokenizer.encode(text)
        chunks = []
        
        # Calculate number of chunks
        stride = chunk_size - overlap
        for i in range(0, len(tokens), stride):
            chunk_tokens = tokens[i:i + chunk_size]
            chunk_text = self.tokenizer.decode(chunk_tokens)
            # Clean up the chunk text
            chunk_text = re.sub(r'\s+', ' ', chunk_text).strip()
            if chunk_text:
                chunks.append(chunk_text)
        
        return chunks

    async def index_document(self, document: DocumentModel) -> None:
        """Index a document by creating embeddings for its chunks."""
        try:
            # Get document text
            text = document.file_text_content
            
            # Split into chunks
            chunks = self._chunk_text(text)
            
            # Generate embeddings for chunks
            embeddings = self.embedding_model.encode(chunks)
            
            # Prepare IDs and metadata for chunks
            chunk_ids = [f"{document.id}_{i}" for i in range(len(chunks))]
            metadatas = [{
                "document_id": str(document.id),
                "document_name": document.file_name,
                "chunk_index": i
            } for i in range(len(chunks))]
            
            # Add to ChromaDB
            self.collection.add(
                ids=chunk_ids,
                embeddings=embeddings.tolist(),
                documents=chunks,
                metadatas=metadatas
            )
            
        except Exception as e:
            raise Exception(f"Error indexing document: {str(e)}")

    async def search_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant document chunks using the query."""
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query)
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=self.collection.count(),
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results["ids"][0])):
                formatted_results.append({
                    "chunk_id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "similarity": 1 - results["distances"][0][i]  # Convert distance to similarity
                })
            
            return formatted_results
            
        except Exception as e:
            raise Exception(f"Error searching documents: {str(e)}")

    async def query_documents(self, query: str, model_id: str = None) -> Dict[str, Any]:
        """Main method to search documents and generate a response."""
        try:
            # Search for relevant chunks
            search_results = await self.search_documents(query)
            print(f"Search results: {search_results}")
            
            # Extract relevant text chunks and combine them
            top_chunks = search_results[:5]
            context_chunks = [result["text"] for result in top_chunks]
            combined_context = "\n\n".join(context_chunks)
            
            # Generate response using the specified model
            if model_id:
                result = qa_service.answer_question(query, combined_context, model_id)
                answer = result["answer"]
                confidence = result["confidence"]
            else:
                # Use default model if none specified
                result = qa_service.answer_question(query, combined_context)
                answer = result["answer"]
                confidence = result["confidence"]
            
            # Get document details for the sources
            print(f"Search results: {result}")
            source_documents = {}
            for result in search_results:
                doc_id = result["metadata"]["document_id"]
                if doc_id not in source_documents:
                    document = await DocumentModel.get(doc_id)
                    if document:
                        source_documents[doc_id] = {
                            "id": doc_id,
                            "file_name": document.file_name,
                            "similarity": result["similarity"]
                        }
            
            return {
                "answer": answer,
                "confidence": confidence,
                "sources": list(source_documents.values())
            }
            
        except Exception as e:
            raise Exception(f"Error querying documents: {str(e)}")

# Create singleton instance
rag_service = RAGService() 