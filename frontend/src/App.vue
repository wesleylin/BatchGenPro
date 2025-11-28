<template>
  <div id="app">
    <!-- API配置对话框 -->
    <ApiConfigDialog 
      v-model="showApiConfigDialog" 
      @confirmed="handleApiConfigConfirmed"
    />
    
    <div class="app-container">
      <div class="main-content">
        <!-- 左侧操作面板 -->
        <div class="left-panel">
          <div class="panel-content">
            <!-- 顶部标题区域 -->
            <div class="header-section">
              <div class="title-row">
                <div class="logo-icon">
                  <div class="icon-stack">
                    <div class="icon-layer"></div>
                    <div class="icon-layer"></div>
                    <div class="icon-layer"></div>
                  </div>
                </div>
                <h1 class="app-title">BatchGen Pro</h1>
                <p class="app-subtitle">批量图片生成工具</p>
              </div>
              
              <!-- 标签切换 -->
              <div class="tab-switcher">
                <div class="tab-item" :class="{ active: activeTab === 'generate' }" @click="activeTab = 'generate'">
                  <span>批量生图</span>
                </div>
                <div class="tab-item" :class="{ active: activeTab === 'edit' }" @click="activeTab = 'edit'">
                  <span>批量改图</span>
                </div>
              </div>
              
              <p class="tab-description">
                {{ activeTab === 'generate' ? '批量生图会用同一份提示词（可带参考图）重复生成多张图' : '批量改图会对多张图用同一份提示词来生图' }}
              </p>
            </div>
            
            <!-- 操作区域 -->
            <div class="operation-section">
              <!-- 大模型选择器 -->
              <div class="form-group">
                <div class="model-selector-header">
                  <label class="form-label">大模型</label>
                  <el-button 
                    type="text" 
                    class="api-config-link"
                    @click="showApiConfigDialog = true"
                  >
                    <el-icon><Setting /></el-icon>
                    API Key 配置
                  </el-button>
                </div>
                <el-select 
                  v-model="selectedModel" 
                  class="model-selector"
                  placeholder="选择模型"
                  @change="handleModelChange"
                >
                  <el-option
                    v-for="model in availableModels"
                    :key="model.value"
                    :label="model.label"
                    :value="model.value"
                  />
                </el-select>
              </div>
              
              <!-- Prompt输入 -->
              <div class="form-group">
                <label class="form-label">Prompt</label>
                <el-input
                  v-model="batchPrompt"
                  type="textarea"
                  :rows="3"
                  :placeholder="activeTab === 'generate' ? '输入提示词，使用 {变量名} 来定义变量（仅支持一个变量），例如：生成一张{动物}的图片' : '输入提示词'"
                  class="prompt-input"
                  @input="activeTab === 'generate' ? handlePromptChange() : null"
                />
              </div>
              
              <!-- 批量生图：参考图片上传（单图） + 数量选择 -->
              <template v-if="activeTab === 'generate'">
                <div class="form-group">
                  <div class="upload-header">
                    <label class="form-label">参考图片（可选）</label>
                    <el-icon class="clear-icon" @click="clearReferenceImage"><RefreshLeft /></el-icon>
                  </div>
                  
                  <el-upload
                    class="reference-upload"
                    :auto-upload="false"
                    :limit="1"
                    :on-change="handleReferenceImageChange"
                    :on-remove="handleReferenceImageRemove"
                    :file-list="referenceImageList"
                    accept="image/*"
                    list-type="picture-card"
                  >
                    <el-icon><Plus /></el-icon>
                  </el-upload>
                </div>
                
                <!-- 变量检测和输入 -->
                <div v-if="detectedVariables.length > 0" class="form-group variable-section">
                  <div class="variable-header">
                    <label class="form-label">✨ 检测到变量: {{'{'}}{{ detectedVariables[0] }}{{'}'}}</label>
                  </div>
                  
                  <div class="variable-input-group">
                    <label class="variable-label">{{'{'}}{{ detectedVariables[0] }}{{'}'}}</label>
                    <el-input
                      v-model="variableValues[detectedVariables[0]]"
                      type="textarea"
                      :rows="3"
                      :placeholder="`每行一个值，例如：\n鸭子\n兔子\n老虎`"
                      class="variable-textarea"
                      @input="updateVariableCount"
                    />
                    <span class="variable-count">{{ getVariableValueCount(detectedVariables[0]) }} 个值</span>
                  </div>
                </div>
                
                <div class="form-group">
                  <label class="form-label">生成数量</label>
                  <el-input-number 
                    v-model="imageCount" 
                    :min="1" 
                    :max="10" 
                    class="count-selector"
                    :disabled="hasVariables"
                  />
                  <span class="count-hint" v-if="!hasVariables">最多生成10张</span>
                  <span class="count-hint" v-else>使用变量时，数量由变量值决定（当前: {{ totalVariableCombinations }} 个）</span>
                </div>
              </template>
              
              <!-- 批量改图：参考图片上传（多图） -->
              <template v-if="activeTab === 'edit'">
                <div class="form-group">
                  <div class="upload-header">
                    <label class="form-label">参考图片</label>
                    <el-icon class="clear-icon" @click="clearAllImages"><RefreshLeft /></el-icon>
                  </div>
                  
                  <MultiImageUpload 
                    v-model:files="uploadedFiles"
                    @files-change="handleBatchFileChange"
                  />
                </div>
              </template>
            </div>
            
            <!-- 开始按钮 -->
            <div class="start-button-container">
              <el-button 
                type="primary" 
                class="start-button"
                :loading="isBatchGenerating"
                @click="handleStartTask"
                :disabled="isStartButtonDisabled"
              >
                开始
              </el-button>
            </div>
          </div>
        </div>
        
        <!-- 分隔线 -->
        <div class="divider"></div>
        
        <!-- 右侧结果面板 -->
        <div class="right-panel">
          <BatchTaskManager ref="taskManagerRef" />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowDown, RefreshLeft, Plus, Setting } from '@element-plus/icons-vue'
