"""
测试统计页数据库加解密 API
"""
from pathlib import Path

import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture
def temp_db_file(tmp_path, monkeypatch):
    db_file = tmp_path / "DB.xlsx"
    db_file.write_bytes(b"PK\x03\x04fake-xlsx-for-api-test")
    monkeypatch.setattr("routes.statistics.DB_FILE", db_file)
    return db_file


class TestStatisticsEncryptionAPI:
    def test_encrypt_status_and_decrypt_flow(self, client, temp_db_file: Path):
        status_before = client.get("/api/statistics/db-encryption-status").get_json()
        assert status_before["success"] is True
        assert status_before["encrypted"] is False

        encrypt_resp = client.post(
            "/api/statistics/db-encrypt",
            json={"password": "TestPass!123"},
        )
        encrypt_data = encrypt_resp.get_json()
        assert encrypt_resp.status_code == 200
        assert encrypt_data["success"] is True

        status_after_encrypt = client.get("/api/statistics/db-encryption-status").get_json()
        assert status_after_encrypt["encrypted"] is True

        stats_resp = client.get("/api/statistics")
        stats_data = stats_resp.get_json()
        assert stats_resp.status_code == 423
        assert stats_data["success"] is False
        assert stats_data["code"] == "DB_ENCRYPTED"

        wrong_decrypt_resp = client.post(
            "/api/statistics/db-decrypt",
            json={"password": "WrongPassword"},
        )
        wrong_decrypt_data = wrong_decrypt_resp.get_json()
        assert wrong_decrypt_resp.status_code == 400
        assert wrong_decrypt_data["success"] is False

        decrypt_resp = client.post(
            "/api/statistics/db-decrypt",
            json={"password": "TestPass!123"},
        )
        decrypt_data = decrypt_resp.get_json()
        assert decrypt_resp.status_code == 200
        assert decrypt_data["success"] is True

        status_after_decrypt = client.get("/api/statistics/db-encryption-status").get_json()
        assert status_after_decrypt["encrypted"] is False

    def test_encrypt_with_empty_password(self, client, temp_db_file: Path):
        response = client.post("/api/statistics/db-encrypt", json={"password": ""})
        data = response.get_json()
        assert response.status_code == 400
        assert data["success"] is False

    def test_decrypt_when_not_encrypted(self, client, temp_db_file: Path):
        response = client.post("/api/statistics/db-decrypt", json={"password": "abc"})
        data = response.get_json()
        assert response.status_code == 409
        assert data["success"] is False
