<template>
  <main class="app-shell">
    <section class="masthead">
      <div class="appbar" :aria-label="tr('application')">
        <img class="appbar-logo" :src="branding.logo" alt="" aria-hidden="true" width="20" height="20" />
        <span>{{ appbarTitle }}</span>
      </div>
      <div class="masthead-right">
        <SearchBar
          v-if="activeView === 'shortcuts'"
          v-model="searchQuery"
          class="masthead-search"
          :clear-title="tr('clearSearch')"
          :placeholder="tr('searchApplications')"
          autofocus
          :focus-key="activePage"
          @focus-change="searchFocused = $event"
          @navigate="moveSearchSelection"
          @submit="openSelectedSearchResult"
        />
        <div v-if="showDisplayControls" class="appbar-actions" :aria-label="tr('displayControls')">
          <button v-if="showThemeToggle" class="appbar-button" type="button" :title="themeTitle" @click="toggleTheme">
            <i :class="['mdi', theme === 'dark' ? 'mdi-weather-sunny' : 'mdi-weather-night']"></i>
          </button>
          <button v-if="showDensityToggle" class="appbar-button" type="button" :title="compactTitle" @click="toggleCompactView">
            <i :class="['mdi', compactView ? 'mdi-view-agenda-outline' : 'mdi-view-compact-outline']"></i>
          </button>
        </div>
      </div>
    </section>

    <AppHeader
      :active-page="activePage"
      :active-view="activeView"
      :current-page="currentPage"
      :page="page"
      :pages="navigationPages"
      :views-label="tr('views')"
      :subtitle="pageSubtitle"
      @select-page="selectPage"
    />

    <ShortcutsView
      v-if="activeView === 'shortcuts'"
      :active-page="activePage"
      :builtin-icons="builtinIcons"
      :compact-view="compactView"
      :labels="shortcutLabels"
      :loading="loading"
      :pages="pages"
      :page-shortcuts="pageShortcuts"
      :search-query="searchQuery"
      :selected-shortcut-id="selectedSearchShortcutId"
    />

    <BuiltinIconsView
      v-else
      v-model:search-query="iconSearchQuery"
      :active-view="activeView"
      :icons="builtinIcons"
      :labels="iconLabels"
    />

    <section v-if="error" class="config-error">
      <div>
        <strong>{{ error.title }}</strong>
        <p>{{ error.message }}</p>
      </div>
    </section>

    <AppFooter
      v-if="showFooter"
      :active-view="activeView"
      :labels="footerLabels"
      :version="appVersion"
      @toggle-icons-view="toggleIconsView"
    />
  </main>
</template>

<script setup>
import axios from 'axios'
import { computed, onMounted, ref, watch } from 'vue'
import AppFooter from './components/AppFooter.vue'
import AppHeader from './components/AppHeader.vue'
import BuiltinIconsView from './components/BuiltinIconsView.vue'
import SearchBar from './components/SearchBar.vue'
import ShortcutsView from './components/ShortcutsView.vue'
import { useDisplayPreferences } from './composables/useDisplayPreferences'
import { useAppRoutes } from './composables/useAppRoutes'
import { useTheme } from './composables/useTheme'
import { API_BASE, APP_VERSION } from './constants'
import { resolveLocale, translate } from './i18n'
import { applyAccent } from './utils/accent'
import { applyBranding, brandingFromPage, DEFAULT_BRANDING } from './utils/branding'
import { buildSearchUrl, matchesShortcutSearch } from './utils/shortcuts'

const appVersion = APP_VERSION

