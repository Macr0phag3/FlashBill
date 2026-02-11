# ⚡️ 闪记(FlashBill)

一小时记完一年的账单！

自动化 & 智能化的记账助手，基于 Python Flask + Vue 3 + Element Plus 的个人记账分析工具。支持支付宝/微信账单导入、自动规则打标、AI 智能分类以及多维度统计分析。

（本项目属于 vibe coding 的一个项目，基于 Antigravity 以及内置的 LLM 开发，配套的文章见: [🚧 施工中]

~~有什么 bug 和 gemini 说去吧~~

## 🤖 AI Native & Robust Testing

- **100% AI Generated**: 本项目的核心逻辑、前端 UI 以及文档均由 AI 辅助生成。
- **Test Driven**: 包含完善的单元测试 (`tests/`)，覆盖了账单解析、规则匹配等核心功能，确保重构与迭代的稳定性。
- **Quality Assurance**: 通过自动化测试保证数据处理的准确性，一定程度上解决了 AI 生成代码不可控的问题。

备注：打标完成之后，需要导出账单 -> 手动复制粘贴到 DB.xlsx 中，这么设计主要是处于以下考虑：
1. 避免 AI 后续改动代码或者测试时，导致 DB.xlsx 出现非预期的改动，这是作为本项目的数据库，数据安全很重要，因此最好不提供这个功能
2. 打标完成之后，可以通过导出的账单人工审核对账，为自动打标或者 ai 打标的问题兜底

## ✨ 功能特性

- **账单导入**：
  <img width="2560" height="716" alt="image" src="https://github.com/user-attachments/assets/c83fdb67-224b-48c7-bb9c-3f0f662119f1" />
  - 支持 **支付宝** 和 **微信** 账单文件（CSV/Excel）直接导入解析。
  - 自动识别文件格式与编码。

- **智能打标**：
  <img width="2560" height="1313" alt="image" src="https://github.com/user-attachments/assets/6b7af1c5-3ef2-4af5-b8bb-37f75be51ff0" />
  - **规则引擎**：基于关键字/正则的自动分类规则，支持优先级排序。
  - **划词打标**：支持划词创建自动打标规则<br>
    <img height="300" alt="image" src="https://github.com/user-attachments/assets/a075cf82-cc02-42c3-94e3-9b021fcc90ba" />
    <img height="300" alt="image" src="https://github.com/user-attachments/assets/037b444b-02d5-4c61-b6b4-461e46a109fa" />
  - **AI 辅助**：集成 OpenAI API，对未知账单进行智能分类与打标，并能反向生成规则。

- **统计分析**：
  - **数据表格**：直观展示历史账单。
    <img width="2560" height="1313" alt="image" src="https://github.com/user-attachments/assets/47572cf5-bc8f-4feb-8dd7-b4aacc8d7278" />
  - **时间线**：展示每日流水。
    <img width="2560" height="1313" alt="image" src="https://github.com/user-attachments/assets/dea71007-5d72-468e-856b-9eb7c94e1d91" />
  - **统计图**：通过折线图的方式按时间窗口汇总消费情况，配备多种均线。
    <img width="2560" height="1313" alt="image" src="https://github.com/user-attachments/assets/439f5d1f-0bc4-4c6b-a746-82af809067d8" />
  - **日历视图**：直观展示每日消费力度。
    <img width="2560" height="1313" alt="image" src="https://github.com/user-attachments/assets/a50bc453-e944-47f8-bea8-a220787683f6" />
  - **分类统计**：通过饼图展示支出构成。
    <img width="2560" height="1313" alt="image" src="https://github.com/user-attachments/assets/4efb20bd-1438-4d11-9878-8b69d50e9ada" />
  - **数据透视**：通过柱状图透视消费时间段的习惯。
    <img width="2560" height="1313" alt="image" src="https://github.com/user-attachments/assets/f5b378bb-502a-46ac-924d-e1d1ac348ae4" />
  - **数据分析**：提供账单的组合计算功能。
    <img width="2560" height="1313" alt="image" src="https://github.com/user-attachments/assets/c137f1b6-7250-48b1-a299-ec830fc35084" />

- **现代化 UI**：
  - 基于 Element Plus 的简洁响应式设计。
  - 适配深色模式（Dark Mode）。
  - 多处酷炫动画。


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

在支付宝/微信申请导出账单之后，上传即可触发自动打标。

## ☁️ Render 免费部署（示例站）

仓库已内置 `render.yaml`，可以直接用 Render Blueprint 一键部署。

请注意：

- Render 免费实例会休眠，首次访问可能需要等待冷启动。
- 免费实例文件系统是临时的：上传账单、规则修改、进度缓存在重启后可能丢失。
- **仅作为在线 Demo，请不要上传你的真实账单**


### 1. 推送代码到 GitHub

确保当前分支已经包含：
- `render.yaml`
- `requirements.txt`（包含 `gunicorn`）

### 2. 在 Render 创建服务

1. 打开 Render，选择 **New +** -> **Blueprint**
2. 连接你的 GitHub 仓库
3. 选择本项目仓库并创建

Render 会自动读取 `render.yaml`，使用以下命令启动：
- Build Command: `pip install -r requirements.txt`
- Start Command: `python setup.py && gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120`

### 3. 访问示例站

部署完成后，Render 会给你一个 `https://xxx.onrender.com` 的公开地址，用户可直接访问体验。

## 📄 许可证

[MIT License](LICENSE)
