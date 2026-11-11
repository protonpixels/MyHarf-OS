<script setup lang="ts">
import { reactive, watch } from 'vue'
import AppButton from '../../../components/ui/AppButton.vue'
import type { DiagnosticFieldErrors, DiagnosticFormValues } from '../diagnosticFormValidation'
import { normalizeDiagnosticUpdateForm, validateDiagnosticForm } from '../diagnosticFormValidation'
import type { Diagnostic, DiagnosticUpdatePayload } from '../types'

const props = withDefaults(defineProps<{
  diagnostic: Diagnostic
  busy?: boolean
  fieldErrors?: DiagnosticFieldErrors
  generalErrors?: string[]
}>(), { busy: false, fieldErrors: () => ({}), generalErrors: () => [] })
const emit = defineEmits<{
  submit: [payload: DiagnosticUpdatePayload]
  cancel: []
  'clear-field-error': [field: 'website_url' | 'summary']
}>()
const values = reactive<DiagnosticFormValues>({ website_url: '', summary: '' })
const localErrors = reactive<DiagnosticFieldErrors>({})

watch(() => props.diagnostic, (diagnostic) => {
  values.website_url = diagnostic.website_url
  values.summary = diagnostic.summary ?? ''
  Object.keys(localErrors).forEach((key) => delete localErrors[key as 'website_url' | 'summary'])
}, { immediate: true })

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
  emit('submit', normalizeDiagnosticUpdateForm(values))
}
</script>

<template>
  <form class="customer-form diagnostic-form" novalidate @submit.prevent="submit">
    <div v-if="generalErrors.length" class="feedback feedback--error" role="alert">
      <strong>We couldn’t save this diagnostic.</strong>
      <ul><li v-for="(error, index) in generalErrors" :key="`${index}-${error}`">{{ error }}</li></ul>
    </div>

    <div class="form-field">
      <label for="edit-diagnostic-website-url">Website URL <span aria-hidden="true">*</span></label>
      <input id="edit-diagnostic-website-url" v-model="values.website_url" type="url" inputmode="url" required :aria-invalid="Boolean(errorFor('website_url'))" :aria-describedby="errorFor('website_url') ? 'edit-diagnostic-website-error' : undefined" @input="clearError('website_url')" />
      <p v-if="errorFor('website_url')" id="edit-diagnostic-website-error" class="field-error" role="alert">{{ errorFor('website_url') }}</p>
    </div>

    <div class="form-field">
      <label for="edit-diagnostic-summary">Summary <span class="optional-label">Optional</span></label>
      <textarea id="edit-diagnostic-summary" v-model="values.summary" rows="4" :aria-invalid="Boolean(errorFor('summary'))" :aria-describedby="errorFor('summary') ? 'edit-diagnostic-summary-error' : 'edit-diagnostic-summary-hint'" @input="clearError('summary')" />
      <small id="edit-diagnostic-summary-hint">Leave this blank to clear the summary.</small>
      <p v-if="errorFor('summary')" id="edit-diagnostic-summary-error" class="field-error" role="alert">{{ errorFor('summary') }}</p>
    </div>

    <div class="form-actions">
      <AppButton variant="secondary" :disabled="busy" @click="emit('cancel')">Cancel</AppButton>
      <AppButton type="submit" :disabled="busy">{{ busy ? 'Saving…' : 'Save diagnostic' }}</AppButton>
    </div>
  </form>
</template>
