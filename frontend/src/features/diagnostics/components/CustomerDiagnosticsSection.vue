<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ApiClientError } from '../../../api/errors'
import AppButton from '../../../components/ui/AppButton.vue'
import AppCard from '../../../components/ui/AppCard.vue'
import EmptyState from '../../../components/ui/EmptyState.vue'
import StatusBadge from '../../../components/ui/StatusBadge.vue'
import { listCustomerDiagnostics } from '../diagnosticService'
import type { Diagnostic, DiagnosticStatus } from '../types'

const props = defineProps<{ customerId: number; customerStatus: 'active' | 'archived' }>()
const diagnostics = ref<Diagnostic[]>([])
const loading = ref(true)
const error = ref('')
const includeArchived = ref(false)
let requestSequence = 0

const visibleDiagnostics = computed(() => includeArchived.value
  ? diagnostics.value
  : diagnostics.value.filter((diagnostic) => diagnostic.status !== 'archived'))

function statusLabel(status: DiagnosticStatus) {
  return status.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function statusTone(status: DiagnosticStatus) {
  if (status === 'completed') return 'success'
  if (status === 'in_progress') return 'warning'
  if (status === 'cancelled' || status === 'archived') return 'neutral'
  return 'neutral'
}

function formatDate(value: string) {
  const date = new Date(value)
  return Number.isNaN(date.valueOf()) ? '—' : new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' }).format(date)
}

async function load() {
  const sequence = ++requestSequence
  diagnostics.value = []
  error.value = ''
  loading.value = true
  try {
    const result = await listCustomerDiagnostics(props.customerId)
    if (sequence !== requestSequence) return
    diagnostics.value = result
  } catch (cause) {
    if (sequence !== requestSequence) return
    if (cause instanceof ApiClientError && cause.status === 404) error.value = 'This customer could not be found.'
    else error.value = cause instanceof Error ? cause.message : 'Diagnostics could not be loaded.'
  } finally {
    if (sequence === requestSequence) loading.value = false
  }
}

watch(() => props.customerId, () => { void load() }, { immediate: true })
</script>

<template>
  <section class="diagnostics-section" aria-labelledby="customer-diagnostics-title">
    <div class="section-heading diagnostics-heading">
      <div><span class="form-step">INSPECTIONS</span><h3 id="customer-diagnostics-title">Diagnostics</h3></div>
      <RouterLink v-if="customerStatus === 'active'" class="button button--primary" :aria-disabled="loading" :to="{ name: 'diagnostic-create', params: { customerId } }">New diagnostic</RouterLink>
    </div>
    <p v-if="customerStatus === 'archived'" class="feedback feedback--archived" role="status">This customer is archived. The backend does not allow new diagnostics for archived customers.</p>
    <AppCard v-if="loading" class="diagnostics-state"><div class="loading-panel" role="status"><span class="loading-spinner" aria-hidden="true" />Loading diagnostics…</div></AppCard>
    <AppCard v-else-if="error" class="diagnostics-state"><EmptyState title="Diagnostics didn’t load" :description="error"><AppButton variant="secondary" @click="load">Try again</AppButton></EmptyState></AppCard>
    <AppCard v-else class="diagnostics-card">
      <div class="diagnostics-toolbar">
        <p>{{ visibleDiagnostics.length }} {{ visibleDiagnostics.length === 1 ? 'diagnostic' : 'diagnostics' }}</p>
        <label class="archived-toggle"><input v-model="includeArchived" type="checkbox" /> Include archived</label>
      </div>
      <EmptyState v-if="!visibleDiagnostics.length" title="No diagnostics yet" :description="includeArchived ? 'No diagnostics are recorded for this customer.' : 'Start an inspection to record this customer’s website assessment.'">
        <RouterLink v-if="customerStatus === 'active'" class="button button--secondary" :to="{ name: 'diagnostic-create', params: { customerId } }">Create first diagnostic</RouterLink>
      </EmptyState>
      <ul v-else class="diagnostic-list">
        <li v-for="diagnostic in visibleDiagnostics" :key="diagnostic.id" class="diagnostic-list-item">
          <div class="diagnostic-list-primary">
            <RouterLink class="diagnostic-website-link" :to="{ name: 'diagnostic-workspace', params: { diagnosticId: diagnostic.id } }">{{ diagnostic.website_url }}</RouterLink>
            <p v-if="diagnostic.summary" class="diagnostic-summary">{{ diagnostic.summary }}</p>
            <p class="diagnostic-created">Created {{ formatDate(diagnostic.created_at) }}</p>
          </div>
          <StatusBadge :tone="statusTone(diagnostic.status)">{{ statusLabel(diagnostic.status) }}</StatusBadge>
        </li>
      </ul>
    </AppCard>
  </section>
</template>