import axios from 'axios'
import MultiImageUpload from './components/MultiImageUpload.vue'
import BatchTaskManager from './components/BatchTaskManager.vue'
import ApiConfigDialog from './components/ApiConfigDialog.vue'

// —— session id 隔离 ——
function getOrCreateSessionId() {
  let sessionId = localStorage.getItem('session_id')
  if (!sessionId) {
    if (window.crypto && window.crypto.randomUUID) {
      sessionId = window.crypto.randomUUID()
    } else {
      sessionId = Math.random().toString(36).substring(2) + Date.now().toString(36)
    }
    localStorage.setItem('session_id', sessionId)
  }
  return sessionId
}

const sessionId = getOrCreateSessionId()
axios.defaults.headers.common['X-Session-ID'] = sessionId

// API key管理函数
function getApiKey(apiType) {
  if (apiType === 'gemini') {
    return localStorage.getItem('gemini_api_key')
  } else if (apiType === 'doubao') {
    return localStorage.getItem('doubao_api_key')
  }
  return null
}

// 拦截器：添加Session ID和API Key
axios.interceptors.request.use(config => {
  config.headers['X-Session-ID'] = sessionId
  
  // 根据请求中的api_type判断需要哪个API key
  // 如果是FormData，从formData中获取api_type
  let apiType = 'gemini'
  if (config.data instanceof FormData) {
    apiType = config.data.get('api_type') || 'gemini'
  } else if (config.params && config.params.api_type) {
    apiType = config.params.api_type
  }
  
  const apiKey = getApiKey(apiType)
  // 只有当API key存在且不为空时才设置header
  // 如果为空，不设置header，让后端使用服务器配置的key
  if (apiKey && apiKey.trim()) {
    config.headers['X-API-Key'] = apiKey.trim()
    config.headers['X-API-Type'] = apiType
  }
  // 如果没有API key，不设置header，让后端使用服务器配置的key
  
  return config
})

// 响应拦截器：处理API key相关的错误
axios.interceptors.response.use(
  response => response,
  error => {
    // 如果是401或403错误，可能是API key问题
    if (error.response && (error.response.status === 401 || error.response.status === 403)) {
      const errorMsg = error.response.data?.error || error.response.data?.message || 'API Key 验证失败'
      if (errorMsg.includes('API Key') || errorMsg.includes('api_key') || errorMsg.includes('未提供')) {
        ElMessage.error('API Key 无效或未配置，请检查配置')
        // 可以在这里触发显示配置对话框
        // showApiConfigDialog.value = true
      }
    }
    return Promise.reject(error)
  }
)

