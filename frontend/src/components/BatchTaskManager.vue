<template>
  <div class="batch-task-manager">
    <div class="task-header">
      <h3>批量任务管理</h3>
      <el-button @click="refreshTasks" type="primary" size="small">
        刷新
      </el-button>
    </div>
    
    <!-- 任务列表 -->
    <div v-if="tasks.length > 0" class="tasks-list">
      <el-card 
        v-for="task in tasks" 
        :key="task.task_id" 
        class="task-card"
        :class="getTaskStatusClass(task.status)"
      >
        <template #header>
          <div class="task-header-info">
            <span class="task-id">任务ID: {{ task.task_id.substring(0, 8) }}...</span>
            <el-tag :type="getStatusTagType(task.status)">
              {{ getStatusText(task.status) }}
            </el-tag>
          </div>
        </template>
        
        <div class="task-content">
          <div class="task-info">
            <p><strong>Prompt:</strong> {{ task.prompt }}</p>
            <p><strong>创建时间:</strong> {{ formatTime(task.created_at) }}</p>
            <p><strong>图片数量:</strong> {{ task.total_images }}</p>
          </div>
          
          <!-- 进度条 -->
          <div v-if="task.status === 'processing'" class="progress-section">
            <el-progress 
              :percentage="Math.round(task.progress)" 
              :status="task.status === 'completed' ? 'success' : ''"
            />
            <p class="progress-text">
              已处理: {{ task.processed_images }}/{{ task.total_images }}
            </p>
          </div>
          
          <!-- 结果统计 -->
          <div v-if="task.status === 'completed'" class="results-summary">
            <el-tag type="success">成功: {{ task.results.success_count }}</el-tag>
            <el-tag v-if="task.results.failed_count > 0" type="danger">
              失败: {{ task.results.failed_count }}
            </el-tag>
          </div>
          
          <!-- 操作按钮 -->
          <div class="task-actions">
            <el-button 
              @click="viewTaskDetails(task)" 
              type="primary" 
              size="small"
            >
              查看详情
            </el-button>
            <el-button 
              v-if="task.status === 'processing'" 
              @click="cancelTask(task.task_id)" 
              type="danger" 
              size="small"
            >
              取消任务
            </el-button>
            <el-button 
              v-if="task.status === 'completed'" 
              @click="downloadResults(task)" 
              type="success" 
              size="small"
            >
              下载结果
            </el-button>
          </div>
        </div>
      </el-card>
    </div>
    
    <!-- 空状态 -->
    <div v-else class="empty-state">
      <el-empty description="暂无批量任务" />
    </div>
    
    <!-- 任务详情对话框 -->
    <el-dialog
      v-model="showTaskDetails"
      :title="`任务详情 - ${currentTask?.task_id?.substring(0, 8)}...`"
      width="80%"
      :before-close="closeTaskDetails"
    >
      <div v-if="currentTask" class="task-details">
        <div class="details-section">
          <h4>基本信息</h4>
          <p><strong>任务ID:</strong> {{ currentTask.task_id }}</p>
          <p><strong>状态:</strong> {{ getStatusText(currentTask.status) }}</p>
          <p><strong>创建时间:</strong> {{ formatTime(currentTask.created_at) }}</p>
          <p><strong>更新时间:</strong> {{ formatTime(currentTask.updated_at) }}</p>
          <p><strong>Prompt:</strong> {{ currentTask.prompt }}</p>
        </div>
        
        <div class="details-section">
          <h4>进度信息</h4>
          <p><strong>总图片数:</strong> {{ currentTask.total_images }}</p>
          <p><strong>已处理:</strong> {{ currentTask.processed_images }}</p>
          <p><strong>进度:</strong> {{ Math.round(currentTask.progress) }}%</p>
        </div>
        
        <div class="details-section">
          <h4>图片列表</h4>
          <div class="images-grid">
            <div 
              v-for="(image, index) in currentTask.images" 
              :key="index"
              class="image-item"
            >
              <div class="image-info">
                <p><strong>文件名:</strong> {{ image.filename }}</p>
                <p><strong>状态:</strong> {{ getStatusText(image.status) }}</p>
                <p v-if="image.error"><strong>错误:</strong> {{ image.error }}</p>
              </div>
              <div v-if="image.result_url" class="image-result">
                <el-image
                  :src="image.result_url"
                  fit="cover"
                  style="width: 100px; height: 100px; border-radius: 4px;"
                />
                <el-button 
                  type="primary" 
                  size="small" 
                  @click="downloadSingleImage(image.result_url, image.filename)"
                  style="margin-top: 8px;"
                >
                  下载
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

