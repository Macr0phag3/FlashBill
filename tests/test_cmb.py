"""
测试招商银行退款匹配逻辑
"""
from core.utils import CmbPDF
from core.utils import _cmb_reconcile_refunds_with_issues
from core.utils import _cmb_reconcile_refunds


def test_cmb_full_refund_within_three_days():
    bills = {
        "expense_1": {
            "交易时间": "2026-03-01 00:00:00",
            "金额": 88.0,
            "收/支": "支出",
            "交易对方": "星巴克",
            "商品说明": "门店消费",
        },
        "refund_1": {
            "交易时间": "2026-03-03 00:00:00",
            "金额": 88.0,
            "收/支": "收入",
            "交易对方": "星巴克",
            "商品说明": "门店消费",
            "__is_refund_candidate": True,
        },
    }

    result = _cmb_reconcile_refunds(bills)

    assert result == {}


def test_cmb_refund_over_three_days_is_not_matched():
    bills = {
        "expense_1": {
            "交易时间": "2026-03-01 00:00:00",
            "金额": 88.0,
            "收/支": "支出",
            "交易对方": "星巴克",
            "商品说明": "门店消费",
        },
        "refund_1": {
            "交易时间": "2026-03-05 00:00:00",
            "金额": 88.0,
            "收/支": "收入",
            "交易对方": "星巴克",
            "商品说明": "门店消费",
            "__is_refund_candidate": True,
        },
    }

    result = _cmb_reconcile_refunds(bills)

    assert "expense_1" in result
    assert "refund_1" not in result


def test_cmb_refund_requires_same_counterparty_and_summary():
    bills = {
        "expense_1": {
            "交易时间": "2026-03-01 00:00:00",
            "金额": 88.0,
            "收/支": "支出",
            "交易对方": "星巴克",
            "商品说明": "门店消费",
        },
        "refund_1": {
            "交易时间": "2026-03-02 00:00:00",
            "金额": 88.0,
            "收/支": "收入",
            "交易对方": "瑞幸",
            "商品说明": "门店消费",
            "__is_refund_candidate": True,
        },
    }

    result = _cmb_reconcile_refunds(bills)

    assert "expense_1" in result
    assert "refund_1" not in result


def test_cmb_unmatched_refund_is_reported():
    bills = {
        "refund_1": {
            "交易时间": "2026-03-02 00:00:00",
            "金额": 88.0,
            "收/支": "收入",
            "交易对方": "星巴克",
            "商品说明": "门店消费",
            "__is_refund_candidate": True,
        },
    }

    result, unmatched_refund_ids = _cmb_reconcile_refunds_with_issues(bills)

    assert result == {}
    assert unmatched_refund_ids == {"refund_1"}


def test_cmb_refund_matches_latest_eligible_expense():
    bills = {
        "expense_old": {
            "交易时间": "2026-03-01 00:00:00",
            "金额": 50.0,
            "收/支": "支出",
            "交易对方": "滴滴出行",
            "商品说明": "行程支付",
        },
        "expense_new": {
            "交易时间": "2026-03-03 00:00:00",
            "金额": 50.0,
            "收/支": "支出",
            "交易对方": "滴滴出行",
            "商品说明": "行程支付",
        },
        "refund_1": {
            "交易时间": "2026-03-04 00:00:00",
            "金额": 50.0,
            "收/支": "收入",
            "交易对方": "滴滴出行",
            "商品说明": "行程支付",
            "__is_refund_candidate": True,
        },
    }

    result = _cmb_reconcile_refunds(bills)

    assert "expense_new" not in result
    assert "refund_1" not in result
    assert "expense_old" in result


def test_cmb_count_bills_excludes_refund_deduction_from_parse_stats():
    processor = CmbPDF.__new__(CmbPDF)
    processor.raw_rows = [
        {
            "date": "2026-03-01",
            "currency": "CNY",
            "amount": "-88.00",
            "balance": "1000.00",
            "summary": "消费",
            "counterparty": "星巴克",
            "customer_summary": "门店消费",
        },
        {
            "date": "2026-03-03",
            "currency": "CNY",
            "amount": "88.00",
            "balance": "1088.00",
            "summary": "退款入账",
            "counterparty": "星巴克",
            "customer_summary": "门店消费",
        },
    ]
    processor.failed_rows = []
    processor.bill = {}
    processor.count_bills = 0

    CmbPDF._preprocess(processor)

    assert processor.count_bills == 2
    assert processor.bill == {}


def test_cmb_unmatched_refund_goes_to_failed_rows():
    processor = CmbPDF.__new__(CmbPDF)
    processor.raw_rows = [
        {
            "date": "2026-03-03",
            "currency": "CNY",
            "amount": "88.00",
            "balance": "1088.00",
            "summary": "退款入账",
            "counterparty": "星巴克",
            "customer_summary": "门店消费",
        },
    ]
    processor.failed_rows = []
    processor.bill = {}
    processor.count_bills = 0

    CmbPDF._preprocess(processor)

    assert processor.count_bills == 0
    assert processor.bill == {}
    assert len(processor.failed_rows) == 1
    assert processor.failed_rows[0]["原因"] == "退款未匹配到支付记录"


def test_cmb_normal_income_without_refund_keyword_is_not_reported():
    processor = CmbPDF.__new__(CmbPDF)
    processor.raw_rows = [
        {
            "date": "2026-03-03",
            "currency": "CNY",
            "amount": "88.00",
            "balance": "1088.00",
            "summary": "工资入账",
            "counterparty": "某公司",
            "customer_summary": "三月工资",
        },
    ]
    processor.failed_rows = []
    processor.bill = {}
    processor.count_bills = 0

    CmbPDF._preprocess(processor)

    assert processor.count_bills == 1
    assert len(processor.failed_rows) == 0
    assert len(processor.bill) == 1


def test_cmb_falls_back_to_summary_when_counterparty_and_customer_summary_missing():
    processor = CmbPDF.__new__(CmbPDF)
    processor.raw_rows = [
        {
            "date": "2026-03-03",
            "currency": "CNY",
            "amount": "-18.80",
            "balance": "1088.00",
            "summary": "便利店消费",
            "counterparty": "",
            "customer_summary": "",
        },
    ]
    processor.failed_rows = []
    processor.bill = {}
    processor.count_bills = 0

    CmbPDF._preprocess(processor)

    assert processor.count_bills == 1
    assert len(processor.bill) == 1
    bill = next(iter(processor.bill.values()))
    assert bill["交易对方"] == ""
    assert bill["商品说明"] == "便利店消费"
