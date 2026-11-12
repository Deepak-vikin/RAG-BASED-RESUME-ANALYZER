import os
import sys
import unittest
from starlette.testclient import TestClient

# Ensure backend is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.app.main import app
from backend.app.services.document_service import document_service
from backend.app.services.retrieval_service import retrieval_service


class TestDocumentAnalyzerBackend(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.sample_pdf = os.path.join(project_root, "resumes", "resume.pdf")

    def test_01_health_check(self):
        """Test GET /health returns 200 and healthy status."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("openrouter_configured", data)
        self.assertIn("default_model", data)
        print("✓ Health endpoint OK:", data)

    def test_02_upload_and_index_document(self):
        """Test uploading a real PDF resume and verifying FAISS indexing."""
        self.assertTrue(os.path.exists(self.sample_pdf), "Sample PDF must exist")
        
        with open(self.sample_pdf, "rb") as f:
            response = self.client.post(
                "/api/documents/upload",
                files={"file": ("test_resume.pdf", f, "application/pdf")}
            )

        self.assertEqual(response.status_code, 200, f"Upload failed: {response.text}")
        data = response.json()
        doc = data["document"]
        self.assertIn("id", doc)
        self.assertEqual(doc["filename"], "test_resume.pdf")
        self.assertGreater(doc["chunk_count"], 0)
        self.assertGreater(doc["page_count"], 0)
        print(f"✓ Upload & Index OK: Document ID {doc['id']}, Chunks: {doc['chunk_count']}, Pages: {doc['page_count']}")

        # Verify in documents list
        list_res = self.client.get("/api/documents")
        self.assertEqual(list_res.status_code, 200)
        docs = list_res.json()["documents"]
        found = any(d["id"] == doc["id"] for d in docs)
        self.assertTrue(found, "Uploaded document should appear in list")

        # Test RAG retrieval directly
        chunks = retrieval_service.retrieve_relevant_chunks("technical skills programming", document_id=doc["id"])
        self.assertGreater(len(chunks), 0, "Retrieval should return matching chunks")
        sources = retrieval_service.format_sources(chunks)
        self.assertGreater(len(sources), 0)
        print(f"✓ Vector Retrieval OK: Retrieved {len(chunks)} chunks. Source snippet: {sources[0].content_snippet[:80]}...")

        # Test prompt grounding formatting
        from backend.app.rag.prompts import format_context_from_documents, construct_rag_messages
        context = format_context_from_documents(chunks)
        self.assertIn("Sai Dhinakar", context)
        messages = construct_rag_messages("What is candidate's email?", context)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "system")
        self.assertIn("Strict Grounding Rules", messages[0]["content"])
        self.assertIn("User Question: What is candidate's email?", messages[1]["content"])
        print("✓ RAG Prompt Grounding OK: Context properly constructed and formatted.")

        # Test Chat API error handling without API key
        chat_res = self.client.post("/api/chat", json={
            "question": "What is candidate's name?",
            "document_id": doc["id"]
        })
        self.assertEqual(chat_res.status_code, 401)
        self.assertIn("OPENROUTER_API_KEY", chat_res.json()["detail"])
        print(f"✓ Chat API Authentication Check OK: {chat_res.json()['detail']}")

        # Test cleanup
        del_res = self.client.delete(f"/api/documents/{doc['id']}")
        self.assertEqual(del_res.status_code, 200)
        print(f"✓ Delete OK for {doc['id']}")


if __name__ == "__main__":
    unittest.main()
