import { describe, expect, it } from 'vitest'
import { groupShortcuts, iconSource, matchesShortcutSearch } from './shortcuts'

describe('shortcut utilities', () => {
  const pages = [{ id: 'ops', title: 'Operations', rubrique: 'Infra' }]
  const shortcut = {
    description: 'Metrics and alerts',
    group: 'Monitoring',
    icon_type: 'auto',
    icon_value: 'https://grafana.example.test/favicon.ico',
    name: 'Grafana',
    page: 'ops',
    url: 'https://grafana.example.test',
  }

  it('matches search terms across shortcut and page fields', () => {
    expect(matchesShortcutSearch(shortcut, 'grafana infra', pages)).toBe(true)
    expect(matchesShortcutSearch(shortcut, 'billing', pages)).toBe(false)
  })

  it('groups shortcuts by group name', () => {
    expect(groupShortcuts([shortcut, { ...shortcut, name: 'Prometheus' }])).toEqual([
      { name: 'Monitoring', items: [shortcut, { ...shortcut, name: 'Prometheus' }] },
    ])
  })

  it('resolves Homarr predefined icon URLs when not cached locally', () => {
    expect(iconSource({ icon_type: 'predefined', icon_value: 'homarr/grafana' }, [])).toContain('/grafana.svg')
  })
})
