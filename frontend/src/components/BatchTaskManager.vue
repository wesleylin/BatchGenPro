<template>
  <div class="batch-task-manager">
    <!-- 任务列表头部 -->
    <div class="task-header">
      <div class="header-left">
        <h3 class="task-title">任务列表</h3>
        <span v-if="currentTask" class="task-progress">{{ getTaskProgress() }}</span>
      </div>
      <el-button 
        v-if="currentTask && currentTask.status === 'completed'" 
        @click="downloadResults(currentTask)" 
        type="primary" 
        size="small"
        class="download-all-btn"
      >
        下载全部
      </el-button>
    </div>
    
    <!-- 进度条 -->
    <div v-if="currentTask && currentTask.status === 'processing'" class="progress-bar">
      <div class="progress-fill" :style="{ width: currentTask.progress + '%' }"></div>
    </div>
    
    <!-- 结果网格 -->
    <div v-if="currentTask && currentTask.results && currentTask.results.generated_images" class="results-grid">
      <div 
        v-for="(result, index) in currentTask.results.generated_images" 
        :key="index" 
        class="result-item"
      >
        <div class="result-image">
          <el-image
            v-if="result.generated_url"
            :src="result.generated_url"
            fit="cover"
            class="image-preview"
            lazy
          >
            <template #error>
              <div class="image-placeholder">
                <el-icon><Picture /></el-icon>
              </div>
            </template>
          </el-image>
          <div v-else class="image-placeholder">
            <el-icon><Picture /></el-icon>
          </div>
        </div>
        <p class="result-filename">{{ result.filename }}</p>
      </div>
    </div>
    
    <!-- 无任务状态 -->
    <div v-else-if="!currentTask" class="no-task">
      <div class="empty-state">
        <el-icon size="60" class="empty-icon"><Document /></el-icon>
        <p class="empty-text">暂无任务</p>
      </div>
    </div>
    
    <!-- 任务进行中但无结果 -->
    <div v-else-if="currentTask && (!currentTask.results || !currentTask.results.generated_images || currentTask.results.generated_images.length === 0)" class="processing-state">
      <div class="processing-info">
        <el-icon size="40" class="processing-icon"><Loading /></el-icon>
        <p class="processing-text">正在处理中...</p>
        <p class="processing-detail">{{ getTaskProgress() }}</p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import { Picture, Download, Document, Loading } from '@element-plus/icons-vue'

