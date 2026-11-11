import { describe, expect, it } from 'vitest'
import router from '../../router'

describe('customer route records', () => {
  it.each([
    ['/customers', 'customers', 'Customers'],
    ['/customers/new', 'customer-create', 'New customer'],
    ['/customers/17', 'customer-overview', 'Customer overview'],
    ['/customers/17/edit', 'customer-edit', 'Edit customer'],
  ])('resolves %s to the named customer page', (path, name, title) => {
    const resolved = router.resolve(path)
    expect(resolved.name).toBe(name)
    expect(resolved.meta.title).toBe(title)
    expect(resolved.matched.at(-1)?.components?.default).toBeTypeOf('function')
  })

  it('provides customer profile navigation from the edit breadcrumb', () => {
    const editRoute = router.resolve('/customers/17/edit')
    expect(editRoute.meta.breadcrumbs).toEqual([
      { label: 'Customers', to: '/customers' },
      { label: 'Customer overview', customerProfile: true },
      { label: 'Edit customer' },
    ])
  })

  it('uses the diagnostic creation page with customer profile breadcrumbs', () => {
    const diagnosticRoute = router.resolve('/customers/17/diagnostics/new')
    expect(diagnosticRoute.name).toBe('diagnostic-create')
    expect(diagnosticRoute.meta.title).toBe('New diagnostic')
    expect(diagnosticRoute.meta.breadcrumbs).toEqual([
      { label: 'Customers', to: '/customers' },
      { label: 'Customer overview', customerProfile: true },
      { label: 'New diagnostic' },
    ])
    expect(diagnosticRoute.matched.at(-1)?.components?.default).toBeTypeOf('function')
  })

  it('keeps the diagnostic workspace named route and metadata', () => {
    const detailRoute = router.resolve('/diagnostics/31')
    expect(detailRoute.name).toBe('diagnostic-workspace')
    expect(detailRoute.meta.title).toBe('Diagnostic workspace')
    expect(detailRoute.matched.at(-1)?.components?.default).toBeTypeOf('function')
  })
})
