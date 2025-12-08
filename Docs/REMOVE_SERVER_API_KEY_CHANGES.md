# 移除服务端API Key配置 - 修改清单

## 📋 修改目标

完全移除服务端API Key配置逻辑，所有请求必须使用用户自己的API Key。

## 🔍 需要修改的文件和位置

### 一、后端修改 (Backend)

#### 1. `backend/ai_image_generator.py`

**位置1: `_init_doubao` 方法 (第80-91行)**
- **当前逻辑**: 如果用户未提供API key，则使用服务器配置的 `DOUBAO_API_KEY`
- **问题**: `DOUBAO_API_KEY` 在 `config/api_keys.py` 中已被注释掉，但代码中仍在使用，会导致 `NameError`
- **修改**: 移除fallback逻辑，必须使用用户提供的API key
- **修改内容**:
  ```python
  # 当前代码（第82-90行）:
  # 优先使用用户提供的API key，如果没有或为空则使用服务器配置的
  if api_key and api_key.strip() and api_key.strip() != "your_doubao_api_key_here":
      final_api_key = api_key.strip()
  else:
      final_api_key = DOUBAO_API_KEY  # ❌ 这行会导致NameError，因为DOUBAO_API_KEY已被注释
  
  # 修改为:
  # 必须使用用户提供的API key
  if not api_key or not api_key.strip() or api_key.strip() == "your_doubao_api_key_here":
      raise ValueError("豆包 API Key 未提供，请先在设置中配置 API Key")
  final_api_key = api_key.strip()
  self.api_key = final_api_key
  ```

**位置2: 导入语句 (第18-22行)**
- **当前**: 从 `config.api_keys` 导入，不包含 `DOUBAO_API_KEY`（已正确）
- **状态**: ✅ 无需修改

#### 2. `backend/tasks.py`

**位置1: `process_batch_task_sync` 函数 (第237行)**
- **当前注释**: "如果没有提供API key，传递None，让create_image_generator使用服务器配置的"
- **修改**: 更新注释，说明必须提供API key

**位置2: `process_batch_generate_sync` 函数 (第366行)**
- **当前注释**: "如果没有提供API key，传递None，让create_image_generator使用服务器配置的"
- **修改**: 更新注释，说明必须提供API key

**位置3: `process_batch_generate_multi_prompt_sync` 函数 (第437行)**
- **当前注释**: "如果没有提供API key，传递None，让create_image_generator使用服务器配置的"
- **修改**: 更新注释，说明必须提供API key

#### 3. `backend/app.py`

**位置1: `get_api_key_from_request` 函数 (第149-157行)**
- **当前**: 已有检查，如果未提供API key会抛出异常 ✅
- **状态**: 无需修改（已正确）

**位置2: 注释 (第32行, 第83行)**
- **当前**: 注释中提到"使用服务器配置的"
- **修改**: 更新注释，明确说明只使用用户提供的API key

### 二、前端修改 (Frontend)

#### 1. `frontend/src/App.vue`

**位置1: `getApiKey` 函数 (第238-256行)**
- **当前逻辑**: 如果key为空，返回null，让后端使用服务器配置
- **修改**: 如果key为空，应该抛出错误或返回错误提示，不允许使用服务器配置
- **修改内容**:
  ```javascript
  // 当前代码（第251-253行）:
  // 如果key是空字符串、null或占位符，返回null，让后端使用服务器配置的
  if (!oldKey || !oldKey.trim() || oldKey.trim() === 'your_gemini_api_key_here' || oldKey.trim() === 'your_doubao_api_key_here') {
      return null  // ❌ 需要修改
  }
  
  // 修改为:
  // 如果key为空，返回null，前端会检查并提示用户配置
  // 后端不再使用服务器配置，必须由用户提供
  ```

