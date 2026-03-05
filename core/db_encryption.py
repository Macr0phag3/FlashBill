"""
数据库文件加解密工具

对 data/DB.xlsx 执行密码加密/解密，避免明文落盘。
"""
from __future__ import annotations

import os
from pathlib import Path

from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Protocol.KDF import PBKDF2


MAGIC = b"BILLDBENCv1\x00"
SALT_SIZE = 16
NONCE_SIZE = 12
TAG_SIZE = 16
KEY_SIZE = 32
PBKDF2_ROUNDS = 200_000


class DBEncryptionError(Exception):
    """数据库加解密错误"""


class DBAlreadyEncryptedError(DBEncryptionError):
    """文件已加密"""


class DBNotEncryptedError(DBEncryptionError):
    """文件未加密"""


class DBWrongPasswordError(DBEncryptionError):
    """密码错误"""


def _ensure_file_exists(file_path: Path) -> None:
    if not file_path.exists():
        raise DBEncryptionError(f"数据库文件不存在: {file_path}")
    if not file_path.is_file():
        raise DBEncryptionError(f"数据库路径不是文件: {file_path}")


def _derive_key(password: str, salt: bytes) -> bytes:
    return PBKDF2(
        password=password.encode("utf-8"),
        salt=salt,
        dkLen=KEY_SIZE,
        count=PBKDF2_ROUNDS,
        hmac_hash_module=SHA256,
    )


def _is_valid_excel_bytes(content: bytes) -> bool:
    # XLSX 本质是 zip，通常以 PK 头开始
    return content.startswith(b"PK\x03\x04")


def is_db_encrypted(file_path: Path) -> bool:
    """判断文件是否为本项目自定义加密格式"""
    if not file_path.exists() or file_path.stat().st_size < len(MAGIC):
        return False
    with file_path.open("rb") as f:
        prefix = f.read(len(MAGIC))
    return prefix == MAGIC


def encrypt_db_file(file_path: Path, password: str) -> None:
    """加密数据库文件"""
    _ensure_file_exists(file_path)

    if not password:
        raise DBEncryptionError("密码不能为空")
    if is_db_encrypted(file_path):
        raise DBAlreadyEncryptedError("数据库已经是加密状态")

    plain = file_path.read_bytes()
    if not _is_valid_excel_bytes(plain):
        raise DBEncryptionError("数据库文件不是有效的 xlsx 文件")

    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key = _derive_key(password, salt)

    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(plain)

    encrypted_payload = MAGIC + salt + nonce + tag + ciphertext

    temp_file = file_path.with_suffix(file_path.suffix + ".enc_tmp")
    temp_file.write_bytes(encrypted_payload)
    temp_file.replace(file_path)


def decrypt_db_file(file_path: Path, password: str) -> None:
    """解密数据库文件"""
    _ensure_file_exists(file_path)

    if not password:
        raise DBEncryptionError("密码不能为空")
    if not is_db_encrypted(file_path):
        raise DBNotEncryptedError("数据库当前不是加密状态")

    encrypted_payload = file_path.read_bytes()
    min_size = len(MAGIC) + SALT_SIZE + NONCE_SIZE + TAG_SIZE
    if len(encrypted_payload) <= min_size:
        raise DBEncryptionError("加密文件格式不完整")

    offset = len(MAGIC)
    salt = encrypted_payload[offset : offset + SALT_SIZE]
    offset += SALT_SIZE
    nonce = encrypted_payload[offset : offset + NONCE_SIZE]
    offset += NONCE_SIZE
    tag = encrypted_payload[offset : offset + TAG_SIZE]
    offset += TAG_SIZE
    ciphertext = encrypted_payload[offset:]

    key = _derive_key(password, salt)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)

    try:
        plain = cipher.decrypt_and_verify(ciphertext, tag)
    except ValueError as exc:
        raise DBWrongPasswordError("密码错误，解密失败") from exc

    if not _is_valid_excel_bytes(plain):
        raise DBEncryptionError("解密后的文件不是有效的 xlsx 数据")

    temp_file = file_path.with_suffix(file_path.suffix + ".dec_tmp")
    temp_file.write_bytes(plain)
    temp_file.replace(file_path)
