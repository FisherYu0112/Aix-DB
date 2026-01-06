<script setup>
import { h } from 'vue'
import * as GlobalAPI from '@/api'

const props = defineProps({
  show: Boolean,
})

const emit = defineEmits(['update:show', 'delete'])

const localShow = ref(props.show)
const tableData = ref([])
const columns = ref([
  {
    type: 'selection',
  },
  {
    title: '用户问题',
    key: 'question',
    ellipsis: true,
    render(row) {
      const questionText = row.question || row.key || '无标题'
      return h('div', { class: 'flex items-center gap-2' }, [
        h('div', { class: 'i-hugeicons:comment-01 text-20 text-indigo-500' }),
        h('span', {
          style: {
            fontSize: '15px',
            fontWeight: '500',
            color: 'red', // gray-700
            lineHeight: '1.4',
            wordBreak: 'break-word',
          },
        }, questionText),
      ])
    },
  },
  {
    title: '创建时间',
    key: 'create_time',
    width: 200, // Increased width
    render(row) {
      // Fallback for create_time if it's missing or named differently
      const timeText = row.create_time || '刚刚'
      return h('div', { class: 'flex items-center gap-2 text-gray-500' }, [
        h('div', { class: 'i-hugeicons:time-01 text-16' }), // Increased icon size
        h('span', { class: 'text-14' }, timeText), // Increased text size
      ])
    },
  },
])
const loading = ref(false)
const checkedRowKeys = ref([])

// 分页配置
const pagination = ref({
  page: 1,
  pageSize: 8,
  total: 0, // 总记录数
  pageCount: 0, // 总页数
  onChange: (page) => handlePageChange(page),
  onUpdatePageSize: (pageSize) => handlePageSizeChange(pageSize),
})

async function fetchData() {
  loading.value = true
  try {
    const res = await GlobalAPI.query_user_qa_record(
      pagination.value.page,
      pagination.value.pageSize,
    )
    if (res.ok) {
      const data = await res.json()
      if (data && data.data) {
        tableData.value = data.data.records || []
        pagination.value.total = data.data.total_count || 0
        pagination.value.pageCount = data.data.total_pages || 0
      } else {
        console.error('Unexpected data format:', data)
        tableData.value = []
        pagination.value.total = 0
        pagination.value.pageCount = 0
      }
    } else {
      console.error('API request failed with status:', res.status)
      tableData.value = []
      pagination.value.total = 0
      pagination.value.pageCount = 0
    }
  } catch (error) {
    console.error('Error fetching data:', error)
    tableData.value = []
    pagination.value.total = 0
    pagination.value.pageCount = 0
  } finally {
    loading.value = false
  }
}
function close() {
  localShow.value = false
  emit('update:show', false)
  pagination.value.page = 1
}

const rowKey = (row) => row.chat_id

function handleCheck(rowKeys) {
  checkedRowKeys.value = rowKeys
}

async function deleteSelectedData() {
  if (checkedRowKeys.value.length === 0) {
    return
  }
  const res = await GlobalAPI.delete_user_record(checkedRowKeys.value)
  if (res.ok) {
    fetchData()
  }
}

function handlePageChange(page) {
  pagination.value.page = page
  fetchData()
}

function handlePageSizeChange(newPageSize) {
  pagination.value.pageSize = newPageSize
  pagination.value.page = 1 // 重置到第一页
  fetchData()
}

const modalTitle = computed(
  () => `管理对话记录 · 共${pagination.value.total}条`,
)

watch(
  () => props.show,
  (newVal) => {
    if (newVal !== localShow.value) {
      localShow.value = newVal
      if (newVal) {
        fetchData()
      }
    }
  },
)

const tableRef = useTemplateRef('tableRef')
</script>

