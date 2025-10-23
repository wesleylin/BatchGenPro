<template>
  <div id="app">
    <el-container>
      <el-header>
        <h1>BatchGen Pro - V2</h1>
        <p>批量图片生成工具</p>
        <div class="header-actions">
          <el-button 
            @click="currentMode = 'single'" 
            :type="currentMode === 'single' ? 'primary' : 'default'"
            size="small"
          >
            单张生成
          </el-button>
          <el-button 
            @click="currentMode = 'batch'" 
            :type="currentMode === 'batch' ? 'primary' : 'default'"
            size="small"
          >
            批量生成
          </el-button>
        </div>
      </el-header>
      
      <el-main>
        <!-- 单张生成模式 -->
        <div v-if="currentMode === 'single'">
          <el-row :gutter="20">
            <!-- 左侧：上传和配置 -->
            <el-col :span="12">
              <el-card>
                <template #header>
                  <span>图片上传</span>
                </template>
                
                <ImageUpload 
                  v-model:file="uploadedFile"
                  @file-change="handleFileChange"
                />
                
                <el-divider />
                
                <PromptInput 
                  v-model:prompt="prompt"
                  :loading="isGenerating"
                  @generate="handleGenerate"
                />
              </el-card>
            </el-col>
            
            <!-- 右侧：结果显示 -->
            <el-col :span="12">
              <el-card>
                <template #header>
                  <span>生成结果</span>
                </template>
                
                <ResultDisplay 
                  :original-file="uploadedFile"
                  :result="generationResult"
                  :loading="isGenerating"
                />
              </el-card>
            </el-col>
          </el-row>
        </div>
        
        <!-- 批量生成模式 -->
        <div v-if="currentMode === 'batch'">
          <el-row :gutter="20">
            <!-- 左侧：批量上传和配置 -->
            <el-col :span="12">
              <el-card>
                <template #header>
                  <span>批量图片上传</span>
                </template>
                
                <MultiImageUpload 
                  v-model:files="uploadedFiles"
                  @files-change="handleFilesChange"
                />
                
                <el-divider />
                
                <PromptInput 
                  v-model:prompt="batchPrompt"
                  :loading="isBatchGenerating"
                  @generate="handleBatchGenerate"
                  :disabled="uploadedFiles.length === 0"
                />
              </el-card>
            </el-col>
            
            <!-- 右侧：任务管理 -->
            <el-col :span="12">
              <el-card>
                <template #header>
                  <span>任务管理</span>
                </template>
                
                <BatchTaskManager />
              </el-card>
            </el-col>
          </el-row>
        </div>
      </el-main>
    </el-container>
  </div>
</template>

<script>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import ImageUpload from './components/ImageUpload.vue'
import MultiImageUpload from './components/MultiImageUpload.vue'
import PromptInput from './components/PromptInput.vue'
import ResultDisplay from './components/ResultDisplay.vue'
import BatchTaskManager from './components/BatchTaskManager.vue'
import axios from 'axios'

export default {
  name: 'App',
  components: {
    ImageUpload,
    MultiImageUpload,
    PromptInput,
    ResultDisplay,
    BatchTaskManager
  },
  setup() {
    // 模式切换
    const currentMode = ref('single')
    
    // 单张生成相关
    const uploadedFile = ref(null)
    const prompt = ref('')
    const isGenerating = ref(false)
    const generationResult = ref(null)
    
    // 批量生成相关
    const uploadedFiles = ref([])
    const batchPrompt = ref('')
    const isBatchGenerating = ref(false)

    // 单张生成处理
    const handleFileChange = (file) => {
      uploadedFile.value = file
    }

    const handleGenerate = async () => {
      if (!uploadedFile.value || !prompt.value.trim()) {
        ElMessage.warning('请先上传图片并输入Prompt')
        return
      }

      isGenerating.value = true
      generationResult.value = null

      try {
        const formData = new FormData()
        formData.append('file', uploadedFile.value)
        formData.append('prompt', prompt.value)

        const response = await axios.post('/api/generate', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          timeout: 60000 // 60秒超时
        })

        if (response.data.success) {
          generationResult.value = response.data
          ElMessage.success('图片生成成功！')
        } else {
          ElMessage.error('生成失败：' + response.data.error)
        }
      } catch (error) {
        console.error('生成错误:', error)
        ElMessage.error('生成失败：' + (error.response?.data?.error || error.message))
      } finally {
        isGenerating.value = false
      }
    }

    // 批量生成处理
    const handleFilesChange = (files) => {
      uploadedFiles.value = files
    }

    const handleBatchGenerate = async () => {
      if (uploadedFiles.value.length === 0 || !batchPrompt.value.trim()) {
        ElMessage.warning('请先上传图片并输入Prompt')
        return
      }

      isBatchGenerating.value = true

      try {
        const formData = new FormData()
        
        // 添加所有文件
        uploadedFiles.value.forEach(fileObj => {
          formData.append('files', fileObj.file)
        })
        
        formData.append('prompt', batchPrompt.value)

        const response = await axios.post('/api/batch/generate', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          timeout: 120000 // 2分钟超时
        })

        if (response.data.success) {
          ElMessage.success(`批量任务已创建！任务ID: ${response.data.task_id.substring(0, 8)}...`)
          // 清空文件列表
          uploadedFiles.value = []
          batchPrompt.value = ''
        } else {
          ElMessage.error('创建批量任务失败：' + response.data.error)
        }
      } catch (error) {
        console.error('批量生成错误:', error)
        ElMessage.error('创建批量任务失败：' + (error.response?.data?.error || error.message))
      } finally {
        isBatchGenerating.value = false
      }
    }

    return {
      currentMode,
      uploadedFile,
      prompt,
      isGenerating,
      generationResult,
      uploadedFiles,
      batchPrompt,
      isBatchGenerating,
      handleFileChange,
      handleGenerate,
      handleFilesChange,
      handleBatchGenerate
    }
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
}

.el-header {
  background-color: #f5f5f5;
  text-align: center;
  padding: 20px;
  position: relative;
}

.el-header h1 {
  margin: 0;
  color: #409eff;
}

.el-header p {
  margin: 5px 0 0 0;
  color: #666;
}

.header-actions {
  position: absolute;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
}

.el-main {
  padding: 20px;
}
</style>