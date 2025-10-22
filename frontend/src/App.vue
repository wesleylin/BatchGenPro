<template>
  <div id="app">
    <el-container>
      <el-header>
        <h1>BatchGen Pro - MVP</h1>
        <p>单张图片生成工具</p>
      </el-header>
      
      <el-main>
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
          
          <!-- 右侧：结果展示 -->
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
      </el-main>
    </el-container>
  </div>
</template>

<script>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import ImageUpload from './components/ImageUpload.vue'
import PromptInput from './components/PromptInput.vue'
import ResultDisplay from './components/ResultDisplay.vue'
import axios from 'axios'

export default {
  name: 'App',
  components: {
    ImageUpload,
    PromptInput,
    ResultDisplay
  },
  setup() {
    const uploadedFile = ref(null)
    const prompt = ref('')
    const isGenerating = ref(false)
    const generationResult = ref(null)

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
          }
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

    return {
      uploadedFile,
      prompt,
      isGenerating,
      generationResult,
      handleFileChange,
      handleGenerate
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
}

.el-header h1 {
  margin: 0;
  color: #409eff;
}

.el-header p {
  margin: 5px 0 0 0;
  color: #666;
}

.el-main {
  padding: 20px;
}
</style>
