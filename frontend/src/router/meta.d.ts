import 'vue-router'

declare module 'vue-router' {
  interface RouteMeta {
    title?: string
    description?: string
    section?: string
    breadcrumbs?: Array<{ label: string; to?: string }>
  }
}

export {}
