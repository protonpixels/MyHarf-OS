<script setup lang="ts">
import { computed, reactive, watch } from 'vue'
import AppButton from '../../../components/ui/AppButton.vue'
import type { FindingFieldErrors, FindingFormValues } from '../findingFormValidation'
import { findingToFormValues, normalizeFindingCreateForm, normalizeFindingUpdateForm, validateFindingForm } from '../findingFormValidation'
import type { Finding, FindingCreatePayload, FindingUpdatePayload } from '../types'

const props = withDefaults(defineProps<{
  finding?: Finding | null
  busy?: boolean
  fieldErrors?: FindingFieldErrors
  generalErrors?: string[]
}>(), { finding: null, busy: false, fieldErrors: () => ({}), generalErrors: () => [] })
const emit = defineEmits<{
  create: [payload: FindingCreatePayload]
  update: [payload: FindingUpdatePayload]
  cancel: []
  'clear-field-error': [field: keyof FindingFieldErrors]
}>()
const values = reactive<FindingFormValues>(findingToFormValues(props.finding ?? undefined))
const localErrors = reactive<FindingFieldErrors>({})
const editing = computed(() => Boolean(props.finding))

watch(() => props.finding, (finding) => {
  Object.assign(values, findingToFormValues(finding ?? undefined))
  Object.keys(localErrors).forEach((key) => delete localErrors[key as keyof FindingFieldErrors])
}, { immediate: true })

function clearError(field: keyof FindingFieldErrors) {
  delete localErrors[field]
  emit('clear-field-error', field)
}

function errorFor(field: keyof FindingFieldErrors) {
  return localErrors[field] ?? props.fieldErrors[field]
}

function submit() {
  Object.keys(localErrors).forEach((key) => delete localErrors[key as keyof FindingFieldErrors])
  Object.assign(localErrors, validateFindingForm(values, props.finding ?? undefined))
  if (Object.keys(localErrors).length || props.busy) return
  if (props.finding) emit('update', normalizeFindingUpdateForm(values))
  else emit('create', normalizeFindingCreateForm(values))
}
</script>

<template>
  <form class="customer-form diagnostic-form finding-form" novalidate @submit.prevent="submit">
    <div v-if="generalErrors.length" class="feedback feedback--error" role="alert">
      <strong>We couldn’t save this finding.</strong>
      <ul><li v-for="(error, index) in generalErrors" :key="`${index}-${error}`">{{ error }}</li></ul>
    </div>

    <div class="form-field">
      <label for="finding-title">Title <span aria-hidden="true">*</span></label>
      <input id="finding-title" v-model="values.title" type="text" maxlength="250" required :aria-invalid="Boolean(errorFor('title'))" :aria-describedby="errorFor('title') ? 'finding-title-error' : undefined" @input="clearError('title')" />
      <small>Use a short, specific description of the observed issue (250 characters maximum).</small>
      <p v-if="errorFor('title')" id="finding-title-error" class="field-error" role="alert">{{ errorFor('title') }}</p>
    </div>

    <div class="form-field">
      <label for="finding-description">Description <span class="optional-label">Optional</span></label>
      <textarea id="finding-description" v-model="values.description" rows="3" :aria-invalid="Boolean(errorFor('description'))" :aria-describedby="errorFor('description') ? 'finding-description-error' : 'finding-description-hint'" @input="clearError('description')" />
      <small id="finding-description-hint">Leave blank to clear the description when editing.</small>
      <p v-if="errorFor('description')" id="finding-description-error" class="field-error" role="alert">{{ errorFor('description') }}</p>
    </div>

    <div class="form-field">
      <label for="finding-page-url">Page URL <span class="optional-label">Optional</span></label>
      <input id="finding-page-url" v-model="values.page_url" type="url" inputmode="url" :aria-invalid="Boolean(errorFor('page_url'))" :aria-describedby="errorFor('page_url') ? 'finding-page-url-error' : 'finding-page-url-hint'" @input="clearError('page_url')" />
      <small id="finding-page-url-hint">When editing, replace this URL with another valid URL; it cannot be cleared.</small>
      <p v-if="errorFor('page_url')" id="finding-page-url-error" class="field-error" role="alert">{{ errorFor('page_url') }}</p>
    </div>

    <div class="form-field">
      <label for="finding-evidence">Evidence <span class="optional-label">Optional</span></label>
      <textarea id="finding-evidence" v-model="values.evidence" rows="3" :aria-invalid="Boolean(errorFor('evidence'))" :aria-describedby="errorFor('evidence') ? 'finding-evidence-error' : 'finding-evidence-hint'" @input="clearError('evidence')" />
      <small id="finding-evidence-hint">Leave blank to clear the evidence when editing.</small>
      <p v-if="errorFor('evidence')" id="finding-evidence-error" class="field-error" role="alert">{{ errorFor('evidence') }}</p>
    </div>

    <div v-if="editing" class="form-field">
      <label for="finding-status">Status</label>
      <select id="finding-status" v-model="values.status" @change="clearError('status')">
        <option value="identified">Identified</option>
        <option value="reviewed">Reviewed</option>
        <option value="dismissed">Dismissed</option>
      </select>
      <p v-if="errorFor('status')" class="field-error" role="alert">{{ errorFor('status') }}</p>
    </div>

    <div class="form-actions">
      <AppButton variant="secondary" :disabled="busy" @click="emit('cancel')">Cancel</AppButton>
      <AppButton type="submit" :disabled="busy">{{ busy ? 'Saving…' : editing ? 'Save finding' : 'Create finding' }}</AppButton>
    </div>
  </form>
</template>
