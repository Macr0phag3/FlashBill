"""
分类管理路由

处理分类的页面展示和 API 操作。
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from core.utils import load_categories, save_categories

# ==================== Blueprint 配置 ====================
categories_bp = Blueprint('categories', __name__)


# ==================== 工具函数 ====================
def parse_tags(tags_str: str) -> list:
    """将逗号分隔的标签字符串转换为列表"""
    return [tag.strip() for tag in tags_str.split(",") if tag.strip()]


# ==================== 路由：分类页面 ====================
@categories_bp.route("/categories", methods=["GET", "POST"])
def handle_categories():
    """分类页面和表单处理"""
    if request.method == "GET":
        return render_template("categories.html", categories=load_categories())
    
    # POST: 处理表单提交
    new_categories = {}
    form = request.form
    
    # 解析现有类别（category_0, category_1, ...）
    existing_keys = [k for k in form.keys() 
                     if k.startswith("category_") and not k.endswith("_new")]
    
    for key in existing_keys:
        idx = key.split("_")[-1]
        category = form.get(f"category_{idx}", "").strip()
        if category:
            tags = parse_tags(form.get(f"tags_{idx}", ""))
            new_categories[category] = tags
    
    # 解析新类别
    category_new = form.get("category_new", "").strip()
    if category_new:
        new_categories[category_new] = parse_tags(form.get("tags_new", ""))
    
    save_categories(new_categories)
    return redirect(url_for("categories.handle_categories"))


# ==================== 路由：分类 API ====================
@categories_bp.route("/api/categories", methods=["GET"])
def get_categories():
    """获取所有分类"""
    return jsonify({"success": True, "categories": load_categories()})


@categories_bp.route("/api/categories", methods=["POST"])
def update_categories():
    """更新分类"""
    try:
        data = request.get_json()
        categories = data.get("categories", {})
        
        if not isinstance(categories, dict):
            return jsonify({"success": False, "message": "无效的数据格式"}), 400
        
        save_categories(categories)
        return jsonify({"success": True, "message": "分类和标签更新成功"})
    
    except Exception as e:
        return jsonify({"success": False, "message": f"更新失败：{str(e)}"}), 500
