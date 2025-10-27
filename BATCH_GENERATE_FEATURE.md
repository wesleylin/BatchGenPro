# 批量生图功能开发完成

## 📋 功能说明

### 批量生图 vs 批量改图

| 功能 | 批量生图 | 批量改图 |
|------|---------|---------|
| **参考图** | 单张参考图 | 多张不同的图片 |
| **生成方式** | 同一参考图 + Prompt 重复生成 N 次 | 对每张图应用相同 Prompt 分别生成 |
| **生成数量** | 可配置（1-10张） | 取决于上传图片数量 |
| **使用场景** | 探索不同生成结果 | 批量处理多张图片 |

## ✅ 已完成的改动

### 后端改动

#### 1. 删除重复文件
- ❌ 删除 `backend/doubao_client.py`（功能已整合到 `ai_image_generator.py`）

#### 2. 新增批量生图处理函数（`backend/tasks.py`）
```python
def process_batch_generate_sync(task_id, reference_image_data, prompt, image_count, api_type="gemini"):
    """
    批量生图：使用同一张参考图和prompt重复生成多张图片
    """
```

#### 3. 新增批量生图API接口（`backend/app.py`）
```python
@app.route('/api/batch/generate-from-image', methods=['POST'])
def create_batch_generate_task():
    """创建批量生图任务（同一参考图重复生成N次）"""
```

**接口参数：**
- `file`: 参考图片（单张）
- `prompt`: 生成提示词
- `image_count`: 生成数量（1-10）
- `api_type`: API类型（gemini/doubao）

### 前端改动

#### 1. UI差异化（`frontend/src/App.vue`）

**批量生图UI：**
- 单图上传组件（`el-upload`）
- 数量选择器（`el-input-number`）
- 支持1-10张生成

**批量改图UI：**
- 多图上传组件（`MultiImageUpload`）
- 无数量限制，取决于上传数量

#### 2. 新增状态管理
```javascript
// 批量生图状态
const referenceImage = ref(null)
const referenceImageList = ref([])
const imageCount = ref(3) // 默认生成3张

// 批量改图状态
const uploadedFiles = ref([])
```

#### 3. 新增处理函数
- `handleBatchGenerate()`: 批量生图处理
- `handleBatchEdit()`: 批量改图处理
- `handleStartTask()`: 统一的任务启动入口

## 🎯 使用方法

### 批量生图
1. 切换到"批量生图"标签
2. 选择大模型（Gemini/豆包）
3. 输入Prompt
4. 上传单张参考图
5. 设置生成数量（1-10）
6. 点击"开始"

### 批量改图
1. 切换到"批量改图"标签
2. 选择大模型（Gemini/豆包）
3. 输入Prompt
4. 上传多张图片
5. 点击"开始"

## 🧪 测试建议

### 本地测试
```bash
# 1. 启动后端
cd backend
source .venv312/bin/activate
python app.py

# 2. 启动前端
cd frontend
npm run dev
```

### 测试用例

#### 批量生图测试
1. **基础测试**
   - 上传1张参考图
   - Prompt: "添加一朵花"
   - 数量: 3
   - 验证生成3张不同的图片

2. **边界测试**
   - 最小数量: 1
   - 最大数量: 10
   - 验证数量限制

3. **模型切换**
   - 测试Gemini模型
   - 测试豆包模型

#### 批量改图测试
1. **多图测试**
   - 上传3-5张不同图片
   - Prompt: "添加一朵花"
   - 验证每张图都生成对应结果

2. **清空功能**
   - 测试清空按钮
   - 验证状态重置

## 📝 注意事项

1. **API限流**
   - 每次生成间隔1秒，避免触发API限流

2. **任务管理**
   - 批量生图和批量改图共用任务管理系统
   - 可在右侧面板查看进度和结果

3. **错误处理**
   - 参数验证
   - 文件格式检查
   - API调用失败重试

## 🚀 后续优化建议

1. **异步处理**
   - 当前是同步处理，可改为异步（使用Celery或其他任务队列）

2. **进度实时更新**
   - 添加WebSocket支持实时进度推送

3. **结果预览**
   - 在生成过程中显示已完成的图片

4. **更多模型**
   - 支持更多AI模型（Midjourney、Stable Diffusion等）

5. **批量下载**
   - 优化下载逻辑，支持ZIP打包下载

