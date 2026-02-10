"""
规则管理路由

处理规则的页面展示和 API 操作。
"""
import json
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from core.utils import load_rules, save_rules, load_categories, apply_rules_to_bills
from core.config import PROGRESS_FILE

# ==================== Blueprint 配置 ====================
rules_bp = Blueprint('rules', __name__)


# ==================== 账单状态访问器 ====================
def get_current_bills() -> dict:
    """获取当前账单数据（延迟导入避免循环依赖）"""
    from app import current_bills
    return current_bills


def set_current_bills(bills: dict) -> None:
    """设置当前账单数据"""
    import app
    app.current_bills = bills


def apply_rules_and_sync(bills: dict) -> dict:
    """应用规则并同步到进度文件"""
    updated = apply_rules_to_bills(bills)
    set_current_bills(updated)
    
    try:
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(updated, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存进度失败: {e}")
    
    return updated


# ==================== 路由：规则页面 ====================
@rules_bp.route("/rules-page")
def rules_page():
    """规则页面（简洁版）"""
    return render_template("rules.html")


@rules_bp.route("/rules", methods=["GET", "POST"])
def handle_rules():
    """规则表单处理"""
    if request.method == "GET":
        return render_template(
            "rules.html", 
            rules=load_rules(), 
            categories=load_categories()
        )
    
    # POST: 处理表单提交
    form = request.form
    new_rules = []
    
    existing_keys = [k for k in form.keys() 
                     if k.startswith("counter_party_") and not k.endswith("_new")]
    
    for key in existing_keys:
        idx = key.split("_")[-1]
        cp = form.get(f"counter_party_{idx}", "").strip()
        gd = form.get(f"goods_desc_{idx}", "").strip()
        
        if cp or gd:
            new_rules.append({
                "counter_party": cp,
                "goods_desc": gd,
                "category": form.get(f"category_{idx}", "").strip(),
                "tag": form.get(f"tag_{idx}", "").strip(),
            })
    
    cp_new = form.get("counter_party_new", "").strip()
    gd_new = form.get("goods_desc_new", "").strip()
    
    if cp_new or gd_new:
        new_rules.append({
            "counter_party": cp_new,
            "goods_desc": gd_new,
            "category": form.get("category_new", "").strip(),
            "tag": form.get("tag_new", "").strip(),
        })
    
    save_rules(new_rules)
    
    bills = get_current_bills()
    if bills:
        apply_rules_and_sync(bills)
    
    return redirect(url_for("rules.handle_rules"))


# ==================== 路由：规则 API ====================
@rules_bp.route("/api/rules", methods=["GET"])
def get_rules():
    """获取所有规则"""
    return jsonify({"success": True, "rules": load_rules()})


@rules_bp.route("/api/rules", methods=["POST"])
def update_rules():
    """更新规则"""
    try:
        data = request.get_json()
        rules = data.get("rules", [])
        
        if not isinstance(rules, list):
            return jsonify({"success": False, "message": "无效的数据格式"}), 400
        
        save_rules(rules)
        
        bills = get_current_bills()
        if bills:
            apply_rules_and_sync(bills)
        
        return jsonify({"success": True, "message": "规则已更新"})
    
    except Exception as e:
        return jsonify({"success": False, "message": f"更新失败：{str(e)}"}), 500