export default {
  name: 'App',
  components: {
    MultiImageUpload,
    BatchTaskManager,
    ApiConfigDialog,
    ArrowDown,
    RefreshLeft,
    Plus,
    Setting
  },
  setup() {
    const taskManagerRef = ref(null)
    
    // API配置相关状态
    const showApiConfigDialog = ref(false)
    
    // 批量改图相关状态
    const uploadedFiles = ref([])
    
    // 批量生图相关状态
    const referenceImage = ref(null)
    const referenceImageList = ref([])
    const imageCount = ref(3) // 默认生成3张
    
    // 变量功能相关状态
    const detectedVariables = ref([])  // 检测到的变量名列表
    const variableValues = ref({})     // 变量值对象 { "动物": "鸭子\n兔子\n老虎" }
    
    // 通用状态
    const batchPrompt = ref('')
    const isBatchGenerating = ref(false)
    const selectedApi = ref('gemini') // 默认使用Gemini
    const activeTab = ref('generate') // 默认选中批量生图
    const selectedModel = ref('gemini-2.5-flash-image') // 默认模型
    
    // 可用模型列表
    const availableModels = ref([
      { value: 'gemini-2.5-flash-image', label: 'gemini-2.5-flash-image' },
      { value: 'models/gemini-3-pro-image-preview', label: 'models/gemini-3-pro-image-preview' },
      { value: 'doubao-seedream-4-0-250828', label: 'doubao-seedream-4-0-250828' }
    ])

    // 计算属性：开始按钮是否禁用
    const isStartButtonDisabled = computed(() => {
      if (!batchPrompt.value.trim()) return true
      
      if (activeTab.value === 'generate') {
        // 批量生图：只需要prompt，参考图可选
        return false
      } else {
        // 批量改图：需要上传的图片
        return uploadedFiles.value.length === 0
      }
    })

    // 处理批量改图文件变化
    const handleBatchFileChange = (files) => {
      uploadedFiles.value = files
    }

    // 处理批量生图参考图变化
    const handleReferenceImageChange = (file) => {
      referenceImage.value = file.raw
      referenceImageList.value = [file]
    }

    // 移除参考图
    const handleReferenceImageRemove = () => {
      referenceImage.value = null
      referenceImageList.value = []
    }

    // 清空所有批量改图的图片
    const clearAllImages = () => {
      uploadedFiles.value = []
      ElMessage.success('已清空所有图片')
    }

    // 清空批量生图的参考图
    const clearReferenceImage = () => {
      referenceImage.value = null
      referenceImageList.value = []
      ElMessage.success('已清空参考图')
    }

    // 根据模型名称获取API类型
    const getApiTypeFromModel = (modelName) => {
      if (modelName.includes('gemini') || modelName.startsWith('models/gemini')) {
        return 'gemini'
      } else if (modelName.includes('doubao')) {
        return 'doubao'
      }
      return 'gemini' // 默认
    }

    // 变量相关函数
    // 检测Prompt中的变量
    const detectVariables = (prompt) => {
      const regex = /\{([^}]+)\}/g
      const matches = [...prompt.matchAll(regex)]
      const vars = matches.map(m => m[1].trim())
      return [...new Set(vars)]  // 去重
    }

    // 监听Prompt变化，自动检测变量
    const handlePromptChange = () => {
      if (activeTab.value === 'generate') {
        const vars = detectVariables(batchPrompt.value)
        // 只支持一个变量，取第一个
        detectedVariables.value = vars.length > 0 ? [vars[0]] : []
        
        // 为新检测到的变量初始化空值
        detectedVariables.value.forEach(varName => {
          if (!variableValues.value[varName]) {
            variableValues.value[varName] = ''
          }
        })
        
        // 移除不再存在的变量
        Object.keys(variableValues.value).forEach(key => {
          if (!detectedVariables.value.includes(key)) {
            delete variableValues.value[key]
          }
        })
      }
    }

    // 获取变量值列表（按行分割）
    const getVariableValuesList = (varName) => {
      const text = variableValues.value[varName] || ''
      return text.split('\n')
        .map(line => line.trim())
        .filter(line => line.length > 0)
    }

    // 获取变量值数量
    const getVariableValueCount = (varName) => {
      return getVariableValuesList(varName).length
    }

    // 更新变量数量（用于实时显示）
    const updateVariableCount = () => {
      // 触发视图更新
    }

    // 计算总的生成数量（变量组合）
    const totalVariableCombinations = computed(() => {
      if (detectedVariables.value.length === 0) {
        return imageCount.value
      }
      
      // 只支持单变量，直接返回第一个变量的值数量
      const varName = detectedVariables.value[0]
      const count = getVariableValueCount(varName)
      return Math.min(count, 10)  // 最多10个
    })

    // 是否有变量
    const hasVariables = computed(() => {
      return detectedVariables.value.length > 0 && 
             detectedVariables.value.some(v => getVariableValueCount(v) > 0)
    })
    
    // 检查API key（不再强制要求，可以使用服务器配置的）
    const checkApiKey = () => {
      // 不再强制要求API key，服务器有配置的fallback
      return true
    }
    
    // 处理API配置确认
    const handleApiConfigConfirmed = (config) => {
      // API key已保存到localStorage，无需额外处理
      ElMessage.success('API Key 配置成功，可以开始使用了')
    }
    
    // 处理模型切换
    const handleModelChange = (modelValue) => {
      // 不再强制要求API key，可以使用服务器配置的
      // 如果用户想使用自己的API key，可以点击配置按钮
    }

    // 生成所有变量组合的Prompt列表
    const generatePromptVariants = () => {
      if (detectedVariables.value.length === 0) {
        return [batchPrompt.value]
      }
      
      // 只支持单变量
      const varName = detectedVariables.value[0]
      const values = getVariableValuesList(varName)
      
      // 如果变量没有值，返回原始prompt
      if (values.length === 0) {
        return [batchPrompt.value]
      }
      
      // 替换变量生成prompt列表
      const prompts = values.map(value => {
        return batchPrompt.value.replace(new RegExp(`\\{${varName}\\}`, 'g'), value)
      }).slice(0, 10)  // 最多10个
      
      console.log('生成的prompt列表:', prompts)
      return prompts
    }

    // 创建并设置本地任务的公共方法
    const createAndSetLocalTask = (items, referenceImageUrl = null) => {
      const localTaskId = 'local_' + Date.now()
      const localTask = {
        task_id: localTaskId,
        status: 'processing',
        total_images: items.length,
        processed_images: 0,
        progress: 0,
        prompt: items[0]?.prompt || '',
        items: items,
        reference_image_url: referenceImageUrl
      }
      
      // 立即设置本地任务，让UI显示出来
      if (taskManagerRef.value && taskManagerRef.value.setLocalTask) {
        taskManagerRef.value.setLocalTask(localTask)
      }
      
      return localTask
    }

    // 统一的开始任务处理
    const handleStartTask = async () => {
      // 不再强制要求API key，可以使用服务器配置的
      // 如果用户想使用自己的API key，可以点击配置按钮
      
      if (activeTab.value === 'generate') {
        await handleBatchGenerate()
      } else {
        await handleBatchEdit()
      }
    }

    // 批量生图处理
    const handleBatchGenerate = async () => {
      if (!batchPrompt.value.trim()) {
        ElMessage.warning('请输入生成提示词')
        return
      }

      // 检查变量是否都有值
      if (hasVariables.value) {
        for (const varName of detectedVariables.value) {
          if (getVariableValueCount(varName) === 0) {
            ElMessage.warning(`请为变量 {${varName}} 输入至少一个值`)
            return
          }
        }
      }

      isBatchGenerating.value = true
      
      try {
        // 生成所有变量组合的prompt
        const promptVariants = generatePromptVariants()
        const actualCount = hasVariables.value ? promptVariants.length : imageCount.value
        
        if (actualCount > 10) {
          ElMessage.warning('生成数量超过10张，将只生成前10张')
        }
        
        // 如果有变量，使用新接口一次性提交所有prompt
        if (hasVariables.value) {
          console.log('变量模式，prompt变体:', promptVariants)
          const actualCount = Math.min(promptVariants.length, 10)
          const limitedVariants = promptVariants.slice(0, actualCount)
          console.log('将创建任务数:', actualCount)
          ElMessage.info(`检测到 ${limitedVariants.length} 个变量值，开始生成...`)
          
          // 先创建本地任务对象，立即显示给用户
          const referenceImageUrl = referenceImage.value ? URL.createObjectURL(referenceImage.value) : null
          const items = limitedVariants.map((prompt, index) => ({
            index: index,
            prompt: prompt,
            status: 'pending',
            reference_image_url: referenceImageUrl  // 所有item共享一个参考图
          }))
          createAndSetLocalTask(items, null)
          
          // 使用新接口，一次性提交所有prompt
          const formData = new FormData()
          
          // 添加参考图片（如果有）
          if (referenceImage.value) {
            formData.append('file', referenceImage.value)
          }
          
          // 添加所有prompt（JSON格式）
          formData.append('prompts', JSON.stringify(limitedVariants))
          formData.append('api_type', getApiTypeFromModel(selectedModel.value))
          formData.append('model_name', selectedModel.value)
          
          const response = await axios.post('/api/batch/generate-with-prompts', formData, {
            headers: {
              'Content-Type': 'multipart/form-data'
            },
            timeout: 180000
          })
          
          if (response.data.success) {
            // 用后端返回的真实task_id更新本地任务
            if (taskManagerRef.value && taskManagerRef.value.updateLocalTaskId && response.data.task_id) {
              taskManagerRef.value.updateLocalTaskId(response.data.task_id)
            }
            // 不显示消息，任务结果会在任务列表中显示
          } else {
            ElMessage.error('创建批量生图任务失败: ' + response.data.error)
          }
        } else {
          // 无变量，使用原有逻辑
          // 先创建本地任务对象，立即显示给用户
          const referenceImageUrl = referenceImage.value ? URL.createObjectURL(referenceImage.value) : null
          const items = Array.from({length: imageCount.value}, (_, index) => ({
            index: index,
            prompt: batchPrompt.value,
            status: 'pending',
            reference_image_url: referenceImageUrl  // 所有item共享一个参考图
          }))
          createAndSetLocalTask(items, null)
          
          const formData = new FormData()
          
          // 添加参考图片（如果有）
          if (referenceImage.value) {
            formData.append('file', referenceImage.value)
          }
          
          // 添加提示词、数量和API类型
          formData.append('prompt', batchPrompt.value)
          formData.append('image_count', imageCount.value)
          formData.append('api_type', getApiTypeFromModel(selectedModel.value))
          formData.append('model_name', selectedModel.value)
          
          const response = await axios.post('/api/batch/generate-from-image', formData, {
            headers: {
              'Content-Type': 'multipart/form-data'
            },
            timeout: 180000
          })
          
          if (response.data.success) {
            // 用后端返回的真实task_id更新本地任务
            if (taskManagerRef.value && taskManagerRef.value.updateLocalTaskId && response.data.task_id) {
              taskManagerRef.value.updateLocalTaskId(response.data.task_id)
            }
            // 不显示消息，因为任务已完成（同步处理）
          } else {
            ElMessage.error('创建批量生图任务失败: ' + response.data.error)
          }
        }
        
        // 不清空参考图和提示词，让用户可以继续使用或修改
        
      } catch (error) {
        console.error('批量生图错误:', error)
        console.error('错误详情:', error.response?.data)
        console.error('错误信息:', error.message)
        console.error('请求URL:', error.config?.url)
        ElMessage.error('批量生图失败: ' + (error.response?.data?.error || error.message))
      } finally {
        isBatchGenerating.value = false
      }
    }

    // 批量改图处理
    const handleBatchEdit = async () => {
      if (uploadedFiles.value.length === 0) {
        ElMessage.warning('请先上传图片')
        return
      }
      
      if (!batchPrompt.value.trim()) {
        ElMessage.warning('请输入生成提示词')
        return
      }

      isBatchGenerating.value = true
      
      try {
        // 先创建本地任务对象，立即显示给用户
        const items = uploadedFiles.value.map((fileObj, index) => ({
          index: index,
          prompt: batchPrompt.value,
          status: 'pending',
          reference_image_url: URL.createObjectURL(fileObj.file)
        }))
        createAndSetLocalTask(items)
        
        const formData = new FormData()
        
        // 添加所有文件
        uploadedFiles.value.forEach(fileObj => {
          formData.append('files', fileObj.file)
        })
        
        // 添加提示词和API类型
        formData.append('prompt', batchPrompt.value)
        formData.append('api_type', getApiTypeFromModel(selectedModel.value))
        formData.append('model_name', selectedModel.value)
        
        const response = await axios.post('/api/batch/generate', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          timeout: 180000  // 增加到3分钟
        })
        
        if (response.data.success) {
          // 用后端返回的真实task_id更新本地任务
          if (taskManagerRef.value && taskManagerRef.value.updateLocalTaskId && response.data.task_id) {
            taskManagerRef.value.updateLocalTaskId(response.data.task_id)
          }
          // 不显示消息，任务结果会在任务列表中显示
          // 不清空上传的文件和提示词，让用户可以继续使用或修改
        } else {
          ElMessage.error('创建批量改图任务失败: ' + response.data.error)
        }
      } catch (error) {
        console.error('批量改图错误:', error)
        ElMessage.error('批量改图失败: ' + (error.response?.data?.error || error.message))
      } finally {
        isBatchGenerating.value = false
      }
    }

    // 组件挂载时不再强制检查API key，用户可以选择使用服务器配置的
    onMounted(() => {
      // 不再强制显示API配置对话框
      // 用户可以通过点击"API Key 配置"按钮来配置自己的key
    })
    
    return {
      taskManagerRef,
      uploadedFiles,
      referenceImage,
      referenceImageList,
      imageCount,
      batchPrompt,
      isBatchGenerating,
      selectedApi,
      activeTab,
      selectedModel,
      availableModels,
      isStartButtonDisabled,
      handleBatchFileChange,
      handleReferenceImageChange,
      handleReferenceImageRemove,
      handleStartTask,
      handleBatchGenerate,
      handleBatchEdit,
      clearAllImages,
      clearReferenceImage,
      getApiTypeFromModel,
      // 变量相关
      detectedVariables,
      variableValues,
      handlePromptChange,
      getVariableValueCount,
      updateVariableCount,
      totalVariableCombinations,
      hasVariables,
      createAndSetLocalTask,
      // API配置相关
      showApiConfigDialog,
      handleApiConfigConfirmed,
      handleModelChange
    }
  }
}
</script>

