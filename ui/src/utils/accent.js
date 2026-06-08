import { ACCENT_PALETTE } from '../constants'

export function normalizeAccent(value) {
  const normalized = String(value || '').trim().toLowerCase()
  if (ACCENT_PALETTE[normalized]) {
    return ACCENT_PALETTE[normalized]
  }
  return /^#[0-9a-f]{6}$/i.test(normalized) ? normalized : ACCENT_PALETTE.green
}

export function lightenHex(hex, amount = 28) {
  const color = normalizeAccent(hex).slice(1)
  const parts = [0, 2, 4].map((index) => parseInt(color.slice(index, index + 2), 16))
  const lightened = parts.map((part) => Math.min(255, part + amount).toString(16).padStart(2, '0'))
  return `#${lightened.join('')}`
}

export function applyAccent(accent) {
  const nextAccent = normalizeAccent(accent)
  document.documentElement.style.setProperty('--accent', nextAccent)
  document.documentElement.style.setProperty('--accent-hover', lightenHex(nextAccent))
}

