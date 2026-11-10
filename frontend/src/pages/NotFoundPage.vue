<script setup lang="ts">
import AppButton from '../components/ui/AppButton.vue'
import AppCard from '../components/ui/AppCard.vue'
import EmptyState from '../components/ui/EmptyState.vue'
</script>

<template>
  <div class="page-stack">
    <AppCard>
      <EmptyState title="We couldn’t find that page" description="The address may be incomplete or the page may have moved.">
        <RouterLink to="/"><AppButton>Back to dashboard</AppButton></RouterLink>
      </EmptyState>
    </AppCard>
  </div>
</template>