<template>
  <n-modal
    v-model:show="localShow"
    :mask-closable="false"
    :on-after-leave="close"
    preset="card"
    :title="modalTitle"
    class="custom-modal w-[900px] h-[650px] flex flex-col rounded-2xl overflow-hidden shadow-xl"
    :header-style="{ padding: '20px 24px', borderBottom: '1px solid #f3f4f6' }"
    :content-style="{ padding: 0, flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }"
    :bordered="false"
  >
    <!-- Modal Header Customization -->
    <!-- Removed manual header-extra as n-modal usually provides a close button by default with preset='card'.
         If duplication occurs, we should let the preset handle it or hide the preset one.
         Since user said 'two icons', we likely added one manually while the preset added another.
         We'll remove our manual one here. -->

    <div class="modal-content flex-1 flex flex-col min-h-0 bg-[#f9f9fb]">
      <n-spin :show="loading" class="flex-1 overflow-hidden flex flex-col">
        <div class="p-4 flex-1 overflow-auto">
             <n-data-table
              ref="tableRef"
              :data="tableData"
              :columns="columns"
              :row-key="rowKey"
              :checked-row-keys="checkedRowKeys"
              :single-line="false"
              class="custom-table"
              :row-class-name="() => 'custom-row'"
              @update:checked-row-keys="handleCheck"
            />
        </div>
      </n-spin>

      <div class="footer px-6 py-4 bg-white border-t border-gray-100 flex justify-between items-center">
        <n-pagination
          v-model:page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-count="pagination.pageCount"
          :page-size="pagination.pageSize"
          :display-order="['pages', 'quick-jumper']"
          size="medium"
          @update:page="handlePageChange"
          @update:page-size="handlePageSizeChange"
        >
          <template #prev>
            <div class="flex items-center gap-1 text-gray-500">
              <div class="i-hugeicons:arrow-left-01 text-14"></div>
            </div>
          </template>
          <template #next>
            <div class="flex items-center gap-1 text-gray-500">
              <div class="i-hugeicons:arrow-right-01 text-14"></div>
            </div>
          </template>
        </n-pagination>

        <div class="flex items-center gap-3">
          <button
            class="px-6 py-2.5 rounded-lg bg-red-50 text-red-600 hover:bg-red-100 transition-colors font-medium text-15 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm hover:shadow"
            :disabled="checkedRowKeys.length === 0"
            @click="deleteSelectedData"
          >
            <div class="i-hugeicons:delete-02 text-18"></div>
            <span>删除所选</span>
          </button>
        </div>
      </div>
    </div>
  </n-modal>
</template>

<style scoped lang="scss">
/* Modal Customization */

:deep(.n-modal-body-wrapper) {
  padding: 0 !important;
}

/* Table Customization */

:deep(.n-data-table) {
  --n-th-font-weight: 600 !important;
  --n-th-text-color: #666 !important;

  background-color: transparent !important;
}

:deep(.n-data-table .n-data-table-th) {
  background-color: transparent !important;
  border-bottom: 1px solid #e5e7eb !important;
  font-size: 13px;
  padding: 12px 16px;
  color: #666; /* Ensure header text is visible */
}

:deep(.n-data-table .n-data-table-td) {
    background-color: #fff !important;
    border-bottom: 1px solid #f3f4f6 !important;
    padding: 16px;
    color: #333 !important;
    font-size: 14px;
}

:deep(.n-data-table .n-data-table-tr:hover .n-data-table-td) {
  background-color: #fff !important;
}

/* Row Hover Effect */

:deep(.custom-row) {
  transition: all 0.2s;

  &:hover {
    background-color: #f9fafb !important;

    td {
      background-color: #f9fafb !important;
    }
  }
}

/* Pagination Customization */

:deep(.n-pagination .n-pagination-item) {
  border: 1px solid transparent;
  border-radius: 8px;

  &.n-pagination-item--active {
    background-color: #f3f4f6;
    color: #333;
    border-color: #e5e7eb;
  }

  &:hover:not(.n-pagination-item--active) {
    background-color: #f9fafb;
    color: #6366f1;
  }
}
</style>
