"""
账单处理工具模块

提供支付宝和微信账单的解析、过滤、自动打标功能，以及配置文件读写操作。
"""
import re
import csv
import json
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

from core.config import (
    MEAL_TIME_PERIODS,
    ALIPAY_CHECKPOINT_LINE,
    ALIPAY_FORMAT_MARKER,
    WECHAT_CHECKPOINT_LINE,
    WECHAT_FORMAT_MARKER,
    SUPPORTED_ENCODINGS,
    SUBSIDY_KEYWORDS,
    SUBSIDY_DEDUCTION,
    MIN_AMOUNT,
    ALIPAY_FILTER_KEYWORDS,
    WECHAT_FIELD_MAPPING,
    RULES_FILE,
    CATEGORIES_FILE,
    CATEGORIES_META_FILE,
    BOOKS_FILE,
    BOOKS_META_FILE,
    # OpenAI 配置
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
    AI_TAG_BATCH_SIZE,
    AI_TAG_SYSTEM_PROMPT,
)


# ==================== 配置文件读写 ====================

def _load_json(file_path, default: Any) -> Any:
    """加载 JSON 文件，文件不存在时返回默认值"""
    try:
        return json.loads(file_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default


def _save_json(file_path, data: Any, indent: int = 2) -> None:
    """保存数据到 JSON 文件"""
    file_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=indent),
        encoding="utf-8"
    )


def load_rules() -> list:
    """加载规则配置"""
    return _load_json(RULES_FILE, [])


def save_rules(rules: list) -> None:
    """保存规则配置"""
    _save_json(RULES_FILE, rules)


def load_categories() -> dict:
    """加载分类配置"""
    return _load_json(CATEGORIES_FILE, {})


def save_categories(categories: dict) -> None:
    """保存分类配置"""
    _save_json(CATEGORIES_FILE, categories, indent=4)


def load_category_meta() -> dict:
    """加载分类元数据（图标、颜色）"""
    return _load_json(CATEGORIES_META_FILE, {})


def save_category_meta(meta: dict) -> None:
    """保存分类元数据（图标、颜色）"""
    _save_json(CATEGORIES_META_FILE, meta, indent=4)


def load_books() -> dict:
    """加载账本配置"""
    return _load_json(BOOKS_FILE, {})


def save_books(books: dict) -> None:
    """保存账本配置"""
    _save_json(BOOKS_FILE, books, indent=4)


def load_book_meta() -> dict:
    """加载账本元数据（图标、颜色）"""
    return _load_json(BOOKS_META_FILE, {})


def save_book_meta(meta: dict) -> None:
    """保存账本元数据（图标、颜色）"""
    _save_json(BOOKS_META_FILE, meta, indent=4)


# ==================== 自定义异常 ====================

class BillProcessError(Exception):
    """账单处理异常基类"""


class FileFormatError(BillProcessError):
    """文件格式错误"""


class DuplicateBillError(BillProcessError):
    """重复账单错误"""


class RefundError(BillProcessError):
    """退款处理错误"""


# ==================== 时间处理函数 ====================

def _parse_time(time_str: str) -> time.struct_time:
    """解析时间字符串"""
    fmt = "%H:%M:%S" if time_str.count(":") == 2 else "%H:%M"
    return time.strptime(time_str, fmt)


def time_cmp(start: str, check: str, end: str = "23:59") -> bool:
    """
    检查时间是否在指定范围内 [start, end]
    
    Args:
        start: 起始时间
        check: 待检查时间  
        end: 结束时间，默认 23:59
    
    Returns:
        bool: check 是否在 [start, end] 范围内
    """
    return _parse_time(start) <= _parse_time(check) <= _parse_time(end)


def time_map(bill_time: str) -> Optional[str]:
    """
    根据时间返回对应的餐点类型
    
    Args:
        bill_time: 时间字符串 "HH:MM" 或 "HH:MM:SS"
    
    Returns:
        餐点类型或 None
    """
    for start, end, meal_type in MEAL_TIME_PERIODS:
        if time_cmp(start, bill_time, end):
            return meal_type
    return None


# ==================== 规则引擎 ====================

