<template>
  <article class="shortcut-card" @mouseenter="prepareDescriptionScroll">
    <a class="shortcut-link" :href="shortcut.url" target="_blank" rel="noopener noreferrer">
      <span class="shortcut-icon">
        <img v-if="shortcut.icon_type !== 'preset' && shortcut.icon_value" :src="iconUrl" alt="" @error="hideBrokenImage" />
        <i v-else :class="['mdi', shortcut.icon_value || 'mdi-web']"></i>
        <span
          v-if="shortcut.badge?.icon"
          class="shortcut-badge"
          :title="shortcut.badge.tooltip || shortcut.badge.icon"
          :aria-label="shortcut.badge.tooltip || shortcut.badge.icon"
        >
          <i :class="['mdi', shortcut.badge.icon]"></i>
        </span>
      </span>
      <span class="shortcut-text">
        <strong>{{ shortcut.name }}</strong>
        <small class="shortcut-description">
          <span>{{ shortcut.description || displayHost(shortcut.url) }}</span>
        </small>
      </span>
      <i class="mdi mdi-open-in-new open-icon"></i>
    </a>
  </article>
</template>

<script setup>
import { computed } from 'vue'
import { displayHost, iconSource } from '../utils/shortcuts'

const props = defineProps({
  builtinIcons: {
    type: Array,
    default: () => [],
  },
  shortcut: {
    type: Object,
    required: true,
  },
})

const iconUrl = computed(() => iconSource(props.shortcut, props.builtinIcons))

function hideBrokenImage(event) {
  event.target.style.display = 'none'
}

function prepareDescriptionScroll(event) {
  const description = event.currentTarget.querySelector('.shortcut-description')
  const track = description?.querySelector('span')
  if (!description || !track) {
    return
  }
  const overflow = track.scrollWidth - description.clientWidth
  description.classList.toggle('scrollable', overflow > 0)
  description.style.setProperty('--scroll-distance', overflow > 0 ? `-${overflow}px` : '0px')
}
</script>
