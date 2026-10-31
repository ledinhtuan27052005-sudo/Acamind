"""Regression checks for private uploaded PDFs and the public corpus."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.db.postgres import SessionLocal
from app.models.document import Document, User
from main import app


class DocumentAccessSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()
        cls.owner = cls.db.query(User).filter(User.email == "acamind-browser-a2528485@example.test").first()
        cls.private = cls.db.query(Document).filter(Document.filename == "browser_study_a.pdf").first()
        cls.public = cls.db.query(Document).filter(Document.user_id.is_(None)).first()
        cls.admin_corpus = cls.db.query(Document).join(User, Document.user_id == User.id).filter(User.role == "admin").first()
        cls.other = cls.db.query(User).filter(User.id != cls.owner.id, User.role != "admin").first() if cls.owner else None
        if not cls.owner or not cls.private or not cls.public:
            raise unittest.SkipTest("Local security smoke documents are unavailable")
        cls.client = TestClient(app)
        token = create_access_token({"sub": str(cls.owner.id)})
        cls.auth = {"Authorization": f"Bearer {token}"}

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "db"):
            cls.db.close()

    def test_guest_cannot_read_private_document(self):
        doc_id = str(self.private.id)
        for path in (
            f"/api/v1/document/{doc_id}",
            f"/api/v1/document/{doc_id}/file",
            f"/api/v1/document/{doc_id}/highlighted-file",
            f"/api/v1/library/articles/{doc_id}",
            f"/api/v1/library/articles/{doc_id}/pdf",
        ):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)

    def test_owner_can_read_private_document(self):
        doc_id = str(self.private.id)
        for path in (f"/api/v1/document/{doc_id}", f"/api/v1/document/{doc_id}/file"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path, headers=self.auth).status_code, 200)

    def test_other_user_cannot_read_private_document(self):
        if not self.other:
            self.skipTest("No second non-admin account")
        token = create_access_token({"sub": str(self.other.id)})
        headers = {"Authorization": f"Bearer {token}"}
        doc_id = str(self.private.id)
        self.assertEqual(self.client.get(f"/api/v1/document/{doc_id}/file", headers=headers).status_code, 404)
        self.assertEqual(self.client.get(f"/api/v1/library/articles/{doc_id}", headers=headers).status_code, 404)

    def test_guest_list_excludes_private_document(self):
        for path, key in (("/api/v1/document/list", "documents"), ("/api/v1/library/articles", None)):
            with self.subTest(path=path):
                result = self.client.get(path)
                self.assertEqual(result.status_code, 200)
                rows = result.json()[key] if key else result.json()
                ids = {row["id"] for row in rows}
                self.assertNotIn(str(self.private.id), ids)
                self.assertIn(str(self.public.id), ids)

    def test_guest_cannot_lookup_or_retrieve_private_document(self):
        lookup = self.client.get("/api/v1/document/lookup", params={"filename": self.private.filename})
        self.assertEqual(lookup.status_code, 404)
        response = self.client.post("/api/v1/chat", json={"query": "Summarize this paper", "document_ids": [str(self.private.id)]})
        self.assertEqual(response.status_code, 404)

    def test_public_document_stays_readable(self):
        self.assertEqual(self.client.get(f"/api/v1/document/{self.public.id}").status_code, 200)
        if self.admin_corpus:
            self.assertEqual(self.client.get(f"/api/v1/document/{self.admin_corpus.id}").status_code, 200)


if __name__ == "__main__":
    unittest.main()
