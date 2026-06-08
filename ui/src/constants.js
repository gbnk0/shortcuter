const defaultApiBase = window.location.port === '5173'
  ? `${window.location.protocol}//${window.location.hostname}:8000`
  : window.location.origin

export const API_BASE = import.meta.env.VITE_API_URL || defaultApiBase
export const APP_VERSION = '0.4.0'
export const HOMARR_ICON_CDN = 'https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg'

export const ACCENT_PALETTE = {
  blue: '#3f6edb',
  cyan: '#0ea5b7',
  green: '#16803f',
  orange: '#d97706',
  pink: '#d9468f',
  purple: '#7c5cc4',
  red: '#dc3f4d',
  slate: '#64748b',
  yellow: '#b88700',
}
