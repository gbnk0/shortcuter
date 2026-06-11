import { describe, expect, it } from 'vitest'
import { resolveLocale, translate } from './i18n'

describe('i18n', () => {
  it('uses the browser base language in auto mode', () => {
    expect(resolveLocale('auto', 'fr-FR')).toBe('fr')
  })

  it('falls back to English for unsupported languages', () => {
    expect(resolveLocale('auto', 'it-IT')).toBe('en')
  })

  it('translates parameterized labels', () => {
    expect(translate('en', 'applicationCount', { count: 2 })).toBe('2 applications')
    expect(translate('fr', 'applicationCount', { count: 1 })).toBe('1 application')
  })
})
