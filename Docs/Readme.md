# BatchGen Pro - 批量图片生成工具

## 📦 代码仓库

**GitHub**: https://github.com/wesleylin/BatchGen-Pro.git

```bash
# 克隆项目
git clone https://github.com/wesleylin/BatchGen-Pro.git
cd BatchGen-Pro
```

## 📋 项目简介

BatchGen Pro 是一个基于 AI 的批量图片生成和修改工具，支持使用多个 AI 模型批量生成或编辑图片。通过简单的 Web 界面，用户可以快速批量处理图片，提高工作效率。

## ✨ 核心功能

### 1. 批量生图（Batch Image Generation）
- **功能描述**：使用同一份提示词（可选参考图）重复生成多张图片
- **变量支持**：支持在 prompt 中使用 `{变量名}` 定义变量，自动生成多组 prompt
  - 例如：`生成一张{动物}的图片` + 变量值：`["鸭子", "兔子", "老虎"]`
  - 系统会自动生成 3 张不同 prompt 的图片
- **参考图**：可选择性上传参考图片，所有生成的图片共享同一个参考图
- **生成数量**：最多支持生成 10 张图片

### 2. 批量改图（Batch Image Modification）
- **功能描述**：对多张图片使用同一份提示词进行批量修改
- **支持格式**：支持上传多张图片同时处理
- **每张图片独立**：每张图片都有独立的参考图和生成结果

### 3. 多 API 支持
- **Gemini API**：支持 `gemini-2.5-flash-image` 模型
- **豆包 API**：支持豆包图像生成 API
- **统一接口**：通过 `AIImageGenerator` 统一封装，方便扩展新 API

### 4. 实时任务管理
- **任务列表**：提交后立即显示所有任务项，每个任务项包含：
  - Prompt（变量替换后的实际 prompt）
  - 参考图（如果有）
  - 生成结果
  - 任务状态（未开始/生成中/已完成/失败）
- **实时更新**：通过轮询机制（3秒间隔）实时更新任务状态和结果
- **进度追踪**：显示任务完成进度（已完成/总数）
- **任务持久化**：任务状态保存在 Redis 中，支持跨会话查看

### 5. 图片下载
- **单张下载**：每个任务项支持单独下载生成的图片
- **批量下载**：支持一键下载所有生成的图片

## 🏗️ 技术架构

### 前端架构
- **框架**：Vue 3 (Composition API)
- **UI 库**：Element Plus
- **构建工具**：Vite
- **HTTP 客户端**：Axios
- **状态管理**：Vue `ref` 和 `computed`

**主要组件**：
- `App.vue`：主应用组件，包含标签切换、表单输入、任务提交
- `BatchTaskManager.vue`：任务管理器，显示任务列表、进度、结果
- `MultiImageUpload.vue`：多图片上传组件（批量改图）
- `ImageUpload.vue`：单图片上传组件（批量生图参考图）

### 后端架构
- **框架**：Flask
- **语言**：Python 3.12
- **任务管理**：Redis (存储任务状态)
- **文件存储**：本地文件系统
  - `uploads/`：上传的原始图片
  - `results/`：生成的图片结果
- **API 客户端**：
  - `AIImageGenerator`：统一的 AI 图片生成接口
  - 支持 Gemini 和豆包 API，易于扩展

**核心模块**：
- `app.py`：Flask 应用主文件，定义所有 API 端点
- `task_manager.py`：任务管理器，负责任务创建、状态更新、结果存储
- `tasks.py`：任务处理逻辑，包含同步批处理函数
- `ai_image_generator.py`：统一的 AI API 客户端封装

### 数据流架构

```
用户提交任务
    ↓
前端创建本地任务（立即显示）
    ↓
调用后端 API
    ↓
后端创建任务（存储到 Redis）
    ↓
同步处理任务（调用 AI API）
    ↓
更新任务状态和结果
    ↓
前端轮询获取最新状态
    ↓
更新 UI 显示
```

### 部署架构
- **容器化**：Docker + Docker Compose
- **Web 服务器**：Nginx（生产环境）
- **服务编排**：
  - Frontend：Nginx 静态文件服务
  - Backend：Flask 应用（端口 5001/8989）
  - Redis：任务状态存储（端口 6379）

**部署文件**：
- `docker-compose.server.yml`：服务器环境（共享 Nginx，位于项目根目录）
- **注意**：本地开发不需要 Docker，直接运行前后端服务

## 🔌 API 接口

### 单图生成（MVP阶段）
- `POST /api/generate`：单张图片生成接口

### 批量任务接口
- `POST /api/batch/generate`：批量改图接口（多图片 + 单 prompt）
- `POST /api/batch/generate-from-image`：批量生图接口（可选参考图 + 数量）
- `POST /api/batch/generate-with-prompts`：批量生图接口（多 prompt，支持变量）

### 任务管理接口
- `GET /api/batch/tasks`：获取所有任务列表
- `GET /api/batch/tasks/<task_id>`：获取指定任务详情
- `GET /api/batch/tasks/<task_id>/results`：获取任务结果
- `DELETE /api/batch/tasks/<task_id>`：删除任务

### 静态文件
- `/static/uploads/<filename>`：访问上传的图片
- `/static/results/<filename>`：访问生成的图片

### 健康检查
- `GET /api/health`：服务健康检查

## 📂 项目结构

