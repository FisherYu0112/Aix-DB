<script lang="ts" setup>
import type { FormInst } from 'naive-ui'
import { useMessage } from 'naive-ui'
import { computed, ref, watch } from 'vue'
import { authorize_datasource, get_authorized_users } from '@/api/datasource'
import { queryUserList } from '@/api/user'

interface Props {
  show: boolean
  datasourceId: number | null
  datasourceName?: string
}

interface Emits {
  (e: 'update:show', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const message = useMessage()
const formRef = ref<FormInst | null>(null)

const loading = ref(false)
const userList = ref<any[]>([])
const selectedUserIds = ref<number[]>([])
const searchKeyword = ref('')

// 计算属性：显示的用户列表（过滤管理员，并根据搜索关键词过滤）
const filteredUserList = computed(() => {
  // 先过滤掉管理员
  let users = userList.value.filter((user) => user.role !== 'admin')
  
  // 再根据搜索关键词过滤（前端过滤）
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    users = users.filter((user) =>
      user.userName?.toLowerCase().includes(keyword) ||
      user.mobile?.includes(keyword)
    )
  }
  
  return users
})

// 获取用户列表（调用后端接口，获取所有用户）
const fetchUserList = async () => {
  loading.value = true
  try {
    // 获取所有用户（使用大的 pageSize）
    const res = await queryUserList(1, 1000)
    const result = await res.json()
    if (result.code === 200) {
      userList.value = result.data.records || []
    } else {
      message.error(result.msg || '获取用户列表失败')
    }
  } catch (error) {
    console.error('获取用户列表失败:', error)
    message.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

// 获取已授权用户列表
const fetchAuthorizedUsers = async () => {
  if (!props.datasourceId) {
    return
  }
  try {
    const res = await get_authorized_users(props.datasourceId)
    const result = await res.json()
    if (result.code === 200) {
      // 设置已授权的用户ID为选中状态
      selectedUserIds.value = result.data || []
    } else {
      console.error('获取已授权用户失败:', result.msg)
    }
  } catch (error) {
    console.error('获取已授权用户失败:', error)
  }
}

// 监听弹框显示状态，当打开时调用接口
watch(
  () => props.show,
  (newVal) => {
    if (newVal) {
      // 重置状态
      searchKeyword.value = ''
      selectedUserIds.value = []
      // 先获取用户列表，再获取已授权用户
      fetchUserList().then(() => {
        fetchAuthorizedUsers()
      })
    }
  },
)

// 处理授权
const handleSubmit = async () => {
  if (!props.datasourceId) {
    message.error('数据源ID不存在')
    return
  }

  loading.value = true
  try {
    const res = await authorize_datasource(props.datasourceId, selectedUserIds.value)
    const result = await res.json()
    if (result.code === 200) {
      message.success('授权成功')
      emit('success')
      handleClose()
    } else {
      message.error(result.msg || '授权失败')
    }
  } catch (error) {
    console.error('授权失败:', error)
    message.error('授权失败')
  } finally {
    loading.value = false
  }
}

// 关闭对话框
const handleClose = () => {
  selectedUserIds.value = []
  searchKeyword.value = ''
  emit('update:show', false)
}

// 监听显示状态
const showModal = computed({
  get: () => props.show,
  set: (value) => emit('update:show', value),
})
</script>

<template>
  <n-modal
    v-model:show="showModal"
    preset="card"
    size="large"
    style="width: 650px"
    :bordered="false"
    :segmented="true"
  >
    <template #header>
      <div class="modal-header">
        <div class="header-icon">
          <div class="i-hugeicons:user-check-02 text-24"></div>
        </div>
        <div class="header-content">
          <div class="header-title">
            数据源授权
          </div>
          <div
            v-if="datasourceName"
            class="header-subtitle"
          >
            {{ datasourceName }}
          </div>
        </div>
      </div>
    </template>

    <n-spin :show="loading">
      <div class="modal-body">
        <div class="search-section">
          <n-input
            v-model:value="searchKeyword"
            placeholder="搜索用户名或手机号..."
            clearable
            size="large"
          >
            <template #prefix>
              <div class="i-carbon-search text-18 text-gray-400" />
            </template>
          </n-input>
        </div>

        <div class="user-list-section">
          <n-scrollbar
            v-if="filteredUserList.length > 0"
            style="max-height: 420px;"
          >
            <div class="user-list">
              <n-checkbox-group
                v-model:value="selectedUserIds"
              >
                <div
                  v-for="user in filteredUserList"
                  :key="user.id"
                  class="user-item"
                  :class="{ 'user-item--selected': selectedUserIds.includes(user.id) }"
                  @click="
                    selectedUserIds.includes(user.id)
                      ? selectedUserIds.splice(selectedUserIds.indexOf(user.id), 1)
                      : selectedUserIds.push(user.id)
                  "
                >
                <div class="user-item-checkbox">
                  <n-checkbox :value="user.id" />
                </div>
                <div class="user-item-avatar">
                  <div class="i-hugeicons:user-circle text-24"></div>
                </div>
                <div class="user-item-info">
                  <div class="user-item-header">
                    <div class="user-item-name">
                      {{ user.userName }}
                    </div>
                    <n-tag
                      :type="selectedUserIds.includes(user.id) ? 'success' : 'default'"
                      size="small"
                      round
                    >
                      {{ selectedUserIds.includes(user.id) ? '已授权' : '未授权' }}
                    </n-tag>
                  </div>
                  <div class="user-item-mobile">
                    <div class="i-carbon-phone text-14"></div>
                    <span>{{ user.mobile || '未绑定' }}</span>
                  </div>
                </div>
                <div
                  v-if="selectedUserIds.includes(user.id)"
                  class="user-item-badge"
                >
                  <div class="i-carbon-checkmark-filled text-16"></div>
                </div>
              </div>
            </n-checkbox-group>
            </div>
          </n-scrollbar>
          <div
            v-else
            class="empty-state"
          >
            <div class="i-hugeicons:user-block text-48 text-gray-300"></div>
            <div class="empty-text">
              {{ searchKeyword ? '未找到匹配的用户' : '暂无可授权的用户' }}
            </div>
          </div>
        </div>
      </div>
    </n-spin>

    <template #footer>
      <div class="modal-footer">
        <div class="footer-info">
          <span>已选择</span>
          <n-badge
            :value="selectedUserIds.length"
            :max="99"
            type="info"
            show-zero
          />
          <span>位用户</span>
        </div>
        <div class="footer-actions">
          <n-button
            @click="handleClose"
          >
            取消
          </n-button>
          <n-button
            type="primary"
            :loading="loading"
            @click="handleSubmit"
          >
            <template #icon>
              <div class="i-carbon-checkmark text-16"></div>
            </template>
            {{ selectedUserIds.length === 0 ? '清空授权' : '确定授权' }}
          </n-button>
        </div>
      </div>
    </template>
  </n-modal>
</template>

<style lang="scss" scoped>
.modal-header {
  display: flex;
  align-items: center;
  gap: 12px;
  
  .header-icon {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    flex-shrink: 0;
  }
  
  .header-content {
    flex: 1;
    min-width: 0;
    
    .header-title {
      font-size: 18px;
      font-weight: 600;
      color: #1f2937;
      margin-bottom: 4px;
    }
    
    .header-subtitle {
      font-size: 14px;
      color: #6b7280;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }
}

.modal-body {
  .search-section {
    margin-bottom: 20px;
  }
  
  .user-list-section {
      .user-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
        padding: 4px;
      }
    
    .user-item {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 12px 16px;
      background: #fff;
      border: 2px solid #e5e7eb;
      border-radius: 10px;
      cursor: pointer;
      transition: all 0.2s ease;
      
      &:hover {
        border-color: #c7d2fe;
        background: #f8fafc;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
      }
      
      &--selected {
        border-color: #667eea;
        background: linear-gradient(135deg, #f0f4ff 0%, #e8efff 100%);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
      }
      
      .user-item-checkbox {
        flex-shrink: 0;
      }
      
      .user-item-avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        color: #6b7280;
        flex-shrink: 0;
      }
      
      .user-item--selected .user-item-avatar {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: #fff;
      }
      
      .user-item-info {
        flex: 1;
        min-width: 0;
        
        .user-item-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 4px;
          
          .user-item-name {
            font-size: 15px;
            font-weight: 500;
            color: #1f2937;
            flex: 1;
            min-width: 0;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }
        }
        
        .user-item-mobile {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 13px;
          color: #6b7280;
          
          .i-carbon-phone {
            opacity: 0.6;
          }
        }
      }
      
      .user-item-badge {
        width: 24px;
        height: 24px;
        border-radius: 50%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        color: #fff;
        flex-shrink: 0;
        animation: scaleIn 0.2s ease;
      }
    }
    
    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 60px 20px;
      text-align: center;
      
      .empty-text {
        margin-top: 16px;
        font-size: 14px;
        color: #9ca3af;
      }
    }
  }
}

.modal-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  .footer-info {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    color: #6b7280;
  }
  
  .footer-actions {
    display: flex;
    gap: 12px;
  }
}

@keyframes scaleIn {
  from {
    transform: scale(0);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}
</style>
