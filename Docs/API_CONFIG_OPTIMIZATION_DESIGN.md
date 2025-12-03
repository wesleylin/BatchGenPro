# API配置优化设计方案

## 一、需求概述

优化现有的API配置页面，实现以下功能：
1. **首次使用引导**：第一次使用时，用户需要先设置API才能使用
2. **模型与API联动**：只有设置了对应API的模型才能被选择和使用
3. **API类型选择**：支持官方API和第三方API两种模式
   - 官方API：需要填写API Key
   - 第三方API：只需要填写URL（API Key可选）

## 二、当前实现分析

### 2.1 现有组件结构
- `ApiConfigDialog.vue`：API配置对话框组件
- `App.vue`：主应用组件，包含模型选择器
- 数据存储：使用 `localStorage` 存储API配置

### 2.2 现有问题
1. API配置是可选的，用户可以不配置就使用（依赖服务器配置）
2. 模型选择与API配置没有联动关系
3. 没有首次使用引导机制
4. API类型选择不够清晰（官方/第三方）

## 三、设计方案

### 3.1 数据结构设计

#### 3.1.1 API配置数据结构
```javascript
// localStorage 存储结构
{
  // API配置状态标记
  "api_config_initialized": true/false,  // 是否已完成首次配置
  
  // Gemini API配置
  "gemini_api_config": {
    "type": "official" | "third_party",  // API类型
    "api_key": "xxx",                     // API Key（官方必填，第三方可选）
    "base_url": "xxx",                    // Base URL（仅第三方需要）
    "configured": true/false              // 是否已配置
  },
  
  // 豆包 API配置
  "doubao_api_config": {
    "type": "official" | "third_party",
    "api_key": "xxx",
    "base_url": "xxx",
    "configured": true/false
  }
}
```

#### 3.1.2 模型与API的映射关系
```javascript
const MODEL_API_MAPPING = {
  // Gemini 模型
  "gemini-2.5-flash-image": {
    apiType: "gemini",
    displayName: "Gemini 2.5 Flash Image"
  },
  "gemini-3-pro-image-preview": {
    apiType: "gemini",
    displayName: "Gemini 3 Pro Image Preview"
  },
  // 豆包模型
  "doubao-seedream-4-0-250828": {
    apiType: "doubao",
    displayName: "豆包 Seedream 4.0"
  }
}
```

### 3.2 UI/UX 设计

#### 3.2.1 首次使用流程
1. **检测机制**：
   - 应用启动时检查 `api_config_initialized` 标志
   - 如果为 `false` 或不存在，强制显示API配置对话框
   - 对话框不可关闭（不显示关闭按钮，点击遮罩层不关闭）

2. **引导提示**：
   - 显示欢迎信息："欢迎使用 BatchGen Pro！请先配置API才能开始使用"
   - 提供清晰的配置步骤说明

#### 3.2.2 API配置对话框优化

**布局结构**：
```
┌─────────────────────────────────────┐
│  API 配置（首次使用必填）            │
├─────────────────────────────────────┤
│                                     │
│  [欢迎提示信息]                      │
│                                     │
│  ┌─ Gemini API 配置 ────────────┐  │
│  │                              │  │
│  │  ○ 官方API  ● 第三方API      │  │
│  │                              │  │
│  │  API Key: [____________]     │  │
│  │  Base URL: [____________]     │  │
│  │  (仅第三方需要)               │  │
│  │                              │  │
│  │  ✓ 已配置                     │  │
│  └──────────────────────────────┘  │
│                                     │
│  ┌─ 豆包 API 配置 ──────────────┐  │
│  │                              │  │
│  │  ○ 官方API  ● 第三方API      │  │
│  │                              │  │
│  │  API Key: [____________]     │  │
│  │  Base URL: [____________]     │  │
│  │  (仅第三方需要)               │  │
│  │                              │  │
│  │  ⚠ 未配置                     │  │
│  └──────────────────────────────┘  │
│                                     │
│  [提示：至少需要配置一个API]        │
│                                     │
│              [保存并开始使用]        │
└─────────────────────────────────────┘
```

**功能特性**：
1. **API类型切换**：
   - 使用 Radio 按钮组切换"官方API"和"第三方API"
   - 切换时动态显示/隐藏相关字段
   - 官方API：显示 API Key 输入框（必填）
   - 第三方API：显示 Base URL 输入框（必填）+ API Key 输入框（可选）

