import { API_BASE, HOMARR_ICON_CDN } from '../constants'

export function apiAssetUrl(src) {
  if (src?.startsWith('/icons/')) {
    return `${API_BASE}${src}`
  }
  return src
}

export function displayHost(url) {
  try {
    return new URL(url).host
  } catch {
    return url
  }
}

export function iconSource(shortcut, builtinIcons) {
  if (shortcut.icon_type === 'predefined') {
    const key = shortcut.icon_value.replace(/\.[^.]+$/, '')
    const icon = builtinIcons.find((candidate) => candidate.key === key)
    if (icon) {
      return apiAssetUrl(icon.src)
    }
    if (key.startsWith('homarr/')) {
      return `${HOMARR_ICON_CDN}/${key.replace('homarr/', '')}.svg`
    }
    return ''
  }
  if (shortcut.icon_value?.startsWith('/icons/')) {
    return apiAssetUrl(shortcut.icon_value)
  }
  return shortcut.icon_value
}

export function groupShortcuts(shortcuts) {
  const groups = new Map()
  for (const shortcut of shortcuts) {
    const groupName = shortcut.group || 'Applications'
    if (!groups.has(groupName)) {
      groups.set(groupName, [])
    }
    groups.get(groupName).push(shortcut)
  }
  return Array.from(groups, ([name, items]) => ({ name, items }))
}
