<script setup lang="ts">
import { reactive } from 'vue'
import AppButton from '../../../components/ui/AppButton.vue'
import type { DiagnosticFieldErrors } from '../diagnosticFormValidation'
import { normalizeDiagnosticForm, validateDiagnosticForm } from '../diagnosticFormValidation'
import type { DiagnosticCreatePayload } from '../types'

const props = withDefaults(defineProps<{
  busy?: boolean
  fieldErrors?: DiagnosticFieldErrors
  generalErrors?: string[]
  customerId: number
}>(), { busy: false, fieldErrors: () => ({}), generalErrors: () => [] })
const emit = defineEmits<{
  submit: [payload: DiagnosticCreatePayload]
  'clear-field-error': [field: 'website_url' | 'summary']
}>()
const values = reactive({ website_url: '', summary: '' })
const localErrors = reactive<DiagnosticFieldErrors>({})

function clearError(field: 'website_url' | 'summary') {
  delete localErrors[field]
  emit('clear-field-error', field)
}

function errorFor(field: 'website_url' | 'summary') {
  return localErrors[field] ?? props.fieldErrors[field]
}

function submit() {
  Object.keys(localErrors).forEach((key) => delete localErrors[key as 'website_url' | 'summary'])
  Object.assign(localErrors, validateDiagnosticForm(values))
  if (Object.keys(localErrors).length || props.busy) return
  emit('submit', normalizeDiagnosticForm(values))
}
</script>

<template>
  <form class="customer-form diagnostic-form" novalidate @submit.prevent="submit">
    <div v-if="generalErrors.length" class="feedback feedback--error" role="alert">
      <strong>We couldn’t create this diagnostic.</strong>
      <ul><li v-for="(error, index) in generalErrors" :key="`${index}-${error}`">{{ error }}</li></ul>
    </div>

    <div class="form-field">
      <label for="diagnostic-website-url">Website URL <span aria-hidden="true">*</span></label>
      <input id="diagnostic-website-url" v-model="values.website_url" name="website_url" type="url" inputmode="url" autocomplete="url" placeholder="https://example.com" required :aria-invalid="Boolean(errorFor('website_url'))" :aria-describedby="errorFor('website_url') ? 'diagnostic-website-error' : 'diagnostic-website-hint'" @input="clearError('website_url')" />
      <small id="diagnostic-website-hint">Include the full address starting with http:// or https://.</small>
      <p v-if="errorFor('website_url')" id="diagnostic-website-error" class="field-error" role="alert">{{ errorFor('website_url') }}</p>
    </div>

    <div class="form-field">
      <label for="diagnostic-summary">Summary <span class="optional-label">Optional</span></label>
      <textarea id="diagnostic-summary" v-model="values.summary" name="summary" rows="4" :aria-invalid="Boolean(errorFor('summary'))" :aria-describedby="errorFor('summary') ? 'diagnostic-summary-error' : undefined" @input="clearError('summary')" />
      <p v-if="errorFor('summary')" id="diagnostic-summary-error" class="field-error" role="alert">{{ errorFor('summary') }}</p>
    </div>

    <div class="form-actions">
      <RouterLink class="button button--secondary" :to="{ name: 'customer-overview', params: { customerId } }">Cancel</RouterLink>
      <AppButton type="submit" :disabled="busy">{{ busy ? 'Creating…' : 'Create diagnostic' }}</AppButton>
    </div>
  </form>
</template>
