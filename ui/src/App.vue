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
      :compact-title="compactTitle"
      :compact-view="compactView"
      @select-page="selectPage"
      @toggle-compact-view="toggleCompactView"
      @toggle-theme="toggleTheme"
    />

    <ShortcutsView
      v-if="activeView === 'shortcuts'"
      v-model:search-query="searchQuery"
      :active-page="activePage"
      :builtin-icons="builtinIcons"
      :compact-view="compactView"
      :loading="loading"
      :pages="pages"
      :page-shortcuts="pageShortcuts"
    />

    <BuiltinIconsView
      v-else
      v-model:search-query="iconSearchQuery"
      :active-view="activeView"
      :icons="builtinIcons"
    />

    <section v-if="error" class="config-error">
      <div>
        <strong>{{ error.title }}</strong>
        <p>{{ error.message }}</p>
      </div>
    </section>

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
import { useDisplayPreferences } from './composables/useDisplayPreferences'
import { useAppRoutes } from './composables/useAppRoutes'
import { useTheme } from './composables/useTheme'
import { API_BASE, APP_VERSION } from './constants'
import { applyAccent } from './utils/accent'

const appVersion = APP_VERSION

const shortcuts = ref([])
const builtinIcons = ref([])
const loading = ref(false)
const error = ref(null)
const searchQuery = ref('')
const iconSearchQuery = ref('')
const page = ref({
  title: 'Shortcuter',
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
const {
  compactTitle,
  compactView,
  toggleCompactView,
} = useDisplayPreferences()

const showAllTab = computed(() => page.value.show_all_tab === true)

const navigationPages = computed(() => {
  if (!showAllTab.value) {
    return pages.value
  }
  return [
    {
      id: '__all',
      title: 'All',
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
      title: 'Icon Catalog',
      subtitle: 'Names available for YAML',
      rubrique: 'Catalog',
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
  const message = Array.isArray(detail)
    ? detail.map((item) => item.msg).join(', ')
    : detail || err.message || 'Unknown error'
  const isConfigError = err?.response?.status >= 500 && /yaml|shortcut|page|url/i.test(message)
  return {
    title: isConfigError ? 'Configuration error' : 'Unable to load shortcuts',
    message,
  }
}

async function loadShortcuts() {
  loading.value = true
  error.value = null
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
