<template>
  <section class="search-band">
    <i class="mdi mdi-magnify"></i>
    <input
      ref="inputRef"
      :value="modelValue"
      type="search"
      :placeholder="placeholder"
      :autofocus="autofocus"
      @input="$emit('update:modelValue', $event.target.value.trim())"
    />
    <button v-if="modelValue" class="clear-search" type="button" :title="clearTitle" @click="$emit('update:modelValue', '')">
      <i class="mdi mdi-close"></i>
    </button>
  </section>
</template>

<script setup>
import { nextTick, onMounted, ref, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: '',
  },
  placeholder: {
    type: String,
    default: 'Search',
  },
  autofocus: {
    type: Boolean,
    default: false,
  },
  focusKey: {
    type: [String, Number],
    default: '',
  },
  clearTitle: {
    type: String,
    default: 'Clear search',
  },
})

defineEmits(['update:modelValue'])

const inputRef = ref(null)

async function focusInput() {
  if (!props.autofocus) {
    return
  }
  await nextTick()
  inputRef.value?.focus()
}

onMounted(focusInput)
watch(() => props.autofocus, focusInput)
watch(() => props.focusKey, focusInput)
</script>
