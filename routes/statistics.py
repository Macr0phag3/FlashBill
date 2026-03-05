"""
统计路由

处理统计页面展示和数据接口。
"""
import pandas as pd
from flask import Blueprint, render_template, request, jsonify
from core.config import DB_FILE, STATISTICS_COLUMN_MAPPING, STATISTICS_TEXT_COLUMNS
from core.db_encryption import (
    is_db_encrypted,
    encrypt_db_file,
    decrypt_db_file,
    DBEncryptionError,
    DBAlreadyEncryptedError,
    DBNotEncryptedError,
    DBWrongPasswordError,
)

# ==================== Blueprint 配置 ====================
statistics_bp = Blueprint('statistics', __name__)


# ==================== 工具函数 ====================
def load_and_process_data() -> pd.DataFrame:
    """加载并预处理统计数据"""
    df = pd.read_excel(DB_FILE)
    
    # 重命名列
    df = df.rename(columns={
        old: new for old, new in STATISTICS_COLUMN_MAPPING.items() 
        if old in df.columns
    })
    
    # 只保留需要的列
    df = df[list(STATISTICS_COLUMN_MAPPING.values())]
    
    # 过滤空日期行
    df = df.dropna(subset=["date"])
    
    # 填充空值
    df[STATISTICS_TEXT_COLUMNS] = df[STATISTICS_TEXT_COLUMNS].fillna("")
    df["amount"] = df["amount"].fillna(0)
    df["remark"] = df["remark"].astype(str)
    
    return df


# ==================== 路由：统计页面 ====================
@statistics_bp.route("/statistics")
def statistics_page():
    """统计页面"""
    return render_template("statistics.html")


# ==================== 路由：统计 API ====================
@statistics_bp.route("/api/statistics")
def get_statistics():
    """
    获取统计数据
    
    支持参数：sort_by, sort_order, page, page_size
    """
    try:
        if is_db_encrypted(DB_FILE):
            return jsonify({
                "success": False,
                "error": "数据库已加密，请先解密",
                "code": "DB_ENCRYPTED",
            }), 423

        df = load_and_process_data()
        
        # 排序
        sort_by = request.args.get("sort_by", "")
        sort_order = request.args.get("sort_order", "")
        if sort_by and sort_order:
            df = df.sort_values(by=sort_by, ascending=(sort_order == "asc"))
        
        # 分页
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 20))
        total = len(df)
        
        start = (page - 1) * page_size
        df_page = df.iloc[start : start + page_size]
        
        return jsonify({
            "success": True,
            "items": df_page.to_dict("records"),
            "total": total,
            "all_items": df.to_dict("records"),
        })
    
    except Exception as e:
        print(f"Error in get_statistics: {e}")
        return jsonify({"success": False, "error": str(e)})


@statistics_bp.route("/api/statistics/db-encryption-status", methods=["GET"])
def get_db_encryption_status():
    """获取 DB.xlsx 加密状态"""
    try:
        return jsonify({
            "success": True,
            "encrypted": is_db_encrypted(DB_FILE),
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"获取加密状态失败: {str(e)}"}), 500


@statistics_bp.route("/api/statistics/db-encrypt", methods=["POST"])
def encrypt_db():
    """加密 DB.xlsx"""
    data = request.get_json(silent=True) or {}
    password = (data.get("password") or "").strip()

    if not password:
        return jsonify({"success": False, "message": "密码不能为空"}), 400

    try:
        encrypt_db_file(DB_FILE, password)
        return jsonify({"success": True, "message": "数据加密成功"})
    except DBAlreadyEncryptedError as e:
        return jsonify({"success": False, "message": str(e)}), 409
    except DBEncryptionError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"数据加密失败: {str(e)}"}), 500


@statistics_bp.route("/api/statistics/db-decrypt", methods=["POST"])
def decrypt_db():
    """解密 DB.xlsx"""
    data = request.get_json(silent=True) or {}
    password = (data.get("password") or "").strip()

    if not password:
        return jsonify({"success": False, "message": "密码不能为空"}), 400

    try:
        decrypt_db_file(DB_FILE, password)
        return jsonify({"success": True, "message": "数据解密成功"})
    except DBNotEncryptedError as e:
        return jsonify({"success": False, "message": str(e)}), 409
    except DBWrongPasswordError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except DBEncryptionError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"数据解密失败: {str(e)}"}), 500
