"""
数据初始化模块

负责在应用启动时检查必要的数据文件是否存在，
如果不存在则自动创建并写入默认数据。
"""
import os
import json
import random
from datetime import datetime, timedelta
import pandas as pd
from core.config import (
    DATA_DIR,
    RULES_FILE,
    CATEGORIES_FILE,
    CATEGORIES_META_FILE,
    BOOKS_FILE,
    BOOKS_META_FILE,
    DB_FILE,
)

# 默认分类数据
DEFAULT_CATEGORIES = {
    "娱乐": ["游戏", "电影"],
    "行": ["共享单车", "铁路", "地铁", "加油"],
    "食": ["晚餐", "午餐", "早餐", "零食", "水果", "夜宵", "午饭", "晚饭", "饮料"]
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

DEFAULT_BOOKS = {
    "日常开销": {"fixed_quota": 0},
    "零花钱": {"fixed_quota": 3000},
}

DEFAULT_BOOKS_META = {
    "日常开销": {"icon": "Wallet", "color": "#409EFF"},
    "零花钱": {"icon": "ChatDotRound", "color": "#67C23A"},
}

CATEGORY_ICON_POOL = [
    "ForkSpoon",
    "Van",
    "Film",
    "ShoppingCart",
    "Bicycle",
    "CoffeeCup",
    "Ticket",
    "Basketball",
]

CATEGORY_COLOR_POOL = [
    "#409EFF",
    "#67C23A",
    "#E6A23C",
    "#F56C6C",
    "#909399",
    "#36CFC9",
    "#9254DE",
    "#FF7A45",
]

ENV_FILE = ".env"
DEFAULT_ENV = """# OpenAI Configuration
OPENAI_API_KEY=
OPENAI_BASE_URL=
OPENAI_MODEL=gpt-5.2
"""

# 示例账单数据模板：(类别, 标签, 交易对方, 商品说明, 金额范围, 账本)
SAMPLE_BILL_TEMPLATES = [
    # 食 - 正餐
    ("食", "午餐", "麦当劳", "麦辣鸡腿堡套餐", (20, 45), "日常开销"),
    ("食", "午餐", "肯德基", "吮指原味鸡套餐", (25, 50), "日常开销"),
    ("食", "晚餐", "海底捞", "火锅", (80, 200), "日常开销"),
    ("食", "午餐", "沙县小吃", "拌面套餐", (12, 25), "日常开销"),
    ("食", "晚餐", "外婆家", "家常菜", (40, 90), "日常开销"),
    ("食", "早餐", "包子铺", "包子豆浆", (5, 15), "日常开销"),
    ("食", "午餐", "兰州拉面", "牛肉面", (15, 30), "日常开销"),
    ("食", "晚餐", "必胜客", "披萨套餐", (50, 120), "日常开销"),
    ("食", "午饭", "黄焖鸡米饭", "黄焖鸡", (18, 30), "日常开销"),
    ("食", "晚饭", "烧烤摊", "烤串", (30, 80), "日常开销"),
    ("食", "夜宵", "烧烤摊", "烤串啤酒", (40, 100), "日常开销"),
    ("食", "早餐", "便利店", "早餐组合", (8, 20), "日常开销"),
    # 食 - 零食
    ("食", "零食", "便利店", "零食饮料", (5, 30), "日常开销"),
    ("食", "零食", "良品铺子", "坚果零食", (15, 50), "日常开销"),
    # 食 - 水果
    ("食", "水果", "鲜丰水果", "时令水果", (10, 40), "日常开销"),
    ("食", "水果", "水果店", "水果拼盘", (15, 50), "日常开销"),
    # 食 - 饮料
    ("食", "饮料", "星巴克", "拿铁咖啡", (25, 40), "日常开销"),
    ("食", "饮料", "奈雪的茶", "霸气橙子", (18, 35), "日常开销"),
    ("食", "饮料", "1点点", "波霸奶茶", (10, 20), "日常开销"),
    # 行 - 交通
    ("行", "地铁", "上海地铁", "地铁", (3, 8), "日常开销"),
    ("行", "地铁", "城市轨道交通", "轨道交通", (3, 10), "日常开销"),
    ("行", "共享单车", "哈啰出行", "哈啰单车", (1.5, 3), "日常开销"),
    ("行", "加油", "中国石油", "92号汽油", (5000, 15000), "日常开销"),
    ("行", "铁路", "铁路12306", "火车票", (1000, 8000), "日常开销"),
    # 娱乐
    ("娱乐", "电影", "万达影城", "电影票", (200, 300), "零花钱"),
    ("娱乐", "电影", "CGV影城", "电影票", (400, 900), "零花钱"),
    ("娱乐", "游戏", "Steam", "游戏充值", (1000, 2000), "零花钱"),
    ("娱乐", "游戏", "腾讯游戏", "游戏充值", (4000, 8000), "零花钱"),
]

# 各类别权重（食占大头，更贴近真实消费）
SAMPLE_CATEGORY_WEIGHTS = {
    "食": 40,
    "行": 30,
    "娱乐": 30,
}


def generate_sample_db():
    """
    生成 2025 年全年示例账单数据（365 笔，每天一笔）

    根据已有的分类和标签体系随机生成真实感的账单数据，
    用于演示和测试。
    """
    records = []
    start_date = datetime(2024, 1, 1)

    # 按类别分组模板
    templates_by_cat = {}
    for t in SAMPLE_BILL_TEMPLATES:
        cat = t[0]
        templates_by_cat.setdefault(cat, []).append(t)

    categories = list(SAMPLE_CATEGORY_WEIGHTS.keys())
    weights = list(SAMPLE_CATEGORY_WEIGHTS.values())

    for day_offset in range(365*2):
        current_date = start_date + timedelta(
            days=day_offset,
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59),
        )
        date_str = current_date.strftime("%Y-%m-%d %H:%M:%S")

        # 按权重随机选类别
        category = random.choices(categories, weights=weights, k=1)[0]

        # 从该类别的模板中随机选一个
        template = random.choice(templates_by_cat[category])
        cat, tag, counter_party, goods_desc, (min_amt, max_amt), book = template

        # 随机金额（保留两位小数）
        amount = round(random.uniform(min_amt, max_amt), 2)

        records.append({
            "日期": date_str,
            "金额": amount,
            "类别": cat,
            "标签": tag,
            "交易对方": counter_party,
            "商品说明": goods_desc,
            "备注": "",
            "账本": book,
        })

    return pd.DataFrame(sorted(records, key=lambda x: x["日期"]))


