import os
import sys

# Force unbuffered output so logs appear instantly
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Ensure offline embeddings if network is not available in sandbox
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import time
import asyncio
from unittest.mock import patch, AsyncMock

# Setup python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
backend_dir = os.path.join(project_root, "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print("=" * 60)
print("DocuQuery AI — Full Pipeline Verification")
print("=" * 60)

# Step 1: Config and App Import
t0 = time.time()
print("\n[1/7] Importing backend application and configuration...")
from app.config import settings
from app.api.routes.health import health_check
from app.services.text_extraction import TextExtractor
from app.rag.chunking import DocumentSplitter
from app.services.embedding_service import embedding_service
from app.services.retrieval_service import retrieval_service
from app.services.openrouter_client import openrouter_client
from app.services.llm_service import llm_service
from app.rag.prompts import format_context_from_documents, construct_rag_messages
print(f"  ✓ Imports completed in {time.time() - t0:.2f}s")
print(f"  ✓ App Name: {settings.APP_NAME}")
print(f"  ✓ Default Model: {settings.OPENROUTER_MODEL}")
print(f"  ✓ Storage Dir: {settings.DATA_DIR}")

# Step 2: Health Check Endpoint Logic
t0 = time.time()
print("\n[2/7] Testing health check logic...")
health = asyncio.run(health_check())
print(f"  ✓ Health response: {health}")
assert health["status"] == "healthy"
assert "openrouter_configured" in health

# Step 3: Text Extraction and Chunking
t0 = time.time()
print("\n[3/7] Testing PDF text extraction and chunking...")
sample_pdf = os.path.join(project_root, "resumes", "resume.pdf")
assert os.path.exists(sample_pdf), f"PDF not found at {sample_pdf}"

test_doc_id = "test-verify-doc-001"
docs = TextExtractor.extract_from_file(sample_pdf, "resume.pdf", test_doc_id)
print(f"  ✓ Extracted {len(docs)} page(s) from resume.pdf")
assert len(docs) > 0

splitter = DocumentSplitter(chunk_size=800, chunk_overlap=150)
chunks = splitter.split_documents(docs)
print(f"  ✓ Split into {len(chunks)} chunk(s) (chunk_size=800, overlap=150)")
assert len(chunks) > 0
assert chunks[0].metadata.get("chunk_index") == 0
assert chunks[0].metadata.get("document_id") == test_doc_id

# Step 4: Embedding and FAISS Vector Storage
t0 = time.time()
print("\n[4/7] Testing Sentence Transformers embedding & FAISS indexing...")
print("  (Loading all-MiniLM-L6-v2 embedding model...)")
t_embed = time.time()
store = retrieval_service.save_document_chunks(test_doc_id, chunks)
print(f"  ✓ FAISS index built and persisted in {time.time() - t_embed:.2f}s")

# Step 5: Vector Similarity Retrieval
t0 = time.time()
print("\n[5/7] Testing vector similarity search and source citation...")
query = "What are the candidate's skills and programming languages?"
retrieved = retrieval_service.retrieve_relevant_chunks(query, document_id=test_doc_id, k=3)
print(f"  ✓ Retrieved {len(retrieved)} chunk(s) for query: '{query}'")
assert len(retrieved) > 0

sources = retrieval_service.format_sources(retrieved)
print(f"  ✓ Formatted {len(sources)} source citations:")
for i, s in enumerate(sources):
    print(f"    [{i+1}] Source: {s.source}, Page: {s.page}, Snippet: {s.content_snippet[:70]}...")

context = format_context_from_documents(retrieved)
messages = construct_rag_messages(question=query, context=context)
assert len(messages) == 2
assert messages[0]["role"] == "system"
assert "Strict Grounding Rules" in messages[0]["content"]
assert messages[1]["role"] == "user"
print("  ✓ Grounding prompt structure verified (system prompt + user context)")

# Step 6: OpenRouter Client Key Validation & RAG Completion
t0 = time.time()
print("\n[6/7] Testing OpenRouter validation and end-to-end RAG synthesis...")

# Test 6a: Validation check without API key
try:
    openrouter_client._verify_api_key()
    print("  Note: OPENROUTER_API_KEY is configured in environment.")
except Exception as e:
    print(f"  ✓ Unconfigured API key caught correctly: {type(e).__name__} ({e.status_code if hasattr(e, 'status_code') else ''})")

# Test 6b: End-to-end RAG with mocked OpenRouter response
mock_answer = "Based on the provided resume, the candidate has experience in Python, SQL, and Machine Learning [Source: resume.pdf, Page: 1]."
with patch.object(openrouter_client, "chat_completion", new_callable=AsyncMock) as mock_complete:
    mock_complete.return_value = {
        "content": mock_answer,
        "model": "meta-llama/llama-3.3-70b-instruct",
        "usage": {"prompt_tokens": 150, "completion_tokens": 30}
    }

    rag_response = asyncio.run(llm_service.answer_question(
        question=query,
        document_id=test_doc_id,
        model="meta-llama/llama-3.3-70b-instruct"
    ))

    print(f"  ✓ RAG Answer generated successfully:")
    print(f"    Answer: {rag_response.answer}")
    print(f"    Model: {rag_response.model_used}")
    print(f"    Sources count: {len(rag_response.sources)}")
    assert rag_response.answer == mock_answer
    assert len(rag_response.sources) > 0

# Step 7: Cleanup Test Artifacts
t0 = time.time()
print("\n[7/7] Cleaning up test vector store...")
retrieval_service.delete_document_store(test_doc_id)
print("  ✓ Test FAISS store removed successfully.")

print("\n" + "=" * 60)
print("🎉 ALL 7 PIPELINE VERIFICATION STEPS PASSED SUCCESSFULLY!")
print("=" * 60)
