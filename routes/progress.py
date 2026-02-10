"""
进度管理路由

处理账单进度的保存、加载、检查、清除操作。
"""
import os
import json
from flask import Blueprint, request, jsonify
from core.config import PROGRESS_FILE, REQUIRED_BILL_FIELDS

# ==================== Blueprint 配置 ====================
progress_bp = Blueprint('progress', __name__)


# ==================== 账单状态访问器 ====================
def set_current_bills(bills: dict) -> None:
    """设置当前账单数据"""
    import app
    app.current_bills = bills


def ensure_required_fields(bills) -> None:
    """确保账单数据包含必要字段（原地修改）"""
    items = bills.values() if isinstance(bills, dict) else bills
    for bill in items:
        for field in REQUIRED_BILL_FIELDS:
            bill.setdefault(field, "")


# ==================== 路由：加载进度 ====================
@progress_bp.route("/api/load_progress", methods=["GET"])
def load_progress():
    """从文件加载账单进度"""
    try:
        if not os.path.exists(PROGRESS_FILE):
            return jsonify({"success": False, "message": "没有找到进度文件"})
        
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        ensure_required_fields(data)
        set_current_bills(data)
        
        return jsonify({"success": True, "bills": data})
    
    except Exception as e:
        return jsonify({"success": False, "message": f"加载进度失败: {str(e)}"})


# ==================== 路由：检查进度 ====================
@progress_bp.route("/api/check_progress", methods=["GET"])
def check_progress():
    """检查是否存在有效的进度文件"""
    try:
        has_progress = (
            os.path.exists(PROGRESS_FILE) and 
            os.path.getsize(PROGRESS_FILE) > 0
        )
        return jsonify({"success": True, "has_progress": has_progress})
    
    except Exception as e:
        return jsonify({"success": False, "message": f"检查进度失败: {str(e)}"}), 500


# ==================== 路由：清除缓存 ====================
@progress_bp.route("/api/clear_cache", methods=["POST"])
def clear_cache():
    """清除进度文件和内存数据"""
    try:
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)
        
        set_current_bills({})
        return jsonify({"success": True, "message": "缓存已清除"})
    
    except Exception as e:
        return jsonify({"success": False, "message": f"清除缓存失败: {str(e)}"})


# ==================== 路由：保存进度 ====================
@progress_bp.route("/api/save_progress", methods=["POST"])
def save_progress():
    """保存账单进度到文件"""
    try:
        data = request.get_json()
        if not data or "bills" not in data:
            return jsonify({"success": False, "message": "无效的数据格式"})
        
        bills = data["bills"]
        ensure_required_fields(bills)
        
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(bills, f, ensure_ascii=False, indent=2)
        
        return jsonify({"success": True, "message": "保存成功"})
    
    except Exception as e:
        return jsonify({"success": False, "message": f"保存失败: {str(e)}"})