export default {
  name: 'BatchTaskManager',
  setup() {
    const tasks = ref([])
    const showTaskDetails = ref(false)
    const currentTask = ref(null)
    const refreshInterval = ref(null)

    // 获取任务列表
    const fetchTasks = async () => {
      try {
        const response = await axios.get('/api/batch/tasks')
        if (response.data.success) {
          tasks.value = response.data.tasks
        }
      } catch (error) {
        console.error('获取任务列表失败:', error)
      }
    }

    // 刷新任务列表
    const refreshTasks = () => {
      fetchTasks()
    }

    // 查看任务详情
    const viewTaskDetails = async (task) => {
      try {
        const response = await axios.get(`/api/batch/tasks/${task.task_id}`)
        if (response.data.success) {
          currentTask.value = response.data.task
          showTaskDetails.value = true
        }
      } catch (error) {
        ElMessage.error('获取任务详情失败')
        console.error('获取任务详情失败:', error)
      }
    }

    // 关闭任务详情
    const closeTaskDetails = () => {
      showTaskDetails.value = false
      currentTask.value = null
    }

    // 取消任务
    const cancelTask = async (taskId) => {
      try {
        await ElMessageBox.confirm('确定要取消这个任务吗？', '确认取消', {
          type: 'warning'
        })
        
        const response = await axios.delete(`/api/batch/tasks/${taskId}`)
        if (response.data.success) {
          ElMessage.success('任务已取消')
          fetchTasks()
        }
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('取消任务失败')
          console.error('取消任务失败:', error)
        }
      }
    }

    // 下载结果
    const downloadResults = async (task) => {
      try {
        const response = await axios.get(`/api/batch/tasks/${task.task_id}/results`)
        if (response.data.success) {
          const results = response.data.results
          const images = response.data.images
          
          // 下载所有生成的图片
          let downloadCount = 0
          
          // 从 results.generated_images 中下载
          if (results.generated_images && results.generated_images.length > 0) {
            for (let i = 0; i < results.generated_images.length; i++) {
              const imageInfo = results.generated_images[i]
              if (imageInfo.generated_url) {
                // 创建下载链接
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
      const statusMap = {
        'pending': 'info',
        'processing': 'warning',
        'completed': 'success',
        'failed': 'danger',
        'cancelled': 'info'
      }
      return statusMap[status] || 'info'
    }

    // 获取状态文本
    const getStatusText = (status) => {
      const statusMap = {
        'pending': '等待中',
        'processing': '处理中',
        'completed': '已完成',
        'failed': '失败',
        'cancelled': '已取消'
      }
      return statusMap[status] || '未知'
    }

    // 获取任务状态样式类
    const getTaskStatusClass = (status) => {
      return `task-status-${status}`
    }

    // 格式化时间
    const formatTime = (timeString) => {
      return new Date(timeString).toLocaleString('zh-CN')
    }

    // 组件挂载时获取任务列表
    onMounted(() => {
      fetchTasks()
      // 每5秒自动刷新一次
      refreshInterval.value = setInterval(fetchTasks, 5000)
    })

    // 组件卸载时清除定时器
    onUnmounted(() => {
      if (refreshInterval.value) {
        clearInterval(refreshInterval.value)
      }
    })

    return {
      tasks,
      showTaskDetails,
      currentTask,
      refreshTasks,
      viewTaskDetails,
      closeTaskDetails,
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
  padding: 20px;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.task-header h3 {
  margin: 0;
}

.tasks-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.task-card {
  transition: all 0.3s ease;
}

.task-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
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

.task-header-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.task-id {
  font-family: monospace;
  font-size: 14px;
}

.task-content {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.task-info p {
  margin: 5px 0;
  font-size: 14px;
}

.progress-section {
  margin: 10px 0;
}

.progress-text {
  margin: 5px 0 0 0;
  font-size: 12px;
  color: #666;
}

.results-summary {
  display: flex;
  gap: 10px;
}

.task-actions {
  display: flex;
  gap: 10px;
}

.empty-state {
  text-align: center;
  padding: 40px;
}

.task-details {
  max-height: 60vh;
  overflow-y: auto;
}

.details-section {
  margin-bottom: 20px;
  padding: 15px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
}

.details-section h4 {
  margin: 0 0 10px 0;
  color: #333;
}

.details-section p {
  margin: 5px 0;
  font-size: 14px;
}

.images-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 15px;
  margin-top: 10px;
}

.image-item {
  padding: 10px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background-color: #fafafa;
}

.image-info p {
  margin: 3px 0;
  font-size: 12px;
}

.image-result {
  margin-top: 10px;
  text-align: center;
}
</style>
