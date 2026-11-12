import os
from typing import List
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from backend.app.core.exceptions import DocumentProcessingError


class TextExtractor:
    @staticmethod
    def extract_from_file(file_path: str, original_filename: str, document_id: str) -> List[Document]:
        """
        Extract text from file preserving document pages and metadata.
        Uses LangChain PyPDFLoader matching original implementation.
        """
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        try:
            if ext == ".pdf":
                loader = PyPDFLoader(file_path)
                docs = loader.load()
                # Normalize metadata: keep page number 1-indexed for human readability
                for doc in docs:
                    page_num = doc.metadata.get("page", 0)
                    doc.metadata["page"] = page_num + 1 if isinstance(page_num, int) else 1
                    doc.metadata["source"] = original_filename
                    doc.metadata["document_id"] = document_id
                return docs

            elif ext in [".txt", ".md"]:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                return [
                    Document(
                        page_content=content,
                        metadata={
                            "source": original_filename,
                            "page": 1,
                            "document_id": document_id
                        }
                    )
                ]
            else:
                raise DocumentProcessingError(f"Unsupported file format: {ext}")

        except Exception as e:
            if isinstance(e, DocumentProcessingError):
                raise
            raise DocumentProcessingError(f"Failed to extract text from {original_filename}: {str(e)}")

