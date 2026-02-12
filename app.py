"""
记账应用主入口

Flask 应用初始化和 Blueprint 注册
"""
import os
from flask import Flask, render_template, redirect

from routes.categories import categories_bp
from routes.rules import rules_bp
from routes.bills import bills_bp
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
app.register_blueprint(progress_bp)
app.register_blueprint(statistics_bp)


# ==================== 首页路由 ====================
@app.route("/")
def index():
    """首页重定向到统计页面"""
    return redirect("/statistics")


@app.route("/tagging")
def tagging():
    """新增记账（原首页）"""
    return render_template("tagging.html")


@app.route("/books")
def books():
    """账本管理页面"""
    return render_template("books.html")


# ==================== 启动应用 ====================
if __name__ == "__main__":
    app.run(
        debug=os.getenv("FLASK_DEBUG", "1") == "1",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
    )
