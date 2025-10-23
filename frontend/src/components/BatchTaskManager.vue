<template>
  <div class="batch-task-manager">
    <div class="task-header">
      <h3>当前任务</h3>
      <el-button @click="refreshTasks" type="primary" size="small" :icon="Refresh">
        刷新
      </el-button>
    </div>
    
    <!-- 当前任务显示 -->
    <div v-if="currentTask" class="current-task">
      <el-card class="task-card" :class="getTaskStatusClass(currentTask.status)">
        <template #header>
          <div class="task-header-info">
            <span class="task-id">任务ID: {{ currentTask.task_id.substring(0, 8) }}...</span>
            <el-tag :type="getStatusTagType(currentTask.status)">
              {{ getStatusText(currentTask.status) }}
            </el-tag>
            <span v-if="currentTask.api_type" class="api-type">
              使用: {{ currentTask.api_type === 'gemini' ? 'Gemini API' : '豆包 API' }}
            </span>
          </div>
        </template>
        
        <div class="task-content">
          <div class="task-info">
            <p><strong>Prompt:</strong> {{ currentTask.prompt }}</p>
            <p><strong>创建时间:</strong> {{ formatTime(currentTask.created_at) }}</p>
            <p><strong>图片数量:</strong> {{ currentTask.total_images }}</p>
          </div>
          
          <!-- 进度条 -->
          <div v-if="currentTask.status === 'processing'" class="progress-section">
            <el-progress 
              :percentage="Math.round(currentTask.progress)" 
              :status="currentTask.status === 'completed' ? 'success' : ''"
            />
            <p class="progress-text">
              已处理: {{ currentTask.processed_images }}/{{ currentTask.total_images }}
            </p>
          </div>
          
          <!-- 结果统计 -->
          <div v-if="currentTask.status === 'completed'" class="results-summary">
            <el-tag type="success">成功: {{ currentTask.results.success_count }}</el-tag>
            <el-tag v-if="currentTask.results.failed_count > 0" type="danger">
              失败: {{ currentTask.results.failed_count }}
            </el-tag>
            <el-button 
              v-if="currentTask.status === 'completed'" 
              @click="downloadResults(currentTask)" 
              type="success" 
              size="small"
              :icon="Download"
            >
              下载结果
            </el-button>
          </div>
          
          <!-- 操作按钮 -->
          <div class="task-actions">
            <el-button 
              v-if="currentTask.status === 'processing'" 
              @click="cancelTask(currentTask.task_id)" 
              type="danger" 
              size="small"
              :icon="CircleClose"
            >
              取消任务
            </el-button>
          </div>
        </div>
        
        <!-- 生成结果详情 -->
        <div v-if="currentTask.results && currentTask.results.generated_images && currentTask.results.generated_images.length > 0" class="task-results">
          <el-divider>生成结果</el-divider>
          <div class="results-grid">
            <div v-for="(result, index) in currentTask.results.generated_images" :key="index" class="result-item">
              <div class="result-image">
                <el-image
                  v-if="result.generated_url"
                  :src="result.generated_url"
                  fit="cover"
                  style="width: 120px; height: 120px; border-radius: 8px;"
                  lazy
                >
                  <template #error>
                    <div class="image-slot">
                      <el-icon><Picture /></el-icon>
                    </div>
                  </template>
                </el-image>
                <div v-else class="image-slot no-image">
                  <el-icon><Picture /></el-icon>
                  <span>无图片</span>
                </div>
              </div>
              <div class="result-info">
                <p class="result-filename">{{ result.filename }}</p>
                <p class="result-description">{{ result.description ? result.description.substring(0, 50) + '...' : '无描述' }}</p>
                <el-button 
                  v-if="result.generated_url"
                  type="primary" 
                  size="small" 
                  :icon="Download" 
                  @click="downloadSingleImage(result.generated_url, result.generated_filename || `generated_${currentTask.task_id.substring(0,4)}_${index}.png`)"
                  plain
                >
                  下载
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </el-card>
    </div>
    
    <!-- 无任务状态 -->
    <div v-else class="no-task">
      <el-empty description="暂无任务">
        <template #image>
          <el-icon size="60"><Document /></el-icon>
        </template>
      </el-empty>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import { Refresh, CircleClose, Picture, Download, Document } from '@element-plus/icons-vue'

export default {
  name: 'BatchTaskManager',
  components: {
    Refresh,
    CircleClose,
    Picture,
    Download,
    Document
  },
  setup() {
    const currentTask = ref(null)
    const isLoadingTasks = ref(false)
    let refreshInterval = null

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
      refreshTasks,
      cancelTask,
      downloadResults,
      downloadSingleImage,
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
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.task-header h3 {
  margin: 0;
  color: #303133;
}

.current-task {
  margin-bottom: 20px;
}

.task-card {
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.task-header-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.task-id {
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 14px;
  color: #606266;
}

.api-type {
  font-size: 12px;
  color: #909399;
  background: #f5f7fa;
  padding: 2px 8px;
  border-radius: 4px;
}

.task-content {
  padding: 16px 0;
}

.task-info p {
  margin: 8px 0;
  color: #606266;
}

.progress-section {
  margin: 16px 0;
}

.progress-text {
  margin-top: 8px;
  font-size: 14px;
  color: #606266;
}

.results-summary {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 16px 0;
  flex-wrap: wrap;
}

.task-actions {
  margin-top: 16px;
}

.task-results {
  margin-top: 20px;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.result-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: #fafafa;
}

.result-image {
  margin-bottom: 8px;
}

.image-slot {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 120px;
  height: 120px;
  background: #f5f7fa;
  border-radius: 8px;
  color: #c0c4cc;
}

.image-slot.no-image {
  background: #fef0f0;
  color: #f56c6c;
}

.result-info {
  text-align: center;
  width: 100%;
}

.result-filename {
  font-size: 12px;
  color: #606266;
  margin: 4px 0;
  word-break: break-all;
}

.result-description {
  font-size: 11px;
  color: #909399;
  margin: 4px 0 8px 0;
  line-height: 1.4;
}

.no-task {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
}

/* 任务状态样式 */
.task-status-pending {
  border-left: 4px solid #409eff;
}

.task-status-processing {
  border-left: 4px solid #e6a23c;
}

.task-status-completed {
  border-left: 4px solid #67c23a;
}

.task-status-failed {
  border-left: 4px solid #f56c6c;
}

.task-status-cancelled {
  border-left: 4px solid #909399;
}
</style>