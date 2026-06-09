<template>
  <footer class="app-footer">
    <span>{{ labels.version }} {{ version }}</span>
    <button type="button" @click="$emit('toggle-icons-view')">
      {{ activeView === 'icons' ? labels.backToShortcuts : labels.yamlIconCatalog }}
    </button>
    <a href="https://github.com/gbnk0/shortcuter" target="_blank" rel="noreferrer">GitHub</a>
  </footer>
</template>

<script setup>
defineProps({
  activeView: {
    type: String,
    required: true,
  },
  version: {
    type: String,
    required: true,
  },
  labels: {
    type: Object,
    required: true,
  },
})

defineEmits(['toggle-icons-view'])
</script>