export default {
  name: 'BatchTaskManager',
  components: {
    Picture,
    Download,
    Document,
    Loading
  },
  setup() {
    const currentTask = ref(null)
    const isLoadingTasks = ref(false)
    let refreshInterval = null

    // 获取任务进度文本
    const getTaskProgress = () => {
      if (!currentTask.value) return ''
      const processed = currentTask.value.processed_images || 0
      const total = currentTask.value.total_images || 0
      return `${processed}/${total}`
    }

    // 获取最新任务
    const fetchLatestTask = async () => {
      try {
        isLoadingTasks.value = true
        const response = await axios.get('/api/batch/tasks')
        
        if (response.data.success && response.data.tasks && response.data.tasks.length > 0) {
          // 只显示最新的任务
          currentTask.value = response.data.tasks[0]
        } else {
          currentTask.value = null
        }
      } catch (error) {
        console.error('获取任务失败:', error)
        ElMessage.error('获取任务失败')
      } finally {
        isLoadingTasks.value = false
      }
    }

    // 刷新任务
    const refreshTasks = () => {
      fetchLatestTask()
    }

    // 取消任务
    const cancelTask = async (taskId) => {
      try {
        await ElMessageBox.confirm('确定要取消这个任务吗？', '确认取消', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        const response = await axios.delete(`/api/batch/tasks/${taskId}`)
        if (response.data.success) {
          ElMessage.success('任务已取消')
          fetchLatestTask()
        } else {
          ElMessage.error('取消任务失败')
        }
      } catch (error) {
        if (error !== 'cancel') {
          console.error('取消任务失败:', error)
          ElMessage.error('取消任务失败')
        }
      }
    }

    // 下载结果 (批量)
    const downloadResults = async (task) => {
      try {
        const response = await axios.get(`/api/batch/tasks/${task.task_id}/results`)
        if (response.data.success) {
          const results = response.data.results
          
          let downloadCount = 0
          
          // 从 results.generated_images 中下载
          if (results.generated_images && results.generated_images.length > 0) {
            for (let i = 0; i < results.generated_images.length; i++) {
              const imageInfo = results.generated_images[i]
              if (imageInfo.generated_url) {
                const link = document.createElement('a')
                link.href = imageInfo.generated_url
                link.download = imageInfo.generated_filename || `generated_${task.task_id.substring(0, 8)}_${i + 1}.png`
                document.body.appendChild(link)
                link.click()
                document.body.removeChild(link)
                downloadCount++
              }
            }
          }
          
          if (downloadCount > 0) {
            ElMessage.success(`已开始下载 ${downloadCount} 张图片`)
          } else {
            ElMessage.warning('没有可下载的图片')
          }
        } else {
          ElMessage.error('获取结果失败')
        }
      } catch (error) {
        ElMessage.error('下载结果失败')
        console.error('下载结果失败:', error)
      }
    }

    // 下载单个图片
    const downloadSingleImage = (imageUrl, filename) => {
      try {
        const link = document.createElement('a')
        link.href = imageUrl
        link.download = filename || 'generated_image.png'
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        ElMessage.success('开始下载图片')
      } catch (error) {
        ElMessage.error('下载失败')
        console.error('下载失败:', error)
      }
    }

    // 获取状态标签类型
    const getStatusTagType = (status) => {
      switch (status) {
        case 'pending': return 'info'
        case 'processing': return 'warning'
        case 'completed': return 'success'
        case 'failed': return 'danger'
        case 'cancelled': return 'info'
        default: return 'info'
      }
    }

    // 获取状态文本
    const getStatusText = (status) => {
      switch (status) {
        case 'pending': return '等待中'
        case 'processing': return '处理中'
        case 'completed': return '已完成'
        case 'failed': return '失败'
        case 'cancelled': return '已取消'
        default: return '未知'
      }
    }

    // 获取任务状态样式类
    const getTaskStatusClass = (status) => {
      return `task-status-${status}`
    }

    // 格式化时间
    const formatTime = (timeString) => {
      if (!timeString) return '未知时间'
      const date = new Date(timeString)
      return date.toLocaleString('zh-CN')
    }

    onMounted(() => {
      fetchLatestTask()
      // 每3秒刷新一次任务状态
      refreshInterval = setInterval(fetchLatestTask, 3000)
    })

    onUnmounted(() => {
      if (refreshInterval) {
        clearInterval(refreshInterval)
      }
    })

    return {
      currentTask,
      isLoadingTasks,
      fetchLatestTask,
      refreshTasks,
      cancelTask,
      downloadResults,
      downloadSingleImage,
      getTaskProgress,
      getStatusTagType,
      getStatusText,
      getTaskStatusClass,
      formatTime
    }
  }
}
</script>

<style scoped>
.batch-task-manager {
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* 任务头部 */
.task-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  margin-bottom: 8px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.task-title {
  font-size: 16px;
  font-weight: 600;
  color: #333333;
  margin: 0;
}

.task-progress {
  font-size: 16px;
  font-weight: 600;
  color: #333333;
}

.download-all-btn {
  background: #04a864;
  border: 1px solid #dddddd;
  border-radius: 6px;
  font-size: 14px;
  color: white;
  padding: 5px 16px;
}

.download-all-btn:hover {
  background: #038a56;
}

/* 进度条 */
.progress-bar {
  height: 8px;
  background: #d9d9d9;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 20px;
}

.progress-fill {
  height: 100%;
  background: #04a864;
  border-radius: 4px;
  transition: width 0.3s ease;
}

/* 结果网格 */
.results-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  padding: 20px 0;
}

.result-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.result-image {
  width: 160px;
  height: 160px;
  background: #d9d9d9;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
}

.image-preview {
  width: 100%;
  height: 100%;
}

.image-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  background: #d9d9d9;
  color: #999999;
  font-size: 24px;
}

.result-filename {
  font-size: 14px;
  color: #333333;
  text-align: center;
  margin: 0;
  word-break: break-all;
  max-width: 160px;
}

/* 无任务状态 */
.no-task {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-state {
  text-align: center;
}

.empty-icon {
  color: #c0c4cc;
  margin-bottom: 16px;
}

.empty-text {
  font-size: 16px;
  color: #909399;
  margin: 0;
}

/* 处理中状态 */
.processing-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.processing-info {
  text-align: center;
}

.processing-icon {
  color: #04a864;
  margin-bottom: 16px;
  animation: spin 1s linear infinite;
}

.processing-text {
  font-size: 16px;
  color: #333333;
  margin: 0 0 8px 0;
}

.processing-detail {
  font-size: 14px;
  color: #666666;
  margin: 0;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .results-grid {
    gap: 16px;
  }
  
  .result-image {
    width: 140px;
    height: 140px;
  }
  
  .result-filename {
    max-width: 140px;
  }
}

@media (max-width: 768px) {
  .results-grid {
    gap: 12px;
    padding: 16px 0;
  }
  
  .result-image {
    width: 120px;
    height: 120px;
  }
  
  .result-filename {
    max-width: 120px;
    font-size: 12px;
  }
  
  .task-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>