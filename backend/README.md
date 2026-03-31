# Backend 目录说明

## 项目架构

backend 目录是项目的后端服务部分，基于 Flask 框架开发，主要负责处理前端的 API 请求，包括用户管理、聊天功能、内容生成等。

## 目录结构

```
backend/
├── avatars/            # 用户头像存储目录
├── feature_content_generation/  # 内容生成功能模块
├── feature_intelligent_chat/    # 智能聊天功能模块
├── feature_llm_integration/     # LLM 集成功能模块
├── feature_post_interaction/    # 帖子交互功能模块
├── feature_user_profile/        # 用户资料功能模块
├── app.py              # 主应用入口
├── dating.db           # SQLite 数据库文件
├── requirements.txt    # 依赖包列表
└── README.md           # 本文件
```

## 修改的文件

### 1. app.py

**功能描述**：主应用入口，包含所有 API 路由和核心逻辑。

**主要修改**：

- 修复了 `get_chat_history` 函数，解决了 `sqlite3.Row` 对象没有 `get` 方法的问题
- 确保 `sender_type` 字段的正确处理，即使数据库中缺少该字段也能正常返回数据
- 添加了数据库表结构检查和字段添加逻辑，确保 `chats` 表包含 `sender_type` 字段

**作用**：确保聊天历史记录能够正确保存和加载，解决了历史对话记录丢失的问题。

### 2. feature\_llm\_integration/services/llm\_service.py

**功能描述**：LLM 服务集成模块，负责与大语言模型 API 的交互。

### 3. frontend/src/views/SquareView\.vue

**功能描述**：前端聊天广场页面，包含聊天功能的用户界面。

**主要修改**：

- 增强了 `loadChatHistory` 函数，添加了详细的日志输出
- 增强了 `sendMessage` 函数，添加了详细的日志输出
- 确保了聊天 ID 的生成逻辑在加载和保存时保持一致
- 确保了消息数据的正确映射和赋值
- 修改了 `closeChatDialog` 函数，保存好感度数据到 localStorage

**作用**：确保聊天历史记录和好感度数据能够正确保存和恢复，提升用户体验。

## 核心功能模块

### 1. 聊天功能

- **聊天记录存储**：使用 SQLite 数据库存储聊天历史记录
- **聊天历史加载**：通过 `/api/chat/history/<chat_id>` API 加载历史记录
- **消息发送**：通过 `/api/chat` API 保存聊天消息
- **好感度系统**：通过 localStorage 存储好感度数据

### 2. LLM 集成

- **模型配置**：默认使用 `qwen3.5-flash` 模型
- **API 调用**：通过 `/api/llm/chat` API 调用大语言模型
- **会话管理**：支持多轮对话和上下文理解

### 3. 用户管理

- **用户注册**：通过 `/api/register` API 注册新用户
- **用户登录**：通过 `/api/login` API 登录用户
- **用户资料**：通过 `/api/profile` API 管理用户资料

## 依赖项

- Flask：Web 框架
- Flask-CORS：处理跨域请求
- SQLite3：数据库
- requests：HTTP 客户端

## 启动方式

1. 安装依赖：`pip install -r requirements.txt`
2. 启动服务：`python app.py`
3. 服务将在 `http://localhost:5000` 运行

## 注意事项

- 数据库文件 `dating.db` 会自动创建，无需手动初始化
- 头像文件存储在 `avatars` 目录中
- 所有 API 路由都以 `/api` 开头
- 前端应用需要在 `http://localhost:5173` 运行，以避免 CORS 问题

