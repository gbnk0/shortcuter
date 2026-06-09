export const DEFAULT_BRANDING = {
  appleTouchIcon: '/apple-touch-icon-v2.png',
  favicon: '/favicon-v2.ico',
  faviconPng: '/favicon-32x32-v2.png',
  icon192: '/icon-192-v2.png',
  logo: '/logo.png',
}

const generatedIconCache = new Map()

function normalizeAssetPath(value) {
  if (!value) {
    return ''
  }
  if (/^(https?:)?\/\//.test(value) || value.startsWith('/') || value.startsWith('data:')) {
    return value
  }
  return `/${value}`
}

export function brandingFromPage(page = {}) {
  const logo = normalizeAssetPath(page.logo) || DEFAULT_BRANDING.logo
  const fallbackIcon = page.logo ? logo : ''
  const favicon = normalizeAssetPath(page.favicon)
  const faviconPng = normalizeAssetPath(page.favicon_png)
  const appleTouchIcon = normalizeAssetPath(page.apple_touch_icon || page.favicon_apple_touch)
  const icon192 = normalizeAssetPath(page.icon_192 || page.favicon_192)

  return {
    appleTouchIcon: appleTouchIcon || fallbackIcon || DEFAULT_BRANDING.appleTouchIcon,
    favicon: favicon || fallbackIcon || DEFAULT_BRANDING.favicon,
    faviconPng: faviconPng || fallbackIcon || DEFAULT_BRANDING.faviconPng,
    generateIconsFromLogo: Boolean(fallbackIcon) && (!appleTouchIcon || !favicon || !faviconPng || !icon192),
    icon192: icon192 || fallbackIcon || DEFAULT_BRANDING.icon192,
    logo,
  }
}

function imageLoaded(src) {
  return new Promise((resolve, reject) => {
    const image = new Image()
    image.crossOrigin = 'anonymous'
    image.onload = () => resolve(image)
    image.onerror = reject
    image.src = src
  })
}

function resizedPngDataUrl(image, size) {
  const canvas = document.createElement('canvas')
  canvas.width = size
  canvas.height = size
  const context = canvas.getContext('2d')
  context.clearRect(0, 0, size, size)
  context.drawImage(image, 0, 0, size, size)
  return canvas.toDataURL('image/png')
}

async function generateIcons(src) {
  if (!src || typeof document === 'undefined') {
    return null
  }
  if (!generatedIconCache.has(src)) {
    generatedIconCache.set(
      src,
      imageLoaded(src)
        .then((image) => ({
          appleTouchIcon: resizedPngDataUrl(image, 180),
          favicon: resizedPngDataUrl(image, 32),
          faviconPng: resizedPngDataUrl(image, 32),
          icon192: resizedPngDataUrl(image, 192),
        }))
        .catch(() => null),
    )
  }
  return generatedIconCache.get(src)
}

function setHeadLink(selector, attributes) {
  let link = document.head.querySelector(selector)
  if (!link) {
    link = document.createElement('link')
    document.head.append(link)
  }
  for (const [name, value] of Object.entries(attributes)) {
    if (value) {
      link.setAttribute(name, value)
    } else {
      link.removeAttribute(name)
    }
  }
}

export async function applyBranding(branding) {
  const generatedIcons = branding.generateIconsFromLogo ? await generateIcons(branding.logo) : null
  const favicon = branding.favicon === branding.logo ? generatedIcons?.favicon || branding.favicon : branding.favicon
  const faviconPng =
    branding.faviconPng === branding.logo ? generatedIcons?.faviconPng || branding.faviconPng : branding.faviconPng
  const appleTouchIcon =
    branding.appleTouchIcon === branding.logo
      ? generatedIcons?.appleTouchIcon || branding.appleTouchIcon
      : branding.appleTouchIcon
  const icon192 = branding.icon192 === branding.logo ? generatedIcons?.icon192 || branding.icon192 : branding.icon192

  setHeadLink('link[data-shortcuter-icon="favicon"]', {
    'data-shortcuter-icon': 'favicon',
    href: favicon,
    rel: 'icon',
    sizes: '32x32',
    type: 'image/png',
  })
  setHeadLink('link[data-shortcuter-icon="favicon-png"]', {
    'data-shortcuter-icon': 'favicon-png',
    href: faviconPng,
    rel: 'icon',
    sizes: '32x32',
    type: 'image/png',
  })
  setHeadLink('link[data-shortcuter-icon="apple-touch"]', {
    'data-shortcuter-icon': 'apple-touch',
    href: appleTouchIcon,
    rel: 'apple-touch-icon',
    sizes: '180x180',
  })
  setHeadLink('link[data-shortcuter-icon="icon-192"]', {
    'data-shortcuter-icon': 'icon-192',
    href: icon192,
    rel: 'icon',
    sizes: '192x192',
    type: 'image/png',
  })
}
