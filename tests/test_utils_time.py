"""
测试时间处理工具函数

测试 time_cmp() 和 time_map() 函数的正确性
"""
from core.utils import time_cmp, time_map


class TestTimeComparison:
    """测试时间比较函数 time_cmp()"""
    
    def test_time_cmp_basic(self):
        """测试基本的时间比较功能"""
        # 时间在范围内
        assert time_cmp("08:00", "09:00", "10:00") == True
        # 时间在范围边界（起始）
        assert time_cmp("08:00", "08:00", "10:00") == True
        # 时间超出范围
        assert time_cmp("08:00", "11:00", "10:00") == False
    
    def test_time_cmp_with_seconds(self):
        """测试带秒的时间格式"""
        assert time_cmp("08:00:00", "09:30:00", "10:00") == True
        assert time_cmp("08:00:00", "09:30:45", "10:00") == True
        # 混合格式（有秒和无秒）
        assert time_cmp("08:00", "09:30:00", "10:00") == True
    
    def test_time_cmp_boundary_cases(self):
        """测试边界情况"""
        # 完全相等的时间
        assert time_cmp("09:00", "09:00", "09:00") == True
        # 跨越午夜（23:59）
        assert time_cmp("20:00", "23:00", "23:59") == True
        assert time_cmp("20:00", "23:59", "23:59") == True


class TestTimeMapping:
    """测试时间映射函数 time_map()"""
    
    def test_time_map_breakfast(self):
        """测试早餐时间识别（06:00 - 11:00）"""
        assert time_map("06:00") == "早餐"
        assert time_map("07:30") == "早餐"
        assert time_map("09:00") == "早餐"
        assert time_map("10:59") == "早餐"
    
    def test_time_map_lunch(self):
        """测试午餐时间识别（11:00 - 14:00）"""
        # 注意：11:00 会被早餐识别（早餐是 06:00-11:00，包含11:00）
        assert time_map("11:01") == "午餐"
        assert time_map("11:30") == "午餐"
        assert time_map("12:00") == "午餐"
        assert time_map("13:30") == "午餐"
        assert time_map("13:59") == "午餐"
    
    def test_time_map_dinner(self):
        """测试晚餐时间识别（17:00 - 20:00）"""
        assert time_map("17:00") == "晚餐"
        assert time_map("18:00") == "晚餐"
        assert time_map("19:00") == "晚餐"
        assert time_map("19:59") == "晚餐"
    
    def test_time_map_midnight_snack(self):
        """测试夜宵时间识别（20:00 - 03:00）"""
        # 注意：20:00 会被晚餐识别（晚餐是 17:00-20:00，包含20:00）
        # 晚上时段
        assert time_map("20:01") == "夜宵"
        assert time_map("22:00") == "夜宵"
        assert time_map("23:59") == "夜宵"
        # 凌晨时段
        assert time_map("00:00") == "夜宵"
        assert time_map("01:00") == "夜宵"
        assert time_map("02:30") == "夜宵"
    
    def test_time_map_unmapped_periods(self):
        """测试非就餐时段"""
        # 早餐前
        assert time_map("05:30") == None
        # 午餐和晚餐之间
        assert time_map("14:30") == None
        assert time_map("15:00") == None
        assert time_map("16:30") == None
        # 夜宵后
        assert time_map("03:30") == None
        assert time_map("04:00") == None
    
    def test_time_map_with_seconds(self):
        """测试带秒的时间格式"""
        assert time_map("08:30:45") == "早餐"
        assert time_map("12:00:00") == "午餐"
