<template>
  <main class="app-shell">
    <AppHeader
      :active-page="activePage"
      :active-view="activeView"
      :current-page="currentPage"
      :page="page"
      :pages="navigationPages"
      :subtitle="pageSubtitle"
      :theme="theme"
      :theme-title="themeTitle"
      @select-page="selectPage"
      @toggle-theme="toggleTheme"
    />

    <ShortcutsView
      v-if="activeView === 'shortcuts'"
      v-model:search-query="searchQuery"
      :active-page="activePage"
      :builtin-icons="builtinIcons"
      :loading="loading"
      :page-shortcuts="pageShortcuts"
    />

    <BuiltinIconsView
      v-else
      v-model:search-query="iconSearchQuery"
      :active-view="activeView"
      :icons="builtinIcons"
    />

    <p v-if="error" class="error-message">{{ error }}</p>

    <AppFooter :active-view="activeView" :version="appVersion" @toggle-icons-view="toggleIconsView" />
  </main>
</template>

<script setup>
import axios from 'axios'
import { computed, onMounted, ref, watch } from 'vue'
import AppFooter from './components/AppFooter.vue'
import AppHeader from './components/AppHeader.vue'
import BuiltinIconsView from './components/BuiltinIconsView.vue'
import ShortcutsView from './components/ShortcutsView.vue'
import { useAppRoutes } from './composables/useAppRoutes'
import { useTheme } from './composables/useTheme'
import { API_BASE, APP_VERSION } from './constants'
import { applyAccent } from './utils/accent'

const appVersion = APP_VERSION

const shortcuts = ref([])
const builtinIcons = ref([])
const loading = ref(false)
const error = ref('')
const searchQuery = ref('')
const iconSearchQuery = ref('')
const page = ref({
  title: 'Raccourcis',
  subtitle: '',
  rubrique: 'General',
  accent: 'green',
  show_all_tab: false,
  all_tab_accent: '',
})
const pages = ref([
  {
    id: 'general',
    title: 'General',
    subtitle: '',
    rubrique: 'General',
    accent: 'green',
    shortcuts: [],
  },
])

const {
  activePage,
  activeView,
  currentPath,
  initRoutes,
  lastShortcutPage,
  replaceRoute,
  selectPage,
  toggleIconsView,
} = useAppRoutes()

const { theme, themeTitle, initTheme, toggleTheme } = useTheme()

const showAllTab = computed(() => page.value.show_all_tab === true)

const navigationPages = computed(() => {
  if (!showAllTab.value) {
    return pages.value
  }
  return [
    {
      id: '__all',
      title: 'Tous',
      subtitle: '',
      rubrique: page.value.rubrique,
      accent: page.value.all_tab_accent || page.value.accent,
      shortcuts: shortcuts.value,
    },
    ...pages.value,
  ]
})

const currentPage = computed(() => {
  if (activeView.value === 'icons') {
    return {
      title: 'Catalogue des icones',
      subtitle: 'Noms utilisables dans le YAML',
      rubrique: 'Catalogue',
      accent: page.value.accent || '#16807a',
    }
  }
  return navigationPages.value.find((item) => item.id === activePage.value) || pages.value[0] || page.value
})

const pageShortcuts = computed(() => {
  if (showAllTab.value && activePage.value === '__all') {
    return shortcuts.value
  }
  const item = pages.value.find((candidate) => candidate.id === activePage.value)
  if (item?.shortcuts) {
    return item.shortcuts
  }
  return shortcuts.value.filter((shortcut) => shortcut.page === activePage.value)
})

const pageSubtitle = computed(() => {
  if (currentPage.value.subtitle) {
    return currentPage.value.subtitle
  }
  return `${pageShortcuts.value.length} application${pageShortcuts.value.length > 1 ? 's' : ''}`
})

function apiError(err) {
  const detail = err?.response?.data?.detail
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg).join(', ')
  }
  return detail || err.message || 'Erreur inconnue'
}

async function loadShortcuts() {
  loading.value = true
  error.value = ''
  try {
    const response = await axios.get(`${API_BASE}/shortcuts`)
    page.value = response.data.page || page.value
    pages.value = response.data.pages?.length
      ? response.data.pages
      : [{ id: 'general', ...page.value, shortcuts: response.data.shortcuts || [] }]
    shortcuts.value = response.data.shortcuts || []
    const firstPageId = navigationPages.value[0]?.id || pages.value[0]?.id || 'general'
    const pageExists = navigationPages.value.some((item) => item.id === activePage.value)
    if (activeView.value === 'icons') {
      if (!navigationPages.value.some((item) => item.id === lastShortcutPage.value)) {
        lastShortcutPage.value = firstPageId
      }
    } else if (!pageExists) {
      replaceRoute(`/page/${firstPageId}`)
    } else if (currentPath.value === '/') {
      replaceRoute(`/page/${activePage.value}`)
    }
    lastShortcutPage.value = activePage.value
  } catch (err) {
    error.value = apiError(err)
  } finally {
    loading.value = false
  }
}

async function loadBuiltinIcons() {
  try {
    const response = await axios.get(`${API_BASE}/builtin-icons`)
    builtinIcons.value = response.data.icons || []
  } catch {
    builtinIcons.value = []
  }
}

onMounted(() => {
  initTheme()
  initRoutes()
  loadShortcuts()
  loadBuiltinIcons()
})

watch(() => currentPage.value.accent, (accent) => applyAccent(accent), { immediate: true })
</script>
