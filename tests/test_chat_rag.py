import os
import sys
import unittest
from unittest.mock import patch, AsyncMock
from starlette.testclient import TestClient

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
backend_dir = os.path.join(project_root, "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.main import app
from app.config import settings


class TestRAGChatPipeline(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.sample_pdf = os.path.join(project_root, "resumes", "resume.pdf")

    def test_rag_chat_with_mocked_openrouter(self):
        """Test complete RAG flow from upload through grounded generation."""
        # 1. Upload document
        with open(self.sample_pdf, "rb") as f:
            upload_res = self.client.post(
                "/api/documents/upload",
                files={"file": ("candidate_resume.pdf", f, "application/pdf")}
            )
        self.assertEqual(upload_res.status_code, 200)
        doc_id = upload_res.json()["document"]["id"]

        # 2. Mock OpenRouter response
        mock_response = {
            "content": "Sai Dhinakar is proficient in Python, SQL, and Machine Learning [Source: candidate_resume.pdf, Page: 1].",
            "model": "meta-llama/llama-3.3-70b-instruct",
            "usage": {"prompt_tokens": 120, "completion_tokens": 28}
        }

        with patch("app.services.openrouter_client.openrouter_client.chat_completion", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_response

            chat_res = self.client.post("/api/chat", json={
                "question": "What are the candidate's technical skills?",
                "document_id": doc_id
            })

            self.assertEqual(chat_res.status_code, 200, f"Chat failed: {chat_res.text}")
            data = chat_res.json()
            self.assertIn("Sai Dhinakar is proficient", data["answer"])
            self.assertEqual(data["model_used"], "meta-llama/llama-3.3-70b-instruct")
            self.assertGreater(len(data["sources"]), 0)
            self.assertEqual(data["sources"][0]["source"], "candidate_resume.pdf")
            print(f"✓ End-to-End Grounded RAG Chat OK:\n  Answer: {data['answer']}\n  Sources: {len(data['sources'])} chunks")

            # Check history was recorded
            hist_res = self.client.get(f"/api/chat/history/{doc_id}")
            self.assertEqual(hist_res.status_code, 200)
            history = hist_res.json()["history"]
            self.assertEqual(len(history), 2)
            self.assertEqual(history[0]["role"], "user")
            self.assertEqual(history[1]["role"], "assistant")
            print("✓ Conversation History Recorded OK")

        # Cleanup
        self.client.delete(f"/api/documents/{doc_id}")
        print("✓ Cleanup completed.")


if __name__ == "__main__":
    unittest.main()
