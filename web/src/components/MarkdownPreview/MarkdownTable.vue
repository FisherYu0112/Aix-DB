<template>
  <div style="background-color: #fff">
    <n-card
      title="表格"
      embedded
      bordered
      :content-style="{ 'background-color': '#ffffff' }"
      :header-style="{
        color: '#26244c',
        height: '10px',
        'background-color': '#f0effe',
        'text-align': 'left',
        'font-size': '14px',
        'font-family': 'PMingLiU'
      }"
      :footer-style="{
        color: '#666',
        'background-color': '#ffffff',
        'text-align': 'left',
        'font-size': '14px',
        'font-family': 'PMingLiU'
      }"
    >
      <div flex="~ space-between" mb-10></div>
      <n-data-table
        :columns="columns"
        :data="data"
        :pagination="pagination"
      />
      <template #footer>
        数据来源: 大模型生成的数据, 以上信息仅供参考
      </template>
    </n-card>
  </div>
</template>

<script lang="ts" setup>
import { computed, onMounted, ref } from 'vue'
import type { DataTableColumns, DataTableRowKey } from 'naive-ui'
import { useBusinessStore } from '@/store/business'

// 定义 emit
const emit = defineEmits<{
  (e: 'tableRendered'): void
}>()

// 使用 store
const businessStore = useBusinessStore()

// 响应式数据：从 store 获取表格数据
const tableData = ref<RowData[]>(
  businessStore.writerList.data?.data || []
)

// 类型定义
interface RowData {
  [key: string]: any // 动态字段支持，如 name, age, address 等
  key?: DataTableRowKey
}

// 动态生成列（响应式）
const columns = computed<DataTableColumns<RowData>>(() => {
  const firstRow = tableData.value[0]
  if (!firstRow) return []

  return Object.keys(firstRow).map(key => ({
    title: key,
    key,
    width: 120,
    render(row: RowData) {
      return row[key] ?? ''
    }
  }))
})

// 使用 computed 保持数据响应性
const data = computed(() => tableData.value)

// 分页配置
const pagination = ref({
  page: 1,
  pageSize: 6,
  showSizePicker: true,
  pageSizes: [3, 5, 7],
  onChange: (page: number) => {
    pagination.value.page = page
  },
  onUpdatePageSize: (pageSize: number) => {
    pagination.value.pageSize = pageSize
    pagination.value.page = 1
  }
})

// 组件挂载后触发事件并可选清空 store
onMounted(() => {
  emit('tableRendered')
  // 可按需保留或清除
  businessStore.clearWriterList()
})
</script>

<style scoped>
/* 可添加样式 */
</style>