<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { ApiClientError } from '../../../api/errors'
import AppButton from '../../../components/ui/AppButton.vue'
import AppCard from '../../../components/ui/AppCard.vue'
import EmptyState from '../../../components/ui/EmptyState.vue'
import StatusBadge from '../../../components/ui/StatusBadge.vue'
import { findingErrorMessages, type FindingFieldErrors } from '../findingFormValidation'
import { archiveFinding, createFinding, listDiagnosticFindings, updateFinding } from '../findingService'
import type { DiagnosticStatus, Finding, FindingCreatePayload, FindingStatus, FindingUpdatePayload } from '../types'
import FindingForm from './FindingForm.vue'

const props = defineProps<{ diagnosticId: number; diagnosticStatus: DiagnosticStatus }>()
const findings = ref<Finding[]>([])
const loading = ref(true)
const loadError = ref('')
const includeArchived = ref(false)
const formDialog = ref<HTMLDialogElement | null>(null)
const archiveDialog = ref<HTMLDialogElement | null>(null)
const editingFinding = ref<Finding | null>(null)
const findingToArchive = ref<Finding | null>(null)
const saving = ref(false)
const archiving = ref(false)
const fieldErrors = ref<FindingFieldErrors>({})
const generalErrors = ref<string[]>([])
const archiveError = ref('')
const successMessage = ref('')
let requestSequence = 0
let mutationSequence = 0

const visibleFindings = computed(() => includeArchived.value
  ? findings.value
  : findings.value.filter((finding) => finding.status !== 'archived'))
const canCreate = computed(() => props.diagnosticStatus !== 'archived')

