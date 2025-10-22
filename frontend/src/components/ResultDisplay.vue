<template>
  <div class="result-display">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="3" animated />
      <el-progress 
        :percentage="50" 
        :show-text="false"
        status="success"
      />
      <p>正在生成图片，请稍候...</p>
    </div>
    
    <!-- 结果展示 -->
    <div v-else-if="result" class="result-content">
      <el-row :gutter="20">
        <!-- 原图 -->
        <el-col :span="12">
          <div class="image-section">
            <h4>原图</h4>
            <el-image
              :src="originalFileUrl"
              fit="cover"
              style="width: 100%; height: 200px; border-radius: 8px;"
            />
          </div>
        </el-col>
        
        <!-- 生成结果 -->
        <el-col :span="12">
          <div class="image-section">
            <h4>生成结果</h4>
            <!-- 如果有生成的图像，显示图像 -->
            <div v-if="result.generated_image_url" class="generated-image">
              <el-image
                :src="result.generated_image_url"
                fit="cover"
                style="width: 100%; height: 200px; border-radius: 8px;"
                @error="handleImageError"
                @load="handleImageLoad"
              />
              <div v-if="result.description" class="image-description">
                <el-card style="margin-top: 10px;">
                  <h5>AI描述：</h5>
                  <p>{{ result.description }}</p>
                </el-card>
              </div>
            </div>
            <!-- 否则显示文本结果 -->
            <div v-else-if="result.description" class="text-result">
              <el-card>
                <h5>AI分析结果：</h5>
                <p>{{ result.description }}</p>
              </el-card>
            </div>
            <div v-else class="no-result">
              <el-empty description="暂无结果" />
            </div>
          </div>
        </el-col>
      </el-row>
      
      <!-- 操作按钮 -->
      <div class="action-buttons">
        <el-button 
          type="primary" 
          @click="downloadResult"
          :disabled="!result.result_url && !result.generated_image_url"
        >
          <el-icon><Download /></el-icon>
          下载结果
        </el-button>
        
        <el-button @click="clearResult">
          <el-icon><Delete /></el-icon>
          清除结果
        </el-button>
      </div>
      
      <!-- 注意事项 -->
      <el-alert
        v-if="result.note"
        :title="result.note"
        type="warning"
        :closable="false"
        show-icon
        style="margin-top: 20px;"
      />
    </div>
    
    <!-- 空状态 -->
    <div v-else class="empty-state">
      <el-empty description="请上传图片并生成结果" />
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { Download, Delete } from '@element-plus/icons-vue'

export default {
  name: 'ResultDisplay',
  props: {
    originalFile: {
      type: File,
      default: null
    },
    result: {
      type: Object,
      default: null
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  emits: ['clear-result'],
  components: {
    Download,
    Delete
  },
  setup(props, { emit }) {
    const originalFileUrl = computed(() => {
      if (props.originalFile) {
        return URL.createObjectURL(props.originalFile)
      }
      return ''
    })

    const downloadResult = () => {
      if (props.result) {
        const link = document.createElement('a')
        
        // 优先下载生成的图像
        if (props.result.generated_image_url) {
          link.href = props.result.generated_image_url
          link.download = 'generated_image.png'
        } else if (props.result.result_url) {
          link.href = props.result.result_url
          link.download = 'generated_result.txt'
        }
        
        if (link.href) {
          document.body.appendChild(link)
          link.click()
          document.body.removeChild(link)
        }
      }
    }

    const clearResult = () => {
      emit('clear-result')
    }

    const handleImageError = (error) => {
      console.error('图片加载失败:', error)
    }

    const handleImageLoad = () => {
      console.log('图片加载成功')
    }

    return {
      originalFileUrl,
      downloadResult,
      clearResult,
      handleImageError,
      handleImageLoad
    }
  }
}
</script>

<style scoped>
.result-display {
  min-height: 300px;
}

.loading-state {
  text-align: center;
  padding: 40px 20px;
}

.loading-state p {
  margin-top: 20px;
  color: #666;
}

.result-content {
  padding: 20px 0;
}

.image-section {
  text-align: center;
}

.image-section h4 {
  margin-bottom: 15px;
  color: #409eff;
}

.text-result {
  height: 200px;
  overflow-y: auto;
}

.text-result h5 {
  margin-bottom: 10px;
  color: #67c23a;
}

.text-result p {
  line-height: 1.6;
  color: #606266;
}

.no-result {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-buttons {
  text-align: center;
  margin-top: 30px;
}

.action-buttons .el-button {
  margin: 0 10px;
}

.empty-state {
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
