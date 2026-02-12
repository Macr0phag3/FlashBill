"""
配置常量模块

集中存放所有配置常量，便于统一管理和修改。
所有文件路径、字段映射、处理器配置都在此处定义。
"""
from pathlib import Path
from typing import List, Tuple


# ==================== 路径配置 ====================

# 数据目录
DATA_DIR = Path("data")

# 进度文件（账单处理进度）
PROGRESS_FILE = DATA_DIR / "bills.process"

# 配置文件路径
RULES_FILE = DATA_DIR / "rules.json"
CATEGORIES_FILE = DATA_DIR / "categories.json"
CATEGORIES_META_FILE = DATA_DIR / "categories_meta.json"
BOOKS_FILE = DATA_DIR / "books.json"
BOOKS_META_FILE = DATA_DIR / "books_meta.json"
DB_FILE = DATA_DIR / "DB.xlsx"


# ==================== 账单字段配置 ====================

# 账单必要字段（不存在时自动补充空值）
REQUIRED_BILL_FIELDS: List[str] = ["备注", "账本", "命中规则"]

# 标准字段列表
STANDARD_FIELDS: List[str] = [
    "交易对方", "商品说明", "交易时间", "金额", "类别", "标签", "备注"
]

# 导出时保留的字段
EXPORT_COLUMNS: List[str] = [
    "交易时间", "金额", "类别", "标签",
    "交易对方", "商品说明", "备注", "账本", "命中规则",
]


# ==================== 统计页面列名映射 ====================

# 列名映射（中文 -> 英文，用于 API 返回）
STATISTICS_COLUMN_MAPPING: dict = {
    "日期": "date",
    "金额": "amount",
    "类别": "category",
    "标签": "tag",
    "交易对方": "counter_party",
    "商品说明": "goods_desc",
    "备注": "remark",
    "账本": "book",
}

# 统计页面文本列（用于填充空值）
STATISTICS_TEXT_COLUMNS: List[str] = [
    "date", "category", "tag", "counter_party", "goods_desc", "remark", "book"
]


# ==================== 餐点相关配置 ====================

# 所有餐点类型
MEAL_PERIODS: List[str] = ["早餐", "午餐", "晚餐", "夜宵"]

# 餐点时间段定义：(开始时间, 结束时间, 餐点类型)
MEAL_TIME_PERIODS: List[Tuple[str, str, str]] = [
    ("06:00", "11:00", "早餐"),
    ("11:00", "14:00", "午餐"),
    ("17:00", "20:00", "晚餐"),
    ("20:00", "23:59", "夜宵"),
    ("00:00", "03:00", "夜宵"),
]


# ==================== 账单文件格式验证 ====================

# 支付宝账单
ALIPAY_CHECKPOINT_LINE: int = 24
ALIPAY_FORMAT_MARKER: str = f"{'-'*24}支付宝支付科技有限公司  电子客户回单{'-'*24}"

# 微信账单
WECHAT_CHECKPOINT_LINE: int = 16
WECHAT_FORMAT_MARKER: str = "----------------------微信支付账单明细列表--------------------"

# 支持的文件编码
SUPPORTED_ENCODINGS: List[str] = ['utf-8', 'gbk', 'gb2312', 'utf-16']


# ==================== 金额相关配置 ====================

# 餐补关键词
SUBSIDY_KEYWORDS: List[str] = ["因公付"]

# 餐补扣除金额
SUBSIDY_DEDUCTION: float = 20.0

# 最小金额阈值（小于此金额的交易将被忽略）
MIN_AMOUNT: float = 0.001


# ==================== 过滤规则配置 ====================

# 支付宝需要过滤的关键词（理财、转账等）
ALIPAY_FILTER_KEYWORDS: List[str] = [
    "蚂蚁财富",
    "余额宝",
    "基金销售",
    "蚂蚁合花-转入",
    "支付宝小荷包-转入",
    "自动攒",
    "实时提现",
    "余利宝转入",
    "转出到网商银行",
]


# ==================== 字段映射配置 ====================

# 微信字段到标准字段的映射
WECHAT_FIELD_MAPPING: dict = {
    "商品": "商品说明",
}


import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# ==================== OpenAI 配置 ====================

# OpenAI API 密钥（必填，从环境变量获取）
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

# OpenAI API 地址（支持自定义代理）
OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL")

# 使用的模型
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL")

# AI 打标每批处理数量（最多处理多少条未打标账单）
AI_TAG_BATCH_SIZE: int = 5

# AI 打标系统提示词
AI_TAG_SYSTEM_PROMPT: str = """
你是一个记账软件的智能打标助手。用户会提供现有的类别和标签体系，以及待打标的账单。

你的任务：
1. 根据账单的交易对方、商品说明等信息，为每笔账单分配合适的类别和标签
2. **必须优先使用用户提供的现有类别和标签**，不要创造新的
3. 【可选】给出可复用的打标规则建议，注意，这个关键字必须来自交易对方、商品说明；如果没有较好的规则推荐，不要强行给出
4. 如果你没法很好地判断，就不要给出建议，类别和标签都留空，不要强行给一个答案

返回格式（严格 JSON，不要有任何其他内容）：
{
  "tagged_bills": [
    {
      "交易订单号": "原订单号",
      "类别": "类别",
      "标签": "标签",
      "备注": ""
    }
  ],
  "suggested_rules": [
    {
      "key": "交易对方 或 商品说明",
      "rule": ["关键词"],
      "category": "类别",
      "tag": "标签",
      "comment": "注意这个不是必须的"
    }
  ]
}
"""