```
BatchGen Pro/
├── backend/                 # 后端代码
│   ├── app.py              # Flask 应用主文件
│   ├── ai_image_generator.py  # 统一的 AI API 客户端
│   ├── task_manager.py     # 任务管理器
│   ├── tasks.py            # 任务处理逻辑
│   ├── celery_config.py    # Celery 配置（未使用）
│   ├── requirements.txt    # Python 依赖
│   ├── uploads/            # 上传图片存储
│   └── results/            # 生成结果存储
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── App.vue         # 主应用组件
│   │   ├── components/
│   │   │   ├── BatchTaskManager.vue  # 任务管理器组件
│   │   │   ├── MultiImageUpload.vue  # 多图片上传
│   │   │   ├── ImageUpload.vue       # 单图片上传
│   │   │   ├── PromptInput.vue       # Prompt 输入
│   │   │   └── ResultDisplay.vue     # 结果展示
│   │   └── main.js         # 入口文件
│   ├── package.json
│   └── vite.config.js
├── config/                 # 配置文件
│   ├── api_keys.py        # API 密钥配置（需要手动创建）
│   └── api_keys.py.example # API 密钥模板
├── docker-compose.server.yml # 服务器 Docker Compose 配置（根目录）
├── docker/                 # Docker 构建文件
│   ├── Dockerfile.backend  # 后端镜像
│   ├── Dockerfile.frontend # 前端镜像
│   ├── nginx.conf         # Nginx 配置
│   └── .dockerignore      # Docker 忽略文件
├── Docs/                   # 文档目录
│   ├── Readme.md          # 项目主文档
│   └── DEPLOYMENT.md      # 部署说明文档
```

## 🚀 快速开始

### 环境要求
- **开发环境**：
  - Python 3.12+
  - Node.js 18+
  - Redis (可选，用于任务队列)

- **生产环境**：
  - Docker 20.10+
  - Docker Compose 2.0+

### 本地开发

1. **启动后端**：
   ```bash
   cd backend
   source .venv312/bin/activate  # 激活虚拟环境
   pip install -r requirements.txt
   python app.py
   ```

2. **启动前端**：
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **访问应用**：
   - 前端：http://localhost:8590
   - 后端 API：http://localhost:5001

### Docker 部署

1. **配置 API 密钥**：
   ```bash
   # 复制模板文件并填入实际的 API 密钥
   cp config/api_keys.py.example config/api_keys.py
   # 编辑 config/api_keys.py，填入真实的 API 密钥
   ```

2. **部署服务**：
   ```bash
   docker-compose -f docker-compose.server.yml up -d --build
   ```

3. **访问应用**：
   - 前端：http://localhost
   - 健康检查：http://localhost/health

### 服务器部署

详见 `Docs/DEPLOYMENT.md` 文档。

## 🎯 使用流程

### 批量生图
1. 切换到"批量生图"标签
2. 选择 AI 模型（Gemini 或豆包）
3. 输入 Prompt（可选使用 `{变量名}` 定义变量）
4. 如果使用变量，在变量输入框中每行输入一个值
5. （可选）上传参考图片
6. 设置生成数量（不使用变量时）
7. 点击"开始"按钮
8. 在右侧任务列表查看生成进度和结果

### 批量改图
1. 切换到"批量改图"标签
2. 选择 AI 模型
3. 上传多张需要修改的图片
4. 输入修改的 Prompt
5. 点击"开始"按钮
6. 在右侧任务列表查看每张图片的修改进度和结果

## 🔧 配置说明

### API 密钥配置
在 `config/api_keys.py` 中配置：
- `GEMINI_API_KEY`：Gemini API 密钥
- `DOUBAO_API_KEY`：豆包 API 密钥

### 支持的 API
- `gemini`：Gemini 2.5 Flash Image 模型
- `doubao`：豆包图像生成 API

### 文件大小限制
- 最大文件大小：16MB
- 支持格式：jpg, jpeg, png, gif, webp

## 📝 开发历史

### MVP 阶段（✅ 已完成）
- ✅ 单张图片生成流程验证
- ✅ 前端：Vue3 + Element Plus
- ✅ 后端：Flask + Gemini API
- ✅ 本地开发环境
- ✅ 图片上传和生成功能
- ✅ 前端图片显示和下载

### V2 阶段（✅ 已完成）
- ✅ 多张图片批量生成
- ✅ 异步任务队列（Redis + 同步处理）
- ✅ 实时状态更新
- ✅ 任务管理和进度显示

### V3 阶段（✅ 已完成）
- ✅ 多 API 支持（Gemini + 豆包 API）
- ✅ UI 优化和用户体验提升
- ✅ API 选择器
- ✅ 任务管理界面优化
- ✅ 批量生图和批量改图功能
- ✅ Prompt 变量支持
- ✅ 参考图支持
- ✅ 实时任务列表显示

### Docker 化阶段（✅ 已完成）
- ✅ Docker 容器化部署
- ✅ Docker Compose 编排
- ✅ Nginx 反向代理
- ✅ 生产环境配置
- ✅ 服务器部署支持

## 🔮 未来计划

- [ ] 批量下载功能
- [ ] 任务历史记录
- [ ] 更多 AI 模型支持
- [ ] 任务暂停/恢复功能
- [ ] 图片预览优化
- [ ] 错误重试机制改进

## 📄 许可证

本项目采用 [MIT License](../LICENSE) 许可证。
