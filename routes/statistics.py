"""
统计路由

处理统计页面展示和数据接口。
"""
import pandas as pd
from flask import Blueprint, render_template, request, jsonify
from core.config import DB_FILE, STATISTICS_COLUMN_MAPPING, STATISTICS_TEXT_COLUMNS

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
