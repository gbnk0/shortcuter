<template>
  <template v-if="loading">
    <section class="empty-state">
      <i class="mdi mdi-loading mdi-spin"></i>
      <span>Loading</span>
    </section>
  </template>

  <Transition name="tab-panel" mode="out-in">
    <div v-if="!loading" :key="activePage" class="tab-panel" :class="{ compact: compactView }">
      <SearchBar v-model="query" placeholder="Search applications" autofocus :focus-key="activePage" />

      <section v-for="group in groups" :key="group.name" class="group-section">
        <h2>{{ group.name }}</h2>
        <div class="shortcuts-grid">
          <ShortcutCard
            v-for="shortcut in group.items"
            :key="shortcut.id"
            :builtin-icons="builtinIcons"
            :source-accent="sourceAccent(shortcut)"
            :shortcut="shortcut"
          />
        </div>
      </section>

      <section v-if="pageShortcuts.length === 0" class="empty-state">
        <i class="mdi mdi-apps"></i>
        <span>No shortcuts on this page</span>
      </section>

      <section v-else-if="filteredShortcuts.length === 0" class="empty-state">
        <i class="mdi mdi-magnify-close"></i>
        <span>No results</span>
      </section>
    </div>
  </Transition>
</template>

<script setup>
import { computed } from 'vue'
import SearchBar from './SearchBar.vue'
import ShortcutCard from './ShortcutCard.vue'
import { normalizeAccent } from '../utils/accent'
import { groupShortcuts, matchesShortcutSearch } from '../utils/shortcuts'

const props = defineProps({
  activePage: {
    type: String,
    required: true,
  },
  builtinIcons: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
  compactView: {
    type: Boolean,
    default: false,
  },
  pages: {
    type: Array,
    default: () => [],
  },
  pageShortcuts: {
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

const filteredShortcuts = computed(() => {
  const search = query.value.trim().toLowerCase()
  if (!search) {
    return props.pageShortcuts
  }
  return props.pageShortcuts.filter((shortcut) => matchesShortcutSearch(shortcut, search, props.pages))
})

const groups = computed(() => groupShortcuts(filteredShortcuts.value))

function sourceAccent(shortcut) {
  if (props.activePage !== '__all') {
    return ''
  }
  const accent = props.pages.find((page) => page.id === shortcut.page)?.accent
  return accent ? normalizeAccent(accent) : ''
}
</script>
