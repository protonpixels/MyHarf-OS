<script setup lang="ts">
import { ref } from 'vue'
import AppCard from '../../../components/ui/AppCard.vue'
import CustomerForm from '../components/CustomerForm.vue'
import { customerErrorMessages, type CustomerFieldErrors } from '../customerFormValidation'
import { createCustomer } from '../customerService'
import type { Customer, CustomerPayload } from '../types'

const saving = ref(false)
const createdCustomer = ref<Customer | null>(null)
const fieldErrors = ref<CustomerFieldErrors>({})
const generalErrors = ref<string[]>([])

async function submit(payload: CustomerPayload) {
  if (saving.value) return
  saving.value = true
  fieldErrors.value = {}
  generalErrors.value = []
  try {
    createdCustomer.value = await createCustomer(payload)
  } catch (error) {
    const normalized = customerErrorMessages(error)
    fieldErrors.value = normalized.fieldErrors
    generalErrors.value = normalized.generalErrors.length ? normalized.generalErrors : ['Please review the highlighted fields and try again.']
  } finally {
    saving.value = false
  }
}

function clearFieldError(field: keyof CustomerFieldErrors) {
  delete fieldErrors.value[field]
  generalErrors.value = []
}
</script>

<template>
  <div class="page-stack customer-edit-page">
    <p class="page-description">Add a business and its primary contact to your customer directory.</p>
    <AppCard v-if="createdCustomer" class="customer-form-card">
      <div class="success-panel" role="status">
        <span class="success-icon" aria-hidden="true">✓</span>
        <h2>Customer created</h2>
        <p>{{ createdCustomer.name }} has been added to your directory.</p>
        <div class="form-actions form-actions--center">
          <RouterLink class="button button--secondary" :to="{ name: 'customers' }">Back to customers</RouterLink>
          <RouterLink class="button button--primary" :to="{ name: 'customer-overview', params: { customerId: createdCustomer.id } }">View customer</RouterLink>
        </div>
      </div>
    </AppCard>
    <AppCard v-else class="customer-form-card">
      <div class="form-card-heading"><span class="form-step">CUSTOMER DETAILS</span><h2>Contact information</h2><p>Fields marked with an asterisk are required.</p></div>
      <CustomerForm :busy="saving" :field-errors="fieldErrors" :general-errors="generalErrors" @submit="submit" @clear-field-error="clearFieldError" />
    </AppCard>
  </div>
</template>