2. **配置状态指示**：
   - 每个API配置区域显示配置状态
   - ✓ 已配置：绿色勾选标记
   - ⚠ 未配置：黄色警告标记
   - 实时更新状态

3. **验证逻辑**：
   - 至少需要配置一个API（Gemini或豆包）
   - 官方API：API Key 必填
   - 第三方API：Base URL 必填，API Key 可选
   - 保存按钮：至少配置一个API后才能启用

#### 3.2.3 模型选择器优化

**联动逻辑**：
1. **可用模型过滤**：
   - 根据已配置的API动态过滤可用模型
   - 只有对应API已配置的模型才显示在下拉列表中
   - 未配置API的模型显示为灰色禁用状态（可选：显示提示）

2. **模型选择器UI**：
```
┌─────────────────────────────────────┐
│ 大模型                              │
│ [API Key 配置]                      │
├─────────────────────────────────────┤
│ [▼] gemini-2.5-flash-image          │
│   ✓ Gemini API 已配置               │
│                                     │
│   gemini-3-pro-image-preview        │
│   ✓ Gemini API 已配置               │
│                                     │
│   doubao-seedream-4-0-250828        │
│   ⚠ 豆包 API 未配置                 │
│   [点击配置]                         │
└─────────────────────────────────────┘
```

3. **交互行为**：
   - 选择未配置API的模型时：
     - 显示提示："请先配置 [API名称] API"
     - 自动打开API配置对话框
     - 高亮显示对应的API配置区域

4. **状态显示**：
   - 每个模型选项旁边显示对应API的配置状态
   - 已配置：显示绿色✓和"已配置"
   - 未配置：显示黄色⚠和"未配置"，并提供快速配置链接

### 3.3 功能流程设计

#### 3.3.1 首次使用流程
```
用户打开应用
    ↓
检查 api_config_initialized
    ↓
未初始化？
    ↓ 是
强制显示API配置对话框（不可关闭）
    ↓
用户配置至少一个API
    ↓
点击"保存并开始使用"
    ↓
验证配置有效性
    ↓
保存到 localStorage
    ↓
设置 api_config_initialized = true
    ↓
关闭对话框，进入主界面
```

#### 3.3.2 模型选择流程
```
用户点击模型选择器
    ↓
获取所有可用模型列表
    ↓
根据已配置的API过滤模型
    ↓
显示可用模型（已配置API）
    ↓
显示不可用模型（未配置API，灰色）
    ↓
用户选择模型
    ↓
检查对应API是否已配置
    ↓
已配置？
    ↓ 否
显示提示："请先配置 [API名称] API"
    ↓
自动打开API配置对话框
    ↓
高亮显示对应API配置区域
```

#### 3.3.3 API配置更新流程
```
用户修改API配置
    ↓
实时验证输入
    ↓
更新配置状态指示
    ↓
保存配置
    ↓
更新模型选择器的可用模型列表
    ↓
如果当前选择的模型对应的API被删除
    ↓
自动切换到第一个可用模型
```

### 3.4 代码实现要点

#### 3.4.1 新增工具函数

**`utils/apiConfig.js`**：
```javascript
// API配置管理工具函数

// 检查是否已完成首次配置
export function isApiConfigInitialized() {
  return localStorage.getItem('api_config_initialized') === 'true'
}

// 获取API配置
export function getApiConfig(apiType) {
  const config = localStorage.getItem(`${apiType}_api_config`)
  return config ? JSON.parse(config) : null
}

// 保存API配置
export function saveApiConfig(apiType, config) {
  localStorage.setItem(`${apiType}_api_config`, JSON.stringify(config))
  // 标记为已初始化
  localStorage.setItem('api_config_initialized', 'true')
}

// 检查API是否已配置
export function isApiConfigured(apiType) {
  const config = getApiConfig(apiType)
  return config && config.configured === true
}

// 获取可用模型列表（根据已配置的API）
export function getAvailableModels() {
  const allModels = [
    { value: 'gemini-2.5-flash-image', apiType: 'gemini', label: 'Gemini 2.5 Flash Image' },
    { value: 'gemini-3-pro-image-preview', apiType: 'gemini', label: 'Gemini 3 Pro Image Preview' },
    { value: 'doubao-seedream-4-0-250828', apiType: 'doubao', label: '豆包 Seedream 4.0' }
  ]
  
  return allModels.filter(model => isApiConfigured(model.apiType))
}
```

