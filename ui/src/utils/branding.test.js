import { describe, expect, it } from 'vitest'
import { brandingFromPage, DEFAULT_BRANDING } from './branding'

describe('brandingFromPage', () => {
  it('uses bundled assets when no custom logo is configured', () => {
    expect(brandingFromPage({})).toMatchObject({
      appleTouchIcon: DEFAULT_BRANDING.appleTouchIcon,
      favicon: DEFAULT_BRANDING.favicon,
      faviconPng: DEFAULT_BRANDING.faviconPng,
      generateIconsFromLogo: false,
      icon192: DEFAULT_BRANDING.icon192,
      logo: DEFAULT_BRANDING.logo,
    })
  })

  it('normalizes a custom logo and derives icon targets from it', () => {
    expect(brandingFromPage({ logo: 'logo.png' })).toMatchObject({
      appleTouchIcon: '/logo.png',
      favicon: '/logo.png',
      faviconPng: '/logo.png',
      generateIconsFromLogo: true,
      icon192: '/logo.png',
      logo: '/logo.png',
    })
  })

  it('keeps explicit favicon overrides', () => {
    expect(brandingFromPage({ logo: '/logo.png', favicon: '/favicon.ico' })).toMatchObject({
      favicon: '/favicon.ico',
      faviconPng: '/logo.png',
      generateIconsFromLogo: true,
      logo: '/logo.png',
    })
  })
})
