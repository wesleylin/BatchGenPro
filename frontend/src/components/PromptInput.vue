<template>
  <div class="prompt-input">
    <el-form>
      <el-form-item label="Prompt">
        <el-input
          v-model="prompt"
          type="textarea"
          :rows="4"
          placeholder="请输入图片生成的提示词..."
          :disabled="loading"
        />
      </el-form-item>
      
      <el-form-item>
        <el-button 
          type="primary" 
          @click="handleGenerate"
          :loading="loading"
          :disabled="!prompt.trim()"
          size="large"
        >
          <el-icon><MagicStick /></el-icon>
          {{ loading ? '生成中...' : '生成图片' }}
        </el-button>
      </el-form-item>
    </el-form>
    
    <!-- 提示信息 -->
    <el-alert
      title="提示"
      type="info"
      :closable="false"
      show-icon
    >
      <p>请描述你希望如何修改或生成图片，例如：</p>
      <ul>
        <li>"将这张图片变成卡通风格"</li>
        <li>"添加阳光明媚的背景"</li>
        <li>"让图片更加生动有趣"</li>
      </ul>
    </el-alert>
  </div>
</template>

<script>
import { ref, watch } from 'vue'
import { MagicStick } from '@element-plus/icons-vue'

export default {
  name: 'PromptInput',
  props: {
    prompt: {
      type: String,
      default: ''
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:prompt', 'generate'],
  components: {
    MagicStick
  },
  setup(props, { emit }) {
    const prompt = ref(props.prompt)

    const handleGenerate = () => {
      if (prompt.value.trim()) {
        emit('generate')
      }
    }

    // 监听prompt变化
    watch(prompt, (newValue) => {
      emit('update:prompt', newValue)
    })

    // 监听props变化
    watch(() => props.prompt, (newValue) => {
      prompt.value = newValue
    })

    return {
      prompt,
      handleGenerate
    }
  }
}
</script>

<style scoped>
.prompt-input {
  text-align: left;
}

.el-form-item {
  margin-bottom: 20px;
}

.el-button {
  width: 100%;
}

.el-alert {
  margin-top: 20px;
  text-align: left;
}

.el-alert ul {
  margin: 10px 0 0 0;
  padding-left: 20px;
}

.el-alert li {
  margin: 5px 0;
  font-size: 14px;
}
</style>
