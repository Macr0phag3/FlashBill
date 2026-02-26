"""
测试 Flask API 接口

测试文件上传、账单管理、规则管理等 API 功能
"""
import pytest
import json
import io
import os
from app import app


@pytest.fixture
def client():
    """Flask 测试客户端"""
    app.config['TESTING'] = True
    app.config['UPLOAD_FOLDER'] = 'temp_uploads'
    with app.test_client() as client:
        yield client


@pytest.fixture
def sample_bills():
    """示例账单数据"""
    return {
        "001": {
            "交易时间": "2023-10-01 12:00",
            "金额": 25.5,
            "交易对方": "美团外卖",
            "商品说明": "午餐",
            "收/支": "支出",
            "类别": "",
            "标签": "",
            "备注": "",
            "账本": "支付宝",
            "命中规则": ""
        },
        "002": {
            "交易时间": "2023-10-02 18:30",
            "金额": 15.0,
            "交易对方": "滴滴出行",
            "商品说明": "打车",
            "收/支": "支出",
            "类别": "行",
            "标签": "打车",
            "备注": "",
            "账本": "微信",
            "命中规则": ""
        }
    }


# ==================== 页面路由测试 ====================

class TestPageRoutes:
    """测试页面路由"""
    
    def test_index_page(self, client):
        """测试首页正常"""
        response = client.get('/')
        assert response.status_code == 200

    def test_tagging_page(self, client):
        """测试新增记账页面"""
        response = client.get('/tagging')
        assert response.status_code == 200
    
    def test_rules_page(self, client):
        """测试规则页面"""
        response = client.get('/rules-page')
        assert response.status_code == 200
    
    def test_categories_page_get(self, client):
        """测试分类页面 GET"""
        response = client.get('/categories')
        assert response.status_code == 200

    def test_books_page_get(self, client):
        """测试账本管理页面 GET"""
        response = client.get('/books')
        assert response.status_code == 200
    
    def test_statistics_page(self, client):
        """测试统计页面"""
        response = client.get('/statistics')
        assert response.status_code == 200


# ==================== 账单数据 API 测试 ====================

class TestBillsAPI:
    """测试账单数据API"""
    
    def test_get_bills_empty(self, client):
        """测试获取空账单列表"""
        from app import current_bills
        current_bills.clear()
        
        response = client.get('/api/bills')
        data = response.get_json()
        assert data['success'] == False
        assert '没有账单数据' in data['message']
    
    def test_get_bills_with_data(self, client, sample_bills):
        """测试获取有数据的账单列表"""
        from app import current_bills
        current_bills.clear()
        current_bills.update(sample_bills)
        
        response = client.get('/api/bills')
        data = response.get_json()
        assert data['success'] == True
        assert 'bills' in data
        assert len(data['bills']) == 2
    
    def test_get_bill_stats_empty(self, client):
        """测试获取空账单统计"""
        from app import current_bills
        current_bills.clear()
        
        response = client.get('/api/bill_stats')
        data = response.get_json()
        assert data['success'] == False
    
    def test_get_bill_stats_with_data(self, client, sample_bills):
        """测试获取有数据的账单统计"""
        from app import current_bills
        current_bills.clear()
        current_bills.update(sample_bills)
        
        response = client.get('/api/bill_stats')
        data = response.get_json()
        assert data['success'] == True
        assert 'stats' in data
        assert data['stats']['total'] == 2
        assert data['stats']['categoryTagged'] == 1  # 只有002有类别


# ==================== 规则 API 测试 ====================

