"""
主题注册表加载器

负责从 static/themes/*/manifest.json 自动发现主题，并生成前端可消费的主题清单。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _safe_int(value: Any, default: int = 1000) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_mode(value: Any) -> str:
    mode = str(value or "light").strip().lower()
    if mode not in {"light", "dark"}:
        return "light"
    return mode


def load_theme_registry(static_folder: str) -> list[dict[str, Any]]:
    """
    从 static/themes 目录加载主题注册表。

    约定:
    1. 每个主题目录包含 manifest.json 和 theme.css
    2. manifest 至少包含 name 字段，id 默认使用目录名
    """
    themes_root = Path(static_folder) / "themes"
    if not themes_root.exists() or not themes_root.is_dir():
        return []

    registry: list[dict[str, Any]] = []
    for theme_dir in themes_root.iterdir():
        if not theme_dir.is_dir():
            continue

        manifest_path = theme_dir / "manifest.json"
        stylesheet_path = theme_dir / "theme.css"
        if not manifest_path.exists() or not stylesheet_path.exists():
            continue

        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue

        theme_id = str(manifest.get("id") or theme_dir.name).strip()
        if not theme_id:
            continue

        registry.append(
            {
                "id": theme_id,
                "name": str(manifest.get("name") or theme_id),
                "description": str(manifest.get("description") or ""),
                "author": str(manifest.get("author") or ""),
                "version": str(manifest.get("version") or "0.1.0"),
                "mode": _safe_mode(manifest.get("mode")),
                "order": _safe_int(manifest.get("order"), 1000),
                "stylesheet": str(manifest.get("stylesheet") or f"themes/{theme_dir.name}/theme.css"),
            }
        )

    registry.sort(key=lambda item: (item["order"], item["name"]))
    return registry
