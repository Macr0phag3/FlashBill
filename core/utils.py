"""
账单处理工具模块

提供支付宝和微信账单的解析、过滤、自动打标功能，以及配置文件读写操作。
"""
import re
import csv
import json
import time
import hashlib
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


# ==================== 招商银行 PDF 解析辅助 ====================

CMB_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
CMB_AMOUNT_RE = re.compile(r"-?\d[\d,]*\.\d+|-?\d[\d,]*")
CMB_REQUIRED_HEADERS = ["记账日期", "货币", "交易金额", "联机余额", "交易摘要", "对手信息"]
CMB_OPTIONAL_HEADERS = ["客户摘要"]
CMB_HEADER_ORDER = CMB_REQUIRED_HEADERS + CMB_OPTIONAL_HEADERS
CMB_HEADER_KEY_MAP = {
    "记账日期": "date",
    "货币": "currency",
    "交易金额": "amount",
    "联机余额": "balance",
    "交易摘要": "summary",
    "对手信息": "counterparty",
    "客户摘要": "customer_summary",
}
CMB_ENGLISH_HEADER_TOKENS = {
    "Date",
    "Currency",
    "Transaction",
    "Amount",
    "Balance",
    "TransactionType",
    "Type",
    "Counter",
    "Party",
    "CounterParty",
    "CustomerSummary",
    "Customer",
    "Summary",
}


def _cmb_parse_amount(text: str) -> Optional[float]:
    """解析金额字符串。"""
    if not text:
        return None
    match = CMB_AMOUNT_RE.search(text.replace(" ", ""))
    if not match:
        return None
    try:
        return float(match.group(0).replace(",", ""))
    except ValueError:
        return None