<style>
/* 全局样式重置 */
body {
  margin: 0 !important;
  padding: 0 !important;
}

html, body {
  margin: 0;
  padding: 0;
  height: 100%;
  overflow: hidden;
}
</style>

<style scoped>
#app {
  font-family: 'PingFang SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #333333;
  background-color: #efefef;
  height: 100vh;
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.app-container {
  padding: 8px;
  height: 100vh;
  box-sizing: border-box;
}

.main-content {
  display: flex;
  background: white;
  border: 1px solid #eeeeee;
  border-radius: 12px;
  overflow: hidden;
  height: calc(100vh - 16px);
}

/* 左侧面板 */
.left-panel {
  width: 440px;
  flex-shrink: 0;
  border-right: 1px solid #eeeeee;
  background: white;
  display: flex;
  flex-direction: column;
}

.panel-content {
  padding: 20px 32px;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex: 1;
  overflow-y: auto;
}

/* 顶部标题区域 */
.header-section {
  padding-bottom: 20px;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 10px 0;
}

.logo-icon {
  width: 32px;
  height: 32px;
  position: relative;
}

.icon-stack {
  position: relative;
  width: 100%;
  height: 100%;
}

.icon-layer {
  position: absolute;
  background: white;
  border: 1.62px solid #333333;
  border-radius: 1.62px;
  width: 22.86px;
  height: 16.92px;
}

