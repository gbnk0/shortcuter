<template>
  <header class="topbar">
    <div>
      <span class="rubrique">{{ page.rubrique }}</span>
      <h1>{{ currentPage.title }}</h1>
      <p>{{ subtitle }}</p>
    </div>
    <div class="top-actions">
      <div class="view-tabs" role="tablist" aria-label="Views">
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
      <button class="icon-button" type="button" :title="themeTitle" @click="$emit('toggle-theme')">
        <i :class="['mdi', theme === 'dark' ? 'mdi-weather-sunny' : 'mdi-weather-night']"></i>
      </button>
      <button class="icon-button" type="button" :title="compactTitle" @click="$emit('toggle-compact-view')">
        <i :class="['mdi', compactView ? 'mdi-view-agenda-outline' : 'mdi-view-compact-outline']"></i>
      </button>
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
  theme: {
    type: String,
    required: true,
  },
  themeTitle: {
    type: String,
    required: true,
  },
  compactTitle: {
    type: String,
    required: true,
  },
  compactView: {
    type: Boolean,
    required: true,
  },
})

defineEmits(['select-page', 'toggle-compact-view', 'toggle-theme'])

function tabStyle(item) {
  const accent = normalizeAccent(item.accent || props.page.accent)
  return {
    '--tab-accent': accent,
    '--tab-accent-soft': `${accent}22`,
  }
}
</script>
