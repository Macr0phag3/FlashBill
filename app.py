"""
记账应用主入口

Flask 应用初始化和 Blueprint 注册
"""
import os
from flask import Flask, render_template

from core.themes import load_theme_registry
from routes.categories import categories_bp
from routes.rules import rules_bp
from routes.bills import bills_bp
from routes.books import books_bp
from routes.progress import progress_bp
from routes.statistics import statistics_bp

# 创建 Flask 应用
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "temp_uploads"
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 16MB max-limit

# 确保上传目录存在
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# 用于存储当前账单数据（供其他模块访问）
current_bills = {}


app.register_blueprint(categories_bp)
app.register_blueprint(rules_bp)
app.register_blueprint(bills_bp)
app.register_blueprint(books_bp)
app.register_blueprint(progress_bp)
app.register_blueprint(statistics_bp)


@app.context_processor
def inject_theme_registry():
    """注入前端主题注册表，供 templates 使用"""
    registry = load_theme_registry(app.static_folder)
    return {
        "theme_registry": registry,
    }



# ==================== 首页路由 ====================
@app.route("/")
def index():
    """首页"""
    return render_template("home.html")


@app.route("/tagging")
def tagging():
    """新增记账（原首页）"""
    return render_template("tagging.html")


# ==================== 启动应用 ====================
if __name__ == "__main__":
    app.run(
        debug=os.getenv("FLASK_DEBUG", "1") == "1",
        host="0.0.0.0" if os.getenv("PUBLIC", "0") == "1" else "127.0.0.1",
        port=int(os.getenv("PORT", "8000")),
    )
