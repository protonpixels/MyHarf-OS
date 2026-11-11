<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { ApiClientError } from '../../../api/errors'
import AppButton from '../../../components/ui/AppButton.vue'
import AppCard from '../../../components/ui/AppCard.vue'
import EmptyState from '../../../components/ui/EmptyState.vue'
import StatusBadge from '../../../components/ui/StatusBadge.vue'
import { getCustomer } from '../../customers/customerService'
import type { Customer } from '../../customers/types'
import { diagnosticErrorMessages, type DiagnosticFieldErrors } from '../diagnosticFormValidation'
import { archiveDiagnostic, getDiagnostic, updateDiagnostic } from '../diagnosticService'
import type { Diagnostic, DiagnosticStatus, DiagnosticUpdatePayload, EditableDiagnosticStatus } from '../types'
import DiagnosticEditForm from '../components/DiagnosticEditForm.vue'
import FindingsSection from '../components/FindingsSection.vue'

const props = defineProps<{ diagnosticId: string }>()
const diagnostic = ref<Diagnostic | null>(null)
const customer = ref<Customer | null>(null)
const loading = ref(true)
const missing = ref(false)
const loadError = ref('')
const customerLoading = ref(false)
const customerError = ref('')
const statusValue = ref<EditableDiagnosticStatus>('planned')
const statusError = ref('')
const successMessage = ref('')
const editDialog = ref<HTMLDialogElement | null>(null)
const archiveDialog = ref<HTMLDialogElement | null>(null)
const editing = ref(false)
const savingEdit = ref(false)
const savingStatus = ref(false)
const archiving = ref(false)
const editFieldErrors = ref<DiagnosticFieldErrors>({})
const editGeneralErrors = ref<string[]>([])
const archiveError = ref('')
let loadSequence = 0
let mutationSequence = 0

const numericDiagnosticId = computed(() => Number(props.diagnosticId))
const archived = computed(() => diagnostic.value?.status === 'archived')
const mutationBusy = computed(() => savingEdit.value || savingStatus.value || archiving.value)