.icon-layer:nth-child(1) {
  top: 3.78px;
  left: 0.9px;
}

.icon-layer:nth-child(2) {
  top: 7.74px;
  left: 4.86px;
}

.icon-layer:nth-child(3) {
  top: 11.7px;
  left: 8.64px;
}

.app-title {
  font-size: 24px;
  font-weight: 600;
  color: #333333;
  margin: 0;
}

.app-subtitle {
  font-size: 16px;
  color: #333333;
  margin: 0;
}

/* 标签切换 */
.tab-switcher {
  display: flex;
  background: #eeeeee;
  border-radius: 6px;
  padding: 2px;
  gap: 2px;
}

.tab-item {
  flex: 1;
  padding: 3px 28px;
  text-align: center;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-item.active {
  background: white;
  border: 1px solid #dddddd;
}

.tab-item span {
  font-size: 14px;
  color: #333333;
}

.tab-description {
  font-size: 14px;
  color: #999999;
  margin: 0;
  padding-top: 10px;
}

/* 操作区域 */
.operation-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  font-size: 16px;
  font-weight: 600;
  color: #333333;
  margin: 0;
}

.model-selector-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.api-config-link {
  padding: 0;
  font-size: 14px;
  color: #04a864;
  display: flex;
  align-items: center;
  gap: 4px;
}

