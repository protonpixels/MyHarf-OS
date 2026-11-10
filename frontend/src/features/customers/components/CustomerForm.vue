<script setup lang="ts">
import { reactive, watch } from 'vue'
import AppButton from '../../../components/ui/AppButton.vue'
import { customerToFormValues, normalizeCustomerForm, validateCustomerForm, type CustomerFieldErrors, type CustomerFormValues } from '../customerFormValidation'
import type { Customer, CustomerPayload } from '../types'

const props = withDefaults(defineProps<{
  customer?: Customer
  busy?: boolean
  fieldErrors?: CustomerFieldErrors
  generalErrors?: string[]
}>(), { busy: false, fieldErrors: () => ({}), generalErrors: () => [] })
const emit = defineEmits<{
  submit: [payload: CustomerPayload]
  'clear-field-error': [field: keyof CustomerFieldErrors]
}>()
const values = reactive<CustomerFormValues>(customerToFormValues(props.customer))
const localErrors = reactive<CustomerFieldErrors>({})

watch(() => props.customer, (customer) => Object.assign(values, customerToFormValues(customer)), { deep: true })

function submit() {
  Object.keys(localErrors).forEach((key) => delete localErrors[key as keyof CustomerFieldErrors])
  Object.assign(localErrors, validateCustomerForm(values))
  if (Object.keys(localErrors).length || props.busy) return
  emit('submit', normalizeCustomerForm(values))
}

function errorFor(field: keyof CustomerFieldErrors) {
  return localErrors[field] ?? props.fieldErrors[field]
}

function clearFieldError(field: keyof CustomerFieldErrors) {
  delete localErrors[field]
  emit('clear-field-error', field)
}
</script>

<template>
  <form class="customer-form" novalidate @submit.prevent="submit">
    <div v-if="generalErrors.length" class="feedback feedback--error" role="alert">
      <strong>We couldn’t save this customer.</strong>
      <ul><li v-for="(error, index) in generalErrors" :key="`${index}-${error}`">{{ error }}</li></ul>
    </div>

    <div class="form-field">
      <label for="customer-name">Customer name <span aria-hidden="true">*</span></label>
      <input id="customer-name" v-model="values.name" name="name" type="text" autocomplete="name" maxlength="200" required :aria-invalid="Boolean(errorFor('name'))" :aria-describedby="errorFor('name') ? 'customer-name-error' : 'customer-name-hint'" @input="clearFieldError('name')" />
      <small id="customer-name-hint">Use the primary contact’s name.</small>
      <p v-if="errorFor('name')" id="customer-name-error" class="field-error" role="alert">{{ errorFor('name') }}</p>
    </div>

    <div class="form-field">
      <label for="customer-business-name">Business name <span class="optional-label">Optional</span></label>
      <input id="customer-business-name" v-model="values.business_name" name="business_name" type="text" autocomplete="organization" maxlength="200" :aria-invalid="Boolean(errorFor('business_name'))" :aria-describedby="errorFor('business_name') ? 'customer-business-error' : undefined" @input="clearFieldError('business_name')" />
      <p v-if="errorFor('business_name')" id="customer-business-error" class="field-error" role="alert">{{ errorFor('business_name') }}</p>
    </div>

    <div class="form-field">
      <label for="customer-email">Email <span class="optional-label">Optional</span></label>
      <input id="customer-email" v-model="values.email" name="email" type="email" autocomplete="email" maxlength="320" :aria-invalid="Boolean(errorFor('email'))" :aria-describedby="errorFor('email') ? 'customer-email-error' : undefined" @input="clearFieldError('email')" />
      <p v-if="errorFor('email')" id="customer-email-error" class="field-error" role="alert">{{ errorFor('email') }}</p>
    </div>

    <div class="form-field">
      <label for="customer-phone">Phone <span class="optional-label">Optional</span></label>
      <input id="customer-phone" v-model="values.phone" name="phone" type="tel" autocomplete="tel" maxlength="50" :aria-invalid="Boolean(errorFor('phone'))" :aria-describedby="errorFor('phone') ? 'customer-phone-error' : undefined" @input="clearFieldError('phone')" />
      <p v-if="errorFor('phone')" id="customer-phone-error" class="field-error" role="alert">{{ errorFor('phone') }}</p>
    </div>

    <div class="form-actions">
      <RouterLink class="button button--secondary" :to="customer ? `/customers/${customer.id}` : '/customers'">Cancel</RouterLink>
      <AppButton type="submit" :disabled="busy">{{ busy ? 'Saving…' : customer ? 'Save changes' : 'Create customer' }}</AppButton>
    </div>
  </form>
</template>
