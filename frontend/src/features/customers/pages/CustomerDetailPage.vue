<script setup lang="ts">
import { ref, watch } from 'vue'
import { ApiClientError } from '../../../api/errors'
import AppButton from '../../../components/ui/AppButton.vue'
import AppCard from '../../../components/ui/AppCard.vue'
import EmptyState from '../../../components/ui/EmptyState.vue'
import StatusBadge from '../../../components/ui/StatusBadge.vue'
import CustomerDiagnosticsSection from '../../diagnostics/components/CustomerDiagnosticsSection.vue'
import { archiveCustomer, getCustomer } from '../customerService'
import type { Customer } from '../types'

const props = defineProps<{ customerId: string }>()
const customer = ref<Customer | null>(null)
const loading = ref(true)
const loadError = ref('')
const missing = ref(false)
const archiveError = ref('')
const archiving = ref(false)
const archiveDialog = ref<HTMLDialogElement | null>(null)
let loadSequence = 0
let archiveSequence = 0

async function load() {
  const sequence = ++loadSequence
  const id = Number(props.customerId)
  loading.value = true
  customer.value = null
  loadError.value = ''
  missing.value = false
  archiveError.value = ''
  archiving.value = false
  archiveSequence += 1
  if (!Number.isSafeInteger(id) || id <= 0) {
    missing.value = true
    loading.value = false
    return
  }
  try {
    const result = await getCustomer(id)
    if (sequence !== loadSequence) return
    customer.value = result
  } catch (error) {
    if (sequence !== loadSequence) return
    if (error instanceof ApiClientError && error.status === 404) missing.value = true
    else loadError.value = error instanceof Error ? error.message : 'Customer details could not be loaded.'
  } finally {
    if (sequence === loadSequence) loading.value = false
  }
}

function openArchiveDialog() {
  archiveError.value = ''
  archiveDialog.value?.showModal()
}

function closeArchiveDialog() {
  if (archiveDialog.value?.open) archiveDialog.value.close()
}

async function confirmArchive() {
  if (!customer.value || customer.value.status === 'archived' || archiving.value) return
  const customerId = customer.value.id
  const sequence = ++archiveSequence
  archiving.value = true
  archiveError.value = ''
  try {
    const result = await archiveCustomer(customerId)
    if (sequence !== archiveSequence || Number(props.customerId) !== customerId) return
    customer.value = result
    closeArchiveDialog()
  } catch (error) {
    if (sequence === archiveSequence && Number(props.customerId) === customerId) {
      archiveError.value = error instanceof Error ? error.message : 'Customer could not be archived. Try again.'
    }
  } finally {
    if (sequence === archiveSequence) archiving.value = false
  }
}

function formatDateTime(value: string) {
  const date = new Date(value)
  return Number.isNaN(date.valueOf())
    ? '—'
    : new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(date)
}

watch(() => props.customerId, () => { void load() }, { immediate: true })
</script>

<template>
  <div class="page-stack customer-profile-page">
    <div v-if="loading" class="loading-panel" role="status"><span class="loading-spinner" aria-hidden="true" />Loading customer…</div>
    <AppCard v-else-if="missing" class="directory-state"><EmptyState title="Customer not found" description="This customer may have been removed or the address may be incorrect."><RouterLink class="button button--secondary" :to="{ name: 'customers' }">Back to customers</RouterLink></EmptyState></AppCard>
    <AppCard v-else-if="loadError" class="directory-state"><EmptyState title="Customer details didn’t load" :description="loadError"><AppButton variant="secondary" @click="load">Try again</AppButton></EmptyState></AppCard>
    <template v-else-if="customer">
      <div class="profile-heading">
        <div class="profile-identity">
          <span class="profile-monogram" aria-hidden="true">{{ customer.name.slice(0, 1).toLocaleUpperCase() }}</span>
          <div><div class="profile-name-line"><h2>{{ customer.name }}</h2><StatusBadge :tone="customer.status === 'active' ? 'success' : 'neutral'">{{ customer.status === 'active' ? 'Active' : 'Archived' }}</StatusBadge></div><p>{{ customer.business_name || 'Business name not provided' }}</p></div>
        </div>
        <div class="profile-actions">
          <RouterLink class="button button--secondary" :to="{ name: 'customer-edit', params: { customerId: customer.id } }">Edit customer</RouterLink>
          <AppButton v-if="customer.status === 'active'" variant="danger" @click="openArchiveDialog">Archive customer</AppButton>
        </div>
      </div>

      <div v-if="customer.status === 'archived'" class="feedback feedback--archived" role="status">This customer is archived. It remains available for reference and is excluded from the active customer list.</div>
      <div class="profile-content-grid">
        <AppCard class="profile-info-card">
          <div class="section-heading"><div><span class="form-step">PROFILE</span><h3>Contact information</h3></div></div>
          <dl class="contact-details">
            <div><dt>Email</dt><dd><a v-if="customer.email" :href="`mailto:${customer.email}`">{{ customer.email }}</a><span v-else class="muted-value">Not provided</span></dd></div>
            <div><dt>Phone</dt><dd><a v-if="customer.phone" :href="`tel:${customer.phone}`">{{ customer.phone }}</a><span v-else class="muted-value">Not provided</span></dd></div>
            <div><dt>Created</dt><dd>{{ formatDateTime(customer.created_at) }}</dd></div>
            <div><dt>Last updated</dt><dd>{{ formatDateTime(customer.updated_at) }}</dd></div>
          </dl>
        </AppCard>
        <aside class="profile-note"><span class="note-mark" aria-hidden="true">M</span><div><strong>Customer workspace</strong><p>This profile is the home for work related to {{ customer.name }}.</p></div></aside>
      </div>

      <section class="future-workspace" aria-labelledby="future-workspace-title">
        <div class="section-heading"><div><span class="form-step">WORKSPACE</span><h3 id="future-workspace-title">Customer activity</h3></div><span class="future-label">EXPANDING IN FUTURE PHASES</span></div>
        <CustomerDiagnosticsSection :customer-id="customer.id" :customer-status="customer.status" />
        <div class="future-section-grid">
          <article v-for="area in ['Findings', 'Fixes', 'Quotations', 'Implementation projects', 'Delivery history']" :key="area" class="future-section-card">
            <div class="future-section-title"><h4>{{ area }}</h4><span aria-hidden="true">↗</span></div>
            <p>Not available in this phase</p>
          </article>
        </div>
      </section>

      <dialog v-if="customer.status === 'active'" ref="archiveDialog" class="confirm-dialog" aria-labelledby="archive-title" aria-describedby="archive-description" @cancel.prevent="closeArchiveDialog">
        <div class="dialog-symbol" aria-hidden="true">!</div>
        <h2 id="archive-title">Archive {{ customer.name }}?</h2>
        <p id="archive-description">Archiving keeps this customer record and its history. It hides the customer from the default active directory. This action does not permanently delete data.</p>
        <p v-if="archiveError" class="feedback feedback--error dialog-error" role="alert">{{ archiveError }}</p>
        <div class="dialog-actions"><AppButton variant="secondary" :disabled="archiving" @click="closeArchiveDialog">Cancel</AppButton><AppButton variant="danger" :disabled="archiving" @click="confirmArchive">{{ archiving ? 'Archiving…' : 'Archive customer' }}</AppButton></div>
      </dialog>
    </template>
  </div>
</template>
