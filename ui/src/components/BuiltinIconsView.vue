<template>
  <section class="builtin-icons-view">
    <div class="builtin-icons-header">
      <h2>Catalogue des icones</h2>
      <span>{{ filteredIcons.length }} / {{ icons.length }} icone{{ icons.length > 1 ? 's' : '' }}</span>
    </div>
    <SearchBar v-model="query" placeholder="Rechercher une icone" autofocus :focus-key="activeView" />
    <div class="builtin-icons-grid">
      <article v-for="icon in filteredIcons" :key="icon.key" class="builtin-icon-card">
        <span class="builtin-icon-preview">
          <img :src="icon.src" :alt="icon.name" />
        </span>
        <strong>{{ icon.name }}</strong>
        <small>{{ icon.key }}</small>
      </article>
    </div>
    <section v-if="filteredIcons.length === 0" class="empty-state">
      <i class="mdi mdi-magnify-close"></i>
      <span>Aucune icone</span>
    </section>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import SearchBar from './SearchBar.vue'
import { apiAssetUrl } from '../utils/shortcuts'

const props = defineProps({
  activeView: {
    type: String,
    required: true,
  },
  icons: {
    type: Array,
    default: () => [],
  },
  searchQuery: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['update:searchQuery'])

const query = computed({
  get: () => props.searchQuery,
  set: (value) => emit('update:searchQuery', value),
})

const displayIcons = computed(() => props.icons.map((icon) => ({
  ...icon,
  src: apiAssetUrl(icon.src),
})))

const filteredIcons = computed(() => {
  const search = query.value.trim().toLowerCase()
  if (!search) {
    return displayIcons.value
  }
  return displayIcons.value.filter((icon) => {
    return [icon.key, icon.name].some((value) => value.toLowerCase().includes(search))
  })
})
</script>
