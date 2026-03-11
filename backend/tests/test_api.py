"""
Tests for the Sales Insight Automator API.
"""

import io
import os
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

# Set env vars before importing app
os.environ["GROQ_API_KEY"] = "test-key"
os.environ["RESEND_API_KEY"] = "test-key"
os.environ["API_KEY_REQUIRED"] = "false"

from main import app

client = TestClient(app)


# ── Health Check Tests ────────────────────────────────────────
class TestHealthCheck:
    def test_health_returns_200(self):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data

    def test_health_reports_service_status(self):
        response = client.get("/api/health")
        data = response.json()
        assert data["services"]["ai_engine"] == "configured"
        assert data["services"]["email_service"] == "configured"


# ── File Validation Tests ────────────────────────────────────
class TestFileValidation:
    def test_rejects_invalid_file_type(self):
        file_content = b"some text content"
        response = client.post(
            "/api/upload",
            files={"file": ("test.txt", io.BytesIO(file_content), "text/plain")},
            data={"email": "test@example.com"},
        )
        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]

    def test_rejects_empty_file(self):
        response = client.post(
            "/api/upload",
            files={"file": ("test.csv", io.BytesIO(b""), "text/csv")},
            data={"email": "test@example.com"},
        )
        assert response.status_code == 400

    def test_rejects_invalid_email(self):
        csv_content = b"col1,col2\n1,2\n3,4"
        response = client.post(
            "/api/upload",
            files={"file": ("test.csv", io.BytesIO(csv_content), "text/csv")},
            data={"email": "not-an-email"},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["status"] == "error"

    @patch("main.generate_summary", new_callable=AsyncMock)
    @patch("main.send_summary_email", new_callable=AsyncMock)
    def test_accepts_valid_csv(self, mock_email, mock_ai):
        mock_ai.return_value = "Test summary content"
        mock_email.return_value = {"status": "sent", "email_id": "test-123"}

        csv_content = b"product,sales,revenue\nWidget A,100,5000\nWidget B,200,10000"
        response = client.post(
            "/api/upload",
            files={"file": ("sales.csv", io.BytesIO(csv_content), "text/csv")},
            data={"email": "test@example.com"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "summary_preview" in data

    @patch("main.generate_summary", new_callable=AsyncMock)
    @patch("main.send_summary_email", new_callable=AsyncMock)
    def test_accepts_valid_xlsx(self, mock_email, mock_ai):
        mock_ai.return_value = "Test summary content"
        mock_email.return_value = {"status": "sent", "email_id": "test-456"}

        # Create a minimal valid XLSX file
        import pandas as pd

        df = pd.DataFrame({"product": ["A", "B"], "sales": [100, 200]})
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)

        response = client.post(
            "/api/upload",
            files={
                "file": (
                    "sales.xlsx",
                    buffer,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
            data={"email": "test@example.com"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


# ── File Parser Unit Tests ───────────────────────────────────
class TestFileParser:
    def test_parse_csv(self):
        from services.file_parser import parse_file

        content = b"name,value\nAlpha,100\nBeta,200"
        df = parse_file(content, "test.csv")
        assert len(df) == 2
        assert list(df.columns) == ["name", "value"]

    def test_parse_invalid_csv(self):
        from fastapi import HTTPException

        from services.file_parser import parse_file

        # A single-column CSV should fail our 2-column minimum
        content = b"name\nAlpha\nBeta"
        with pytest.raises(HTTPException) as exc_info:
            parse_file(content, "test.csv")
        assert exc_info.value.status_code == 400

    def test_dataframe_to_text(self):
        import pandas as pd

        from services.file_parser import dataframe_to_summary_text

        df = pd.DataFrame({"product": ["A", "B", "C"], "sales": [100, 200, 300]})
        text = dataframe_to_summary_text(df)
        assert "3 rows" in text
        assert "product" in text
        assert "sales" in text


# ── API Key Auth Tests ───────────────────────────────────────
class TestAPIKeyAuth:
    @patch.dict(os.environ, {"API_KEY_REQUIRED": "true", "API_KEY": "secret-key"})
    def test_rejects_missing_api_key(self):
        csv_content = b"col1,col2\n1,2"
        response = client.post(
            "/api/upload",
            files={"file": ("test.csv", io.BytesIO(csv_content), "text/csv")},
            data={"email": "test@example.com"},
        )
        assert response.status_code == 403

    @patch.dict(os.environ, {"API_KEY_REQUIRED": "true", "API_KEY": "secret-key"})
    @patch("main.generate_summary", new_callable=AsyncMock)
    @patch("main.send_summary_email", new_callable=AsyncMock)
    def test_accepts_valid_api_key(self, mock_email, mock_ai):
        mock_ai.return_value = "Test summary"
        mock_email.return_value = {"status": "sent", "email_id": "x"}

        csv_content = b"col1,col2\n1,2\n3,4"
        response = client.post(
            "/api/upload",
            files={"file": ("test.csv", io.BytesIO(csv_content), "text/csv")},
            data={"email": "test@example.com"},
            headers={"X-API-Key": "secret-key"},
        )
        assert response.status_code == 200
