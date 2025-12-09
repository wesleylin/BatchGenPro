# BatchGen Pro - 批量图片生成工具

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

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
- **用户自配置**：用户需要在前端配置自己的 API Key

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

### 后端架构
- **框架**：Flask
- **语言**：Python 3.12
- **任务管理**：Redis (存储任务状态)
- **文件存储**：本地文件系统
- **API 客户端**：统一的 AI 图片生成接口封装

### 部署架构
- **容器化**：Docker + Docker Compose
- **Web 服务器**：Nginx（生产环境）

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

1. **克隆项目**：
   ```bash
   git clone https://github.com/wesleylin/BatchGen-Pro.git
   cd BatchGen-Pro
   ```

2. **配置环境变量**：
   ```bash
   cp env.example .env
   # 编辑 .env 文件，配置 Redis 密码等
   ```

3. **启动后端**：
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   python app.py
   ```

4. **启动前端**：
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

5. **访问应用**：
   - 前端：http://localhost:8590
   - 后端 API：http://localhost:5001

### Docker 部署

1. **配置环境变量**：
   ```bash
   cp env.example .env
   # 编辑 .env 文件，配置 Redis 密码等
   ```

2. **配置 Docker Compose**（如果需要服务器部署）：
   ```bash
   cp docker-compose.server.yml.example docker-compose.server.yml
   # 编辑 docker-compose.server.yml，配置网络等
   ```

3. **部署服务**：
   ```bash
   docker-compose -f docker-compose.server.yml up -d --build
   ```

4. **访问应用**：
   - 前端：http://localhost:8590
   - 健康检查：http://localhost:5001/api/health

## 🎯 使用流程

### 批量生图
1. 切换到"批量生图"标签
2. 选择 AI 模型（Gemini 或豆包）
3. **配置 API Key**：点击设置按钮，输入你的 API Key
4. 输入 Prompt（可选使用 `{变量名}` 定义变量）
5. 如果使用变量，在变量输入框中每行输入一个值
6. （可选）上传参考图片
7. 设置生成数量（不使用变量时）
8. 点击"开始"按钮
9. 在右侧任务列表查看生成进度和结果

### 批量改图
1. 切换到"批量改图"标签
2. 选择 AI 模型
3. **配置 API Key**：点击设置按钮，输入你的 API Key
4. 上传多张需要修改的图片
5. 输入修改的 Prompt
6. 点击"开始"按钮
7. 在右侧任务列表查看每张图片的修改进度和结果

## 🔧 配置说明

### 环境变量配置
项目使用环境变量进行配置，复制 `env.example` 为 `.env` 并修改相应配置：

```bash
cp env.example .env
```

主要配置项：
- **AI模型配置**：`GEMINI_MODEL`、`DOUBAO_MODEL`、`DOUBAO_WATERMARK`
- **文件存储**：`UPLOAD_FOLDER`、`RESULT_FOLDER`、`MAX_FILE_SIZE`
- **文件类型**：`ALLOWED_EXTENSIONS`（逗号分隔）
- **API选择**：`DEFAULT_API`、`SUPPORTED_APIS`（逗号分隔）
- **Redis配置**：`REDIS_PASSWORD`

### API 密钥配置
用户需要在前端界面中配置自己的 API Key：
- 点击右上角的设置按钮
- 输入 Gemini API Key 或豆包 API Key
- API Key 仅存储在浏览器本地，不会上传到服务器

### 支持的 API
- `gemini`：Gemini 2.5 Flash Image 模型
- `doubao`：豆包图像生成 API

### 文件大小限制
- 最大文件大小：10MB（可通过 `MAX_FILE_SIZE` 环境变量配置）
- 支持格式：jpg, jpeg, png, gif, webp（可通过 `ALLOWED_EXTENSIONS` 环境变量配置）

## 📂 项目结构

```
BatchGen Pro/
├── backend/                 # 后端代码
│   ├── app.py              # Flask 应用主文件
│   ├── ai_image_generator.py  # 统一的 AI API 客户端
│   ├── task_manager.py     # 任务管理器
│   ├── tasks.py            # 任务处理逻辑
│   └── requirements.txt    # Python 依赖
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── App.vue         # 主应用组件
│   │   └── components/     # 组件目录
│   └── package.json
├── docker/                 # Docker 构建文件
│   ├── Dockerfile.backend  # 后端镜像
│   ├── Dockerfile.frontend # 前端镜像
│   └── nginx.conf         # Nginx 配置
├── Docs/                   # 文档目录
│   └── Readme.md          # 详细文档
└── docker-compose.server.yml.example  # Docker Compose 示例
```

## 🔌 API 接口

### 批量任务接口
- `POST /api/batch/generate`：批量改图接口（多图片 + 单 prompt）
- `POST /api/batch/generate-from-image`：批量生图接口（可选参考图 + 数量）
- `POST /api/batch/generate-with-prompts`：批量生图接口（多 prompt，支持变量）

### 任务管理接口
- `GET /api/batch/tasks`：获取所有任务列表
- `GET /api/batch/tasks/<task_id>`：获取指定任务详情
- `GET /api/batch/tasks/<task_id>/results`：获取任务结果
- `DELETE /api/batch/tasks/<task_id>`：删除任务

### 健康检查
- `GET /api/health`：服务健康检查

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目采用 [MIT License](LICENSE) 许可证。

## 🔮 未来计划

- [ ] 批量下载功能
- [ ] 任务历史记录
- [ ] 更多 AI 模型支持
- [ ] 任务暂停/恢复功能
- [ ] 图片预览优化
- [ ] 错误重试机制改进

## 📝 更新日志

详见 [Docs/Readme.md](Docs/Readme.md) 中的开发历史部分。

