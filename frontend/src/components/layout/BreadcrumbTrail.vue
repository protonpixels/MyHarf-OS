<script setup lang="ts">
import { useRoute } from 'vue-router'
const route = useRoute()
function targetFor(crumb: { to?: string; customerProfile?: boolean }) {
  if (crumb.customerProfile && route.params.customerId) {
    return { name: 'customer-overview', params: { customerId: route.params.customerId } }
  }
  return crumb.to ?? '/'
}
</script>

<template>
  <nav class="breadcrumbs" aria-label="Breadcrumb">
    <template v-for="(crumb, index) in route.meta.breadcrumbs ?? []" :key="`${crumb.label}-${index}`">
      <span v-if="index" class="breadcrumb-separator" aria-hidden="true">/</span>
      <RouterLink v-if="(crumb.to || crumb.customerProfile) && index < (route.meta.breadcrumbs?.length ?? 0) - 1" :to="targetFor(crumb)">{{ crumb.label }}</RouterLink>
      <span v-else :aria-current="index === (route.meta.breadcrumbs?.length ?? 0) - 1 ? 'page' : undefined">{{ crumb.label }}</span>
    </template>
  </nav>
</template>
