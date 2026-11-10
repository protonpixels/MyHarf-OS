<script setup lang="ts">
import { ref, watch } from 'vue'
import { ApiClientError } from '../../../api/errors'
import AppButton from '../../../components/ui/AppButton.vue'
import AppCard from '../../../components/ui/AppCard.vue'
import EmptyState from '../../../components/ui/EmptyState.vue'
import CustomerForm from '../components/CustomerForm.vue'
import { customerErrorMessages, type CustomerFieldErrors } from '../customerFormValidation'
import { getCustomer, updateCustomer } from '../customerService'
import type { Customer, CustomerPayload } from '../types'

const props = defineProps<{ customerId: string }>()
const customer = ref<Customer | null>(null)
const loading = ref(true)
const saving = ref(false)
const loadError = ref('')
const missing = ref(false)
const successMessage = ref('')
const fieldErrors = ref<CustomerFieldErrors>({})
const generalErrors = ref<string[]>([])
let loadSequence = 0
let saveSequence = 0

async function load() {
  const sequence = ++loadSequence
  const id = Number(props.customerId)
  loading.value = true
  customer.value = null
  loadError.value = ''
  missing.value = false
  saving.value = false
  successMessage.value = ''
  fieldErrors.value = {}
  generalErrors.value = []
  saveSequence += 1
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

async function submit(payload: CustomerPayload) {
  if (!customer.value || saving.value) return
  const customerId = customer.value.id
  const sequence = ++saveSequence
  saving.value = true
  fieldErrors.value = {}
  generalErrors.value = []
  successMessage.value = ''
  try {
    const result = await updateCustomer(customerId, payload)
    if (sequence !== saveSequence || Number(props.customerId) !== customerId) return
    customer.value = result
    successMessage.value = 'Customer details saved.'
  } catch (error) {
    if (sequence !== saveSequence || Number(props.customerId) !== customerId) return
    const normalized = customerErrorMessages(error)
    fieldErrors.value = normalized.fieldErrors
    generalErrors.value = normalized.generalErrors.length ? normalized.generalErrors : ['Please review the highlighted fields and try again.']
  } finally {
    if (sequence === saveSequence) saving.value = false
  }
}

function clearFieldError(field: keyof CustomerFieldErrors) {
  delete fieldErrors.value[field]
  generalErrors.value = []
  successMessage.value = ''
}

watch(() => props.customerId, () => { void load() }, { immediate: true })
</script>

<template>
  <div class="page-stack customer-edit-page">
    <p class="page-description">Update contact information for this customer.</p>
    <div v-if="loading" class="loading-panel" role="status"><span class="loading-spinner" aria-hidden="true" />Loading customer details…</div>
    <AppCard v-else-if="missing" class="directory-state"><EmptyState title="Customer not found" description="This customer may have been removed or the address may be incorrect."><RouterLink class="button button--secondary" :to="{ name: 'customers' }">Back to customers</RouterLink></EmptyState></AppCard>
    <AppCard v-else-if="loadError" class="directory-state"><EmptyState title="Customer details didn’t load" :description="loadError"><AppButton variant="secondary" @click="load">Try again</AppButton></EmptyState></AppCard>
    <AppCard v-else-if="customer" class="customer-form-card">
      <div class="form-card-heading"><span class="form-step">CUSTOMER DETAILS</span><h2>Edit {{ customer.name }}</h2><p>Update the customer’s contact information.</p></div>
      <div v-if="successMessage" class="feedback feedback--success form-feedback" role="status">{{ successMessage }}</div>
      <CustomerForm :key="customer.id" :customer="customer" :busy="saving" :field-errors="fieldErrors" :general-errors="generalErrors" @submit="submit" @clear-field-error="clearFieldError" />
    </AppCard>
  </div>
</template>