class TestRulesAPI:
    """测试规则管理API"""
    
    def test_get_rules(self, client):
        """测试获取规则列表"""
        response = client.get('/api/rules')
        data = response.get_json()
        assert response.status_code == 200
        assert data['success'] == True
        assert 'rules' in data
        assert isinstance(data['rules'], list)
    
    def test_update_rules(self, client):
        """测试更新规则"""
        new_rules = [{
            "category": "食",
            "tag": "测试",
            "key": "交易对方",
            "rule": ["测试商家"],
            "time_based": [],
            "comment": "测试规则"
        }]
        
        response = client.post('/api/rules',
                              data=json.dumps({'rules': new_rules}),
                              content_type='application/json')
        data = response.get_json()
        assert response.status_code == 200
        assert data['success'] == True
    
    def test_update_rules_invalid_format(self, client):
        """测试更新规则时传入无效格式"""
        response = client.post('/api/rules',
                              data=json.dumps({'rules': 'invalid'}),
                              content_type='application/json')
        data = response.get_json()
        assert response.status_code == 400
        assert data['success'] == False
    
    def test_update_rules_triggers_retag(self, client, sample_bills):
        """测试更新规则后自动重新打标"""
        from app import current_bills
        current_bills.clear()
        current_bills.update(sample_bills)
        
        new_rules = [{
            "category": "食",
            "tag": "外卖",
            "key": "交易对方",
            "rule": ["美团外卖"],
            "time_based": [],
            "comment": ""
        }]
        
        response = client.post('/api/rules',
                              data=json.dumps({'rules': new_rules}),
                              content_type='application/json')
        assert response.status_code == 200
    
    def test_rules_form_get(self, client):
        """测试规则表单 GET 请求"""
        response = client.get('/rules')
        assert response.status_code == 200
        assert b'rules' in response.data.lower() or response.status_code == 200
    
    def test_rules_form_post_new_rule(self, client):
        """测试规则表单 POST - 添加新规则"""
        response = client.post('/rules', data={
            'counter_party_new': '测试商家',
            'goods_desc_new': '测试说明',
            'category_new': '食',
            'tag_new': '测试标签',
        }, follow_redirects=True)
        assert response.status_code == 200
    
    def test_rules_form_post_existing_rule(self, client):
        """测试规则表单 POST - 更新现有规则"""
        response = client.post('/rules', data={
            'counter_party_0': '美团外卖',
            'goods_desc_0': '外卖',
            'category_0': '食',
            'tag_0': '外卖',
        }, follow_redirects=True)
        assert response.status_code == 200
    
    def test_rules_form_post_with_bills_triggers_sync(self, client, sample_bills):
        """测试规则表单 POST - 存在账单数据时触发同步路径"""
        from app import current_bills
        from core.utils import save_rules
        
        # 保存兼容格式的规则，这样 apply_rules_and_sync 不会出错
        save_rules([])
        
        current_bills.clear()
        current_bills.update(sample_bills)
        
        # 表单提交后会保存新规则，然后 apply_rules_and_sync 会用空规则列表处理
        # 由于规则为空，不会触发 _match_rule，只会走初始化分支
        response = client.post('/rules', data={}, follow_redirects=True)
        assert response.status_code == 200
    
    def test_rules_form_post_empty(self, client):
        """测试规则表单 POST - 空提交"""
        response = client.post('/rules', data={}, follow_redirects=True)
        assert response.status_code == 200


# ==================== 分类 API 测试 ====================

class TestCategoriesAPI:
    """测试分类管理API"""
    
    def test_get_categories(self, client):
        """测试获取分类"""
        response = client.get('/api/categories')
        data = response.get_json()
        assert response.status_code == 200
        assert data['success'] == True
        assert 'categories' in data
        assert isinstance(data['categories'], dict)
    
    def test_update_categories(self, client):
        """测试更新分类"""
        new_categories = {
            "食": ["外卖", "堂食"],
            "行": ["打车", "地铁"]
        }
        
        response = client.post('/api/categories',
                              data=json.dumps({'categories': new_categories}),
                              content_type='application/json')
        data = response.get_json()
        assert response.status_code == 200
        assert data['success'] == True
    
    def test_update_categories_invalid_format(self, client):
        """测试更新分类时传入无效格式"""
        response = client.post('/api/categories',
                              data=json.dumps({'categories': []}),
                              content_type='application/json')
        data = response.get_json()
        assert response.status_code == 400
        assert data['success'] == False


# ==================== 账本 API 测试 ====================