#### 3.4.2 组件修改点

**`ApiConfigDialog.vue` 修改**：
1. 添加 `required` prop，控制是否为必填模式（首次使用）
2. 添加 API类型选择（官方/第三方）
3. 添加配置状态实时显示
4. 添加配置验证逻辑
5. 支持高亮显示特定API配置区域

**`App.vue` 修改**：
1. 添加首次使用检测逻辑（`onMounted`）
2. 修改模型列表为计算属性，根据已配置API动态过滤
3. 修改模型选择处理，检查API配置状态
4. 添加API配置更新监听，实时更新可用模型

### 3.5 向后兼容性

#### 3.5.1 数据迁移
- 检测旧的 localStorage 数据格式
- 自动迁移到新格式：
  ```javascript
  // 旧格式
  localStorage.getItem('gemini_api_key')
  localStorage.getItem('gemini_base_url')
  
  // 迁移到新格式
  {
    type: base_url ? 'third_party' : 'official',
    api_key: api_key || '',
    base_url: base_url || '',
    configured: !!(api_key || base_url)
  }
  ```

#### 3.5.2 兼容性处理
- 如果检测到旧格式数据，自动迁移
- 迁移后设置 `api_config_initialized = true`
- 保持与后端API的兼容性（header格式不变）

### 3.6 用户体验优化

#### 3.6.1 提示信息
- **首次使用**：友好的欢迎信息和清晰的配置步骤
- **未配置API**：明确的提示和快速配置入口
- **配置成功**：成功提示和状态更新

#### 3.6.2 错误处理
- **验证失败**：实时显示错误信息
- **保存失败**：错误提示和重试机制
- **网络错误**：友好的错误提示

#### 3.6.3 交互优化
- **自动聚焦**：打开对话框时自动聚焦到第一个输入框
- **键盘导航**：支持 Tab 键切换，Enter 键保存
- **实时验证**：输入时实时验证，即时反馈

## 四、实施步骤

### 阶段一：数据结构设计
1. 设计新的 localStorage 数据结构
2. 实现数据迁移工具函数
3. 实现配置管理工具函数

### 阶段二：API配置对话框优化
1. 重构 `ApiConfigDialog.vue`
2. 添加API类型选择（官方/第三方）
3. 添加配置状态显示
4. 实现验证逻辑

### 阶段三：模型选择器联动
1. 修改 `App.vue` 中的模型列表逻辑
2. 实现模型与API的联动
3. 添加未配置API的提示和快速配置

### 阶段四：首次使用引导
1. 实现首次使用检测
2. 实现强制配置对话框
3. 添加欢迎信息和引导

### 阶段五：测试和优化
1. 测试各种配置场景
2. 测试数据迁移
3. 优化用户体验
4. 修复bug

## 五、技术细节

### 5.1 验证规则

**官方API验证**：
- API Key：必填，不能为空
- Base URL：不需要

**第三方API验证**：
- Base URL：必填，必须是有效的URL格式
- API Key：可选，如果填写则不能为空

**整体验证**：
- 至少需要配置一个API（Gemini或豆包）
- 每个API配置必须完整（根据类型）

### 5.2 状态管理

使用 Vue 3 的 `ref` 和 `computed` 管理状态：
- API配置状态：响应式数据
- 可用模型列表：计算属性
- 配置验证状态：计算属性

### 5.3 数据持久化

- 使用 `localStorage` 存储配置
- 配置变更时立即保存
- 应用启动时自动加载

## 六、注意事项

1. **向后兼容**：确保旧版本数据可以正常迁移
2. **错误处理**：完善的错误处理和用户提示
3. **性能优化**：避免频繁的 localStorage 读写
4. **安全性**：API Key 使用 password 类型输入框
5. **用户体验**：清晰的提示和流畅的交互

## 七、后续优化方向

1. **API测试功能**：配置后可以测试API是否有效
2. **多API配置**：支持同一类型API的多个配置
3. **配置导入导出**：支持配置的导入导出
4. **配置历史**：保存配置历史，支持回退
5. **配置模板**：提供常用第三方API的配置模板

