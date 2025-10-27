<template>
  <div id="app">
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
                批量改图会对多张图用同一份提示词来生图
              </p>
            </div>
            
            <!-- 操作区域 -->
            <div class="operation-section">
              <!-- 大模型选择器 -->
              <div class="form-group">
                <label class="form-label">大模型</label>
                <el-select 
                  v-model="selectedModel" 
                  class="model-selector"
                  placeholder="选择模型"
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
                  placeholder="输入提示词"
                  class="prompt-input"
                />
              </div>
              
              <!-- 批量生图：参考图片上传（单图） + 数量选择 -->
              <template v-if="activeTab === 'generate'">
                <div class="form-group">
                  <div class="upload-header">
                    <label class="form-label">参考图片（单张）</label>
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
                
                <div class="form-group">
                  <label class="form-label">生成数量</label>
                  <el-input-number 
                    v-model="imageCount" 
                    :min="1" 
                    :max="10" 
                    class="count-selector"
                  />
                  <span class="count-hint">最多生成10张</span>
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
          <BatchTaskManager />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowDown, RefreshLeft, Plus } from '@element-plus/icons-vue'
import axios from 'axios'
import MultiImageUpload from './components/MultiImageUpload.vue'
import BatchTaskManager from './components/BatchTaskManager.vue'

export default {
  name: 'App',
  components: {
    MultiImageUpload,
    BatchTaskManager,
    ArrowDown,
    RefreshLeft,
    Plus
  },
  setup() {
    // 批量改图相关状态
    const uploadedFiles = ref([])
    
    // 批量生图相关状态
    const referenceImage = ref(null)
    const referenceImageList = ref([])
    const imageCount = ref(3) // 默认生成3张
    
    // 通用状态
    const batchPrompt = ref('')
    const isBatchGenerating = ref(false)
    const selectedApi = ref('gemini') // 默认使用Gemini
    const activeTab = ref('edit') // 默认选中批量改图
    const selectedModel = ref('gemini-2.5-flash-image') // 默认模型
    
    // 可用模型列表
    const availableModels = ref([
      { value: 'gemini-2.5-flash-image', label: 'gemini-2.5-flash-image' },
      { value: 'doubao-seedream-4-0-250828', label: 'doubao-seedream-4-0-250828' }
    ])

    // 计算属性：开始按钮是否禁用
    const isStartButtonDisabled = computed(() => {
      if (!batchPrompt.value.trim()) return true
      
      if (activeTab.value === 'generate') {
        // 批量生图：需要参考图
        return !referenceImage.value
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
      if (modelName.includes('gemini')) {
        return 'gemini'
      } else if (modelName.includes('doubao')) {
        return 'doubao'
      }
      return 'gemini' // 默认
    }

    // 统一的开始任务处理
    const handleStartTask = async () => {
      if (activeTab.value === 'generate') {
        await handleBatchGenerate()
      } else {
        await handleBatchEdit()
      }
    }

    // 批量生图处理
    const handleBatchGenerate = async () => {
      if (!referenceImage.value) {
        ElMessage.warning('请先上传参考图片')
        return
      }
      
      if (!batchPrompt.value.trim()) {
        ElMessage.warning('请输入生成提示词')
        return
      }

      isBatchGenerating.value = true
      
      try {
        const formData = new FormData()
        
        // 添加参考图片
        formData.append('file', referenceImage.value)
        
        // 添加提示词、数量和API类型
        formData.append('prompt', batchPrompt.value)
        formData.append('image_count', imageCount.value)
        formData.append('api_type', getApiTypeFromModel(selectedModel.value))
        
        const response = await axios.post('/api/batch/generate-from-image', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          timeout: 60000
        })
        
        if (response.data.success) {
          ElMessage.success(`批量生图任务已创建！将生成${imageCount.value}张图片`)
          // 清空参考图和提示词
          referenceImage.value = null
          referenceImageList.value = []
          batchPrompt.value = ''
        } else {
          ElMessage.error('创建批量生图任务失败: ' + response.data.error)
        }
      } catch (error) {
        console.error('批量生图错误:', error)
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
        const formData = new FormData()
        
        // 添加所有文件
        uploadedFiles.value.forEach(fileObj => {
          formData.append('files', fileObj.file)
        })
        
        // 添加提示词和API类型
        formData.append('prompt', batchPrompt.value)
        formData.append('api_type', getApiTypeFromModel(selectedModel.value))
        
        const response = await axios.post('/api/batch/generate', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          timeout: 60000
        })
        
        if (response.data.success) {
          ElMessage.success(`批量改图任务已创建！任务ID: ${response.data.task_id.substring(0, 8)}...`)
          // 清空上传的文件和提示词
          uploadedFiles.value = []
          batchPrompt.value = ''
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

    return {
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
      getApiTypeFromModel
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