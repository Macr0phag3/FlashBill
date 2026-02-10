# ⚡️ 闪记(FlashBill)

一小时记完一年的账单！

自动化 & 智能化的记账助手，基于 Python Flask + Vue 3 + Element Plus 的个人记账分析工具。支持支付宝/微信账单导入、自动规则打标、AI 智能分类以及多维度统计分析。

（本项目属于 vibe coding 的一个项目，基于 Antigravity 以及内置的 LLM 开发，配套的文章见: [🚧 施工中]

~~有什么 bug 和 gemini 说去吧 ~~

## 🤖 AI Native & Robust Testing

- **100% AI Generated**: 本项目的核心逻辑、前端 UI 以及文档均由 AI 辅助生成。
- **Test Driven**: 包含完善的单元测试 (`tests/`)，覆盖了账单解析、规则匹配等核心功能，确保重构与迭代的稳定性。
- **Quality Assurance**: 通过自动化测试保证数据处理的准确性，一定程度上解决了 AI 生成代码不可控的问题。

## ✨ 功能特性

- **账单导入**：
  - 支持 **支付宝** 和 **微信** 账单文件（CSV/Excel）直接导入解析。
  - 自动识别文件格式与编码。

- **智能打标**：
  - **规则引擎**：基于关键字/正则的自动分类规则，支持优先级排序。
  - **AI 辅助**：集成 OpenAI API，对未知账单进行智能分类与打标，并能反向生成规则。

- **统计分析**：
  - **日历热力图**：直观展示每日消费密度。
  - **分类/标签统计**：饼图展示支出构成。
  - **月度趋势**：折线图追踪消费走势。
  - **明细查询**：支持按账本、时间、类别组合筛选账单。

- **现代化 UI**：
  - 基于 Element Plus 的简洁响应式设计。
  - 适配深色模式（Dark Mode）。


## 🛠️ 技术栈

- **后端**：Python 3, Flask, Pandas, OpenAI API
- **前端**：Vue 3, Element Plus, ECharts, Axios
- **数据存储**：本地文件系统 (JSON/Excel)，无外部数据库依赖。

## 📂 目录结构

```txt
├── app.py              # 应用入口
├── core/               # 核心逻辑
│   ├── config.py       # 配置管理
│   └── utils.py        # 工具函数 (解析器/AI接口)
├── routes/             # 路由模块 (API)
├── static/             # 静态资源 (JS/CSS)
├── templates/          # HTML 模板
├── data/               # 数据存储 (不包含在 git 中)
└── requirements.txt    # 项目依赖
```

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/macr0phag3/flash_bill.git
cd flash_bill
```

### 2. 环境配置
1. 首先安装一下依赖: `pip install -r requirements.txt`
2. 然后 运行 `setup.py` 初始化
3. 编辑 `.env` 文件以配置 API 密钥（用于 AI 打标功能，如果用不到可以不配置）：
```bash
# .env 文件内容
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=
OPENAI_MODEL=gpt-5.2
```

### 3. 运行应用

```bash
python app.py
```

启动后访问：[http://localhost:8000](http://localhost:8000)

## 📝 使用指南

1.  **准备与导入**：
    *   从支付宝/微信导出账单文件（无需解压密码）。
    *   在网页点击“导入账单”，选择文件并上传。
2.  **筛选与分析**：
    *   进入“统计分析”页面查看消费概览。
    *   使用顶部过滤器筛选特定时间段或类别的账单。
3.  **规则与打标**：
    *   对未分类账单使用“自动打标”应用现有规则。
    *   支持划词创建自动打标规则
    *   使用“AI 打标”尝试自动识别，并保存准确的规则以供日后使用。

## 📄 许可证

[MIT License](LICENSE)