const shortcuts = ref([])
const builtinIcons = ref([])
const loading = ref(false)
const error = ref(null)
const searchQuery = ref('')
const searchFocused = ref(false)
const iconSearchQuery = ref('')
const selectedSearchIndex = ref(0)
const keyboardNavigationActive = ref(false)
const branding = ref(DEFAULT_BRANDING)
const page = ref({
  title: 'Shortcuter',
  app_title: 'Shortcuter',
  subtitle: '',
  rubrique: 'Links',
  accent: 'green',
  display_density: 'comfortable',
  language: 'auto',
  search_engine_url: 'https://www.google.com/search?q=',
  logo: DEFAULT_BRANDING.logo,
  favicon: '',
  favicon_png: '',
  apple_touch_icon: '',
  icon_192: '',
  show_all_tab: false,
  all_tab_accent: '',
  show_footer: true,
  show_theme_toggle: true,
  show_density_toggle: true,
})
const pages = ref([
  {
    id: 'general',
    title: 'General',
    subtitle: '',
    rubrique: 'Links',
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

const { theme, initTheme, toggleTheme } = useTheme()
const {
  applyDefaultDisplayDensity,
  compactView,
  toggleCompactView,
} = useDisplayPreferences()

const locale = computed(() => resolveLocale(page.value.language))
const themeTitle = computed(() => tr(theme.value === 'dark' ? 'lightTheme' : 'darkTheme'))
const compactTitle = computed(() => tr(compactView.value ? 'comfortableView' : 'compactView'))
const showAllTab = computed(() => page.value.show_all_tab === true)
const showFooter = computed(() => page.value.show_footer !== false)
const showThemeToggle = computed(() => page.value.show_theme_toggle !== false)
const showDensityToggle = computed(() => page.value.show_density_toggle !== false)
const showDisplayControls = computed(() => showThemeToggle.value || showDensityToggle.value)
const appbarTitle = computed(() => page.value.app_title || page.value.rubrique || page.value.title || 'Shortcuter')

function tr(key, params = {}) {
  return translate(locale.value, key, params)
}

const shortcutLabels = computed(() => ({
  loading: tr('loading'),
  noResults: tr(searchFocused.value ? 'noResultsExternalSearch' : 'noResults'),
  noShortcuts: tr('noShortcuts'),
}))

const iconLabels = computed(() => ({
  clearSearch: tr('clearSearch'),
  iconCatalog: tr('iconCatalog'),
  noIcons: tr('noIcons'),
  searchIcons: tr('searchIcons'),
  iconCount: (filtered, total) => tr('iconCount', { filtered, total }),
}))

const footerLabels = computed(() => ({
  backToShortcuts: tr('backToShortcuts'),
  version: tr('version'),
  yamlIconCatalog: tr('yamlIconCatalog'),
}))

const navigationPages = computed(() => {
  if (!showAllTab.value) {
    return pages.value
  }
  return [
    {
      id: '__all',
      title: tr('all'),
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
      title: tr('iconCatalog'),
      subtitle: tr('iconCatalogSubtitle'),
      rubrique: tr('catalogRubrique'),
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

const filteredPageShortcuts = computed(() => {
  const search = searchQuery.value.trim().toLowerCase()
  if (!search) {
    return pageShortcuts.value
  }
  return pageShortcuts.value.filter((shortcut) => matchesShortcutSearch(shortcut, search, pages.value))
})
const selectedSearchShortcutId = computed(() => {
  if ((!searchQuery.value.trim() && !keyboardNavigationActive.value) || filteredPageShortcuts.value.length === 0) {
    return ''
  }
  return filteredPageShortcuts.value[selectedSearchIndex.value]?.id || filteredPageShortcuts.value[0]?.id || ''
})

const pageSubtitle = computed(() => {
  if (currentPage.value.subtitle) {
    return currentPage.value.subtitle
  }
  return tr('applicationCount', { count: pageShortcuts.value.length })
})

function apiError(err) {
  const detail = err?.response?.data?.detail
  const message = Array.isArray(detail)
    ? detail.map((item) => item.msg).join(', ')
    : detail || err.message || tr('unknownError')
  const isConfigError = err?.response?.status >= 500 && /yaml|shortcut|page|url/i.test(message)
  return {
    title: isConfigError ? tr('configurationError') : tr('unableToLoadShortcuts'),
    message,
  }
}

function moveSearchSelection(direction) {
  const total = filteredPageShortcuts.value.length
  if (total === 0) {
    return
  }
  if (!keyboardNavigationActive.value && !searchQuery.value.trim()) {
    keyboardNavigationActive.value = true
    selectedSearchIndex.value = 0
    return
  }
  keyboardNavigationActive.value = true
  if (direction === 'up' || direction === 'down') {
    const visualIndex = visualSearchIndex(direction)
    if (visualIndex !== -1) {
      selectedSearchIndex.value = visualIndex
    }
    return
  }
  const step = direction === 'left' ? -1 : 1
  selectedSearchIndex.value = (selectedSearchIndex.value + step + total) % total
}

function visualSearchIndex(direction) {
  const selectedShortcut = filteredPageShortcuts.value[selectedSearchIndex.value] || filteredPageShortcuts.value[0]
  if (!selectedShortcut) {
    return -1
  }
  const shortcutIndexById = new Map(filteredPageShortcuts.value.map((shortcut, index) => [shortcut.id, index]))
  const cards = Array.from(document.querySelectorAll('.shortcut-card[data-shortcut-id]'))
    .map((element) => {
      const id = element.dataset.shortcutId
      const index = shortcutIndexById.get(id)
      if (index === undefined) {
        return null
      }
      const rect = element.getBoundingClientRect()
      return {
        centerX: rect.left + rect.width / 2,
        centerY: rect.top + rect.height / 2,
        index,
        rect,
      }
    })
    .filter(Boolean)
  const current = cards.find((card) => card.index === shortcutIndexById.get(selectedShortcut.id))
  if (!current) {
    return -1
  }
  const candidates = cards
    .filter((card) => direction === 'down' ? card.centerY > current.centerY + 1 : card.centerY < current.centerY - 1)
    .sort((a, b) => {
      const rowDelta = Math.abs(a.centerY - current.centerY) - Math.abs(b.centerY - current.centerY)
      if (Math.abs(rowDelta) > 1) {
        return rowDelta
      }
      return Math.abs(a.centerX - current.centerX) - Math.abs(b.centerX - current.centerX)
    })
  return candidates[0]?.index ?? -1
}

function openSelectedSearchResult() {
  const query = searchQuery.value.trim()
  if (!query && !keyboardNavigationActive.value) {
    return
  }
  if (query && filteredPageShortcuts.value.length === 0) {
    window.open(buildSearchUrl(page.value.search_engine_url, query), '_blank', 'noopener,noreferrer')
    return
  }
  if (filteredPageShortcuts.value.length === 0) {
    return
  }
  const shortcut = filteredPageShortcuts.value[selectedSearchIndex.value] || filteredPageShortcuts.value[0]
  window.open(shortcut.url, '_blank', 'noopener,noreferrer')
}

async function loadShortcuts() {
  loading.value = true
  error.value = null
  try {
    const response = await axios.get(`${API_BASE}/shortcuts`)
    page.value = response.data.page || page.value
    branding.value = brandingFromPage(page.value)
    applyDefaultDisplayDensity(page.value.display_density)
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
watch(branding, applyBranding, { immediate: true })
watch([searchQuery, activePage, filteredPageShortcuts], () => {
  selectedSearchIndex.value = 0
  keyboardNavigationActive.value = Boolean(searchQuery.value.trim())
})
watch(() => page.value.app_title || page.value.title, (nextTitle) => {
  document.title = nextTitle || 'Shortcuter'
}, { immediate: true })
watch(locale, (nextLocale) => {
  document.documentElement.lang = nextLocale
}, { immediate: true })
</script>