def _cmb_normalize_text(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def _cmb_extract_char_items(page: Any) -> List[tuple]:
    items: List[tuple] = []
    raw = page.get_text("rawdict")
    for block in raw.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                chars = span.get("chars")
                if chars:
                    for ch in chars:
                        x0, y0, x1, y1 = ch["bbox"]
                        c = ch.get("c", "")
                        if c:
                            items.append((float(x0), float(y0), float(x1), float(y1), str(c)))
                    continue

                text = span.get("text", "")
                bbox = span.get("bbox")
                if not text or not bbox:
                    continue
                x0, y0, x1, y1 = bbox
                char_w = (x1 - x0) / max(len(text), 1)
                for idx, ch in enumerate(text):
                    cx0 = x0 + idx * char_w
                    cx1 = cx0 + char_w
                    items.append((float(cx0), float(y0), float(cx1), float(y1), str(ch)))
    return items


def _cmb_group_items_into_lines(items: List[tuple], y_tol: float = 1.2) -> List[dict]:
    sorted_items = sorted(items, key=lambda item: (item[1], item[0]))
    lines: List[dict] = []

    for x0, y0, x1, _y1, text in sorted_items:
        matched = None
        for line in lines:
            if abs(line["y"] - y0) <= y_tol:
                matched = line
                break
        if matched is None:
            matched = {"y": y0, "items": []}
            lines.append(matched)

        matched["items"].append((x0, x1, text))
        matched["y"] = (matched["y"] + y0) / 2

    for line in lines:
        line["items"].sort(key=lambda item: item[0])
        line["text"] = "".join(text for _, _, text in line["items"]).strip()

    return sorted(lines, key=lambda item: item["y"])


def _cmb_find_header(lines: List[dict]) -> tuple[int, Dict[str, float]]:
    for idx, line in enumerate(lines):
        text = _cmb_normalize_text(line["text"])
        if not all(name in text for name in CMB_REQUIRED_HEADERS):
            continue

        compact_chars = [
            _cmb_normalize_text(item_text)
            for _x0, _x1, item_text in line["items"]
            if _cmb_normalize_text(item_text)
        ]
        compact_xs = [
            x0
            for x0, _x1, item_text in line["items"]
            if _cmb_normalize_text(item_text)
        ]
        compact_text = "".join(compact_chars)
        anchors: Dict[str, float] = {}
        for header in CMB_HEADER_ORDER:
            pos = compact_text.find(header)
            if pos >= 0 and pos < len(compact_xs):
                anchors[CMB_HEADER_KEY_MAP[header]] = compact_xs[pos]

        required_keys = {CMB_HEADER_KEY_MAP[name] for name in CMB_REQUIRED_HEADERS}
        if required_keys.issubset(anchors.keys()):
            return idx, anchors

    raise ValueError("未找到中文表头")


def _cmb_build_column_ranges(anchors: Dict[str, float], page_width: float) -> List[dict]:
    ordered = sorted(anchors.items(), key=lambda item: item[1])
    ranges: List[dict] = []
    for idx, (name, x0) in enumerate(ordered):
        x1 = ordered[idx + 1][1] if idx + 1 < len(ordered) else page_width + 1
        ranges.append({"name": name, "x0": x0, "x1": x1})
    return ranges


def _cmb_pick_column(x0: float, x1: float, ranges: List[dict]) -> Optional[str]:
    cx = (x0 + x1) / 2
    for col in ranges:
        if col["x0"] <= cx < col["x1"]:
            return col["name"]
    if ranges and cx >= ranges[-1]["x0"]:
        return ranges[-1]["name"]
    return None


def _cmb_line_to_cells(line: dict, ranges: List[dict]) -> Dict[str, str]:
    cells = {col["name"]: "" for col in ranges}
    for x0, x1, text in line["items"]:
        col = _cmb_pick_column(x0, x1, ranges)
        if col is None:
            continue
        cells[col] += text
    return {key: value.strip() for key, value in cells.items()}


def _cmb_is_english_header_line(text: str) -> bool:
    compact = _cmb_normalize_text(text)
    if not compact:
        return False
    if re.search(r"[A-Za-z]", compact) and not re.search(r"[\u4e00-\u9fff]", compact):
        return True
    if compact in CMB_ENGLISH_HEADER_TOKENS:
        return True
    tokens = re.findall(r"[A-Za-z]+", text)
    return bool(tokens) and all(token in CMB_ENGLISH_HEADER_TOKENS for token in tokens)


def _cmb_is_footer_line(text: str) -> bool:
    text = _cmb_normalize_text(text)
    if not text:
        return True
    if "——————" in text:
        return True
    if re.fullmatch(r"\d+/\d+", text):
        return True
    if "温馨提示" in text or "交易流水验真" in text:
        return True
    return False


def _cmb_extract_page_visual_rows(page: Any) -> List[dict]:
    lines = _cmb_group_items_into_lines(_cmb_extract_char_items(page), y_tol=1.2)
    try:
        header_idx, anchors = _cmb_find_header(lines)
    except ValueError:
        return []

    ranges = _cmb_build_column_ranges(anchors, page.rect.width)
    rows: List[dict] = []
    for line in lines[header_idx + 1 :]:
        text = line["text"]
        normalized = _cmb_normalize_text(text)

        if not normalized:
            continue
        if any(header in normalized for header in CMB_HEADER_ORDER):
            continue
        if _cmb_is_english_header_line(text):
            continue
        if _cmb_is_footer_line(text):
            break

        cells = _cmb_line_to_cells(line, ranges)
        if not any(cells.values()):
            continue

        row = {
            "date": "",
            "currency": "",
            "amount": "",
            "balance": "",
            "summary": "",
            "counterparty": "",
            "customer_summary": "",
            "page": "",
            "y": "",
        }
        row.update(cells)
        row["page"] = str(getattr(page, "number", 0) + 1)
        row["y"] = f"{line['y']:.2f}"
        rows.append(row)

    return rows


def _cmb_is_main_row(row: dict) -> bool:
    return bool(CMB_DATE_RE.fullmatch(row.get("date", "")))


def _cmb_row_y(row: dict) -> float:
    try:
        return float(row.get("y", "0") or 0)
    except ValueError:
        return 0.0


def _cmb_merge_cells(base: dict, extra: dict, prepend: bool) -> None:
    text_cols = {"summary", "counterparty", "customer_summary"}
    fill_cols = {"currency", "amount", "balance"}

    for key, value in extra.items():
        if key in {"page", "y", "date"} or not value:
            continue
        if key in text_cols:
            if not base.get(key):
                base[key] = value
            elif prepend:
                base[key] = value + base[key]
            else:
                base[key] = base[key] + value
        elif key in fill_cols:
            if not base.get(key):
                base[key] = value


def _cmb_merge_rows(rows: List[dict], y_gap: float = 10.0) -> List[dict]:
    merged: List[dict] = []
    i = 0
    total = len(rows)

    while i < total:
        first = rows[i]
        if _cmb_is_main_row(first):
            merged.append(dict(first))
            i += 1
            continue

        j = i
        pending_rows: List[dict] = []
        while j < total and not _cmb_is_main_row(rows[j]):
            pending_rows.append(rows[j])
            j += 1

        if j >= total:
            merged.extend(dict(row) for row in pending_rows)
            break

        main = dict(rows[j])
        main["page"] = pending_rows[0].get("page", main.get("page", ""))
        main["y"] = pending_rows[0].get("y", main.get("y", ""))

        for pending in pending_rows:
            _cmb_merge_cells(main, pending, prepend=True)

        k = j + 1
        last_row = rows[j]
        while k < total:
            candidate = rows[k]
            if _cmb_is_main_row(candidate):
                break
            if candidate.get("page") != last_row.get("page"):
                break
            if _cmb_row_y(candidate) - _cmb_row_y(last_row) > y_gap:
                break
            _cmb_merge_cells(main, candidate, prepend=False)
            last_row = candidate
            k += 1

        merged.append(main)
        i = k if k > j else j + 1

    return merged


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
        bill_type: 账单类型 "alipay" / "wechat" / "cmb"
    
    Raises:
        ValueError: 不支持的账单类型
    """
    processors = {"alipay": Alipay, "wechat": Wechat, "cmb": CmbPDF}
    
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


# ==================== 招商银行 PDF 账单处理器 ====================

class CmbPDF(BaseBillProcessor):
    """招商银行 PDF 账单处理器（基于 PyMuPDF 坐标提取）"""

    def __init__(self, file_path: str):
        self.count_rows: int = 0
        self.count_bills: int = 0
        self.raw_rows: List[dict] = []
        self.failed_rows: List[dict] = []
        super().__init__(file_path)

    def _validate(self) -> None:
        """读取并解析 PDF 表格行为 raw_rows。"""
        try:
            import fitz
        except ImportError as exc:
            raise FileFormatError("缺少依赖 PyMuPDF，请先安装后再上传招商银行 PDF 账单") from exc

        try:
            with fitz.open(self.file_path) as doc:
                visual_rows = []
                for page in doc:
                    visual_rows.extend(_cmb_extract_page_visual_rows(page))
                self.raw_rows = _cmb_merge_rows(visual_rows)
                self.count_rows = len(self.raw_rows)
        except Exception as exc:
            raise FileFormatError(f"招商银行 PDF 解析失败: {exc}") from exc

    def _preprocess(self) -> None:
        """将 raw_rows 转换为标准账单结构。"""
        self.bill = {}
        self.failed_rows = []

        for idx, row in enumerate(self.raw_rows, start=1):
            date = row.get("date", "").strip()
            customer_summary = row.get("customer_summary", "").strip()
            if not CMB_DATE_RE.fullmatch(date):
                self.failed_rows.append(
                    {
                        "记账日期": row.get("date", ""),
                        "货币": row.get("currency", ""),
                        "交易金额": row.get("amount", ""),
                        "联机余额": row.get("balance", ""),
                        "对手信息": row.get("counterparty", ""),
                        "客户摘要": customer_summary,
                        "原因": "日期格式异常",
                    }
                )
                continue

            raw_amount = _cmb_parse_amount(row.get("amount", ""))
            if raw_amount is None:
                self.failed_rows.append(
                    {
                        "记账日期": row.get("date", ""),
                        "货币": row.get("currency", ""),
                        "交易金额": row.get("amount", ""),
                        "联机余额": row.get("balance", ""),
                        "对手信息": row.get("counterparty", ""),
                        "客户摘要": customer_summary,
                        "原因": "金额解析失败",
                    }
                )
                continue

            if abs(raw_amount) <= MIN_AMOUNT:
                self.failed_rows.append(
                    {
                        "记账日期": row.get("date", ""),
                        "货币": row.get("currency", ""),
                        "交易金额": row.get("amount", ""),
                        "联机余额": row.get("balance", ""),
                        "对手信息": row.get("counterparty", ""),
                        "客户摘要": customer_summary,
                        "原因": "金额过小",
                    }
                )
                continue

            sign = f"{raw_amount:+.2f}"
            goods_desc = customer_summary
            counter_party = row.get("counterparty", "").strip()
            digest = hashlib.sha1(f"{date}|{sign}|{goods_desc}|{counter_party}|{idx}".encode("utf-8")).hexdigest()
            bill_id = f"CMB_{digest[:16]}"

            if bill_id in self.bill:
                raise DuplicateBillError(f"招商银行账单ID重复: {bill_id}")

            self.bill[bill_id] = {
                "交易时间": f"{date} 00:00:00",
                "金额": abs(raw_amount),
                "收/支": "收入" if raw_amount > 0 else ("支出" if raw_amount < 0 else "不计收支"),
                "交易对方": counter_party,
                "商品说明": goods_desc,
            }

        self.count_bills = len(self.bill)

    def _filter(self) -> None:
        self.bill = {
            bid: bill for bid, bill in self.bill.items()
            if not (
                bill.get("收/支") == "收入" or
                # "支付宝" in bill.get("交易对方", "") or
                # "微信" in bill.get("交易对方", "") or
                "财付通" in bill.get("商品说明", "") or
                "支付宝-" in bill.get("商品说明", "") or
                "网商银行" in bill.get("交易对方", "") or
                "基金销售" in bill.get("交易对方", "") or
                "蚂蚁基金" in bill.get("交易对方", "") or
                "基金管理" in bill.get("交易对方", "")
            )
        }