def _match_rule(bill: dict, rule: dict) -> Optional[str]:
    """检查账单是否匹配规则，返回匹配的模式"""
    key = rule.get("key", "")
    
    # 支持多字段匹配 (ANY)
    if key == "ANY":
        target_fields = ["交易对方", "商品说明"]
    else:
        target_fields = [key]
        
    for field in target_fields:
        bill_value = bill.get(field, "")
        for pattern in rule["rule"]:
            # 正则匹配模式
            if rule.get("match_mode") == "regex":
                try:
                    if re.search(pattern, bill_value):
                        return pattern
                except re.error:
                    continue # 忽略无效正则
            # 默认关键词匹配
            elif pattern in bill_value:
                return pattern
    return None


def _apply_time_based_tag(bill: dict, rule: dict) -> str:
    """根据规则和账单时间确定标签"""
    # 只对"食"类别且启用时间标签的规则处理
    if not (rule.get("time_based") and rule["category"] == "食"):
        return rule.get("tag", "")
    
    time_str = bill["交易时间"].split(" ")[1]
    time_tag = time_map(time_str)
    
    if not time_tag:
        return rule.get("tag", "")
    
    time_based = rule.get("time_based", [])
    
    if not isinstance(time_based, list) or not time_based:
        return rule.get("tag", "")
    
    if "全部" in time_based:
        return time_tag
    
    if "无" in time_based:
        return rule.get("tag", "")
    
    return time_tag if time_tag in time_based else rule.get("tag", "")


def apply_rules_to_bills(bills: Dict[str, Any]) -> Dict[str, Any]:
    """
    应用规则到账单，自动打标签
    
    只对未打标的账单进行规则匹配，已标记的账单保持不变
    """
    rules = load_rules()

    
    for bill_id, bill in bills.items():
        if bill.get("类别", "").strip():
            continue
        
        bill["类别"] = ""
        bill["标签"] = ""
        bill["备注"] = ""
        bill["命中规则"] = ""
        
        for rule in rules:
            matched = _match_rule(bill, rule)
            if matched:
                bill["命中规则"] = f"{rule['key']}: {matched}"
                bill["类别"] = rule["category"]
                bill["标签"] = _apply_time_based_tag(bill, rule)
                bill["备注"] = rule.get("comment", "")
                break
        
        if bill["类别"] and not bill["标签"]:
            bill["标签"] = "-"
    
    return bills


# ==================== AI 打标 ====================