.api-config-link:hover {
  color: #038a56;
}

.api-config-link :deep(.el-icon) {
  font-size: 16px;
}

.model-selector {
  width: 100%;
}

.model-selector :deep(.el-input__wrapper) {
  border: 1px solid #dddddd;
  border-radius: 6px;
  padding: 8px 12px;
}

.model-selector :deep(.el-input__inner) {
  font-size: 14px;
  color: #333333;
}

.prompt-input {
  border-radius: 6px;
}

.prompt-input :deep(.el-textarea__inner) {
  border: 1px solid #dddddd;
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 14px;
  color: #333333;
}

.prompt-input :deep(.el-textarea__inner)::placeholder {
  color: #bbbbbb;
}

.upload-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.clear-icon {
  font-size: 16px;
  color: #333333;
  cursor: pointer;
}

/* 开始按钮 */
.start-button-container {
  margin-top: auto;
  padding-top: 10px;
}

.start-button {
  width: 100%;
  height: 40px;
  background: #04a864;
  border: 1px solid #dddddd;
  border-radius: 6px;
  font-size: 14px;
  color: white;
}

.start-button:hover {
  background: #038a56;
}

.start-button:disabled {
  background: #cccccc;
  color: #999999;
}

/* 分隔线 */
.divider {
  width: 1px;
  background: #eeeeee;
  flex-shrink: 0;
}

