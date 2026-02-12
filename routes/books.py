"""
账本管理路由

处理账本页面展示和 API 操作。
"""
from flask import Blueprint, render_template, request, jsonify
from core.utils import load_books, save_books, load_book_meta, save_book_meta

# ==================== Blueprint 配置 ====================
books_bp = Blueprint("books", __name__)


def _normalize_fixed_quota(value):
    """将固定配额标准化为数字，默认 0"""
    if value is None or value == "":
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return 0.0
        return float(stripped)
    raise ValueError("fixed_quota 类型无效")


# ==================== 路由：账本页面 ====================
@books_bp.route("/books", methods=["GET"])
def handle_books():
    """账本管理页面"""
    return render_template("books.html")


# ==================== 路由：账本 API ====================
@books_bp.route("/api/books", methods=["GET"])
def get_books():
    """获取所有账本"""
    return jsonify({
        "success": True,
        "books": load_books(),
        "meta": load_book_meta(),
    })


@books_bp.route("/api/books", methods=["POST"])
def update_books():
    """更新账本"""
    try:
        data = request.get_json() or {}
        books = data.get("books", {})
        meta = data.get("meta", {})

        if not isinstance(books, dict):
            return jsonify({"success": False, "message": "无效的 books 数据格式"}), 400
        if not isinstance(meta, dict):
            return jsonify({"success": False, "message": "无效的 meta 数据格式"}), 400

        normalized_books = {}
        for raw_name, config in books.items():
            if not isinstance(raw_name, str):
                continue
            name = raw_name.strip()
            if not name:
                continue

            fixed_quota_raw = config.get("fixed_quota") if isinstance(config, dict) else config
            try:
                fixed_quota = _normalize_fixed_quota(fixed_quota_raw)
            except ValueError:
                return jsonify({"success": False, "message": f"账本 {name} 的固定配额格式无效"}), 400
            if fixed_quota < 0:
                return jsonify({"success": False, "message": f"账本 {name} 的固定配额不能小于 0"}), 400

            normalized_books[name] = {"fixed_quota": fixed_quota}

        normalized_meta = {}
        for raw_name, config in meta.items():
            if not isinstance(raw_name, str) or not isinstance(config, dict):
                continue
            name = raw_name.strip()
            if not name:
                continue

            normalized_meta[name] = {
                "icon": config.get("icon", "Coin"),
                "color": config.get("color", "#409EFF"),
            }

        save_books(normalized_books)
        save_book_meta(normalized_meta)

        return jsonify({"success": True, "message": "账本更新成功"})
    except Exception as e:
        return jsonify({"success": False, "message": f"更新失败：{str(e)}"}), 500
