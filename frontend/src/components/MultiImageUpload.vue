<template>
  <div class="multi-image-upload">
    <el-upload
      class="upload-demo"
      drag
      :auto-upload="false"
      :on-change="handleFileChange"
      :show-file-list="false"
      accept="image/*"
      multiple
    >
      <el-icon class="el-icon--upload"><upload /></el-icon>
      <div class="el-upload__text">
        将图片拖到此处，或<em>点击上传</em>
      </div>
      <template #tip>
        <div class="el-upload__tip">
          支持多文件上传，jpg/png/gif/webp 格式，单个文件不超过10MB
        </div>
      </template>
    </el-upload>
    
    <!-- 文件列表 -->
    <div v-if="files.length > 0" class="files-list">
      <h4>已选择的文件 ({{ files.length }})</h4>
      <div class="files-grid">
        <div 
          v-for="(file, index) in files" 
          :key="index" 
          class="file-item"
        >
          <el-image
            :src="file.previewUrl"
            fit="cover"
            style="width: 100px; height: 100px; border-radius: 8px;"
          />
          <div class="file-info">
            <p class="filename">{{ file.name }}</p>
            <p class="filesize">{{ formatFileSize(file.size) }}</p>
            <el-button 
              type="danger" 
              size="small" 
              @click="removeFile(index)"
              icon="Delete"
            >
              删除
            </el-button>
          </div>
        </div>
      </div>
      
      <div class="actions">
        <el-button @click="clearAll" type="warning" size="small">
          清空所有
        </el-button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch } from 'vue'
import { Upload } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

export default {
  name: 'MultiImageUpload',
  props: {
    files: {
      type: Array,
      default: () => []
    }
  },
  emits: ['files-change'],
  components: {
    Upload
  },
  setup(props, { emit }) {
    const files = ref([...props.files])

    const handleFileChange = (uploadFile) => {
      const newFile = uploadFile.raw
      if (newFile) {
        // 检查是否已存在相同文件
        const exists = files.value.some(f => f.name === newFile.name && f.size === newFile.size)
        if (exists) {
          ElMessage.warning('文件已存在')
          return
        }
        
        // 创建预览URL
        const previewUrl = URL.createObjectURL(newFile)
        
        // 添加到文件列表
        files.value.push({
          file: newFile,
          name: newFile.name,
          size: newFile.size,
          previewUrl: previewUrl
        })
        
        emit('files-change', files.value)
      }
    }

    const removeFile = (index) => {
      // 释放预览URL
      URL.revokeObjectURL(files.value[index].previewUrl)
      
      // 从列表中移除
      files.value.splice(index, 1)
      
      emit('files-change', files.value)
    }

    const clearAll = () => {
      // 释放所有预览URL
      files.value.forEach(file => {
        URL.revokeObjectURL(file.previewUrl)
      })
      
      // 清空列表
      files.value = []
      
      emit('files-change', files.value)
    }

    const formatFileSize = (bytes) => {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }

    // 监听props变化
    watch(() => props.files, (newFiles) => {
      files.value = [...newFiles]
    }, { deep: true })

    return {
      files,
      handleFileChange,
      removeFile,
      clearAll,
      formatFileSize
    }
  }
}
</script>

<style scoped>
.multi-image-upload {
  text-align: center;
}

.upload-demo {
  margin-bottom: 20px;
}

.files-list {
  margin-top: 20px;
  padding: 20px;
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  background-color: #fafafa;
}

.files-list h4 {
  margin: 0 0 15px 0;
  color: #333;
}

.files-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 15px;
  margin-bottom: 15px;
}

.file-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background-color: white;
}

.file-info {
  margin-top: 10px;
  text-align: center;
}

.filename {
  font-size: 12px;
  font-weight: bold;
  margin: 5px 0;
  word-break: break-all;
}

.filesize {
  font-size: 11px;
  color: #666;
  margin: 2px 0;
}

.actions {
  text-align: center;
  padding-top: 10px;
  border-top: 1px solid #e0e0e0;
}
</style>
