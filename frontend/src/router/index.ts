import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('../layouts/AppShell.vue'),
    children: [
      {
        path: '',
        name: 'dashboard',
        component: () => import('../pages/DashboardPage.vue'),
        meta: {
          title: 'Dashboard',
          description: 'Your MyHarf operations workspace.',
          section: 'dashboard',
          breadcrumbs: [{ label: 'Dashboard' }],
        },
      },
      {
        path: 'customers',
        name: 'customers',
        component: () => import('../features/customers/pages/CustomerListPage.vue'),
        meta: {
          title: 'Customers',
          description: 'Manage the businesses MyHarf supports.',
          section: 'customers',
          breadcrumbs: [{ label: 'Customers' }],
        },
      },
      {
        path: 'customers/new',
        name: 'customer-create',
        component: () => import('../features/customers/pages/CustomerCreatePage.vue'),
        meta: {
          title: 'New customer',
          description: 'Create a customer record.',
          section: 'customers',
          breadcrumbs: [
            { label: 'Customers', to: '/customers' },
            { label: 'New customer' },
          ],
        },
      },
      {
        path: 'customers/:customerId/edit',
        name: 'customer-edit',
        component: () => import('../features/customers/pages/CustomerEditPage.vue'),
        props: true,
        meta: {
          title: 'Edit customer',
          description: 'Update customer contact information.',
          section: 'customers',
          breadcrumbs: [
            { label: 'Customers', to: '/customers' },
            { label: 'Customer overview', customerProfile: true },
            { label: 'Edit customer' },
          ],
        },
      },
      {
        path: 'customers/:customerId',
        name: 'customer-overview',
        component: () => import('../features/customers/pages/CustomerDetailPage.vue'),
        props: true,
        meta: {
          title: 'Customer overview',
          description: 'A home for this customer’s diagnostics, fixes, and quotations.',
          section: 'customers',
          breadcrumbs: [
            { label: 'Customers', to: '/customers' },
            { label: 'Customer overview' },
          ],
        },
      },
      {
        path: 'customers/:customerId/diagnostics/new',
        name: 'diagnostic-create',
        component: () => import('../features/diagnostics/pages/DiagnosticCreatePage.vue'),
        props: true,
        meta: {
          title: 'New diagnostic',
          description: 'Start a website diagnostic for this customer.',
          section: 'customers',
          breadcrumbs: [
            { label: 'Customers', to: '/customers' },
            { label: 'Customer overview', customerProfile: true },
            { label: 'New diagnostic' },
          ],
        },
      },
      {
        path: 'diagnostics/:diagnosticId',
        name: 'diagnostic-workspace',
        component: () => import('../features/diagnostics/pages/DiagnosticWorkspacePage.vue'),
        props: true,
        meta: {
          title: 'Diagnostic workspace',
          description: 'Review a website diagnostic and its findings.',
          section: 'customers',
          breadcrumbs: [
            { label: 'Customers', to: '/customers' },
            { label: 'Diagnostic workspace' },
          ],
        },
      },
      {
        path: 'fixes',
        name: 'fix-ledger',
        component: () => import('../pages/PlaceholderPage.vue'),
        meta: {
          title: 'Fix Ledger',
          description: 'Track actionable website fixes across customers.',
          section: 'fixes',
          breadcrumbs: [{ label: 'Fix Ledger' }],
        },
      },
      {
        path: 'fixes/:fixId',
        name: 'fix-details',
        component: () => import('../pages/PlaceholderPage.vue'),
        props: true,
        meta: {
          title: 'Fix details',
          description: 'Review a customer-specific website fix.',
          section: 'fixes',
          breadcrumbs: [
            { label: 'Fix Ledger', to: '/fixes' },
            { label: 'Fix details' },
          ],
        },
      },
      {
        path: 'fix-types',
        name: 'fix-catalog',
        component: () => import('../pages/PlaceholderPage.vue'),
        meta: {
          title: 'Fix Catalog',
          description: 'Manage standardized types of website fixes.',
          section: 'fix-types',
          breadcrumbs: [{ label: 'Fix Catalog' }],
        },
      },
      {
        path: 'quotations',
        name: 'quotations',
        component: () => import('../pages/PlaceholderPage.vue'),
        meta: {
          title: 'Quotations',
          description: 'Review customer quotations and their itemized pricing.',
          section: 'quotations',
          breadcrumbs: [{ label: 'Quotations' }],
        },
      },
      {
        path: 'quotations/:quotationId',
        name: 'quotation-details',
        component: () => import('../pages/PlaceholderPage.vue'),
        props: true,
        meta: {
          title: 'Quotation details',
          description: 'Review a saved quotation and its price snapshots.',
          section: 'quotations',
          breadcrumbs: [
            { label: 'Quotations', to: '/quotations' },
            { label: 'Quotation details' },
          ],
        },
      },
      {
        path: 'customers/:customerId/quotations/new',
        name: 'quotation-create',
        component: () => import('../pages/PlaceholderPage.vue'),
        props: true,
        meta: {
          title: 'New quotation',
          description: 'Prepare a quotation for this customer.',
          section: 'quotations',
          breadcrumbs: [
            { label: 'Customers', to: '/customers' },
            { label: 'Customer overview' },
            { label: 'New quotation' },
          ],
        },
      },
      {
        path: '/:pathMatch(.*)*',
        name: 'not-found',
        component: () => import('../pages/NotFoundPage.vue'),
        meta: {
          title: 'Page not found',
          description: 'The requested workspace could not be found.',
          breadcrumbs: [{ label: 'Page not found' }],
        },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

router.afterEach((to) => {
  document.title = `${to.meta.title ?? 'MyHarf OS'} · MyHarf OS`
})

export default router