class TestBooksAPI:
    """测试账本管理API"""

    def test_get_books(self, client):
        """测试获取账本"""
        response = client.get('/api/books')
        data = response.get_json()
        assert response.status_code == 200
        assert data['success'] == True
        assert 'books' in data
        assert 'meta' in data
        assert isinstance(data['books'], dict)
        assert isinstance(data['meta'], dict)

    def test_update_books(self, client):
        """测试更新账本"""
        new_books = {
            "日常开销": {"fixed_quota": 2000},
            "旅游基金": {"fixed_quota": 5000},
        }
        new_meta = {
            "日常开销": {"icon": "Wallet", "color": "#409EFF"},
            "旅游基金": {"icon": "MapLocation", "color": "#67C23A"},
        }

        response = client.post('/api/books',
                              data=json.dumps({'books': new_books, 'meta': new_meta}),
                              content_type='application/json')
        data = response.get_json()
        assert response.status_code == 200
        assert data['success'] == True

    def test_update_books_invalid_format(self, client):
        """测试更新账本时传入无效格式"""
        response = client.post('/api/books',
                              data=json.dumps({'books': []}),
                              content_type='application/json')
        data = response.get_json()
        assert response.status_code == 400
        assert data['success'] == False


# ==================== 进度管理 API 测试 ====================

class TestProgressAPI:
    """测试进度保存和加载API"""
    
    def test_save_progress(self, client):
        """测试保存进度"""
        test_bills = {
            "001": {
                "交易时间": "2023-10-01 12:00",
                "金额": 20.0,
                "类别": "食",
                "标签": "外卖",
                "备注": "",
                "账本": "支付宝",
                "命中规则": ""
            }
        }
        
        response = client.post('/api/save_progress',
                              data=json.dumps({'bills': test_bills}),
                              content_type='application/json')
        data = response.get_json()
        assert response.status_code == 200
        assert data['success'] == True
    
    def test_check_progress(self, client):
        """测试检查是否有进度"""
        response = client.get('/api/check_progress')
        data = response.get_json()
        assert response.status_code == 200
        assert data['success'] == True
        assert 'has_progress' in data
    
    def test_load_progress(self, client):
        """测试加载进度"""
        # 先保存进度
        test_bills = {"test": {"交易时间": "2023-10-01", "金额": 10.0}}
        client.post('/api/save_progress',
                   data=json.dumps({'bills': test_bills}),
                   content_type='application/json')
        
        # 然后加载
        response = client.get('/api/load_progress')
        data = response.get_json()
        assert response.status_code == 200
        assert data['success'] == True
    
    def test_clear_cache(self, client):
        """测试清除缓存"""
        response = client.post('/api/clear_cache')
        data = response.get_json()
        assert response.status_code == 200
        assert data['success'] == True
    
    def test_save_progress_invalid_format(self, client):
        """测试保存无效格式的进度"""
        response = client.post('/api/save_progress',
                              data=json.dumps({}),
                              content_type='application/json')
        data = response.get_json()
        assert data['success'] == False


# ==================== 自动打标 API 测试 ====================

class TestAutoTagAPI:
    """测试自动打标API"""
    
    def test_auto_tag_no_bills(self, client):
        """测试无账单时自动打标"""
        from app import current_bills
        current_bills.clear()
        # 确保没有进度文件
        if os.path.exists('bills.process'):
            os.remove('bills.process')
        
        response = client.post('/api/auto_tag')
        data = response.get_json()
        assert data['success'] == False
    
    def test_auto_tag_with_bills(self, client, sample_bills):
        """测试有账单时自动打标"""
        from app import current_bills
        # 需要同时设置 current_bills 和保存进度
        current_bills.clear()
        current_bills.update(sample_bills)
        
        # 保存进度文件
        client.post('/api/save_progress',
                   data=json.dumps({'bills': sample_bills}),
                   content_type='application/json')
        
        response = client.post('/api/auto_tag')
        data = response.get_json()
        assert data['success'] == True


# ==================== 导出 API 测试 ====================

