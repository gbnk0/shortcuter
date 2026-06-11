const browserLocation = globalThis.window?.location
const defaultApiBase = browserLocation
  ? browserLocation.port === '5173'
    ? `${browserLocation.protocol}//${browserLocation.hostname}:8000`
    : browserLocation.origin
  : 'http://localhost:8000'

export const API_BASE = import.meta.env.VITE_API_URL || defaultApiBase
export const APP_VERSION = import.meta.env.VITE_APP_VERSION || 'dev'
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
