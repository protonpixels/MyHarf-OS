<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ApiClientError } from '../../../api/errors'
import AppButton from '../../../components/ui/AppButton.vue'
import AppCard from '../../../components/ui/AppCard.vue'
import EmptyState from '../../../components/ui/EmptyState.vue'
import { getCustomer } from '../../customers/customerService'
import type { Customer } from '../../customers/types'
import { diagnosticErrorMessages, type DiagnosticFieldErrors } from '../diagnosticFormValidation'
import { createCustomerDiagnostic } from '../diagnosticService'
import type { DiagnosticCreatePayload } from '../types'
import DiagnosticForm from '../components/DiagnosticForm.vue'

const props = defineProps<{ customerId: string }>()
const router = useRouter()
const customer = ref<Customer | null>(null)
const loading = ref(true)
const missing = ref(false)
const loadError = ref('')
const saving = ref(false)
const fieldErrors = ref<DiagnosticFieldErrors>({})
const generalErrors = ref<string[]>([])
let loadSequence = 0
let saveSequence = 0
const numericCustomerId = computed(() => Number(props.customerId))

async function loadCustomer() {
  const sequence = ++loadSequence
  const customerId = numericCustomerId.value
  loading.value = true
  customer.value = null
  missing.value = false
  loadError.value = ''
  generalErrors.value = []
  fieldErrors.value = {}
  saving.value = false
  saveSequence += 1
  if (!Number.isSafeInteger(customerId) || customerId <= 0) {
    missing.value = true
    loading.value = false
    return
  }
  try {
    const result = await getCustomer(customerId)
    if (sequence !== loadSequence) return
    customer.value = result
  } catch (cause) {
    if (sequence !== loadSequence) return
    if (cause instanceof ApiClientError && cause.status === 404) missing.value = true
    else loadError.value = cause instanceof Error ? cause.message : 'Customer details could not be loaded.'
  } finally {
    if (sequence === loadSequence) loading.value = false
  }
}

async function submit(payload: DiagnosticCreatePayload) {
  if (!customer.value || customer.value.status !== 'active' || saving.value) return
  const customerId = customer.value.id
  const sequence = ++saveSequence
  saving.value = true
  fieldErrors.value = {}
  generalErrors.value = []
  try {
    const diagnostic = await createCustomerDiagnostic(customerId, payload)
    if (sequence !== saveSequence || numericCustomerId.value !== customerId) return
    await router.push({ name: 'diagnostic-workspace', params: { diagnosticId: diagnostic.id } })
  } catch (cause) {
    if (sequence !== saveSequence || numericCustomerId.value !== customerId) return
    const normalized = diagnosticErrorMessages(cause)
    fieldErrors.value = normalized.fieldErrors
    generalErrors.value = normalized.generalErrors.length
      ? normalized.generalErrors
      : ['Please review the highlighted fields and try again.']
  } finally {
    if (sequence === saveSequence) saving.value = false
  }
}

function clearFieldError(field: keyof DiagnosticFieldErrors) {
  delete fieldErrors.value[field]
  generalErrors.value = []
}

watch(() => props.customerId, () => { void loadCustomer() }, { immediate: true })
</script>

<template>
  <div class="page-stack diagnostic-create-page">
    <RouterLink class="back-link" :to="{ name: 'customer-overview', params: { customerId: customerId } }">← Back to customer</RouterLink>
    <div v-if="loading" class="loading-panel" role="status"><span class="loading-spinner" aria-hidden="true" />Loading customer…</div>
    <AppCard v-else-if="missing" class="directory-state"><EmptyState title="Customer not found" description="This customer may have been removed or the address may be incorrect."><RouterLink class="button button--secondary" :to="{ name: 'customers' }">Back to customers</RouterLink></EmptyState></AppCard>
    <AppCard v-else-if="loadError" class="directory-state"><EmptyState title="Customer details didn’t load" :description="loadError"><AppButton variant="secondary" @click="loadCustomer">Try again</AppButton></EmptyState></AppCard>
    <AppCard v-else-if="customer?.status === 'archived'" class="directory-state"><EmptyState title="Customer is archived" description="The backend does not allow new diagnostics for archived customers. The existing customer record remains available for reference."><RouterLink class="button button--secondary" :to="{ name: 'customer-overview', params: { customerId: customer.id } }">Return to customer</RouterLink></EmptyState></AppCard>
    <AppCard v-else-if="customer" class="customer-form-card">
      <div class="form-card-heading"><span class="form-step">WEBSITE INSPECTION</span><h2>New diagnostic</h2><p>For {{ customer.name }}. The diagnostic will remain associated with this customer.</p></div>
      <DiagnosticForm :customer-id="customer.id" :busy="saving" :field-errors="fieldErrors" :general-errors="generalErrors" @submit="submit" @clear-field-error="clearFieldError" />
    </AppCard>
  </div>
</template>