/* 右侧面板 */
.right-panel {
  flex: 1;
  background: white;
  padding: 20px 32px;
}

/* 批量生图相关样式 */
.reference-upload {
  width: 100%;
}

.reference-upload :deep(.el-upload) {
  width: 148px;
  height: 148px;
  border: 1px dashed #dddddd;
  border-radius: 6px;
}

.reference-upload :deep(.el-upload:hover) {
  border-color: #04a864;
}

.reference-upload :deep(.el-upload-list__item) {
  width: 148px;
  height: 148px;
  border-radius: 6px;
}

.count-selector {
  width: 100%;
}

.count-selector :deep(.el-input-number__decrease),
.count-selector :deep(.el-input-number__increase) {
  background: white;
  border: 1px solid #dddddd;
}

.count-selector :deep(.el-input__inner) {
  border: 1px solid #dddddd;
  border-radius: 6px;
  text-align: center;
}

.count-hint {
  display: block;
  font-size: 12px;
  color: #999999;
  margin-top: 8px;
}

/* 变量功能样式 */
.variable-section {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  margin: 12px 0;
}

.variable-header {
  margin-bottom: 12px;
}

.variable-header .form-label {
  color: #04a864;
  font-weight: 600;
}

.variable-input-group {
  margin-bottom: 16px;
}

.variable-input-group:last-child {
  margin-bottom: 0;
}

.variable-label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: #495057;
  margin-bottom: 8px;
  font-family: 'Courier New', monospace;
}

.variable-textarea {
  width: 100%;
}

.variable-textarea :deep(.el-textarea__inner) {
  border: 1px solid #dddddd;
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 14px;
  color: #333333;
  background: white;
  line-height: 1.6;
}

.variable-textarea :deep(.el-textarea__inner)::placeholder {
  color: #bbbbbb;
}

.variable-count {
  display: block;
  font-size: 12px;
  color: #6c757d;
  margin-top: 6px;
  font-style: italic;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .left-panel {
    width: 380px;
  }
  
  .panel-content {
    padding: 16px 24px;
  }
}

@media (max-width: 768px) {
  .main-content {
    flex-direction: column;
  }
  
  .left-panel {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid #eeeeee;
  }
  
  .divider {
    width: 100%;
    height: 1px;
  }
  
  .right-panel {
    padding: 16px 24px;
  }
}
</style>