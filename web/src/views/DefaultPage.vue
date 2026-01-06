<script lang="ts" setup>
import { ref } from 'vue'

const emit = defineEmits(['submit'])

const inputValue = ref('')
const selectedMode = ref<{ label: string, value: string, icon: string, color: string } | null>(null)

const handleEnter = (e?: KeyboardEvent) => {
  if (e && e.shiftKey) {
    return
  }
  if (!inputValue.value.trim()) {
    return
  }

  emit('submit', {
    text: inputValue.value,
    mode: selectedMode.value?.value || 'COMMON_QA', // Default to Smart QA if nothing selected
  })
  inputValue.value = ''
}

const chips = [
  { icon: 'i-hugeicons:ai-chat-02', label: '智能问答', value: 'COMMON_QA', color: '#3b82f6' },
  { icon: 'i-hugeicons:database-01', label: '数据问答', value: 'DATABASE_QA', color: '#10b981' },
  { icon: 'i-hugeicons:table-01', label: '表格问答', value: 'FILEDATA_QA', color: '#f59e0b' },
  { icon: 'i-hugeicons:search-02', label: '深度搜索', value: 'REPORT_QA', color: '#8b5cf6' },
]

const handleChipClick = (chip: typeof chips[0]) => {
  selectedMode.value = chip
}

const clearMode = () => {
  selectedMode.value = null
}
</script>

<template>
  <div class="default-page-container">
    <div class="content-wrapper">
      <!-- Title -->
      <div class="header-section">
        <h1 class="page-title">
          Aix · 智能助手
        </h1>
      </div>

      <!-- Search Box -->
      <div class="search-box">
        <!-- Input Area Wrapper to handle pill -->
        <div class="input-wrapper">
          <!-- Selected Mode Pill -->
          <div
            v-if="selectedMode"
            class="mode-pill"
            :style="{ color: selectedMode.color, backgroundColor: `${selectedMode.color}15` }"
          >
            <div
              :class="selectedMode.icon"
              class="pill-icon"
            ></div>
            <span>{{ selectedMode.label }}</span>
            <div
              class="i-hugeicons:cancel-01 close-icon"
              @click.stop="clearMode"
            ></div>
          </div>

          <!-- Input Area -->
          <n-input
            v-model:value="inputValue"
            type="textarea"
            placeholder="帮你完成复杂任务，并生成研究报告"
            :autosize="{ minRows: 1, maxRows: 6 }"
            class="custom-input"
            @keydown.enter.prevent="handleEnter"
          />
        </div>

        <!-- Chips and Actions Row -->
        <div class="bottom-row">
          <!-- Show chips only if no mode is selected (optional, or keep them to allow switching)
                 Based on Image 1, the chip is inside. The user said "Click specific function style becomes B style".
                 So maybe we hide the bottom chips if one is selected? Or keep them?
                 Let's keep them for easy switching, but visually maybe dim them?
                 Actually, usually these UIs hide the suggestions once you start typing or select one.
                 But for now let's just keep them below for accessibility.
            -->
          <div
            v-if="!selectedMode"
            class="chips-container"
          >
            <div
              v-for="chip in chips"
              :key="chip.label"
              class="chip"
              @click="handleChipClick(chip)"
            >
              <div
                :class="chip.icon"
                class="chip-icon"
                :style="{ color: chip.color }"
              ></div>
              {{ chip.label }}
            </div>
          </div>
          <div
            v-else
            class="chips-container"
          >
            <!-- Placeholder to keep layout stable or show nothing -->
          </div>

          <div class="actions-container">
            <!-- Send Button -->
            <div
              class="send-button"
              @click="handleEnter"
            >
              <div class="i-hugeicons:arrow-up-01 send-icon"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Bottom Icons -->
      <div class="features-row">
        <div
          v-for="item in bottomIcons"
          :key="item.label"
          class="feature-item"
        >
          <div
            class="feature-icon-wrapper"
            :style="{ color: item.color }"
          >
            <div
              :class="item.icon"
              class="feature-icon"
            ></div>
          </div>
          <span class="feature-label">{{ item.label }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.default-page-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  width: 100%;
  background-color: #fff;
}

.content-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  max-width: 800px;
  padding: 0 20px;
}

.header-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 40px;
}

.logo-wrapper {
  margin-bottom: 16px;

  /* Add styling for the moon/astronaut graphic if we had one, for now use an icon */

  background: linear-gradient(135deg, #f0f4ff 0%, #e6eaff 100%);
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.page-title {
  font-size: 32px;
  font-weight: 600;
  color: #26244c;
  letter-spacing: 2px;
  margin: 0;
}

.search-box {
  width: 100%;
  background-color: #fff;
  border-radius: 24px;
  box-shadow: 0 4px 20px rgb(0 0 0 / 5%);
  border: 1px solid #e5e7eb;
  padding: 20px;
  position: relative;
  transition: all 0.3s ease;

  &:hover {
    box-shadow: 0 8px 30px rgb(0 0 0 / 8%);
  }
}

.input-wrapper {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 16px;
  min-height: 40px;
}

.mode-pill {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  user-select: none;
  flex-shrink: 0;
  margin-top: 4px; /* Align with input text */
}

.pill-icon {
  font-size: 14px;
}

.close-icon {
  font-size: 12px;
  cursor: pointer;
  opacity: 0.6;

  &:hover {
    opacity: 1;
  }
}

.custom-input {
  --n-border: none !important;
  --n-border-hover: none !important;
  --n-border-focus: none !important;
  --n-box-shadow: none !important;
  --n-box-shadow-focus: none !important;

  background-color: transparent !important;
  font-size: 16px;
  padding: 0;
  flex: 1;

  :deep(.n-input__textarea-el) {
    padding: 0;
    min-height: 40px;
    line-height: 1.6;
  }

  :deep(.n-input__placeholder) {
    color: #9ca3af;
  }
}

.bottom-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  min-height: 36px;
}

.chips-container {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.chip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background-color: #f8fafc;
  border-radius: 100px;
  font-size: 13px;
  color: #475569;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;

  &:hover {
    background-color: #fff;
    border-color: #e2e8f0;
    box-shadow: 0 2px 4px rgb(0 0 0 / 5%);
  }
}

.chip-icon {
  font-size: 16px;
}

.actions-container {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: auto;
}

.send-button {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-color: #c4b5fd; /* Light Purple/Lavender as in Image 1 */
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  color: #fff;

  &:hover {
    background-color: #a78bfa;
    transform: scale(1.05);
  }

  &:active {
    transform: scale(0.95);
  }
}

.send-icon {
  font-size: 20px;
}

.features-row {
  display: flex;
  gap: 40px;
  margin-top: 80px;
  justify-content: center;
}

.feature-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: transform 0.2s;

  &:hover {
    transform: translateY(-2px);
  }
}

.feature-icon-wrapper {
  width: 48px;
  height: 48px;
  border-radius: 16px;
  background-color: #f9fafb;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s;

  .feature-item:hover & {
    background-color: #f3f4f6;
  }
}

.feature-icon {
  font-size: 24px;
}

.feature-label {
  font-size: 12px;
  color: #6b7280;
}
</style>
