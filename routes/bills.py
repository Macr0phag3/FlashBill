"""
账单管理路由

处理账单上传、获取、统计、自动打标、导出等操作。
"""
import os
import json
import io
import pandas as pd
from flask import Blueprint, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
from core.utils import Alipay, Wechat, apply_rules_to_bills, ai_tag_bills, load_rules, save_rules
from core.config import PROGRESS_FILE, EXPORT_COLUMNS

# ==================== Blueprint 配置 ====================
bills_bp = Blueprint('bills', __name__)

# 支持的账单处理器映射
BILL_PROCESSORS = {
    "alipay": (Alipay, "支付宝"),
    "wechat": (Wechat, "微信"),
}


# ==================== 账单状态访问器 ====================
def get_current_bills() -> dict:
    """获取当前账单数据（延迟导入避免循环依赖）"""
    from app import current_bills
    return current_bills


def set_current_bills(bills: dict) -> None:
    """设置当前账单数据"""
    import app
    app.current_bills = bills


def ensure_dict_format(bills) -> dict:
    """确保账单数据为字典格式"""
    if isinstance(bills, list):
        return {bill["交易订单号"]: bill for bill in bills}
    return bills


def save_to_progress(bills: dict) -> None:
    """保存账单到进度文件"""
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(bills, f, ensure_ascii=False, indent=2)


# ==================== 路由：基础账单操作 ====================
@bills_bp.route("/bills")
def get_bills():
    """获取当前账单"""
    bills = get_current_bills()
    if bills:
        return jsonify({"success": True, "bills": bills})
    return jsonify({"success": False, "message": "没有账单数据"})


@bills_bp.route("/upload", methods=["POST"])
def upload_file():
    """上传账单文件（支持 CSV/XLSX，支付宝/微信）"""
    # 验证文件
    if "file" not in request.files:
        return jsonify({"error": "没有文件"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "没有选择文件"}), 400
    
    if not (file.filename.endswith(".xlsx") or file.filename.endswith(".csv")):
        return jsonify({"error": "不支持的文件格式"}), 400
    
    # 保存上传文件
    filename = secure_filename(file.filename)
    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)
    
    # 转换 xlsx 为 csv
    if file.filename.endswith(".xlsx"):
        df = pd.read_excel(filepath)
        csv_path = os.path.join(current_app.config["UPLOAD_FOLDER"], "temp.csv")
        df.to_csv(csv_path, index=False)
    else:
        csv_path = filepath
    
    # 获取账单类型
    bill_type = request.form.get("bill_type", "alipay")
    if bill_type not in BILL_PROCESSORS:
        return jsonify({"error": "不支持的账单类型"}), 400
    
    # 解析账单
    ProcessorClass, book_name = BILL_PROCESSORS[bill_type]
    processor = ProcessorClass(csv_path)
    bills = processor.bill
    
    # 标记账本来源
    for bill in bills.values():
        bill["账本"] = book_name
    
    save_to_progress(bills)
    set_current_bills(bills)
    
    return jsonify({"success": True, "bills": list(bills.values())})


# ==================== 路由：账单 API ====================
@bills_bp.route("/api/bills", methods=["GET"])
def api_bills():
    """获取账单列表（按时间倒序）"""
    try:
        bills = get_current_bills()
        if not bills:
            return jsonify({"success": False, "message": "没有账单数据"})
        
        bills = ensure_dict_format(bills)
        set_current_bills(bills)
        
        bills_list = sorted(
            bills.values(),
            key=lambda x: x.get("交易时间", ""),
            reverse=True
        )
        return jsonify({"success": True, "bills": bills_list})
    
    except Exception as e:
        return jsonify({"success": False, "message": f"获取账单数据失败: {str(e)}"}), 500


@bills_bp.route("/api/bill_stats", methods=["GET"])
def api_bill_stats():
    """获取账单标记统计"""
    try:
        bills = get_current_bills()
        if not bills:
            return jsonify({"success": False, "message": "没有账单数据"})
        
        bills = ensure_dict_format(bills)
        set_current_bills(bills)
        
        total = len(bills)
        
        category_tagged = sum(1 for b in bills.values() if b.get("类别", "").strip())
        tag_tagged = sum(1 for b in bills.values() if b.get("标签", "").strip() not in ["-", ""])
        
        cat_pct = round(category_tagged / total * 100, 2) if total else 0
        tag_pct = round(tag_tagged / total * 100, 2) if total else 0
        
        return jsonify({
            "success": True,
            "stats": {
                "total": total,
                "tagged": category_tagged,
                "percentage": cat_pct,
                "categoryTagged": category_tagged,
                "categoryPercentage": cat_pct,
                "tagTagged": tag_tagged,
                "tagPercentage": tag_pct,
            },
        })
    
    except Exception as e:
        return jsonify({"success": False, "message": f"获取统计数据失败: {str(e)}"}), 500


# ==================== 路由：自动打标 ====================
@bills_bp.route("/api/auto_tag", methods=["POST"])
def auto_tag():
    """根据规则自动打标"""
    if not get_current_bills():
        return jsonify({"success": False, "message": "没有账单数据"})
    
    try:
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            bills = json.load(f)
        
        bills = ensure_dict_format(bills)
        bills = apply_rules_to_bills(bills)
        
        set_current_bills(bills)
        save_to_progress(bills)
        
        return jsonify({"success": True, "message": "自动打标成功"})
    
    except Exception as e:
        return jsonify({"success": False, "message": f"自动打标失败: {str(e)}"}), 500


