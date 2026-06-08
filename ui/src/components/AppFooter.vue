<template>
  <footer class="app-footer">
    <span>Version {{ version }}</span>
    <button type="button" @click="$emit('toggle-icons-view')">
      {{ activeView === 'icons' ? 'Back to shortcuts' : 'YAML icon catalog' }}
    </button>
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
})

defineEmits(['toggle-icons-view'])
</script>