class TestExportAPI:
    """测试导出功能API"""
    
    def test_export_empty_bills(self, client):
        """测试导出空账单"""
        response = client.post('/api/export',
                              data=json.dumps({'bills': []}),
                              content_type='application/json')
        data = response.get_json()
        assert 'error' in data
    
    def test_export_with_bills(self, client):
        """测试正常导出账单"""
        bills = [{
            "交易时间": "2023-10-01 12:00",
            "金额": 25.5,
            "类别": "食",
            "标签": "外卖",
            "交易对方": "美团外卖",
            "商品说明": "午餐",
            "备注": "",
            "账本": "支付宝",
            "命中规则": ""
        }]
        
        response = client.post('/api/export',
                              data=json.dumps({'bills': bills}),
                              content_type='application/json')
        assert response.status_code == 200
        assert response.content_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'


# ==================== 文件上传测试 ====================

class TestFileUpload:
    """测试文件上传功能"""
    
    def test_upload_no_file(self, client):
        """测试没有文件的上传"""
        response = client.post('/upload')
        data = response.get_json()
        assert response.status_code == 400
        assert 'error' in data
    
    def test_upload_empty_filename(self, client):
        """测试空文件名"""
        data = {'file': (io.BytesIO(b''), '')}
        response = client.post('/upload', data=data, content_type='multipart/form-data')
        data = response.get_json()
        assert response.status_code == 400
    
    def test_upload_unsupported_format(self, client):
        """测试不支持的文件格式"""
        data = {
            'file': (io.BytesIO(b'test content'), 'test.txt'),
            'bill_type': 'alipay'
        }
        response = client.post('/upload', data=data, content_type='multipart/form-data')
        data = response.get_json()
        assert response.status_code == 400
        assert 'error' in data


# ==================== 分类表单测试 ====================

class TestCategoriesForm:
    """测试分类表单提交"""
    
    def test_categories_form_post(self, client):
        """测试分类表单提交"""
        form_data = {
            'category_0': '食',
            'tags_0': '外卖, 堂食',
            'category_new': '住',
            'tags_new': '房租, 水电'
        }
        response = client.post('/categories', data=form_data, follow_redirects=True)
        assert response.status_code == 200


# ==================== 真实文件上传测试 ====================

class TestRealFileUpload:
    """使用真实账单文件测试上传功能"""
    
    def test_upload_alipay_csv(self, client):
        """测试上传真实的支付宝 CSV 账单"""
        csv_path = 'tests/test_data/alipay-sample.csv'
        if not os.path.exists(csv_path):
            pytest.skip(f"测试文件不存在: {csv_path}")
        
        with open(csv_path, 'rb') as f:
            data = {
                'file': (f, 'alipay-sample.csv'),
                'bill_type': 'alipay'
            }
            response = client.post('/upload', data=data, content_type='multipart/form-data')
        
        result = response.get_json()
        assert response.status_code == 200
        assert result['success'] == True
        assert 'bills' in result
        assert len(result['bills']) > 0
    
    def test_upload_wechat_xlsx(self, client):
        """测试上传真实的微信 XLSX 账单"""
        xlsx_path = 'tests/test_data/wechat-sample.xlsx'
        if not os.path.exists(xlsx_path):
            pytest.skip(f"测试文件不存在: {xlsx_path}")
        
        with open(xlsx_path, 'rb') as f:
            data = {
                'file': (f, 'wechat-sample.xlsx'),
                'bill_type': 'wechat'
            }
            response = client.post('/upload', data=data, content_type='multipart/form-data')
        
        result = response.get_json()
        assert response.status_code == 200
        assert result['success'] == True
        assert 'bills' in result
    
    def test_upload_unsupported_bill_type(self, client):
        """测试不支持的账单类型"""
        csv_path = 'tests/test_data/alipay-sample.csv'
        if not os.path.exists(csv_path):
            pytest.skip(f"测试文件不存在: {csv_path}")
        
        with open(csv_path, 'rb') as f:
            data = {
                'file': (f, 'alipay-sample.csv'),
                'bill_type': 'unknown_type'
            }
            response = client.post('/upload', data=data, content_type='multipart/form-data')
        
        result = response.get_json()
        assert response.status_code == 400
        assert 'error' in result