function statusLabel(status: DiagnosticStatus) {
  return status.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function formatDate(value: string) {
  const date = new Date(value)
  return Number.isNaN(date.valueOf())
    ? '—'
    : new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(date)
}

function closeEditDialog() {
  if (editDialog.value?.open) editDialog.value.close()
  editing.value = false
  editFieldErrors.value = {}
  editGeneralErrors.value = []
}

function closeArchiveDialog() {
  if (archiveDialog.value?.open) archiveDialog.value.close()
  archiveError.value = ''
}

async function openEditDialog() {
  if (!diagnostic.value || archived.value || mutationBusy.value) return
  editing.value = true
  editFieldErrors.value = {}
  editGeneralErrors.value = []
  successMessage.value = ''
  await nextTick()
  editDialog.value?.showModal()
}

function openArchiveDialog() {
  if (!diagnostic.value || archived.value || mutationBusy.value) return
  archiveError.value = ''
  archiveDialog.value?.showModal()
}

async function loadCustomer(customerId: number, workspaceSequence: number) {
  customerLoading.value = true
  customerError.value = ''
  try {
    const result = await getCustomer(customerId)
    if (workspaceSequence !== loadSequence) return
    customer.value = result
  } catch (cause) {
    if (workspaceSequence !== loadSequence) return
    customerError.value = cause instanceof Error ? cause.message : 'Customer information is unavailable.'
  } finally {
    if (workspaceSequence === loadSequence) customerLoading.value = false
  }
}

async function loadWorkspace() {
  const sequence = ++loadSequence
  mutationSequence += 1
  const id = numericDiagnosticId.value
  diagnostic.value = null
  customer.value = null
  missing.value = false
  loadError.value = ''
  customerError.value = ''
  statusError.value = ''
  successMessage.value = ''
  archiveError.value = ''
  editFieldErrors.value = {}
  editGeneralErrors.value = []
  loading.value = true
  customerLoading.value = false
  savingEdit.value = false
  savingStatus.value = false
  archiving.value = false
  closeEditDialog()
  closeArchiveDialog()

  if (!Number.isSafeInteger(id) || id <= 0) {
    missing.value = true
    loading.value = false
    return
  }
  try {
    const result = await getDiagnostic(id)
    if (sequence !== loadSequence) return
    diagnostic.value = result
    statusValue.value = result.status === 'archived' ? 'planned' : result.status
    loading.value = false
    void loadCustomer(result.customer_id, sequence)
  } catch (cause) {
    if (sequence !== loadSequence) return
    if (cause instanceof ApiClientError && cause.status === 404) missing.value = true
    else loadError.value = cause instanceof Error ? cause.message : 'The diagnostic could not be loaded.'
  } finally {
    if (sequence === loadSequence) loading.value = false
  }
}

async function saveDiagnostic(payload: DiagnosticUpdatePayload) {
  const current = diagnostic.value
  if (!current || archived.value || mutationBusy.value) return
  const id = current.id
  const sequence = ++mutationSequence
  savingEdit.value = true
  editFieldErrors.value = {}
  editGeneralErrors.value = []
  statusError.value = ''
  successMessage.value = ''
  try {
    const result = await updateDiagnostic(id, payload)
    if (sequence !== mutationSequence || numericDiagnosticId.value !== id) return
    diagnostic.value = result
    successMessage.value = 'Diagnostic details saved.'
    closeEditDialog()
  } catch (cause) {
    if (sequence !== mutationSequence || numericDiagnosticId.value !== id) return
    const normalized = diagnosticErrorMessages(cause)
    editFieldErrors.value = normalized.fieldErrors
    editGeneralErrors.value = normalized.generalErrors.length
      ? normalized.generalErrors
      : ['Please review the highlighted fields and try again.']
  } finally {
    if (sequence === mutationSequence) savingEdit.value = false
  }
}

async function updateStatus(event: Event) {
  const current = diagnostic.value
  if (!current || archived.value || mutationBusy.value) return
  const status = (event.target as HTMLSelectElement).value as EditableDiagnosticStatus
  if (!['planned', 'in_progress', 'completed', 'cancelled'].includes(status)) return
  const id = current.id
  const sequence = ++mutationSequence
  savingStatus.value = true
  statusError.value = ''
  successMessage.value = ''
  try {
    const result = await updateDiagnostic(id, { status })
    if (sequence !== mutationSequence || numericDiagnosticId.value !== id) return
    diagnostic.value = result
    statusValue.value = status
    successMessage.value = 'Diagnostic status updated.'
  } catch (cause) {
    if (sequence !== mutationSequence || numericDiagnosticId.value !== id) return
    statusValue.value = current.status as EditableDiagnosticStatus
    statusError.value = cause instanceof Error ? cause.message : 'Diagnostic status could not be updated.'
  } finally {
    if (sequence === mutationSequence) savingStatus.value = false
  }
}

async function confirmArchive() {
  const current = diagnostic.value
  if (!current || archived.value || mutationBusy.value) return
  const id = current.id
  const sequence = ++mutationSequence
  archiving.value = true
  archiveError.value = ''
  successMessage.value = ''
  try {
    const result = await archiveDiagnostic(id)
    if (sequence !== mutationSequence || numericDiagnosticId.value !== id) return
    diagnostic.value = result
    closeArchiveDialog()
    successMessage.value = 'Diagnostic archived. It is now read-only.'
  } catch (cause) {
    if (sequence !== mutationSequence || numericDiagnosticId.value !== id) return
    archiveError.value = cause instanceof Error ? cause.message : 'Diagnostic could not be archived. Try again.'
  } finally {
    if (sequence === mutationSequence) archiving.value = false
  }
}

function clearEditFieldError(field: keyof DiagnosticFieldErrors) {
  delete editFieldErrors.value[field]
  editGeneralErrors.value = []
}

watch(() => props.diagnosticId, () => { void loadWorkspace() }, { immediate: true })
</script>

<template>
  <div class="page-stack diagnostic-workspace-page">
    <div v-if="loading" class="loading-panel" role="status"><span class="loading-spinner" aria-hidden="true" />Loading diagnostic…</div>
    <AppCard v-else-if="missing" class="directory-state"><EmptyState title="Diagnostic not found" description="This diagnostic may have been removed or the address may be incorrect."><RouterLink class="button button--secondary" :to="{ name: 'customers' }">Back to customers</RouterLink></EmptyState></AppCard>
    <AppCard v-else-if="loadError" class="directory-state"><EmptyState title="Diagnostic didn’t load" :description="loadError"><AppButton variant="secondary" @click="loadWorkspace">Try again</AppButton></EmptyState></AppCard>
    <template v-else-if="diagnostic">
      <div class="workspace-heading">
        <div class="workspace-identity">
          <RouterLink class="back-link" :to="{ name: 'customer-overview', params: { customerId: diagnostic.customer_id } }">← Customer profile</RouterLink>
          <p v-if="customerLoading" class="workspace-customer-context" role="status">Loading customer information…</p>
          <RouterLink v-else-if="customer" class="workspace-customer-context" :to="{ name: 'customer-overview', params: { customerId: customer.id } }">{{ customer.name }}<span v-if="customer.business_name"> · {{ customer.business_name }}</span></RouterLink>
          <p v-else class="workspace-customer-context workspace-customer-error">Customer information is unavailable<span v-if="customerError">: {{ customerError }}</span></p>
          <h2>Diagnostic workspace</h2>
          <a class="workspace-website" :href="diagnostic.website_url" target="_blank" rel="noreferrer">{{ diagnostic.website_url }}</a>
        </div>
        <div class="workspace-actions">
          <StatusBadge :tone="diagnostic.status === 'completed' ? 'success' : diagnostic.status === 'in_progress' ? 'warning' : 'neutral'">{{ statusLabel(diagnostic.status) }}</StatusBadge>
          <AppButton v-if="!archived" variant="secondary" :disabled="mutationBusy" @click="openEditDialog">Edit diagnostic</AppButton>
          <AppButton v-if="!archived" variant="danger" :disabled="mutationBusy" @click="openArchiveDialog">Archive diagnostic</AppButton>
        </div>
      </div>

      <p v-if="archived" class="feedback feedback--archived" role="status">This diagnostic is archived and read-only. Existing findings remain available below.</p>
      <p v-if="successMessage" class="feedback feedback--success" role="status">{{ successMessage }}</p>
      <p v-if="statusError" class="feedback feedback--error" role="alert">{{ statusError }}</p>

      <div class="workspace-grid">
        <AppCard class="diagnostic-details-card">
          <div class="section-heading"><div><span class="form-step">ASSESSMENT</span><h3>Diagnostic details</h3></div></div>
          <p v-if="diagnostic.summary" class="diagnostic-workspace-summary">{{ diagnostic.summary }}</p>
          <p v-else class="diagnostic-workspace-summary diagnostic-workspace-summary--empty">No summary provided.</p>
          <dl class="diagnostic-metadata">
            <div><dt>Status</dt><dd>{{ statusLabel(diagnostic.status) }}</dd></div>
            <div v-if="!archived" class="diagnostic-status-control"><dt><label for="diagnostic-status">Update status</label></dt><dd><select id="diagnostic-status" v-model="statusValue" :disabled="mutationBusy" @change="updateStatus"><option value="planned">Planned</option><option value="in_progress">In Progress</option><option value="completed">Completed</option><option value="cancelled">Cancelled</option></select><small>Status changes are explicit; the backend does not enforce a transition sequence.</small></dd></div>
            <div><dt>Created</dt><dd>{{ formatDate(diagnostic.created_at) }}</dd></div>
            <div><dt>Last updated</dt><dd>{{ formatDate(diagnostic.updated_at) }}</dd></div>
          </dl>
        </AppCard>
      </div>

      <FindingsSection :diagnostic-id="diagnostic.id" :diagnostic-status="diagnostic.status" />
    </template>

    <dialog ref="editDialog" class="confirm-dialog record-form-dialog" aria-labelledby="diagnostic-edit-title" @cancel.prevent="closeEditDialog">
      <div class="form-card-heading"><span class="form-step">ASSESSMENT DETAILS</span><h2 id="diagnostic-edit-title">Edit diagnostic</h2><p>Update the website address and summary. Leave the summary blank to clear it.</p></div>
      <DiagnosticEditForm v-if="editing && diagnostic && !archived" :key="diagnostic.id" :diagnostic="diagnostic" :busy="savingEdit" :field-errors="editFieldErrors" :general-errors="editGeneralErrors" @submit="saveDiagnostic" @cancel="closeEditDialog" @clear-field-error="clearEditFieldError" />
    </dialog>

    <dialog ref="archiveDialog" class="confirm-dialog" aria-labelledby="diagnostic-archive-title" aria-describedby="diagnostic-archive-description" @cancel.prevent="closeArchiveDialog">
      <div class="dialog-symbol" aria-hidden="true">!</div>
      <h2 id="diagnostic-archive-title">Archive this diagnostic?</h2>
      <p id="diagnostic-archive-description">The diagnostic and its findings will be retained for reference. Archiving prevents new findings and makes this workspace read-only. It does not permanently delete data.</p>
      <p v-if="archiveError" class="feedback feedback--error dialog-error" role="alert">{{ archiveError }}</p>
      <div class="dialog-actions"><AppButton variant="secondary" :disabled="archiving" @click="closeArchiveDialog">Cancel</AppButton><AppButton variant="danger" :disabled="archiving" @click="confirmArchive">{{ archiving ? 'Archiving…' : 'Archive diagnostic' }}</AppButton></div>
    </dialog>
  </div>
</template>
