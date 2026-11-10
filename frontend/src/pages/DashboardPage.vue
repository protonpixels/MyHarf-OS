<script setup lang="ts">
import AppCard from '../components/ui/AppCard.vue'
import EmptyState from '../components/ui/EmptyState.vue'
import StatusBadge from '../components/ui/StatusBadge.vue'
</script>

<template>
  <div class="page-stack">
    <section class="welcome-panel">
      <div>
        <StatusBadge tone="neutral">WORKSPACE FOUNDATION</StatusBadge>
        <h2>Your operations, in one place.</h2>
        <p>The MyHarf workspace is ready to grow. Choose an area to get started.</p>
      </div>
      <div class="welcome-decoration" aria-hidden="true"><span /><span /><span /></div>
    </section>
    <AppCard>
      <EmptyState title="Your dashboard is ready" description="Customer, diagnostic, fix, and quotation workflows will appear here as they are introduced." />
    </AppCard>
    <div class="quick-links" aria-label="Workspace areas">
      <RouterLink class="quick-link" to="/customers"><span class="quick-link-number">01</span><span><strong>Customers</strong><small>Customer workspace</small></span><span class="quick-arrow" aria-hidden="true">↗</span></RouterLink>
      <RouterLink class="quick-link" to="/fixes"><span class="quick-link-number">02</span><span><strong>Fix Ledger</strong><small>Actionable website fixes</small></span><span class="quick-arrow" aria-hidden="true">↗</span></RouterLink>
      <RouterLink class="quick-link" to="/quotations"><span class="quick-link-number">03</span><span><strong>Quotations</strong><small>Itemized proposals</small></span><span class="quick-arrow" aria-hidden="true">↗</span></RouterLink>
    </div>
  </div>
</template>
