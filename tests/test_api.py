"""Automated test cases for FastAPI web endpoints and REST API routes."""

import io
from pathlib import Path
import pytest
from starlette.testclient import TestClient

from main import app
from src.config import SAMPLE_DIR


@pytest.fixture(scope="module")
def client():
    """Module-scoped FastAPI TestClient."""
    return TestClient(app)


class TestAPIEndpoints:
    """Validate all web service and API endpoints."""

    def test_get_homepage(self, client: TestClient):
        """GET / must render the HTML dashboard with HTTP 200."""
        resp = client.get("/")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "PII Redaction Tool" in resp.text
        assert "Supported PII Categories" in resp.text

    def test_get_health(self, client: TestClient):
        """GET /health and GET /api/health must report system health with HTTP 200."""
        for endpoint in ["/health", "/api/health"]:
            resp = client.get(endpoint)
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "healthy"
            assert data["service"] == "pii-redaction-tool"
            assert data["spacy_available"] is True

    def test_post_redact_txt(self, client: TestClient):
        """POST /upload and /api/redact with TXT file must redact PII and return metadata."""
        sample_txt = (
            "Ticket ID: TKT-1023\n"
            "Customer: John Doe\n"
            "Email: john.doe@example.com\n"
            "Phone: +91 9876543210\n"
        ).encode("utf-8")

        for endpoint in ["/upload", "/api/redact"]:
            files = {"file": ("test_doc.txt", io.BytesIO(sample_txt), "text/plain")}
            resp = client.post(endpoint, files=files)
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "success"
            assert data["total_detected"] >= 3
            assert "download_url" in data

    def test_post_redact_docx(self, client: TestClient):
        """POST /api/redact with DOCX must successfully produce a redacted DOCX."""
        sample_docx = SAMPLE_DIR / "sample_ticket_document.docx"
        with open(sample_docx, "rb") as f:
            files = {
                "file": (
                    "sample.docx",
                    f,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            }
            resp = client.post("/api/redact", files=files)

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["total_detected"] > 0
        assert "file_id" in data

        # Verify downloading the generated file
        file_id = data["file_id"]
        download_resp = client.get(f"/api/download/{file_id}")
        assert download_resp.status_code == 200
        assert len(download_resp.content) > 1000

    def test_empty_file_rejected(self, client: TestClient):
        """Uploading an empty file must return HTTP 400 Bad Request."""
        files = {"file": ("empty.txt", io.BytesIO(b""), "text/plain")}
        resp = client.post("/api/redact", files=files)
        assert resp.status_code == 400
        assert "empty" in resp.json()["detail"].lower()

    def test_unsupported_format_rejected(self, client: TestClient):
        """Uploading unsupported extensions (e.g. .pdf) must return HTTP 400."""
        files = {"file": ("manual.pdf", io.BytesIO(b"%PDF-1.4 dummy"), "application/pdf")}
        resp = client.post("/api/redact", files=files)
        assert resp.status_code == 400
        assert "unsupported" in resp.json()["detail"].lower()

    def test_download_nonexistent_returns_404(self, client: TestClient):
        """Requesting a missing file must return HTTP 404."""
        resp = client.get("/api/download/nonexistent_document_999.docx")
        assert resp.status_code == 404

    def test_get_evaluate(self, client: TestClient):
        """GET /evaluate and GET /api/evaluate must run benchmark and return metrics."""
        for endpoint in ["/evaluate", "/api/evaluate"]:
            resp = client.get(endpoint)
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "success"
            assert "overall" in data
            assert data["overall"]["precision"] >= 0.90
            assert data["overall"]["recall"] >= 0.90
            assert "markdown_table" in data