function statusLabel(status: FindingStatus) {
  return status.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function statusTone(status: FindingStatus) {
  if (status === 'reviewed') return 'success'
  if (status === 'dismissed') return 'warning'
  return 'neutral'
}

function formatDate(value: string) {
  const date = new Date(value)
  return Number.isNaN(date.valueOf()) ? '—' : new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' }).format(date)
}

function closeFormDialog() {
  if (formDialog.value?.open) formDialog.value.close()
  editingFinding.value = null
  generalErrors.value = []
  fieldErrors.value = {}
}

function closeArchiveDialog() {
  if (archiveDialog.value?.open) archiveDialog.value.close()
  findingToArchive.value = null
  archiveError.value = ''
}

async function openCreateDialog() {
  editingFinding.value = null
  fieldErrors.value = {}
  generalErrors.value = []
  successMessage.value = ''
  await nextTick()
  formDialog.value?.showModal()
}

async function openEditDialog(finding: Finding) {
  editingFinding.value = finding
  fieldErrors.value = {}
  generalErrors.value = []
  successMessage.value = ''
  await nextTick()
  formDialog.value?.showModal()
}

function openArchiveDialog(finding: Finding) {
  findingToArchive.value = finding
  archiveError.value = ''
  archiveDialog.value?.showModal()
}

async function load() {
  const sequence = ++requestSequence
  mutationSequence += 1
  findings.value = []
  loadError.value = ''
  successMessage.value = ''
  saving.value = false
  archiving.value = false
  closeFormDialog()
  closeArchiveDialog()
  loading.value = true
  try {
    const result = await listDiagnosticFindings(props.diagnosticId)
    if (sequence !== requestSequence) return
    findings.value = result
  } catch (cause) {
    if (sequence !== requestSequence) return
    loadError.value = cause instanceof ApiClientError && cause.status === 404
      ? 'This diagnostic could not be found.'
      : cause instanceof Error ? cause.message : 'Findings could not be loaded.'
  } finally {
    if (sequence === requestSequence) loading.value = false
  }
}

async function saveFinding(payload: FindingCreatePayload | FindingUpdatePayload) {
  if (!canCreate.value || saving.value || archiving.value) return
  const diagnosticId = props.diagnosticId
  const editingId = editingFinding.value?.id
  const sequence = ++mutationSequence
  saving.value = true
  fieldErrors.value = {}
  generalErrors.value = []
  successMessage.value = ''
  try {
    const saved = editingId
      ? await updateFinding(editingId, payload as FindingUpdatePayload)
      : await createFinding(diagnosticId, payload as FindingCreatePayload)
    if (sequence !== mutationSequence || diagnosticId !== props.diagnosticId) return
    const index = findings.value.findIndex((finding) => finding.id === saved.id)
    if (index < 0) findings.value = [...findings.value, saved]
    else findings.value[index] = saved
    successMessage.value = editingId ? 'Finding updated.' : 'Finding created.'
    closeFormDialog()
  } catch (cause) {
    if (sequence !== mutationSequence || diagnosticId !== props.diagnosticId) return
    const normalized = findingErrorMessages(cause)
    fieldErrors.value = normalized.fieldErrors
    generalErrors.value = normalized.generalErrors.length
      ? normalized.generalErrors
      : ['Please review the highlighted fields and try again.']
  } finally {
    if (sequence === mutationSequence) saving.value = false
  }
}

function clearFieldError(field: keyof FindingFieldErrors) {
  delete fieldErrors.value[field]
  generalErrors.value = []
}

async function confirmArchive() {
  const finding = findingToArchive.value
  if (!finding || finding.status === 'archived' || !canCreate.value || archiving.value || saving.value) return
  const diagnosticId = props.diagnosticId
  const sequence = ++mutationSequence
  archiving.value = true
  archiveError.value = ''
  successMessage.value = ''
  try {
    const archived = await archiveFinding(finding.id)
    if (sequence !== mutationSequence || diagnosticId !== props.diagnosticId) return
    const index = findings.value.findIndex((item) => item.id === archived.id)
    if (index >= 0) findings.value[index] = archived
    successMessage.value = 'Finding archived.'
    closeArchiveDialog()
  } catch (cause) {
    if (sequence !== mutationSequence || diagnosticId !== props.diagnosticId) return
    archiveError.value = cause instanceof Error ? cause.message : 'Finding could not be archived. Try again.'
  } finally {
    if (sequence === mutationSequence) archiving.value = false
  }
}

watch(() => props.diagnosticId, () => { void load() }, { immediate: true })
</script>

<template>
  <section class="findings-section" aria-labelledby="findings-title">
    <div class="section-heading findings-heading">
      <div><span class="form-step">OBSERVATIONS</span><h2 id="findings-title">Findings</h2></div>
      <AppButton v-if="canCreate" @click="openCreateDialog">Add finding</AppButton>
    </div>
    <p v-if="diagnosticStatus === 'archived'" class="feedback feedback--archived" role="status">This diagnostic is archived. Existing findings are available as read-only records.</p>
    <p v-if="successMessage" class="feedback feedback--success" role="status">{{ successMessage }}</p>
    <AppCard v-if="loading" class="findings-state"><div class="loading-panel" role="status"><span class="loading-spinner" aria-hidden="true" />Loading findings…</div></AppCard>
    <AppCard v-else-if="loadError" class="findings-state"><EmptyState title="Findings didn’t load" :description="loadError"><AppButton variant="secondary" @click="load">Try again</AppButton></EmptyState></AppCard>
    <AppCard v-else class="findings-card">
      <div class="findings-toolbar">
        <p>{{ visibleFindings.length }} {{ visibleFindings.length === 1 ? 'finding' : 'findings' }}</p>
        <label class="archived-toggle"><input v-model="includeArchived" type="checkbox" /> Include archived</label>
      </div>
      <EmptyState v-if="!visibleFindings.length" title="No findings yet" :description="includeArchived ? 'No findings are recorded for this diagnostic.' : 'Record observed issues here as you inspect the website.'" />
      <ul v-else class="finding-list">
        <li v-for="finding in visibleFindings" :key="finding.id" class="finding-card" :class="{ 'finding-card--archived': finding.status === 'archived' }">
          <div class="finding-card-heading">
            <div><h3>{{ finding.title }}</h3><p class="finding-created">Created {{ formatDate(finding.created_at) }}</p></div>
            <StatusBadge :tone="finding.status === 'archived' ? 'neutral' : statusTone(finding.status)">{{ statusLabel(finding.status) }}</StatusBadge>
          </div>
          <p v-if="finding.description" class="finding-description">{{ finding.description }}</p>
          <p v-if="finding.page_url" class="finding-detail"><strong>Page</strong><a :href="finding.page_url" target="_blank" rel="noreferrer">{{ finding.page_url }}</a></p>
          <p v-if="finding.evidence" class="finding-detail finding-evidence"><strong>Evidence</strong><span>{{ finding.evidence }}</span></p>
          <div v-if="canCreate && finding.status !== 'archived'" class="finding-actions">
            <AppButton variant="secondary" @click="openEditDialog(finding)">Edit</AppButton>
            <AppButton variant="danger" @click="openArchiveDialog(finding)">Archive</AppButton>
          </div>
        </li>
      </ul>
    </AppCard>

    <dialog ref="formDialog" class="confirm-dialog record-form-dialog" aria-labelledby="finding-form-title" @cancel.prevent="closeFormDialog">
      <div class="form-card-heading"><span class="form-step">OBSERVED ISSUE</span><h2 id="finding-form-title">{{ editingFinding ? 'Edit finding' : 'New finding' }}</h2><p>Findings record observations. Actionable fixes are managed separately.</p></div>
      <FindingForm :key="editingFinding?.id ?? 'new'" :finding="editingFinding" :busy="saving" :field-errors="fieldErrors" :general-errors="generalErrors" @create="saveFinding" @update="saveFinding" @cancel="closeFormDialog" @clear-field-error="clearFieldError" />
    </dialog>

    <dialog ref="archiveDialog" class="confirm-dialog" aria-labelledby="finding-archive-title" aria-describedby="finding-archive-description" @cancel.prevent="closeArchiveDialog">
      <div class="dialog-symbol" aria-hidden="true">!</div>
      <h2 id="finding-archive-title">Archive this finding?</h2>
      <p id="finding-archive-description">The finding will be retained and can be viewed with Include archived. It will not be permanently deleted.</p>
      <p v-if="archiveError" class="feedback feedback--error dialog-error" role="alert">{{ archiveError }}</p>
      <div class="dialog-actions"><AppButton variant="secondary" :disabled="archiving" @click="closeArchiveDialog">Cancel</AppButton><AppButton variant="danger" :disabled="archiving" @click="confirmArchive">{{ archiving ? 'Archiving…' : 'Archive finding' }}</AppButton></div>
    </dialog>
  </section>
</template>
