import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import CustomerForm from './components/CustomerForm.vue'
import { normalizeCustomerForm, validateCustomerForm } from './customerFormValidation'
import type { CustomerFormValues } from './customerFormValidation'

const emptyValues: CustomerFormValues = {
  name: '',
  business_name: '',
  email: '',
  phone: '',
}

describe('customer form validation and normalization', () => {
  it('requires a nonblank name and validates limits and the backend email format', () => {
    expect(validateCustomerForm(emptyValues).name).toBe('Enter a customer name.')
    expect(validateCustomerForm({ ...emptyValues, name: '  ' }).name).toBe('Enter a customer name.')
    expect(validateCustomerForm({ ...emptyValues, name: 'A'.repeat(201) }).name).toContain('200')
    expect(validateCustomerForm({ ...emptyValues, name: 'Valid', email: 'bad@' }).email).toContain('valid format')
    expect(validateCustomerForm({ ...emptyValues, name: 'Valid', email: 'a@example.com' })).toEqual({})
  })

  it('trims the required name and converts blank optional fields to null', () => {
    expect(normalizeCustomerForm({ name: '  Roofer  ', business_name: '  ', email: '', phone: '  ' })).toEqual({
      name: 'Roofer',
      business_name: null,
      email: null,
      phone: null,
    })
  })

  it('shows validation errors and does not submit invalid values', async () => {
    const wrapper = mount(CustomerForm, { global: { stubs: { RouterLink: true } } })
    await wrapper.get('form').trigger('submit')
    expect(wrapper.text()).toContain('Enter a customer name.')
    expect(wrapper.emitted('submit')).toBeUndefined()
  })

  it('emits a normalized payload and prevents submit while busy', async () => {
    const wrapper = mount(CustomerForm, { global: { stubs: { RouterLink: true } } })
    await wrapper.get('#customer-name').setValue('  Alex  ')
    await wrapper.get('#customer-business-name').setValue(' ')
    await wrapper.get('form').trigger('submit')
    expect(wrapper.emitted('submit')?.[0]?.[0]).toEqual({ name: 'Alex', business_name: null, email: null, phone: null })

    const busy = mount(CustomerForm, { props: { busy: true }, global: { stubs: { RouterLink: true } } })
    expect(busy.get('button[type="submit"]').attributes('disabled')).toBeDefined()
  })
})
