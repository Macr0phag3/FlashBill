"""
测试数据库文件加解密
"""
from pathlib import Path

import pytest

from core.db_encryption import (
    encrypt_db_file,
    decrypt_db_file,
    is_db_encrypted,
    DBAlreadyEncryptedError,
    DBNotEncryptedError,
    DBWrongPasswordError,
    DBEncryptionError,
)


def _create_fake_xlsx(path: Path) -> bytes:
    # 仅用于测试：满足 XLSX zip 头即可
    content = b"PK\x03\x04fake-xlsx-content-for-test"
    path.write_bytes(content)
    return content


class TestDBEncryption:
    def test_encrypt_and_decrypt_roundtrip(self, tmp_path):
        db_file = tmp_path / "DB.xlsx"
        plain = _create_fake_xlsx(db_file)

        encrypt_db_file(db_file, "StrongPass!123")
        assert is_db_encrypted(db_file) is True
        assert db_file.read_bytes() != plain

        decrypt_db_file(db_file, "StrongPass!123")
        assert is_db_encrypted(db_file) is False
        assert db_file.read_bytes() == plain

    def test_encrypt_already_encrypted_file(self, tmp_path):
        db_file = tmp_path / "DB.xlsx"
        _create_fake_xlsx(db_file)

        encrypt_db_file(db_file, "pass")
        with pytest.raises(DBAlreadyEncryptedError):
            encrypt_db_file(db_file, "pass")

    def test_decrypt_with_wrong_password(self, tmp_path):
        db_file = tmp_path / "DB.xlsx"
        _create_fake_xlsx(db_file)

        encrypt_db_file(db_file, "correct")
        with pytest.raises(DBWrongPasswordError):
            decrypt_db_file(db_file, "wrong")

    def test_decrypt_plain_file_should_fail(self, tmp_path):
        db_file = tmp_path / "DB.xlsx"
        _create_fake_xlsx(db_file)

        with pytest.raises(DBNotEncryptedError):
            decrypt_db_file(db_file, "pass")

    def test_encrypt_non_xlsx_should_fail(self, tmp_path):
        db_file = tmp_path / "DB.xlsx"
        db_file.write_bytes(b"not-an-excel-file")

        with pytest.raises(DBEncryptionError):
            encrypt_db_file(db_file, "pass")
