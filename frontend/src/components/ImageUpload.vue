<template>
  <div class="image-upload">
    <el-upload
      class="upload-demo"
      drag
      :auto-upload="false"
      :on-change="handleFileChange"
      :show-file-list="false"
      accept="image/*"
    >
      <el-icon class="el-icon--upload"><upload /></el-icon>
      <div class="el-upload__text">
        将图片拖到此处，或<em>点击上传</em>
      </div>
      <template #tip>
        <div class="el-upload__tip">
          支持 jpg/png/gif/webp 格式，文件大小不超过10MB
        </div>
      </template>
    </el-upload>
    
    <!-- 图片预览 -->
    <div v-if="file" class="image-preview">
      <el-image
        :src="previewUrl"
        fit="cover"
        style="width: 200px; height: 200px; border-radius: 8px;"
      />
      <div class="file-info">
        <p><strong>文件名:</strong> {{ file.name }}</p>
        <p><strong>大小:</strong> {{ formatFileSize(file.size) }}</p>
        <el-button 
          type="danger" 
          size="small" 
          @click="removeFile"
          icon="Delete"
        >
          删除
        </el-button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch } from 'vue'
import { Upload } from '@element-plus/icons-vue'

export default {
  name: 'ImageUpload',
  props: {
    file: {
      type: File,
      default: null
    }
  },
  emits: ['file-change'],
  components: {
    Upload
  },
  setup(props, { emit }) {
    const file = ref(props.file)
    const previewUrl = ref('')

    const handleFileChange = (uploadFile) => {
      const newFile = uploadFile.raw
      if (newFile) {
        file.value = newFile
        createPreviewUrl(newFile)
        emit('file-change', newFile)
      }
    }

    const createPreviewUrl = (file) => {
      if (previewUrl.value) {
        URL.revokeObjectURL(previewUrl.value)
      }
      previewUrl.value = URL.createObjectURL(file)
    }

    const removeFile = () => {
      if (previewUrl.value) {
        URL.revokeObjectURL(previewUrl.value)
      }
      file.value = null
      previewUrl.value = ''
      emit('file-change', null)
    }

    const formatFileSize = (bytes) => {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }

    // 监听props变化
    watch(() => props.file, (newFile) => {
      file.value = newFile
      if (newFile) {
        createPreviewUrl(newFile)
      } else {
        previewUrl.value = ''
      }
    })

    return {
      file,
      previewUrl,
      handleFileChange,
      removeFile,
      formatFileSize
    }
  }
}
</script>

<style scoped>
.image-upload {
  text-align: center;
}

.upload-demo {
  margin-bottom: 20px;
}

.image-preview {
  margin-top: 20px;
  padding: 20px;
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  background-color: #fafafa;
}

.file-info {
  margin-top: 15px;
  text-align: left;
}

.file-info p {
  margin: 5px 0;
  font-size: 14px;
}
</style>