def ai_tag_bills(bills: List[dict]) -> dict:
    """
    调用 OpenAI API 对账单进行智能打标
    
    Args:
        bills: 未打标的账单列表
    
    Returns:
        dict: 包含 tagged_bills（打标结果）和 suggested_rules（规则建议）
    
    Raises:
        ValueError: API Key 未配置或调用失败
    """
    import httpx
    
    # 检查 API Key 配置
    if not OPENAI_API_KEY:
        raise ValueError("请先在 core/config.py 中配置 OPENAI_API_KEY")
    
    # 过滤未打标账单（类别为空）
    untagged_bills = [
        b for b in bills
        if not b.get("类别", "").strip()
    ]
    
    if not untagged_bills:
        return {"tagged_bills": [], "suggested_rules": []}
    
    # 限制批次大小
    batch = untagged_bills[:AI_TAG_BATCH_SIZE]
    
    # 准备发送给 AI 的账单数据（只保留必要字段）
    bills_for_ai = [
        {
            "交易订单号": b.get("交易订单号", ""),
            "交易时间": b.get("交易时间", ""),
            "金额": b.get("金额", 0),
            "交易对方": b.get("交易对方", ""),
            "商品说明": b.get("商品说明", ""),
        }
        for b in batch
    ]
    
    # 加载现有的类别和标签
    categories = load_categories()
    categories_info = "现有的类别和标签：\n"
    for cat, tags in categories.items():
        categories_info += f"- {cat}: {','.join(tags)}\n"
    
    # 构造用户消息，包含类别标签信息和账单数据
    user_message = f"{categories_info}\n待打标账单：\n{json.dumps(bills_for_ai, ensure_ascii=False, indent=2)}"
    
    # 构造请求
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": AI_TAG_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.3,  # 较低温度保证稳定输出
        "response_format": {"type": "json_object"},  # 强制 JSON 输出
    }
    
    # 发送请求
    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{OPENAI_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # 解析 AI 返回的 JSON
            ai_result = json.loads(content)
            
            return {
                "tagged_bills": ai_result.get("tagged_bills", []),
                "suggested_rules": ai_result.get("suggested_rules", []),
            }
            
    except httpx.HTTPStatusError as e:
        raise ValueError(f"OpenAI API 调用失败: {e.response.status_code} - {e.response.text}")
    except httpx.RequestError as e:
        raise ValueError(f"网络请求失败: {str(e)}")
    except json.JSONDecodeError as e:
        raise ValueError(f"AI 返回的 JSON 解析失败: {str(e)}")
    except KeyError as e:
        raise ValueError(f"AI 返回格式异常: 缺少字段 {str(e)}")


# ==================== 账单处理器基类 ====================

class BaseBillProcessor(ABC):
    """
    账单处理器抽象基类
    
    定义统一的处理流程：验证 → 预处理 → 过滤 → 打标
    """
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.raw_data: List[dict] = []
        self.bill: Dict[str, Any] = {}
        
        # 标准处理流程
        self._validate()
        self._preprocess()
        self._filter()
        self.bill = apply_rules_to_bills(self.bill)
    
    @abstractmethod
    def _validate(self) -> None:
        """验证文件格式并读取原始数据到 self.raw_data"""
    
    @abstractmethod
    def _preprocess(self) -> None:
        """预处理数据：结构化、处理退款、计算金额"""
    
    def _filter(self) -> None:
        """
        过滤无效交易
        
        默认实现为空，子类可选择性覆盖
        """
    
    def _parse_refund_id(self, bill_id: str) -> Optional[str]:
        """
        解析退款订单号，提取原始订单号
        
        Returns:
            原始订单号，如果不是订单则返回 None
        """
        if bill_id.isdigit():
            return None
        
        for sep in ["_", "*"]:
            if sep in bill_id:
                return bill_id.split(sep)[0]
        return None
    
    def _apply_field_mapping(self, bill: dict, mapping: dict) -> None:
        """
        应用字段映射，将源字段映射到目标字段
        
        Args:
            bill: 账单数据
            mapping: 字段映射字典 {源字段: 目标字段}
        """
        for src_field, dst_field in mapping.items():
            if src_field in bill:
                bill[dst_field] = bill[src_field]


def process_bills(file_path: str, bill_type: str) -> Dict[str, Any]:
    """
    处理账单文件的入口函数
    
    Args:
        file_path: 账单文件路径
        bill_type: 账单类型 "alipay" 或 "wechat"
    
    Raises:
        ValueError: 不支持的账单类型
    """
    processors = {"alipay": Alipay, "wechat": Wechat}
    
    if bill_type not in processors:
        raise ValueError(f"不支持的账单类型: {bill_type}")
    
    return processors[bill_type](file_path).bill


# ==================== 支付宝账单处理器 ====================

class Alipay(BaseBillProcessor):
    """支付宝账单处理器"""
    
    def _validate(self) -> None:
        """验证支付宝账单格式并读取数据（单次读取优化）"""
        self._encoding = None
        self.raw_data = []
        
        # 尝试多种编码，一次性完成验证和读取
        for enc in SUPPORTED_ENCODINGS:
            try:
                with open(self.file_path, "r", encoding=enc) as f:
                    lines = f.readlines()
                    
                    # 验证格式标记
                    if len(lines) < ALIPAY_CHECKPOINT_LINE:
                        continue
                    
                    checkpoint_line = lines[ALIPAY_CHECKPOINT_LINE - 1]
                    if not checkpoint_line.startswith(ALIPAY_FORMAT_MARKER):
                        continue
                    
                    # 读取 CSV 数据
                    csv_content = "".join(lines[ALIPAY_CHECKPOINT_LINE:])
                    reader = csv.DictReader(csv_content.splitlines())
                    self.raw_data = sorted(
                        list(reader),
                        key=lambda x: x["交易订单号"].strip()
                    )
                    self._encoding = enc
                    return
                    
            except (UnicodeDecodeError, KeyError):
                continue
        
        raise FileFormatError("无法读取文件，尝试了所有支持的编码或文件格式不正确")
    
    def _preprocess(self) -> None:
        """预处理支付宝账单"""
        bills = {}
        
        # 第一轮：结构化数据
        for data in self.raw_data:
            bill_id = data["交易订单号"].strip()
            
            if bill_id in bills:
                raise DuplicateBillError(f"订单号重复: {bill_id}")
            
            bills[bill_id] = dict(data)
            del bills[bill_id]["交易订单号"]
            bills[bill_id]["金额"] = float(data["金额"])
            
            # 处理餐补扣除
            payment = bills[bill_id].get("收/付款方式", "")
            for keyword in SUBSIDY_KEYWORDS:
                if keyword in payment:
                    bills[bill_id]["金额"] = max(0, bills[bill_id]["金额"] - SUBSIDY_DEDUCTION)
                    break
            
            # 过滤金额过小
            if bills[bill_id]["金额"] < MIN_AMOUNT:
                del bills[bill_id]
        
        # 第二轮：处理退款
        self.bill = {}
        processed = set()
        
        for bill_id, bill in bills.items():
            if bill_id in processed:
                continue
            
            original_id = self._parse_refund_id(bill_id)
            
            if original_id is None:
                # 普通订单
                self.bill[bill_id] = bill
            else:
                # 退款订单
                processed.add(bill_id)
                if original_id not in bills:
                    if bill.get("交易分类") != "收入":
                        print(f"退款订单 {bill_id} 找不到原订单 {original_id}")
                    continue

                real_amount = bills[original_id]["金额"] - bill["金额"]
                if real_amount < -MIN_AMOUNT:
                    raise RefundError(f"退款金额超过原订单: {bill_id}")
                elif real_amount > MIN_AMOUNT:
                    self.bill[original_id] = dict(bills[original_id])
                    self.bill[original_id]["金额"] = real_amount
                    processed.add(original_id)
    
    def _filter(self) -> None:
        """过滤不需要的交易"""
        self.bill = {
            bid: bill for bid, bill in self.bill.items()
            if not (
                bill.get("交易状态") == "交易关闭" or
                bill.get("收/支") == "收入" or
                any(kw in bill.get("商品说明", "") for kw in ALIPAY_FILTER_KEYWORDS) or
                "基金销售" in bill.get("交易对方", "")
            )
        }


# ==================== 微信账单处理器 ====================

class Wechat(BaseBillProcessor):
    """微信账单处理器"""
    
    def _validate(self) -> None:
        """验证微信账单格式并读取数据"""
        with open(self.file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
            if len(lines) < WECHAT_CHECKPOINT_LINE:
                raise FileFormatError("文件行数不足")
            
            checkpoint_line = lines[WECHAT_CHECKPOINT_LINE - 1]
            if not checkpoint_line.startswith(WECHAT_FORMAT_MARKER):
                raise FileFormatError(f"文件格式不正确，第 {WECHAT_CHECKPOINT_LINE} 行验证失败")
            
            # 读取 CSV 数据
            csv_content = "".join(lines[WECHAT_CHECKPOINT_LINE:])
            reader = csv.DictReader(csv_content.splitlines())
            self.raw_data = sorted(
                list(reader),
                key=lambda x: x["交易单号"].strip()
            )
    
    def _preprocess(self) -> None:
        """预处理微信账单"""
        self.bill = {}
        
        for data in self.raw_data:
            bill_id = data["交易单号"].strip()
            
            if bill_id in self.bill:
                raise DuplicateBillError(f"交易单号重复: {bill_id}")
            
            bill = dict(data)
            del bill["交易单号"]
            
            # 解析金额（移除¥符号和逗号）
            amount_str = data["金额(元)"].replace("¥", "").replace(",", "")
            bill["金额"] = float(amount_str)
            
            # 只保留支出
            if bill["收/支"] != "支出":
                continue
            
            # 处理全额退款
            if bill["当前状态"] == "已全额退款":
                continue
            
            # 处理部分退款
            if "已退款" in bill["当前状态"]:
                match = re.findall(r"已退款\([￥|¥]([\d.]+)\)", bill["当前状态"])
                if match:
                    bill["金额"] -= float(match[0])
            
            # 过滤金额过小
            if bill["金额"] <= MIN_AMOUNT:
                continue
            
            # 应用字段映射
            self._apply_field_mapping(bill, WECHAT_FIELD_MAPPING)
            
            # 确保标准字段存在
            bill.setdefault("交易对方", "")
            bill.setdefault("商品说明", "")
            bill.setdefault("交易时间", "")
            
            self.bill[bill_id] = bill
