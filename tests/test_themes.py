"""
主题注册表加载器测试
"""

import json

from core.themes import load_theme_registry


def test_load_theme_registry_returns_empty_when_missing_dir(tmp_path):
    registry = load_theme_registry(str(tmp_path))
    assert registry == []


def test_load_theme_registry_loads_and_sorts_themes(tmp_path):
    static_dir = tmp_path / "static"
    themes_dir = static_dir / "themes"
    themes_dir.mkdir(parents=True)

    dark_dir = themes_dir / "dark"
    dark_dir.mkdir()
    (dark_dir / "theme.css").write_text("/* dark */", encoding="utf-8")
    (dark_dir / "manifest.json").write_text(
        json.dumps(
            {
                "id": "dark",
                "name": "深色",
                "mode": "dark",
                "order": 20,
                "stylesheet": "themes/dark/theme.css",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    light_dir = themes_dir / "light"
    light_dir.mkdir()
    (light_dir / "theme.css").write_text("/* light */", encoding="utf-8")
    (light_dir / "manifest.json").write_text(
        json.dumps(
            {
                "id": "light",
                "name": "浅色",
                "mode": "light",
                "order": 10,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    registry = load_theme_registry(str(static_dir))

    assert [item["id"] for item in registry] == ["light", "dark"]
    assert registry[0]["stylesheet"] == "themes/light/theme.css"
    assert registry[1]["mode"] == "dark"