def generate_default_category_meta(categories: dict) -> dict:
    """
    为分类随机生成默认图标与颜色配置。

    Args:
        categories: 分类字典（key 为分类名）

    Returns:
        dict: 形如 {"食": {"icon": "...", "color": "#xxxxxx"}} 的元数据
    """
    category_names = list(categories.keys())
    icons = CATEGORY_ICON_POOL[:]
    colors = CATEGORY_COLOR_POOL[:]
    random.shuffle(icons)
    random.shuffle(colors)

    meta = {}
    for idx, name in enumerate(category_names):
        meta[name] = {
            "icon": icons[idx % len(icons)],
            "color": colors[idx % len(colors)],
        }
    return meta


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

    # 4. 初始化 categories_meta.json
    if not os.path.exists(CATEGORIES_META_FILE):
        categories_for_meta = DEFAULT_CATEGORIES
        if os.path.exists(CATEGORIES_FILE):
            try:
                with open(CATEGORIES_FILE, 'r', encoding='utf-8') as f:
                    loaded_categories = json.load(f)
                if isinstance(loaded_categories, dict) and loaded_categories:
                    categories_for_meta = loaded_categories
            except Exception:
                pass

        default_categories_meta = generate_default_category_meta(categories_for_meta)
        with open(CATEGORIES_META_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_categories_meta, f, ensure_ascii=False, indent=4)
        print(f"[Init] 创建默认分类元数据文件: {CATEGORIES_META_FILE}")

    # 5. 初始化 books.json
    if not os.path.exists(BOOKS_FILE):
        with open(BOOKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_BOOKS, f, ensure_ascii=False, indent=4)
        print(f"[Init] 创建默认账本文件: {BOOKS_FILE}")

    # 6. 初始化 books_meta.json
    if not os.path.exists(BOOKS_META_FILE):
        with open(BOOKS_META_FILE, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_BOOKS_META, f, ensure_ascii=False, indent=4)
        print(f"[Init] 创建默认账本元数据文件: {BOOKS_META_FILE}")

    # 7. 初始化 DB.xlsx（生成示例数据）
    if not os.path.exists(DB_FILE):
        df = generate_sample_db()
        df.to_excel(DB_FILE, index=False)
        print(f"[Init] 创建示例数据库文件: {DB_FILE}（365 笔 2025 年账单）")

    # 8. 初始化 .env
    if not os.path.exists(ENV_FILE):
        with open(ENV_FILE, 'w', encoding='utf-8') as f:
            f.write(DEFAULT_ENV)
        print(f"[Init] 创建默认环境变量文件: {ENV_FILE}")


initialize_data_files()