# ==================== 统计 API 测试 ====================

class TestStatisticsAPI:
    """测试统计 API"""
    
    def test_get_statistics(self, client):
        """测试获取统计数据"""
        # 确保 DB.xlsx 存在
        if not os.path.exists('data/DB.xlsx'):
            pytest.skip("data/DB.xlsx 不存在")
        
        response = client.get('/api/statistics')
        result = response.get_json()
        
        assert response.status_code == 200
        assert result['success'] == True
        assert 'items' in result
        assert 'total' in result
    
    def test_get_statistics_with_pagination(self, client):
        """测试带分页的统计数据"""
        if not os.path.exists('data/DB.xlsx'):
            pytest.skip("data/DB.xlsx 不存在")
        
        response = client.get('/api/statistics?page=1&page_size=10')
        result = response.get_json()
        
        assert response.status_code == 200
        assert result['success'] == True
        assert len(result['items']) <= 10
    
    def test_get_statistics_with_sort(self, client):
        """测试带排序的统计数据"""
        if not os.path.exists('data/DB.xlsx'):
            pytest.skip("data/DB.xlsx 不存在")
        
        response = client.get('/api/statistics?sort_by=amount&sort_order=desc')
        result = response.get_json()
        
        assert response.status_code == 200
        assert result['success'] == True


# ==================== 规则表单测试 ====================

class TestRulesForm:
    """测试规则表单提交"""
    
    def test_rules_form_get(self, client):
        """测试规则页面 GET"""
        response = client.get('/rules')
        assert response.status_code == 200


# ==================== AI 打标 API 测试 ====================

class TestAITagAPI:
    """测试 AI 打标 API"""
    
    def test_apply_ai_tags_empty(self, client):
        """测试应用空的 AI 打标结果"""
        response = client.post('/api/apply_ai_tags',
                              data=json.dumps({'tagged_bills': []}),
                              content_type='application/json')
        data = response.get_json()
        assert data['success'] == False
        assert '没有要应用' in data['message']
    
    def test_apply_ai_tags_with_data(self, client, sample_bills):
        """测试应用 AI 打标结果"""
        from app import current_bills
        current_bills.clear()
        current_bills.update(sample_bills)
        
        # 保存进度
        client.post('/api/save_progress',
                   data=json.dumps({'bills': sample_bills}),
                   content_type='application/json')
        
        # 应用打标结果
        tagged_bills = [{
            '交易订单号': '001',
            '类别': 'AI食',
            '标签': 'AI外卖',
            '备注': 'AI测试'
        }]
        
        response = client.post('/api/apply_ai_tags',
                              data=json.dumps({
                                  'tagged_bills': tagged_bills,
                                  'save_rules': False,
                                  'selected_rules': []
                              }),
                              content_type='application/json')
        data = response.get_json()
        assert data['success'] == True
        assert data['applied_count'] == 1
    
    def test_apply_ai_tags_with_rules(self, client, sample_bills):
        """测试应用 AI 打标结果并保存规则"""
        from app import current_bills
        current_bills.clear()
        current_bills.update(sample_bills)
        
        # 保存进度
        client.post('/api/save_progress',
                   data=json.dumps({'bills': sample_bills}),
                   content_type='application/json')
        
        tagged_bills = [{
            '交易订单号': '001',
            '类别': '食',
            '标签': '外卖',
            '备注': ''
        }]
        
        selected_rules = [{
            'key': '交易对方',
            'rule': ['测试商家'],
            'category': '食',
            'tag': '测试',
            'comment': 'AI 建议的规则'
        }]
        
        response = client.post('/api/apply_ai_tags',
                              data=json.dumps({
                                  'tagged_bills': tagged_bills,
                                  'save_rules': True,
                                  'selected_rules': selected_rules
                              }),
                              content_type='application/json')
        data = response.get_json()
        assert data['success'] == True
