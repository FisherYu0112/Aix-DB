<template>
  <div class="white-nowrap">
    <div
      class="filed"
      :style="computedWidth"
      @mouseover="showDel = true"
      @mouseleave="showDel = false"
    >
      <n-select
        v-model:value="activeNameId"
        filterable
        placeholder="Conditional Filtering"
        style="width: 200px"
        :options="dimensionOptions"
        @update:value="selectItem"
      />
      <template v-if="item.field_id">
        <n-select
          v-model:value="item.filter_type"
          style="width: 120px; margin-left: 8px"
          placeholder="Filter Type"
          :options="filterList"
          @update:value="filterTypeChange"
        />
        <n-select
          v-if="['null', 'not_null', 'empty', 'not_empty'].includes(item.term)"
          v-model:value="item.term"
          style="width: 280px; margin-left: 8px"
          placeholder="Please Select"
          :options="operators"
        />
        <div v-else style="display: flex; margin-left: 8px; width: 280px;">
           <n-input-group>
              <n-select
                  v-model:value="item.term"
                  style="width: 100px"
                  placeholder="Select"
                  :options="operators"
                />
              <n-input
                v-model:value="item.value"
                style="flex: 1"
                placeholder="Please Enter"
                clearable
              />
           </n-input-group>
        </div>
      </template>
      <n-icon v-if="showDel" class="font16" @click="emits('del')">
        <Trash />
      </n-icon>
    </div>
  </div>
</template>

<script lang="ts">
export interface Item {
  term: string
  field_id: string
  filter_type: string
  enum_value: string
  name: string
  value: any
}
</script>

<script lang="ts" setup>
import {
  NIcon,
  NInput,
  NInputGroup,
  NSelect,
} from 'naive-ui'
import { computed, inject, onBeforeMount, watch, nextTick, ref, toRefs, type Ref } from 'vue'
import { allOptions } from '../options'
import Trash from '~icons/material-symbols/delete-outline'

export interface sysVariable {
  label: string
  value: string
  type: string
}

type Props = {
  index: number
  item: Item
}

const props = withDefaults(defineProps<Props>(), {
  index: 0,
  item: () => ({
    term: '',
    field_id: '',
    filter_type: '',
    enum_value: '',
    name: '',
    value: null,
  }) as Item,
})

const t = (key: string, args?: any) => {
  const map: Record<string, string> = {
    'permission.conditional_filtering': '条件过滤',
    'common.empty': '为空',
    'common.not_empty': '不为空',
    'common.is_null': '为空值',
    'common.is_not_null': '不为空值',
    'common.equal': '等于',
    'common.not_equal': '不等于',
    'common.contain': '包含',
    'common.not_contain': '不包含',
    'common.start_with': '开头是',
    'common.end_with': '结尾是',
    'common.gt': '大于',
    'common.lt': '小于',
    'common.ge': '大于等于',
    'common.le': '小于等于',
  }
  let text = map[key] || key
  if (args) {
    Object.keys(args).forEach(k => {
      text = text.replace(`{${k}}`, args[k])
    })
  }
  return text
}
const showDel = ref(false)
const keywords = ref('')
const activeNameId = ref<string | null>(null)
const checklist = ref<string[]>([])
const filterList = ref<any[]>([])

const { item } = toRefs(props)

const filedList = inject('filedList') as Ref<any[]>

const computedWidth = computed(() => {
  const { field_id } = item.value
  return {
    width: !field_id ? '270px' : '670px',
  }
})

const operators = computed(() => {
  return allOptions.map(opt => ({
      value: opt.value,
      label: t(opt.label) !== opt.label ? t(opt.label) : opt.value // Fallback if no translation
  }))
})

const computedFiledList = computed<any[]>(() => {
  return filedList.value || []
})

const dimensions = computed(() => {
  if (!keywords.value) return computedFiledList.value
  return computedFiledList.value.filter((ele) => {
    const searchText = keywords.value.toLowerCase()
    const fieldName = (ele.field_name || '').toLowerCase()
    const fieldComment = (ele.field_comment || '').toLowerCase()
    return fieldName.includes(searchText) || fieldComment.includes(searchText)
  })
})

