# BatchGen Pro - 批量图片生成工具

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

BatchGen Pro 是一个基于 AI 的批量图片生成和修改工具，支持使用多个 AI 模型批量生成或编辑图片。通过简单的 Web 界面，用户可以快速批量处理图片，提高工作效率。

## 🌐 在线使用

**无需部署，直接使用**：访问 [https://batchgenpro.com](https://batchgenpro.com)

只需配置你的 API Key 即可开始使用！

## ✨ 核心功能

### 1. 批量生图（Batch Image Generation）
- 使用同一份提示词（可选参考图）重复生成多张图片
- **变量支持**：支持在 prompt 中使用 `{变量名}` 定义变量，自动生成多组 prompt
  - 例如：`生成一张{动物}的图片` + 变量值：`["鸭子", "兔子", "老虎"]`
  - 系统会自动生成 3 张不同 prompt 的图片
- 可选择性上传参考图片
- 最多支持生成 10 张图片

### 2. 批量改图（Batch Image Modification）
- 对多张图片使用同一份提示词进行批量修改
- 支持上传多张图片同时处理
- 每张图片都有独立的参考图和生成结果

### 3. 实时任务管理
- 提交后立即显示所有任务项
- 实时更新任务状态和结果（3秒间隔）
- 显示任务完成进度
- 支持单张下载和批量下载

## 🔑 API 配置说明

### 获取 API Key

#### 方式一：官方申请

**Gemini API**：
1. 访问 [Google AI Studio](https://aistudio.google.com/)
2. 登录 Google 账号
3. 创建 API Key
4. 复制 API Key

**豆包 API**：
1. 访问 [豆包开放平台](https://console.volcengine.com/)
2. 注册/登录账号
3. 创建应用并获取 API Key
4. 复制 API Key

#### 方式二：通过中转平台申请（推荐）

推荐使用中转平台，通常价格更优惠且稳定：

**SpeeedAI**：
1. 访问 [https://speeedai.com](https://speeedai.com)
2. 注册账号并充值
3. 获取 API Key 和 Base URL

**其他中转平台**：
- 支持任何兼容 Gemini/豆包 API 格式的中转服务
- 获取平台提供的 API Key 和 Base URL

### 配置 API Key

1. **打开设置**：点击页面右上角的设置按钮（⚙️）

2. **选择模型**：选择要配置的 AI 模型（Gemini 或豆包）

3. **填写 API Key**：
   - 如果使用官方 API：直接填写 API Key，关闭"使用自定义端点/代理"开关
   - 如果使用中转平台：填写 API Key，并开启"使用自定义端点/代理"开关

4. **配置自定义端点**（仅中转平台需要）：
   - **Base URL**：填写中转平台提供的 API 地址
     - 例如：`https://api.speeedai.com/v1beta`
     - 注意：不要包含路径末尾的斜杠 `/`
   - **自定义模型名称**（可选）：如果平台使用非标准模型名称，可在此填写
     - 留空则使用标准模型名称

5. **保存配置**：点击"保存"按钮

### 配置示例

#### 使用官方 Gemini API
```
API Key: AIzaSy...
使用自定义端点/代理: 关闭
```

#### 使用 SpeeedAI 中转平台
```
API Key: sk-...
使用自定义端点/代理: 开启
Base URL: https://api.speeedai.com/v1beta
自定义模型名称: （留空或填写平台提供的模型名）
```

### 安全说明

- ✅ API Key 仅存储在浏览器本地（localStorage）
- ✅ 不会上传到服务器
- ✅ 不会泄露给第三方
- ⚠️ 请妥善保管你的 API Key，不要分享给他人

## 🚀 快速开始（本地部署）

### 环境要求
- Python 3.12+
- Node.js 18+
- Redis（可选，用于任务队列）
- Docker 20.10+（生产环境）

### 本地开发

1. **克隆项目**：
   ```bash
   git clone https://github.com/wesleylin/BatchGenPro.git
   cd BatchGenPro
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

2. **部署服务**：
   ```bash
   docker-compose -f docker-compose.server.yml.example up -d --build
   ```

## 🎯 使用流程

### 批量生图
1. 切换到"批量生图"标签
2. 选择 AI 模型
3. **配置 API Key**（如果未配置）：点击设置按钮，输入你的 API Key
4. 输入 Prompt（可选使用 `{变量名}` 定义变量）
5. 如果使用变量，在变量输入框中每行输入一个值
6. （可选）上传参考图片
7. 设置生成数量（不使用变量时）
8. 点击"开始"按钮
9. 在右侧任务列表查看生成进度和结果

### 批量改图
1. 切换到"批量改图"标签
2. 选择 AI 模型
3. **配置 API Key**（如果未配置）：点击设置按钮，输入你的 API Key
4. 上传多张需要修改的图片
5. 输入修改的 Prompt
6. 点击"开始"按钮
7. 在右侧任务列表查看每张图片的修改进度和结果

## 🔧 支持的 API

- **Gemini**：Gemini 2.5 Flash Image、Gemini 3 Pro Image Preview
- **豆包**：豆包 Seedream 4.0

## 📋 文件限制

- 最大文件大小：10MB
- 支持格式：jpg, jpeg, png, gif, webp

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目采用 [MIT License](LICENSE) 许可证。
