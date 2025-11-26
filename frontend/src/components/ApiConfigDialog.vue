<template>
  <el-dialog
    v-model="visible"
    title="API 配置"
    width="500px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    :show-close="false"
    :before-close="handleBeforeClose"
  >
    <div class="api-config-content">
      <div class="info-box">
        <el-icon class="info-icon"><InfoFilled /></el-icon>
        <p class="info-text">
          您的 API Key 仅保存在本地浏览器中，我们不会记录或上传您的 API Key。
        </p>
      </div>
      
      <div class="form-group">
        <label class="form-label">Gemini API Key</label>
        <el-input
          v-model="geminiApiKey"
          type="password"
          placeholder="请输入 Gemini API Key"
          show-password
          :disabled="loading"
        />
        <p class="form-hint">用于 Gemini 模型的图片生成</p>
      </div>
      
      <div class="form-group">
        <label class="form-label">豆包 API Key（可选）</label>
        <el-input
          v-model="doubaoApiKey"
          type="password"
          placeholder="请输入豆包 API Key（可选）"
          show-password
          :disabled="loading"
        />
        <p class="form-hint">用于豆包模型的图片生成，如不使用可留空</p>
      </div>
      
      <div class="error-message" v-if="errorMessage">
        {{ errorMessage }}
      </div>
    </div>
    
    <template #footer>
      <el-button @click="handleCancel" :disabled="loading">取消</el-button>
      <el-button type="primary" @click="handleConfirm" :loading="loading">
        保存并开始使用
      </el-button>
    </template>
  </el-dialog>
</template>

<script>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { InfoFilled } from '@element-plus/icons-vue'

export default {
  name: 'ApiConfigDialog',
  components: {
    InfoFilled
  },
  props: {
    modelValue: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:modelValue', 'confirmed'],
  setup(props, { emit }) {
    const visible = ref(props.modelValue)
    const geminiApiKey = ref('')
    const doubaoApiKey = ref('')
    const loading = ref(false)
    const errorMessage = ref('')
    
    // 监听外部传入的modelValue变化
    watch(() => props.modelValue, (newVal) => {
      visible.value = newVal
      if (newVal) {
        // 对话框打开时，尝试从localStorage加载已保存的key
        const savedGeminiKey = localStorage.getItem('gemini_api_key')
        const savedDoubaoKey = localStorage.getItem('doubao_api_key')
        if (savedGeminiKey) {
          geminiApiKey.value = savedGeminiKey
        }
        if (savedDoubaoKey) {
          doubaoApiKey.value = savedDoubaoKey
        }
        errorMessage.value = ''
      }
    })
    
    // 监听内部visible变化，同步到外部
    watch(visible, (newVal) => {
      emit('update:modelValue', newVal)
    })
    
    const handleBeforeClose = (done) => {
      // 如果还没有保存API key，不允许关闭
      const hasGeminiKey = localStorage.getItem('gemini_api_key')
      if (!hasGeminiKey) {
        ElMessage.warning('请先配置 API Key 才能使用')
        return
      }
      done()
    }
    
    const handleCancel = () => {
      // 如果还没有保存API key，不允许取消
      const hasGeminiKey = localStorage.getItem('gemini_api_key')
      if (!hasGeminiKey) {
        ElMessage.warning('请先配置 API Key 才能使用')
        return
      }
      visible.value = false
    }
    
    const handleConfirm = async () => {
      errorMessage.value = ''
      
      // 验证Gemini API Key
      if (!geminiApiKey.value.trim()) {
        errorMessage.value = '请输入 Gemini API Key'
        return
      }
      
      // 保存到localStorage
      try {
        localStorage.setItem('gemini_api_key', geminiApiKey.value.trim())
        if (doubaoApiKey.value.trim()) {
          localStorage.setItem('doubao_api_key', doubaoApiKey.value.trim())
        } else {
          // 如果清空了，也删除保存的key
          localStorage.removeItem('doubao_api_key')
        }
        
        loading.value = true
        
        // 触发确认事件
        emit('confirmed', {
          geminiApiKey: geminiApiKey.value.trim(),
          doubaoApiKey: doubaoApiKey.value.trim() || null
        })
        
        // 延迟一下再关闭，让父组件有时间处理
        setTimeout(() => {
          visible.value = false
          loading.value = false
          ElMessage.success('API Key 已保存')
        }, 300)
        
      } catch (error) {
        console.error('保存API Key失败:', error)
        errorMessage.value = '保存失败，请重试'
        loading.value = false
      }
    }
    
    return {
      visible,
      geminiApiKey,
      doubaoApiKey,
      loading,
      errorMessage,
      handleBeforeClose,
      handleCancel,
      handleConfirm
    }
  }
}
</script>

<style scoped>
.api-config-content {
  padding: 10px 0;
}

.info-box {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 8px;
  margin-bottom: 24px;
}

.info-icon {
  color: #0284c7;
  font-size: 20px;
  flex-shrink: 0;
  margin-top: 2px;
}

.info-text {
  margin: 0;
  font-size: 14px;
  color: #0369a1;
  line-height: 1.6;
}

.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: #333333;
  margin-bottom: 8px;
}

.form-hint {
  margin: 6px 0 0 0;
  font-size: 12px;
  color: #999999;
}

.error-message {
  padding: 12px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 6px;
  color: #dc2626;
  font-size: 14px;
  margin-top: 16px;
}

:deep(.el-input__wrapper) {
  border-radius: 6px;
}

:deep(.el-dialog__header) {
  padding: 20px 20px 10px;
  border-bottom: 1px solid #eeeeee;
}

:deep(.el-dialog__title) {
  font-size: 18px;
  font-weight: 600;
  color: #333333;
}

:deep(.el-dialog__body) {
  padding: 20px;
}

:deep(.el-dialog__footer) {
  padding: 16px 20px;
  border-top: 1px solid #eeeeee;
}
</style>

