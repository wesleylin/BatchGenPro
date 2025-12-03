<template>
  <el-dialog
    v-model="visible"
    :title="isLogin ? '登录' : '注册'"
    width="400px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="80px"
    >
      <el-form-item label="邮箱" prop="email">
        <el-input
          v-model="form.email"
          placeholder="请输入邮箱"
          type="email"
        />
      </el-form-item>
      
      <el-form-item label="密码" prop="password">
        <el-input
          v-model="form.password"
          type="password"
          placeholder="请输入密码（至少6位）"
          show-password
          @keyup.enter="handleSubmit"
        />
      </el-form-item>
      
      <el-form-item v-if="!isLogin" label="用户名" prop="username">
        <el-input
          v-model="form.username"
          placeholder="请输入用户名（可选）"
        />
      </el-form-item>
    </el-form>
    
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button
          type="primary"
          :loading="loading"
          @click="handleSubmit"
        >
          {{ isLogin ? '登录' : '注册' }}
        </el-button>
      </div>
      <div class="switch-tip">
        <span v-if="isLogin">
          还没有账号？
          <el-link type="primary" @click="switchToRegister">立即注册</el-link>
        </span>
        <span v-else>
          已有账号？
          <el-link type="primary" @click="switchToLogin">立即登录</el-link>
        </span>
      </div>
    </template>
  </el-dialog>
</template>

<script>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

export default {
  name: 'AuthDialog',
  props: {
    modelValue: {
      type: Boolean,
      default: false
    },
    defaultMode: {
      type: String,
      default: 'login' // 'login' 或 'register'
    }
  },
  emits: ['update:modelValue', 'success'],
  setup(props, { emit }) {
    const visible = ref(props.modelValue)
    const isLogin = ref(props.defaultMode === 'login')
    const loading = ref(false)
    const formRef = ref(null)
    
    const form = reactive({
      email: '',
      password: '',
      username: ''
    })
    
    const rules = {
      email: [
        { required: true, message: '请输入邮箱', trigger: 'blur' },
        { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
      ],
      password: [
        { required: true, message: '请输入密码', trigger: 'blur' },
        { min: 6, message: '密码长度至少6位', trigger: 'blur' }
      ]
    }
    
    const switchToLogin = () => {
      isLogin.value = true
      form.username = ''
    }
    
    const switchToRegister = () => {
      isLogin.value = false
    }
    
    const handleClose = () => {
      visible.value = false
      emit('update:modelValue', false)
      // 重置表单
      form.email = ''
      form.password = ''
      form.username = ''
      if (formRef.value) {
        formRef.value.resetFields()
      }
    }
    
    const handleSubmit = async () => {
      if (!formRef.value) return
      
      await formRef.value.validate(async (valid) => {
        if (!valid) return
        
        loading.value = true
        try {
          const url = isLogin.value ? '/api/auth/login' : '/api/auth/register'
          const response = await axios.post(url, {
            email: form.email,
            password: form.password,
            username: form.username || undefined
          })
          
          if (response.data.success) {
            // 保存 token 和用户信息
            const token = response.data.token
            const user = response.data.user
            
            localStorage.setItem('auth_token', token)
            localStorage.setItem('user_info', JSON.stringify(user))
            
            ElMessage.success(isLogin.value ? '登录成功' : '注册成功')
            emit('success', { user, token })
            handleClose()
          } else {
            ElMessage.error(response.data.error || '操作失败')
          }
        } catch (error) {
          console.error('Auth error:', error)
          const errorMsg = error.response?.data?.error || error.message || '操作失败'
          ElMessage.error(errorMsg)
        } finally {
          loading.value = false
        }
      })
    }
    
    // 监听 modelValue 变化
    const updateVisible = (newVal) => {
      visible.value = newVal
      if (newVal) {
        // 打开对话框时重置表单
        form.email = ''
        form.password = ''
        form.username = ''
        isLogin.value = props.defaultMode === 'login'
      }
    }
    
    return {
      visible,
      isLogin,
      loading,
      formRef,
      form,
      rules,
      switchToLogin,
      switchToRegister,
      handleClose,
      handleSubmit,
      updateVisible
    }
  },
  watch: {
    modelValue(newVal) {
      this.visible = newVal
      if (newVal) {
        this.isLogin = this.defaultMode === 'login'
        this.form.email = ''
        this.form.password = ''
        this.form.username = ''
        if (this.formRef) {
          this.formRef.resetFields()
        }
      }
    },
    visible(newVal) {
      this.$emit('update:modelValue', newVal)
    }
  }
}
</script>

<style scoped>
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.switch-tip {
  margin-top: 10px;
  text-align: center;
  font-size: 14px;
  color: #666;
}

.switch-tip .el-link {
  margin-left: 5px;
}
</style>


