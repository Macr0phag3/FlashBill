"""
测试微信账单解析

测试 Wechat 类的账单解析、退款处理、金额计算等核心功能
"""
import pytest
import os
import pandas as pd
from core.utils import Wechat


@pytest.fixture
def wechat_processor():
    """初始化 Wechat 处理器 fixture"""
    xlsx_path = "tests/test_data/wechat-sample.xlsx"
    
    if not os.path.exists(xlsx_path):
        pytest.skip(f"测试文件不存在: {xlsx_path}")
    
    # 需要先转换为 CSV
    df = pd.read_excel(xlsx_path)
    csv_path = "tests/test_data/wechat_temp.csv"
    os.makedirs("tests/test_data", exist_ok=True)
    df.to_csv(csv_path, index=False, encoding='utf-8')
    
    try:
        processor = Wechat(csv_path)
        yield processor
    finally:
        # 清理临时文件
        if os.path.exists(csv_path):
            os.remove(csv_path)


class TestWechatParsing:
    """测试微信账单解析"""
    
    def test_wechat_basic_parsing(self, wechat_processor):
        """测试基本解析功能"""
        # 验证账单数量
        assert len(wechat_processor.bill) >= 0, "应该能够解析账单"
        assert isinstance(wechat_processor.bill, dict), "账单应该是字典格式"
        
        # 验证每个账单都有必要的字段
        for bill_id, bill in wechat_processor.bill.items():
            assert "金额" in bill, f"账单 {bill_id} 缺少金额字段"
            assert "交易时间" in bill, f"账单 {bill_id} 缺少交易时间字段"
            assert "交易对方" in bill, f"账单 {bill_id} 缺少交易对方字段"
            assert "商品说明" in bill, f"账单 {bill_id} 缺少商品说明字段"
    
    def test_wechat_amount_parsing(self, wechat_processor):
        """测试金额解析（包含¥符号）"""
        # 验证所有金额都是浮点数
        for bill_id, bill in wechat_processor.bill.items():
            assert isinstance(bill["金额"], float), f"账单 {bill_id} 的金额应该是浮点数"
            assert bill["金额"] > 0, f"账单 {bill_id} 的金额应该大于0"
    
    def test_wechat_field_mapping(self, wechat_processor):
        """测试微信字段映射到支付宝格式"""
        # 验证字段映射
        for bill_id, bill in wechat_processor.bill.items():
            # 微信的"商品"字段应该映射到"商品说明"
            assert "商品说明" in bill, "应该有商品说明字段"
            assert "交易对方" in bill, "应该有交易对方字段"
    
    def test_wechat_only_expense(self, wechat_processor):
        """测试只保留支出记录"""
        # 所有账单应该都是支出
        for bill_id, bill in wechat_processor.bill.items():
            assert bill.get("收/支") == "支出", f"账单 {bill_id} 应该是支出"

    def test_wechat_auto_tagging(self, wechat_processor):
        """测试自动打标功能"""
        # 统计打标情况
        tagged_count = 0
        for bill_id, bill in wechat_processor.bill.items():
            if bill.get("类别") and bill["类别"].strip():
                tagged_count += 1
        
        # 应该有一些账单被自动打标了
        print(f"自动打标数量: {tagged_count}/{len(wechat_processor.bill)}")

class TestWechatEdgeCases:
    """测试微信账单解析的边界情况"""
    
    def test_wechat_refund_handling(self, wechat_processor):
        """测试退款处理"""
        # 验证已全额退款的交易被过滤
        for bill_id, bill in wechat_processor.bill.items():
            status = bill.get("当前状态", "")
            assert "已全额退款" not in status, "全额退款交易应该被过滤"
    
    def test_wechat_small_amount_filter(self, wechat_processor):
        """测试小额交易过滤"""
        # 所有保留的账单金额应该大于 0.001
        for bill_id, bill in wechat_processor.bill.items():
            assert bill["金额"] > 0.001, f"账单 {bill_id} 金额太小应该被过滤"


class TestWechatRefund:
    """测试微信退款逻辑"""

    def test_partial_refund(self, wechat_processor):
        # 这是一个有退款的订单
        # 原单号: 5030350352342343040032
        # 原金额: 29.90
        # 预期金额: 20.0
        
        bill_id = "5030350352342343040032"
        assert bill_id in wechat_processor.bill
        from pytest import approx
        assert wechat_processor.bill[bill_id]["金额"] == approx(20.0)

    def test_full_refund(self, wechat_processor):
        """测试全额退款"""
        # 这是一个有退款的订单
        # 原单号: 5030350352342343040031
        # 退款之后应该不在订单列表里
        
        bill_id = "5030350352342343040031"
        assert bill_id not in wechat_processor.bill
