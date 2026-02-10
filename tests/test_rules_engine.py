"""
测试规则引擎

测试 apply_rules_to_bills() 函数的规则匹配逻辑
"""
import pytest
import json
import os
from core.utils import apply_rules_to_bills


@pytest.fixture
def temp_rules_file():
    """创建临时的规则文件"""
    # 保存原始规则文件路径
    original_rules = None
    original_path = "data/rules.json"
    if os.path.exists(original_path):
        with open(original_path, 'r', encoding='utf-8') as f:
            original_rules = f.read()
    
    yield
    
    # 恢复原始规则文件
    if original_rules:
        with open(original_path, 'w', encoding='utf-8') as f:
            f.write(original_rules)
    elif os.path.exists(original_path):
        os.remove(original_path)


class TestRulesEngine:
    """测试规则匹配引擎"""
    
    def test_basic_rule_matching_by_counter_party(self, temp_rules_file):
        """测试基于交易对方的基本规则匹配"""
        # 准备测试规则
        rules = [{
            "category": "食",
            "tag": "外卖",
            "key": "交易对方",
            "rule": ["美团外卖", "饿了么"],
            "time_based": [],
            "comment": "外卖消费"
        }]
        with open("data/rules.json", 'w', encoding='utf-8') as f:
            json.dump(rules, f, ensure_ascii=False)
        
        # 准备测试账单
        bills = {
            "001": {
                "交易时间": "2023-10-01 12:00",
                "金额": 25.5,
                "交易对方": "美团外卖",
                "商品说明": "午餐",
                "类别": "",
                "标签": ""
            }
        }
        
        # 应用规则
        result = apply_rules_to_bills(bills)
        
        # 验证结果
        assert result["001"]["类别"] == "食"
        assert result["001"]["标签"] == "外卖"
        assert result["001"]["备注"] == "外卖消费"
    
    def test_basic_rule_matching_by_goods_desc(self, temp_rules_file):
        """测试基于商品说明的规则匹配"""
        rules = [{
            "category": "行",
            "tag": "打车",
            "key": "商品说明",
            "rule": ["滴滴出行", "打车"],
            "time_based": [],
            "comment": ""
        }]
        with open("data/rules.json", 'w', encoding='utf-8') as f:
            json.dump(rules, f, ensure_ascii=False)
        
        bills = {
            "002": {
                "交易时间": "2023-10-01 09:00",
                "金额": 18.0,
                "交易对方": "滴滴快车",
                "商品说明": "滴滴出行-快车",
                "类别": "",
                "标签": ""
            }
        }
        
        result = apply_rules_to_bills(bills)
        assert result["002"]["类别"] == "行"
        assert result["002"]["标签"] == "打车"
    
    def test_time_based_tagging(self, temp_rules_file):
        """测试基于时间的自动标签"""
        rules = [{
            "category": "食",
            "tag": "",
            "key": "交易对方",
            "rule": ["瑞幸咖啡"],
            "time_based": ["早餐", "午餐"],
            "comment": ""
        }]
        with open("data/rules.json", 'w', encoding='utf-8') as f:
            json.dump(rules, f, ensure_ascii=False)
        
        # 测试早餐时段
        bills_breakfast = {
            "003": {
                "交易时间": "2023-10-01 08:30",
                "金额": 15.0,
                "交易对方": "瑞幸咖啡",
                "商品说明": "咖啡",
                "类别": "",
                "标签": ""
            }
        }
        result = apply_rules_to_bills(bills_breakfast)
        assert result["003"]["类别"] == "食"
        assert result["003"]["标签"] == "早餐"  # 应该根据时间自动标记为早餐
        
        # 测试非就餐时段（应该不打标签）
        bills_afternoon = {
            "004": {
                "交易时间": "2023-10-01 15:00",
                "金额": 15.0,
                "交易对方": "瑞幸咖啡",
                "商品说明": "咖啡",
                "类别": "",
                "标签": ""
            }
        }
        result = apply_rules_to_bills(bills_afternoon)
        assert result["004"]["类别"] == "食"
        assert result["004"]["标签"] == "-"  # 时间不在范围内，应该设置为 "-"
    
    def test_time_based_all_option(self, temp_rules_file):
        """测试时间归类的"全部"选项"""
        rules = [{
            "category": "食",
            "tag": "",
            "key": "交易对方",
            "rule": ["麦当劳"],
            "time_based": ["全部"],
            "comment": ""
        }]
        with open("data/rules.json", 'w', encoding='utf-8') as f:
            json.dump(rules, f, ensure_ascii=False)
        
        # 测试不同时段都应该根据时间打标
        test_times = [
            ("08:00", "早餐"),
            ("12:00", "午餐"),
            ("18:00", "晚餐"),
            ("22:00", "夜宵")
        ]
        
        for time, expected_tag in test_times:
            bills = {
                "bill": {
                    "交易时间": f"2023-10-01 {time}",
                    "金额": 20.0,
                    "交易对方": "麦当劳",
                    "商品说明": "套餐",
                    "类别": "",
                    "标签": ""
                }
            }
            result = apply_rules_to_bills(bills)
            assert result["bill"]["标签"] == expected_tag, f"时间 {time} 应该标记为 {expected_tag}"
    
    def test_rule_priority(self, temp_rules_file):
        """测试规则优先级（第一个匹配的规则生效）"""
        rules = [
            {
                "category": "食",
                "tag": "咖啡",
                "key": "交易对方",
                "rule": ["星巴克"],
                "time_based": [],
                "comment": "第一个规则"
            },
            {
                "category": "行",
                "tag": "其他",
                "key": "交易对方",
                "rule": ["星巴克"],  # 同样匹配星巴克
                "time_based": [],
                "comment": "第二个规则"
            }
        ]
        with open("data/rules.json", 'w', encoding='utf-8') as f:
            json.dump(rules, f, ensure_ascii=False)
        
        bills = {
            "005": {
                "交易时间": "2023-10-01 10:00",
                "金额": 30.0,
                "交易对方": "星巴克",
                "商品说明": "咖啡",
                "类别": "",
                "标签": ""
            }
        }
        
        result = apply_rules_to_bills(bills)
        # 应该匹配第一个规则
        assert result["005"]["类别"] == "食"
        assert result["005"]["标签"] == "咖啡"
        assert result["005"]["备注"] == "第一个规则"
    
    def test_already_tagged_bills_not_overwritten(self, temp_rules_file):
        """测试已打标的账单不会被覆盖"""
        rules = [{
            "category": "食",
            "tag": "外卖",
            "key": "交易对方",
            "rule": ["美团外卖"],
            "time_based": [],
            "comment": ""
        }]
        with open("data/rules.json", 'w', encoding='utf-8') as f:
            json.dump(rules, f, ensure_ascii=False)
        
        # 账单已经有类别标记
        bills = {
            "006": {
                "交易时间": "2023-10-01 12:00",
                "金额": 25.0,
                "交易对方": "美团外卖",
                "商品说明": "午餐",
                "类别": "娱乐",  # 已经有类别
                "标签": "手动标记"
            }
        }
        
        result = apply_rules_to_bills(bills)
        # 不应该被规则覆盖
        assert result["006"]["类别"] == "娱乐"
        assert result["006"]["标签"] == "手动标记"
    
    def test_empty_category_with_tag_dash(self, temp_rules_file):
        """测试类别非空但标签为空时，标签设置为 '-'"""
        rules = [{
            "category": "住",
            "tag": "",  # 空标签
            "key": "交易对方",
            "rule": ["房租"],
            "time_based": [],
            "comment": ""
        }]
        with open("data/rules.json", 'w', encoding='utf-8') as f:
            json.dump(rules, f, ensure_ascii=False)
        
        bills = {
            "007": {
                "交易时间": "2023-10-01 10:00",
                "金额": 2000.0,
                "交易对方": "房租支付",
                "商品说明": "房租",
                "类别": "",
                "标签": ""
            }
        }
        
        result = apply_rules_to_bills(bills)
        assert result["007"]["类别"] == "住"
        assert result["007"]["标签"] == "-"
    
    def test_any_key_rule_matching(self, temp_rules_file):
        """测试 'ANY' 关键字同时匹配交易对方和商品说明"""
        rules = [{
            "category": "其他",
            "tag": "杂项",
            "key": "ANY",
            "rule": ["测试"],
            "time_based": [],
            "comment": "任意匹配"
        }]
        with open("data/rules.json", 'w', encoding='utf-8') as f:
            json.dump(rules, f, ensure_ascii=False)
        
        bills = {
            "009": {
                "交易时间": "2023-10-01 12:00",
                "金额": 10.0,
                "交易对方": "测试对方",
                "商品说明": "普通商品",
                "类别": "",
                "标签": ""
            },
            "010": {
                "交易时间": "2023-10-01 12:00",
                "金额": 10.0,
                "交易对方": "普通对方",
                "商品说明": "测试商品",
                "类别": "",
                "标签": ""
            }
        }
        
        result = apply_rules_to_bills(bills)
        
        assert result["009"]["类别"] == "其他"
        assert result["009"]["标签"] == "杂项"
        assert result["010"]["类别"] == "其他"
        assert result["010"]["标签"] == "杂项"
    
    def test_regex_rule_matching(self, temp_rules_file):
        """测试正则匹配规则"""
        rules = [{
            "category": "购物",
            "tag": "网购",
            "key": "交易对方",
            "rule": ["^支付宝-.*商城$"],
            "match_mode": "regex",
            "time_based": [],
            "comment": "正则匹配"
        }]
        with open("data/rules.json", 'w', encoding='utf-8') as f:
            json.dump(rules, f, ensure_ascii=False)
        
        bills = {
            "011": {
                "交易时间": "2023-10-01 12:00",
                "金额": 100.0,
                "交易对方": "支付宝-天猫商城", # Should match
                "商品说明": "商品",
                "类别": "",
                "标签": ""
            },
            "012": {
                "交易时间": "2023-10-01 12:00",
                "金额": 100.0,
                "交易对方": "微信-天猫商城", # Should NOT match start
                "商品说明": "商品",
                "类别": "",
                "标签": ""
            }
        }
        
        result = apply_rules_to_bills(bills)
        
        assert result["011"]["类别"] == "购物"
        assert result["011"]["标签"] == "网购"
        assert result["012"]["类别"] == "" # Not matched
    
    def test_no_rules_file(self):
        """测试没有规则文件的情况"""
        # 临时移除规则文件
        if os.path.exists("data/rules.json"):
            os.rename("data/rules.json", "data/rules.json.bak")
        
        try:
            bills = {
                "008": {
                    "交易时间": "2023-10-01 12:00",
                    "金额": 20.0,
                    "交易对方": "测试",
                    "商品说明": "测试",
                    "类别": "",
                    "标签": ""
                }
            }
            
            result = apply_rules_to_bills(bills)
            # 没有规则，应该保持原样
            assert result["008"]["类别"] == ""
            assert result["008"]["标签"] == ""
        finally:
            # 恢复规则文件
            if os.path.exists("data/rules.json.bak"):
                os.rename("data/rules.json.bak", "data/rules.json")
