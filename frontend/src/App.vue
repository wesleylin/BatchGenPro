<template>
  <div id="app">
    <el-container>
      <el-header>
        <h1>BatchGen Pro - V3</h1>
        <p>批量图片生成工具 - 支持Gemini和豆包API</p>
      </el-header>
      
      <el-main>
        <el-row :gutter="20">
          <!-- 左侧：批量上传和配置 -->
          <el-col :span="8">
            <el-card>
              <template #header>
                <span>批量图片上传</span>
              </template>
              
              <MultiImageUpload 
                v-model:files="uploadedFiles"
                @files-change="handleBatchFileChange"
              />
              
              <el-divider />
              
              <!-- API选择器 -->
              <div class="api-selector">
                <h4>选择AI服务</h4>
                <el-radio-group v-model="selectedApi" size="small">
                  <el-radio-button label="gemini">Gemini API</el-radio-button>
                  <el-radio-button label="doubao">豆包 API</el-radio-button>
                </el-radio-group>
                <p class="api-description">
                  {{ selectedApi === 'gemini' ? '使用Google Gemini 2.5 Flash Image模型' : '使用豆包Seedream 4.0模型' }}
                </p>
              </div>
              
              <el-divider />
              
              <PromptInput 
                v-model:prompt="batchPrompt"
                :loading="isBatchGenerating"
                @generate="handleBatchGenerate"
                button-text="开始批量生成"
                :disabled="uploadedFiles.length === 0"
              />
            </el-card>
          </el-col>
          
          <!-- 右侧：任务管理 -->
          <el-col :span="16">
            <BatchTaskManager />
          </el-col>
        </el-row>
      </el-main>
    </el-container>
  </div>
</template>

<script>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import MultiImageUpload from './components/MultiImageUpload.vue'
import PromptInput from './components/PromptInput.vue'
import BatchTaskManager from './components/BatchTaskManager.vue'

export default {
  name: 'App',
  components: {
    MultiImageUpload,
    PromptInput,
    BatchTaskManager
  },
  setup() {
    // 批量生成相关状态
    const uploadedFiles = ref([])
    const batchPrompt = ref('')
    const isBatchGenerating = ref(false)
    const selectedApi = ref('gemini') // 默认使用Gemini

    // 处理批量文件变化
    const handleBatchFileChange = (files) => {
      uploadedFiles.value = files
    }

    // 批量生成处理
    const handleBatchGenerate = async () => {
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
        formData.append('api_type', selectedApi.value)
        
        const response = await axios.post('/api/batch/generate', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          timeout: 60000
        })
        
        if (response.data.success) {
          ElMessage.success(`批量任务已创建！任务ID: ${response.data.task_id.substring(0, 8)}...`)
          // 清空上传的文件和提示词
          uploadedFiles.value = []
          batchPrompt.value = ''
        } else {
          ElMessage.error('创建批量任务失败: ' + response.data.error)
        }
      } catch (error) {
        console.error('批量生成错误:', error)
        ElMessage.error('批量生成失败: ' + (error.response?.data?.error || error.message))
      } finally {
        isBatchGenerating.value = false
      }
    }

    return {
      uploadedFiles,
      batchPrompt,
      isBatchGenerating,
      selectedApi,
      handleBatchFileChange,
      handleBatchGenerate
    }
  }
}
</script>

<style scoped>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
}

.el-header {
  background-color: #f5f7fa;
  color: #333;
  text-align: center;
  padding: 20px;
  border-bottom: 1px solid #e4e7ed;
}

.el-header h1 {
  margin: 0 0 10px 0;
  font-size: 28px;
  font-weight: bold;
}

.el-header p {
  margin: 0;
  font-size: 16px;
  color: #666;
}

.el-main {
  padding: 20px;
}

.api-selector {
  margin: 20px 0;
}

.api-selector h4 {
  margin: 0 0 15px 0;
  color: #303133;
  font-size: 16px;
}

.api-description {
  margin: 10px 0 0 0;
  font-size: 14px;
  color: #606266;
  font-style: italic;
}

.el-card {
  margin-bottom: 20px;
}

.el-divider {
  margin: 20px 0;
}
</style>