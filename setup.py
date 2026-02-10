"""
数据初始化模块

负责在应用启动时检查必要的数据文件是否存在，
如果不存在则自动创建并写入默认数据。
"""
import os
import json
import pandas as pd
from core.config import DATA_DIR, RULES_FILE, CATEGORIES_FILE, DB_FILE

# 默认分类数据
DEFAULT_CATEGORIES = {
    "娱乐": ["游戏", "电影"],
    "行": ["共享单车", "铁路", "地铁", "加油"],
    "食": ["晚餐", "午餐", "早餐", "零食", "水果", "夜宵", "午饭", "晚饭"]
}

DEFAULT_RULES = [
    {
        "id": None,
        "category": "食",
        "rule": [
            "海底捞",
            "麦当劳",
            "肯德基"
        ],
        "key": "交易对方",
        "match_mode": "keyword",
        "time_based": [
            "全部"
        ],
        "tag": "-",
        "comment": ""
    },
    {
        "id": None,
        "category": "食",
        "rule": [
            "水果超市",
            "流动水果",
            "精品水果",
            "水果店",
            "鲜丰水果",
            "鲜果乐园",
            "水果摊",
        ],
        "key": "交易对方",
        "match_mode": "keyword",
        "time_based": [],
        "tag": "水果",
        "comment": ""
    },
    {
        "id": None,
        "category": "食",
        "rule": [
            "7分甜",
            "奈雪的茶",
            "星巴克",
            "1点点",
            "手打柠檬茶",
            "可口可乐饮料",
            "珍珠奶茶"
        ],
        "key": "交易对方",
        "match_mode": "keyword",
        "time_based": [],
        "tag": "饮料",
        "comment": "饮料"
    },
    {
        "category": "食",
        "rule": [
            "海底捞",
            "麦当劳",
            "肯德基"
        ],
        "key": "商品说明",
        "match_mode": "keyword",
        "time_based": [
            "全部"
        ],
        "tag": "-",
        "comment": ""
    },
    {
        "id": None,
        "category": "行",
        "rule": [
            "地铁",
            "轨道交通"
        ],
        "key": "商品说明",
        "match_mode": "keyword",
        "time_based": [],
        "tag": "地铁",
        "comment": ""
    },
    {
        "id": None,
        "category": "行",
        "rule": [
            "哈啰单车"
        ],
        "key": "商品说明",
        "match_mode": "keyword",
        "time_based": [],
        "tag": "共享单车",
        "comment": ""
    },
    {
        "id": None,
        "category": "行",
        "rule": [
            "中国石油"
        ],
        "key": "商品说明",
        "match_mode": "keyword",
        "time_based": [],
        "tag": "加油",
        "comment": ""
    },
    {
        "id": None,
        "category": "行",
        "rule": [
            "火车票"
        ],
        "key": "商品说明",
        "match_mode": "keyword",
        "time_based": [],
        "tag": "铁路",
        "comment": ""
    },
    {
        "id": None,
        "category": "娱乐",
        "rule": [
            "电影院",
            "电影票"
        ],
        "key": "商品说明",
        "match_mode": "keyword",
        "time_based": [],
        "tag": "电影",
        "comment": ""
    }
]

ENV_FILE = ".env"
DEFAULT_ENV = """# OpenAI Configuration
OPENAI_API_KEY=
OPENAI_BASE_URL=
OPENAI_MODEL=gpt-5.2
"""

def initialize_data_files():
    """初始化数据文件"""
    # 1. 确保 data 目录存在
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"[Init] 创建数据目录: {DATA_DIR}")

    # 2. 初始化 rules.json
    if not os.path.exists(RULES_FILE):
        with open(RULES_FILE, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_RULES, f, ensure_ascii=False, indent=2)
        print(f"[Init] 创建默认规则文件: {RULES_FILE}")

    # 3. 初始化 categories.json
    if not os.path.exists(CATEGORIES_FILE):
        with open(CATEGORIES_FILE, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_CATEGORIES, f, ensure_ascii=False, indent=4)
        print(f"[Init] 创建默认分类文件: {CATEGORIES_FILE}")

    # 4. 初始化 DB.xlsx
    if not os.path.exists(DB_FILE):
        # 统计模块依赖的列名
        columns = ['日期', '金额', '类别', '标签', '交易对方', '商品说明', '备注', '账本']
        df = pd.DataFrame(columns=columns)
        df.to_excel(DB_FILE, index=False)
        print(f"[Init] 创建空数据库文件: {DB_FILE}")

    # 5. 初始化 .env
    if not os.path.exists(ENV_FILE):
        with open(ENV_FILE, 'w', encoding='utf-8') as f:
            f.write(DEFAULT_ENV)
        print(f"[Init] 创建默认环境变量文件: {ENV_FILE}")