# ==================== 路由：导出 ====================
@bills_bp.route("/api/export", methods=["POST"])
def export_bills():
    """导出账单为 Excel 文件"""
    try:
        bills = request.json.get("bills", [])
        if not bills:
            return jsonify({"error": "没有数据可导出"}), 400
        
        df = pd.DataFrame(bills)[EXPORT_COLUMNS]
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="账单数据")
            
            worksheet = writer.sheets["账单数据"]
            for idx, col in enumerate(df.columns):
                max_len = max(df[col].astype(str).str.len().max(), len(col)) + 2
                worksheet.set_column(idx, idx, max_len)
        
        output.seek(0)
        filename = f'账单数据_{pd.Timestamp.now().strftime("%Y%m%d")}.xlsx'
        
        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=filename,
        )
    
    except Exception as e:
        print(f"导出失败：{str(e)}")
        return jsonify({"error": "导出失败"}), 500


# ==================== 路由：AI 打标 ====================
@bills_bp.route("/api/ai_tag", methods=["POST"])
def ai_tag():
    """
    AI 智能打标
    
    根据未打标的账单调用 OpenAI API 进行智能分类，
    返回打标建议和规则建议供用户确认。
    
    支持前端传入筛选后的账单列表，保持前端表格的顺序。
    """
    try:
        # 优先使用前端传来的账单数据（保持前端筛选和排序）
        data = request.json or {}
        bills_list = data.get("bills", [])
        
        # 如果前端没传，则使用后端数据
        if not bills_list:
            if not get_current_bills():
                return jsonify({"success": False, "message": "没有账单数据"})
            bills = get_current_bills()
            bills = ensure_dict_format(bills)
            bills_list = list(bills.values())
        
        # 调用 AI 打标
        result = ai_tag_bills(bills_list)
        
        return jsonify({
            "success": True,
            "tagged_bills": result.get("tagged_bills", []),
            "suggested_rules": result.get("suggested_rules", []),
        })
    
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"AI 打标失败: {str(e)}"}), 500


@bills_bp.route("/api/apply_ai_tags", methods=["POST"])
def apply_ai_tags():
    """
    应用 AI 打标结果
    
    接收用户确认的打标结果，更新账单数据。
    可选地保存用户采纳的规则建议。
    """
    try:
        data = request.json
        tagged_bills = data.get("tagged_bills", [])
        save_rules_flag = data.get("save_rules", False)
        selected_rules = data.get("selected_rules", [])
        
        if not tagged_bills and not (save_rules_flag and selected_rules):
            return jsonify({"success": False, "message": "没有要应用的打标结果或规则"})
        
        bills = get_current_bills()
        bills = ensure_dict_format(bills)
        
        # 应用打标结果
        applied_count = 0
        for tagged in tagged_bills:
            order_id = tagged.get("交易订单号")
            if order_id and order_id in bills:
                bills[order_id]["类别"] = tagged.get("类别", "")
                bills[order_id]["标签"] = tagged.get("标签", "")
                bills[order_id]["备注"] = tagged.get("备注", "")
                bills[order_id]["命中规则"] = "AI 打标"
                applied_count += 1
        
        set_current_bills(bills)
        save_to_progress(bills)
        
        # 保存用户采纳的规则（合并到现有规则）
        if save_rules_flag and selected_rules:
            existing_rules = load_rules()
            for rule in selected_rules:
                key = rule.get("key", "交易对方")
                category = rule.get("category", "")
                tag = rule.get("tag", "")
                new_keywords = rule.get("rule", [])
                
                # 查找是否有相同 key + category + tag 的现有规则
                matched_rule = None
                for existing in existing_rules:
                    if (existing.get("key") == key and 
                        existing.get("category") == category and 
                        existing.get("tag") == tag and
                        existing.get("match_mode", "keyword") == rule.get("match_mode", "keyword")):
                        matched_rule = existing
                        break
                
                if matched_rule:
                    # 合并关键词到现有规则（去重）
                    existing_keywords = matched_rule.get("rule", [])
                    for kw in new_keywords:
                        if kw not in existing_keywords:
                            existing_keywords.insert(0, kw)
                    matched_rule["rule"] = existing_keywords
                else:
                    # 没有匹配的规则，新建一条（插入到最前面）
                    new_rule = {
                        "key": key,
                        "rule": new_keywords,
                        "match_mode": rule.get("match_mode", "keyword"),
                        "category": category,
                        "tag": tag,
                        "time_based": rule.get("time_based", []),
                        "comment": rule.get("comment", "AI 建议"),
                    }
                    existing_rules.insert(0, new_rule)
            save_rules(existing_rules)
        
        return jsonify({
            "success": True,
            "message": f"成功应用 {applied_count} 条打标结果",
            "applied_count": applied_count,
        })
    
    except Exception as e:
        return jsonify({"success": False, "message": f"应用打标结果失败: {str(e)}"}), 500

