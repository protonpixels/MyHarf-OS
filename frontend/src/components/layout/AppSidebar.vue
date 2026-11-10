<script setup lang="ts">
import { useRoute } from 'vue-router'

defineEmits<{ navigate: [] }>()
const route = useRoute()
const navigation = [
  { label: 'Dashboard', to: '/', section: 'dashboard', icon: 'M3 10.5 12 3l9 7.5v9a1.5 1.5 0 0 1-1.5 1.5h-15A1.5 1.5 0 0 1 3 19.5v-9ZM9 21v-7h6v7' },
  { label: 'Customers', to: '/customers', section: 'customers', icon: 'M16 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2m6-10a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm10 10v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75' },
  { label: 'Fix Ledger', to: '/fixes', section: 'fixes', icon: 'M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01' },
  { label: 'Fix Catalog', to: '/fix-types', section: 'fix-types', icon: 'M4 5.5A2.5 2.5 0 0 1 6.5 3H20v16H6.5A2.5 2.5 0 0 0 4 21.5v-16ZM4 5.5v16' },
  { label: 'Quotations', to: '/quotations', section: 'quotations', icon: 'M7 3h10l4 4v14H3V3h4Zm9 0v5h5M7 13h10M7 17h7' },
]
</script>

<template>
  <div class="sidebar">
    <RouterLink to="/" class="brand" aria-label="MyHarf OS home" @click="$emit('navigate')">
      <span class="brand-mark" aria-hidden="true">M</span>
      <span class="brand-copy"><strong>MyHarf</strong><small>OPERATIONS</small></span>
    </RouterLink>
    <div class="sidebar-label">WORKSPACE</div>
    <nav class="nav-list" aria-label="Workspace">
      <RouterLink
        v-for="item in navigation"
        :key="item.section"
        :to="item.to"
        class="nav-link"
        :class="{ 'nav-link--active': route.meta.section === item.section }"
        :aria-current="route.meta.section === item.section ? 'page' : undefined"
        @click="$emit('navigate')"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path :d="item.icon" /></svg>
        <span>{{ item.label }}</span>
      </RouterLink>
    </nav>
    <div class="sidebar-bottom"><span class="online-dot" />MyHarf internal workspace</div>
  </div>
</template>
