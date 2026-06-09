<template>
  <main class="app-shell">
    <section class="masthead">
      <div class="appbar" :aria-label="tr('application')">
        <img class="appbar-logo" :src="branding.logo" alt="" aria-hidden="true" width="20" height="20" />
        <span>{{ page.rubrique }}</span>
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

const appVersion = APP_VERSION

const shortcuts = ref([])
const builtinIcons = ref([])
const loading = ref(false)
const error = ref(null)
const searchQuery = ref('')
const iconSearchQuery = ref('')
const branding = ref(DEFAULT_BRANDING)
const page = ref({
  title: 'Shortcuter',
  subtitle: '',
  rubrique: 'Links',
  accent: 'green',
  display_density: 'comfortable',
  language: 'auto',
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

function tr(key, params = {}) {
  return translate(locale.value, key, params)
}

const shortcutLabels = computed(() => ({
  loading: tr('loading'),
  noResults: tr('noResults'),
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
watch(locale, (nextLocale) => {
  document.documentElement.lang = nextLocale
}, { immediate: true })
</script>
