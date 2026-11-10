<script setup lang="ts">
import { useRoute } from 'vue-router'
import AppCard from '../components/ui/AppCard.vue'
import EmptyState from '../components/ui/EmptyState.vue'
import StatusBadge from '../components/ui/StatusBadge.vue'

const route = useRoute()
</script>

<template>
  <div class="page-stack">
    <p class="page-description">{{ route.meta.description }}</p>
    <AppCard>
      <EmptyState :title="`${route.meta.title} is on the way`" description="This destination is part of the MyHarf workspace foundation. Its workflow will be added in a later phase.">
        <StatusBadge>FOUNDATION PHASE</StatusBadge>
      </EmptyState>
    </AppCard>
  </div>
</template>