const dimensionOptions = computed(() => {
    return dimensions.value.map(ele => ({
        // 优先使用中文注释（field_comment），如果没有则使用字段名（field_name）
        label: ele.field_comment || ele.field_name || String(ele.id),
        // 统一使用字符串类型，确保与 activeNameId 的类型匹配
        value: String(ele.id)
    }))
})

onBeforeMount(() => {
  initNameEnumName()
  filterListInit()
})

// 监听 item.field_id 的变化，当编辑时重新初始化
watch(() => item.value.field_id, (newFieldId) => {
  if (newFieldId) {
    nextTick(() => {
      initNameEnumName()
    })
  }
}, { immediate: true })

// 监听 filedList 的变化，当字段列表加载完成后重新初始化
watch(() => filedList.value, (newList) => {
  if (newList && newList.length > 0 && item.value.field_id) {
    nextTick(() => {
      initNameEnumName()
    })
  }
}, { immediate: false, deep: false })

const initNameEnumName = () => {
  const { name, enum_value, field_id } = item.value
  
  // 如果 field_id 存在，尝试匹配并设置 activeNameId
  if (field_id) {
    // 统一转换为字符串进行比较和设置
    const fieldIdStr = String(field_id)
    
    // 检查 filedList 是否已加载，并且能找到对应的字段
    if (filedList.value && Array.isArray(filedList.value) && filedList.value.length > 0) {
      // 尝试多种方式匹配 field_id（处理数字和字符串类型）
      const foundField = filedList.value.find(ele => {
        if (!ele || ele.id === undefined) return false
        // 支持多种匹配方式：严格相等、字符串相等、数字相等
        return String(ele.id) === fieldIdStr || 
               ele.id === field_id || 
               ele.id === Number(field_id) ||
               String(ele.id) === String(field_id)
      })
      
      if (foundField) {
        // 找到匹配的字段，设置 activeNameId（统一使用字符串类型）
        activeNameId.value = String(foundField.id)
        // 更新 item.name 为中文注释（如果存在）
        const chineseName = foundField.field_comment || foundField.field_name
        if (chineseName && (!item.value.name || item.value.name !== chineseName)) {
          item.value.name = chineseName
        }
      } else {
        // 如果找不到匹配的字段，仍然设置 activeNameId（可能字段列表还没完全加载或字段已被删除）
        activeNameId.value = fieldIdStr
      }
    } else {
      // filedList 还没加载，先设置 activeNameId
      activeNameId.value = fieldIdStr
    }
  } else {
    activeNameId.value = null
  }
  
  const arr = enum_value && enum_value.trim() ? enum_value.split(',') : []
  if (!name && field_id) {
    checklist.value = arr
  }
  if (!name && !field_id) return
  initEnumOptions()
  checklist.value = arr
}

const filterTypeChange = () => {
  item.value.term = ''
  item.value.value = null
  initEnumOptions()
}
const initEnumOptions = () => {
  console.info('initEnumOptions')
}

const selectItem = (id: any) => {
  // id 可能是字符串或数字，需要统一处理
  const idNum = typeof id === 'string' ? parseInt(id, 10) : id
  const selected = dimensions.value.find(ele => ele.id === idNum || String(ele.id) === String(id))
  if (selected) {
      Object.assign(item.value, {
        field_id: selected.id,
        name: selected.field_comment || selected.field_name, // 优先使用中文注释
        filter_type: 'logic',
        value: '',
        term: '',
      })
      filterListInit()
      checklist.value = []
  }
}

const filterListInit = () => {
  filterList.value = [
    {
      value: 'logic',
      label: t('permission.conditional_filtering'),
    },
  ]
}

const emits = defineEmits(['update:item', 'del'])
</script>

<style lang="scss" scoped>
.white-nowrap {
  white-space: nowrap;
}
.filed {
  height: 41.4px;
  padding: 1px 3px 1px 0;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  margin-left: 20px;
  min-width: 200px;
  justify-content: left;
  position: relative;
  white-space: nowrap;

  .filed-title {
    word-wrap: break-word;
    line-height: 28px;
    color: #7e7e7e;
    font-size: 14px;
    white-space: nowrap;
    box-sizing: border-box;
    margin-right: 5px;
    display: inline-block;
    min-width: 50px;
    text-align: right;
  }

  .font16 {
    font-size: 16px;
    margin: 0 10px;
    cursor: pointer;
  }
}
</style>
