<template>
  <header class="topbar">
    <div class="page-title">
      <h1>{{ currentPage.title }}</h1>
      <p>{{ subtitle }}</p>
    </div>
    <div class="top-actions">
      <div class="view-tabs" role="tablist" :aria-label="viewsLabel">
        <button
          v-for="item in pages"
          :key="item.id"
          type="button"
          :class="{ active: activeView === 'shortcuts' && activePage === item.id }"
          :style="tabStyle(item)"
          @click="$emit('select-page', item.id)"
        >
          <span>{{ item.title }}</span>
        </button>
      </div>
    </div>
  </header>
</template>

<script setup>
import { normalizeAccent } from '../utils/accent'

const props = defineProps({
  activePage: {
    type: String,
    required: true,
  },
  activeView: {
    type: String,
    required: true,
  },
  currentPage: {
    type: Object,
    required: true,
  },
  page: {
    type: Object,
    required: true,
  },
  pages: {
    type: Array,
    required: true,
  },
  subtitle: {
    type: String,
    required: true,
  },
  viewsLabel: {
    type: String,
    required: true,
  },
})

defineEmits(['select-page'])

function tabStyle(item) {
  const accent = normalizeAccent(item.accent || props.page.accent)
  return {
    '--tab-accent': accent,
    '--tab-accent-soft': `${accent}22`,
  }
}
</script>