**位置2: axios 拦截器 (第278-283行)**
- **当前逻辑**: 如果API key为空，不设置header，让后端使用服务器配置的key
- **修改**: 如果API key为空，应该抛出错误或提示用户配置
- **修改内容**:
  ```javascript
  // 当前代码（第295行）:
  // 如果为空，不设置header，让后端使用服务器配置的key
  if (apiKey && apiKey.trim() && ...) {
      config.headers['X-API-Key'] = apiKey.trim()
      config.headers['X-API-Type'] = apiType
  }
  // ❌ 需要添加else分支，抛出错误或提示
  
  // 修改为:
  if (!apiKey || !apiKey.trim()) {
      // 抛出错误或返回Promise.reject，提示用户配置API key
      return Promise.reject(new Error(`请先配置 ${apiType} API Key`))
  }
  config.headers['X-API-Key'] = apiKey.trim()
  config.headers['X-API-Type'] = apiType
  ```

**位置3: 错误处理 (第355行)**
- **当前**: "将使用服务器配置的key"
- **修改**: 更新错误提示，说明必须配置API key

**位置4: 注释 (第583-585行)**
- **当前**: "可以使用服务器配置的"
- **修改**: 更新注释，说明必须使用用户配置的API key

#### 2. `frontend/src/components/ApiConfigDialog.vue`

**位置1: `handleSkip` 函数 (第328-331行)**
- **当前**: "将使用服务器配置的 API Key"
- **修改**: 
  - 如果 `required=true`（首次使用），不允许跳过
  - 如果 `required=false`，可以跳过，但提示用户必须配置API key才能使用

**位置2: 对话框的"跳过"按钮**
- **当前**: 显示"跳过（使用服务器配置）"
- **修改**: 
  - 首次使用时隐藏"跳过"按钮
  - 非首次使用时，改为"稍后配置"或直接移除跳过功能

### 三、配置文件修改

#### 1. `config/api_keys.py.example`

**修改内容**:
- 移除或注释掉 `GEMINI_API_KEY` 和 `DOUBAO_API_KEY` 的定义
- 保留其他配置项（MODEL、WATERMARK等）
- 添加说明：API Key必须由用户在客户端配置

**修改示例**:
```python
# API配置
# 注意：API Key 不再在服务器端配置，必须由用户在客户端配置

# GEMINI_API_KEY = "your_gemini_api_key_here"  # 已移除，用户必须在客户端配置
GEMINI_MODEL = "gemini-2.5-flash-image"

# 豆包API配置
# DOUBAO_API_KEY = "your_doubao_api_key_here"  # 已移除，用户必须在客户端配置
DOUBAO_MODEL = "doubao-seedream-4-0-250828"
DOUBAO_WATERMARK = False
```

### 四、文档修改

#### 1. `Docs/DEPLOYMENT.md`

**位置**: API密钥配置部分
- **修改**: 更新说明，明确API Key不再在服务器配置，必须由用户在客户端配置

## 📝 修改优先级

### 高优先级（核心功能）
1. ✅ `backend/ai_image_generator.py` - `_init_doubao` 方法（移除DOUBAO_API_KEY fallback）
2. ✅ `frontend/src/App.vue` - axios拦截器（必须提供API key）
3. ✅ `frontend/src/App.vue` - `getApiKey` 函数（移除fallback逻辑）

### 中优先级（用户体验）
4. ✅ `frontend/src/components/ApiConfigDialog.vue` - 移除"跳过"功能或更新提示
5. ✅ 更新所有相关注释和错误提示

### 低优先级（文档和配置）
6. ✅ `config/api_keys.py.example` - 更新示例文件
7. ✅ `Docs/DEPLOYMENT.md` - 更新部署文档

## ⚠️ 注意事项

1. **向后兼容性**: 
   - 确保现有已配置API key的用户不受影响
   - 首次使用用户必须配置API key

2. **错误处理**:
   - 所有未提供API key的情况都应该有明确的错误提示
   - 错误提示应该引导用户到配置页面

3. **测试场景**:
   - 未配置API key时，所有请求应该失败并提示配置
   - 已配置API key时，功能正常
   - 首次使用强制配置流程正常

4. **代码清理**:
   - 移除所有未使用的导入（如 `DOUBAO_API_KEY`）
   - 更新所有相关注释

## 🔄 修改后的行为

### 修改前
- 用户未配置API key → 使用服务器配置的API key（如果存在）
- 用户配置了API key → 使用用户的API key

### 修改后
- 用户未配置API key → **必须配置，否则无法使用**
- 用户配置了API key → 使用用户的API key
- 服务器不再提供默认API key配置

