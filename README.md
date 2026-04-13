# 企业微信机器人应用

## 项目简介

这是一个基于Docker部署的企业微信机器人应用，集成了自动化问答、信息推送、数据爬取和个人助理功能，通过可视化后端管理所有功能模块。

## 技术架构

- **部署方式**: Docker容器化部署
- **后端框架**: Python (FastAPI)
- **数据库**: SQLite (支持PostgreSQL)
- **前端管理**: 轻量级Web界面 (HTML+CSS+JavaScript)
- **无头浏览器**: Playwright
- **定时任务**: APScheduler

## 功能模块

### 1. 企业微信机器人接口集成
- 接收企业微信消息、发送消息到企业微信群/个人
- 实现企业微信Webhook回调验证、消息加解密
- 支持文本、Markdown、图片、图文消息
- 后端可配置企业微信corpid、secret、agentid、webhook_key

### 2. 可视化后端管理页面
- 管理员账号密码登录
- 仪表盘：显示今日推送状态、消息统计、任务运行状态
- 推送管理：查看/编辑/删除每日推送内容，支持富文本编辑器
- 推送设置：设置推送时间、目标群聊、推送开关
- 日志查看：查看消息发送记录、错误日志、系统运行日志
- 配置中心：统一管理所有API密钥、机器人配置、爬虫配置

### 3. AI自动问答（无头浏览器）
- 企业微信收到特定关键词（如"@助手"）触发
- 使用Playwright打开网页版AI（如ChatGPT/Claude/文心一言等）
- 自动输入问题 → 等待回答生成 → 复制回答内容
- 将获取的回答通过企业微信机器人接口回复给用户
- 后端可配置：目标AI网站URL、登录凭证、等待时间、最大重试次数

### 4. 自定义爬虫模块
- 后端可添加/编辑/删除爬虫任务
- 爬取目标：新闻网站、天气API、股票数据、汇率、自定义API等
- 调度设置：支持定时执行（Cron表达式）、间隔执行
- 数据提取：支持CSS选择器、XPath、正则表达式提取关键信息
- 数据存储：爬取结果保存到数据库，供推送模块使用
- 推送集成：爬取结果可自动作为每日推送内容

### 5. 记忆与提醒模块（个人助理）
- **记忆功能**：发送"记住xxx"保存事项，"我记得什么"查询所有记忆
- **提醒功能**："提醒我明天上午9点开会"，到时间通过企业微信机器人推送提醒消息
- **理财记录**："记录收入1000元工资"、"记录支出50元午餐"，支持自定义分类和统计报表

## 快速开始

### 环境要求
- Python 3.11+
- Docker (可选，用于容器化部署)
- 企业微信开发者账号

### 安装与运行

#### 方法一：本地运行
1. 克隆仓库
   ```bash
   git clone https://github.com/scottHGITUHB/auto_assistant.git
   cd auto_assistant
   ```

2. 安装依赖
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

3. 配置环境变量
   复制 `.env` 文件并填写相关配置

4. 运行应用
   ```bash
   python main.py
   ```

5. 访问管理界面
   打开 `frontend/index.html`

#### 方法二：Docker部署
1. 构建镜像
   ```bash
   docker build -t auto_assistant .
   ```

2. 运行容器
   ```bash
   docker-compose up -d
   ```

3. 访问应用
   - API文档：http://localhost:8000/docs
   - 管理界面：http://localhost:8000/frontend

## 配置说明

### 企业微信配置
- `WECHAT_CORPID`: 企业微信企业ID
- `WECHAT_SECRET`: 应用密钥
- `WECHAT_AGENTID`: 应用ID
- `WECHAT_WEBHOOK_KEY`: 机器人Webhook密钥
- `WECHAT_TOKEN`: 消息加解密Token
- `WECHAT_ENCODING_AES_KEY`: 消息加解密密钥

### AI问答配置
- `AI_WEB_URL`: AI网站URL（如https://chat.openai.com）
- `AI_USERNAME`: AI网站登录用户名
- `AI_PASSWORD`: AI网站登录密码
- `AI_TIMEOUT`: 超时时间（毫秒）

### 数据库配置
- `DATABASE_URL`: 数据库连接字符串

## API文档

启动应用后，可通过以下地址访问自动生成的API文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 项目结构

```
auto_assistant/
├── api/            # API路由模块
├── frontend/       # 前端管理界面
├── models/         # 数据库模型
├── services/       # 核心服务模块
├── data/           # 数据存储
├── logs/           # 日志文件
├── .env            # 环境变量配置
├── Dockerfile      # Docker构建文件
├── docker-compose.yml # Docker Compose配置
├── main.py         # 应用入口
├── requirements.txt # 依赖文件
└── README.md       # 项目说明
```

## 注意事项

1. 确保企业微信后台已正确配置回调URL
2. 首次运行时会自动创建数据库表结构
3. 爬虫任务和提醒任务会在应用启动时自动调度
4. AI自动问答功能需要配置正确的AI网站登录凭证

## 后续优化方向

1. 完善企业微信消息加解密功能
2. 增强AI自动问答的稳定性和可靠性
3. 优化爬虫模块的错误处理和重试机制
4. 完善前端管理页面的交互体验
5. 添加更多的统计和分析功能

## 许可证

MIT License
