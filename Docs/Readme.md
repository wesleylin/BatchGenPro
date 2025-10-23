

### **需求文档：团队批量生图Web工具**

#### **1. 项目目标**

创建一个内部Web应用，使团队成员能批量生成图片。用户上传多张基准图片和一段通用Prompt，系统在后台调用生图API，并实时展示结果。

#### **2. 开发计划（已完成）**

**MVP阶段（✅ 已完成）**：
- ✅ 单张图片生成流程验证
- ✅ 前端：Vue3 + Element Plus
- ✅ 后端：Flask + Gemini API
- ✅ 本地开发环境
- ✅ 图片上传和生成功能
- ✅ 前端图片显示和下载

**V2阶段（✅ 已完成）**：
- ✅ 多张图片批量生成
- ✅ 异步任务队列（Redis + 同步处理）
- ✅ 实时状态更新
- ✅ 任务管理和进度显示

**V3阶段（✅ 已完成）**：
- ✅ 多API支持（Gemini + 豆包API）
- ✅ UI优化和用户体验提升
- ✅ API选择器
- ✅ 任务管理界面优化

**Docker化阶段（✅ 已完成）**：
- ✅ Docker容器化部署
- ✅ Docker Compose编排
- ✅ Nginx反向代理
- ✅ 生产环境配置

#### **3. MVP核心用户流程**

1.  **上传**: 用户上传1张图片
2.  **配置**: 用户输入Prompt
3.  **提交**: 用户点击"生成图片"按钮
4.  **处理**: 系统同步调用Gemini API生成图片
5.  **展示**: 显示原图和生成结果
6.  **下载**: 用户可以下载生成的图片

#### **4. MVP技术栈**

*   **前端**: Vue 3 (Vite) + Element Plus UI库 + Axios
*   **后端**: Python 3.12 + Flask + Flask-CORS
*   **生图API**: Gemini API (google-genai包)
*   **开发环境**: 本地开发（Python虚拟环境）
*   **文件存储**: 本地文件系统（uploads/ 和 results/ 目录）

#### **5. MVP前端组件**

1.  **`App.vue`** (主组件)
    *   功能: 整合上传、输入和结果展示
    *   UI: 简单的单页面布局

2.  **`ImageUpload.vue`**
    *   功能: 单文件上传
    *   UI: 拖拽上传区域，显示上传的图片预览

3.  **`PromptInput.vue`**
    *   功能: 接收用户输入的Prompt
    *   UI: 文本输入框 + 生成按钮

4.  **`ResultDisplay.vue`**
    *   功能: 展示原图和生成结果
    *   UI: 并排显示原图和生成图，下载按钮

#### **6. MVP后端API接口**

*   **Flask App (`app.py`)**

1.  **单图生成接口**
    *   **Endpoint**: `POST /api/generate`
    *   **Request Body**: `multipart/form-data`
        *   `file`: 单个图片文件
        *   `prompt`: 字符串
    *   **Logic**:
        *   接收并保存上传的图片
        *   调用Gemini API生成图片
        *   保存生成结果
        *   返回结果图片URL
    *   **Success Response** (200 OK):
        ```json
        {
          "success": true,
          "description": "AI生成的文字描述",
          "generated_image_url": "/static/results/generated_xxx.png"
        }
        ```

2.  **静态文件服务**
    *   **Endpoint**: `/static/<path:filename>`
    *   **功能**: 提供上传图片和生成结果的访问

#### **7. Gemini API集成**

*   **API配置**:
    *   API Key: `AIzaSyBe1CcdEtm6n--UTp6rXvErKfl3ZZK_Igs`
    *   Model: `gemini-2.5-flash-image`
    *   功能: 根据图片和Prompt生成新图片
    *   包: `google-genai` (官方推荐)

#### **8. 项目结构**

```
BatchGen-Pro/
├── frontend/              # Vue3前端
│   ├── src/
│   │   ├── components/
│   │   ├── App.vue
│   │   └── main.js
│   ├── package.json
│   └── vite.config.js
├── backend/               # Flask后端
│   ├── app.py
│   ├── requirements.txt
│   ├── uploads/           # 上传图片存储
│   └── results/           # 生成结果存储
├── config/                # 配置文件
│   └── api_keys.py
└── Docs/
    └── Readme.md
```

#### **9. Docker部署**

**本地Docker部署**：

1. **克隆项目**：
   ```bash
   git clone <repository-url>
   cd BatchGen\ Pro
   ```

2. **配置环境变量**：
   ```bash
   cp env.example .env
   # 编辑 .env 文件，配置API密钥等
   ```

3. **一键部署**：
   ```bash
   chmod +x deploy.sh
   ./deploy.sh deploy prod
   ```

4. **访问应用**：
   - 前端：http://localhost
   - 健康检查：http://localhost/health

**服务器部署**：

1. **一键部署到服务器**：
   ```bash
   ./deploy-server.sh deploy
   ```

2. **访问地址**：
   - 前端：https://img.qingmood.xyz
   - 健康检查：https://img.qingmood.xyz/health

**部署命令**：
- `./deploy.sh deploy prod` - 本地生产环境部署
- `./deploy-server.sh deploy` - 服务器部署
- `./deploy-server.sh update` - 更新服务器服务
- `./deploy-server.sh status` - 检查服务器状态
- `./deploy-server.sh logs` - 查看服务器日志

#### **10. 本地开发**

**环境要求**：
- Python 3.12+
- Node.js 18+
- Redis (可选，用于任务队列)

**启动步骤**：

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
   - 前端：http://localhost:3000
   - 后端API：http://localhost:5001

**使用流程**：
1. 上传一张图片
2. 输入Prompt描述
3. 点击"生成图片"
4. 查看生成的图片和AI描述
5. 下载结果

#### **10. 后续扩展计划**

**V2阶段**：
- 多张图片批量生成
- Celery异步任务队列
- Redis状态管理
- 实时进度更新

**V3阶段**：
- 豆包API集成
- Docker容器化部署
- UI/UX优化
- 错误重试机制