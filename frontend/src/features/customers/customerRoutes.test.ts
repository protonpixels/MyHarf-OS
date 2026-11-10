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
})
