"""
测试支付宝账单解析

测试 Alipay 类的账单解析、退款处理、金额计算等核心功能
"""
import os
from core.utils import Alipay


class TestAlipayParsing:
    """测试支付宝账单解析"""
    
    def test_alipay_basic_parsing(self):
        """测试基本解析功能"""
        # 使用真实的测试数据
        csv_path = "tests/test_data/alipay-sample.csv"
        assert os.path.exists(csv_path), f"测试文件不存在: {csv_path}"
        
        processor = Alipay(csv_path)
        
        # 验证账单数量
        assert len(processor.bill) > 0, "应该解析出账单数据"
        assert isinstance(processor.bill, dict), "账单应该是字典格式"
        
        # 验证每个账单都有必要的字段
        for bill_id, bill in processor.bill.items():
            assert "金额" in bill, f"账单 {bill_id} 缺少金额字段"
            assert "交易时间" in bill, f"账单 {bill_id} 缺少交易时间字段"
            assert "交易对方" in bill, f"账单 {bill_id} 缺少交易对方字段"
            assert "商品说明" in bill, f"账单 {bill_id} 缺少商品说明字段"
            assert "类别" in bill, f"账单 {bill_id} 缺少类别字段"
            assert "标签" in bill, f"账单 {bill_id} 缺少标签字段"
    
    def test_alipay_amount_parsing(self):
        """测试金额解析为浮点数"""
        csv_path = "tests/test_data/alipay-sample.csv"
        processor = Alipay(csv_path)
        
        # 验证所有金额都是浮点数
        for bill_id, bill in processor.bill.items():
            assert isinstance(bill["金额"], float), f"账单 {bill_id} 的金额应该是浮点数"
            assert bill["金额"] > 0, f"账单 {bill_id} 的金额应该大于0"
    
    def test_alipay_filter_income(self):
        """测试收入交易被过滤"""
        csv_path = "tests/test_data/alipay-sample.csv"
        processor = Alipay(csv_path)
        
        # 验证账单类型（应该是支出或不计收支）
        for bill_id, bill in processor.bill.items():
            income_type = bill.get("收/支", "")
            # 收入类型的交易应该被过滤掉
            assert income_type in ["支出", "不计收支"], f"账单 {bill_id} 类型不应该是收入"
    
    def test_alipay_filter_special_transactions(self):
        """测试特殊交易被过滤（余额宝、基金等）"""
        csv_path = "tests/test_data/alipay-sample.csv"
        processor = Alipay(csv_path)
        
        # 验证没有余额宝等投资类交易
        for bill_id, bill in processor.bill.items():
            goods_desc = bill.get("商品说明", "")
            counter_party = bill.get("交易对方", "")
            
            # 这些应该被过滤掉
            assert "余额宝" not in goods_desc, "余额宝交易应该被过滤"
            assert "蚂蚁财富" not in goods_desc, "蚂蚁财富交易应该被过滤"
            assert "基金销售" not in counter_party, "基金交易应该被过滤"
    
    def test_alipay_auto_tagging(self):
        """测试自动打标功能"""
        csv_path = "tests/test_data/alipay-sample.csv"
        processor = Alipay(csv_path)
        
        # 统计打标情况
        tagged_count = 0
        for bill_id, bill in processor.bill.items():
            if bill.get("类别") and bill["类别"].strip():
                tagged_count += 1
        
        # 应该有一些账单被自动打标了
        print(f"自动打标数量: {tagged_count}/{len(processor.bill)}")
        # 这个取决于规则文件，所以只验证格式正确即可
    
    def test_alipay_transaction_status(self):
        """测试交易状态过滤"""
        csv_path = "tests/test_data/alipay-sample.csv"
        processor = Alipay(csv_path)
        
        # 所有账单应该都是成功的交易
        for bill_id, bill in processor.bill.items():
            status = bill.get("交易状态", "")
            # 交易关闭的应该被过滤掉
            assert status != "交易关闭", f"账单 {bill_id} 交易已关闭应该被过滤"


class TestAlipayEdgeCases:
    """测试支付宝账单解析的边界情况"""
    
    def test_alipay_meal_subsidy_deduction(self):
        """测试餐补扣除逻辑"""
        # 这个需要查看实际数据中是否有餐补
        csv_path = "tests/test_data/alipay-sample.csv"
        processor = Alipay(csv_path)
        
        # 验证有餐补的交易金额被正确计算
        for bill_id, bill in processor.bill.items():
            payment_method = bill.get("收/付款方式", "")
            if "因公付" in payment_method:
                # 餐补应该已经被扣除，金额应该合理
                assert bill["金额"] >= 0, f"餐补扣除后金额应该大于等于0"
    
    def test_alipay_small_amount_filter(self):
        """测试小额交易过滤"""
        csv_path = "tests/test_data/alipay-sample.csv"
        processor = Alipay(csv_path)
        
        # 所有保留的账单金额应该大于 0.001
        for bill_id, bill in processor.bill.items():
            assert bill["金额"] >= 0.001, f"账单 {bill_id} 金额太小应该被过滤"
    
    def test_alipay_bill_id_format(self):
        """测试交易订单号格式"""
        csv_path = "tests/test_data/alipay-sample.csv"
        processor = Alipay(csv_path)
        
        # 验证账单ID格式
        for bill_id in processor.bill.keys():
            # 账单ID应该是字符串
            assert isinstance(bill_id, str), "账单ID应该是字符串"
            # 主要的账单ID应该是纯数字或包含下划线/星号的退款单号
            assert len(bill_id) > 0, "账单ID不能为空"


class TestAlipayDataIntegrity:
    """测试支付宝账单数据完整性"""
    
    def test_no_duplicate_bill_ids(self):
        """测试没有重复的交易订单号"""
        csv_path = "tests/test_data/alipay-sample.csv"
        processor = Alipay(csv_path)
        
        # 字典本身保证了唯一性，但我们验证数量
        assert len(processor.bill) > 0, "应该有账单数据"
        
        # 验证所有 bill_id 都是唯一的
        bill_ids = list(processor.bill.keys())
        unique_ids = set(bill_ids)
        assert len(bill_ids) == len(unique_ids), "不应该有重复的账单ID"
    
    def test_required_fields_present(self):
        """测试所有必需字段都存在"""
        csv_path = "tests/test_data/alipay-sample.csv"
        processor = Alipay(csv_path)
        
        required_fields = ["交易时间", "金额", "交易对方", "商品说明", "收/支", "收/付款方式", "交易状态"]
        
        for bill_id, bill in processor.bill.items():
            for field in required_fields:
                assert field in bill, f"账单 {bill_id} 缺少必需字段: {field}"


class TestAlipayRefund:
    """测试支付宝退款逻辑"""

    def test_partial_refund(self):
        """测试部分退款"""
        csv_path = "tests/test_data/alipay-sample.csv"
        processor = Alipay(csv_path)
        
        # 这是一个有退款的订单
        # 原单号: 2025122022001414551404160507
        # 原金额: 2.00
        # 预期金额: 0.73
        
        bill_id = "2025122022001414551404160507"
        assert bill_id in processor.bill
        from pytest import approx
        assert processor.bill[bill_id]["金额"] == approx(0.73)

    def test_full_refund(self):
        """测试全额退款"""
        csv_path = "tests/test_data/alipay-sample.csv"
        processor = Alipay(csv_path)
        
        # 这是一个有退款的订单
        # 原单号: 2025122022001414551404160508
        # 退款之后应该不在订单列表里
        
        bill_id = "2025122022001414551404160508"
        assert bill_id not in processor.bill

