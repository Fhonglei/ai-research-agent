from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_invalid_report_id_is_rejected():
    response = client.get("/api/report/bad.report")

    assert response.status_code == 400
