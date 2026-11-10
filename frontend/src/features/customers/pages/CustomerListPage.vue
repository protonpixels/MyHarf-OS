<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import AppButton from '../../../components/ui/AppButton.vue'
import AppCard from '../../../components/ui/AppCard.vue'
import EmptyState from '../../../components/ui/EmptyState.vue'
import StatusBadge from '../../../components/ui/StatusBadge.vue'
import { filterCustomers } from '../customerFilters'
import { listCustomers } from '../customerService'
import type { Customer, CustomerStatusFilter } from '../types'

const customers = ref<Customer[]>([])
const statusFilter = ref<CustomerStatusFilter>('active')
const searchInput = ref('')
const searchTerm = ref('')
const loading = ref(false)
const loadError = ref('')
let requestSequence = 0
let searchTimer: ReturnType<typeof setTimeout> | undefined

const filteredCustomers = computed(() => filterCustomers(customers.value, statusFilter.value, searchTerm.value))

watch(searchInput, (value) => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { searchTerm.value = value }, 180)
})

watch(statusFilter, () => { void load() })

async function load() {
  const sequence = ++requestSequence
  loading.value = true
  loadError.value = ''
  try {
    customers.value = await listCustomers(statusFilter.value !== 'active')
  } catch (error) {
    if (sequence !== requestSequence) return
    loadError.value = error instanceof Error ? error.message : 'Customers could not be loaded. Try again.'
  } finally {
    if (sequence === requestSequence) loading.value = false
  }
}

function formatDate(value: string) {
  const date = new Date(value)
  return Number.isNaN(date.valueOf()) ? '—' : new Intl.DateTimeFormat(undefined, { year: 'numeric', month: 'short', day: 'numeric' }).format(date)
}

onMounted(() => { void load() })
onBeforeUnmount(() => clearTimeout(searchTimer))
</script>

<template>
  <div class="page-stack customer-directory">
    <div class="page-heading-row">
      <div><p class="page-description">Keep contact details organized and find the right customer quickly.</p></div>
      <RouterLink class="button button--primary" :to="{ name: 'customer-create' }">＋ New customer</RouterLink>
    </div>

    <AppCard class="directory-tools">
      <div class="directory-search">
        <label class="visually-hidden" for="customer-search">Search customers</label>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><circle cx="10.8" cy="10.8" r="6.8" /><path d="m16 16 4.5 4.5" /></svg>
        <input id="customer-search" v-model="searchInput" type="search" placeholder="Search name, business, email, or phone" autocomplete="off" />
      </div>
      <div class="customer-filters" role="group" aria-label="Filter customers by status">
        <button v-for="option in ([['active', 'Active'], ['archived', 'Archived'], ['all', 'All']] as const)" :key="option[0]" type="button" class="filter-button" :class="{ 'filter-button--selected': statusFilter === option[0] }" :aria-pressed="statusFilter === option[0]" @click="statusFilter = option[0]">{{ option[1] }}</button>
      </div>
    </AppCard>

    <div v-if="loading" class="loading-panel" role="status" aria-live="polite"><span class="loading-spinner" aria-hidden="true" />Loading customers…</div>
    <AppCard v-else-if="loadError" class="directory-state">
      <EmptyState title="Customers didn’t load" :description="loadError"><AppButton variant="secondary" @click="load">Try again</AppButton></EmptyState>
    </AppCard>
    <AppCard v-else-if="filteredCustomers.length === 0" class="directory-state">
      <EmptyState
        :title="searchTerm ? 'No matching customers' : statusFilter === 'active' ? 'No active customers yet' : statusFilter === 'archived' ? 'No archived customers' : 'No customers yet'"
        :description="searchTerm ? 'Try a different name, business name, email, or phone number.' : statusFilter === 'active' ? 'Create a customer record to start building your workspace.' : statusFilter === 'archived' ? 'Archived customers will appear here.' : 'Create a customer record to get started.'"
      >
        <RouterLink v-if="statusFilter === 'active' && !searchTerm" class="button button--primary" :to="{ name: 'customer-create' }">Create customer</RouterLink>
      </EmptyState>
    </AppCard>
    <AppCard v-else class="directory-results">
      <div class="results-caption" aria-live="polite">{{ filteredCustomers.length }} {{ filteredCustomers.length === 1 ? 'customer' : 'customers' }}<span>·</span>{{ statusFilter === 'all' ? 'All statuses' : statusFilter === 'active' ? 'Active only' : 'Archived only' }}</div>
      <div class="customer-table-wrap">
        <table class="customer-table">
          <thead><tr><th scope="col">Customer</th><th scope="col">Contact</th><th scope="col">Status</th><th scope="col">Created</th></tr></thead>
          <tbody>
            <tr v-for="customer in filteredCustomers" :key="customer.id">
              <td><RouterLink class="customer-primary-link" :to="{ name: 'customer-overview', params: { customerId: customer.id } }">{{ customer.name }}</RouterLink><span class="customer-secondary">{{ customer.business_name || '—' }}</span></td>
              <td><a v-if="customer.email" class="customer-contact" :href="`mailto:${customer.email}`">{{ customer.email }}</a><span v-else class="customer-secondary">No email</span><a v-if="customer.phone" class="customer-contact" :href="`tel:${customer.phone}`">{{ customer.phone }}</a><span v-else class="customer-secondary">No phone</span></td>
              <td><StatusBadge :tone="customer.status === 'active' ? 'success' : 'neutral'">{{ customer.status === 'active' ? 'Active' : 'Archived' }}</StatusBadge></td>
              <td class="date-cell">{{ formatDate(customer.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="customer-cards">
        <article v-for="customer in filteredCustomers" :key="customer.id" class="customer-mobile-card">
          <div class="mobile-card-heading"><RouterLink class="customer-primary-link" :to="{ name: 'customer-overview', params: { customerId: customer.id } }">{{ customer.name }}</RouterLink><StatusBadge :tone="customer.status === 'active' ? 'success' : 'neutral'">{{ customer.status === 'active' ? 'Active' : 'Archived' }}</StatusBadge></div>
          <p class="mobile-business-name">{{ customer.business_name || 'Business name not provided' }}</p>
          <a v-if="customer.email" class="customer-contact" :href="`mailto:${customer.email}`">{{ customer.email }}</a>
          <a v-if="customer.phone" class="customer-contact" :href="`tel:${customer.phone}`">{{ customer.phone }}</a>
          <span class="customer-secondary">Added {{ formatDate(customer.created_at) }}</span>
        </article>
      </div>
    </AppCard>
  </div>
</template>
