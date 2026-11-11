import { describe, expect, it } from 'vitest'
import { findingToFormValues, normalizeFindingCreateForm, normalizeFindingUpdateForm, validateFindingForm } from './findingFormValidation'
import type { Finding } from './types'

const existing: Finding = {
  id: 71,
  diagnostic_id: 31,
  title: 'Form issue',
  description: 'Needs clarity',
  page_url: 'https://example.com/contact',
  evidence: 'No action visible',
  status: 'reviewed',
  created_at: '2026-11-10T12:00:00Z',
  updated_at: '2026-11-10T12:00:00Z',
}

describe('finding form validation and payload normalization', () => {
  it('requires a nonblank title and enforces the backend 250-character maximum', () => {
    expect(validateFindingForm(findingToFormValues()).title).toBe('Enter a finding title.')
    expect(validateFindingForm({ ...findingToFormValues(), title: 'x'.repeat(251) }).title)
      .toBe('Title must be 250 characters or fewer.')
  })

  it('accepts a blank optional page URL on creation but validates a supplied URL', () => {
    expect(validateFindingForm({ ...findingToFormValues(), title: 'Valid' })).toEqual({})
    expect(validateFindingForm({ ...findingToFormValues(), title: 'Valid', page_url: 'not a url' }).page_url)
      .toContain('valid page URL')
  })

  it('does not permit clearing an existing page URL', () => {
    expect(validateFindingForm({ ...findingToFormValues(existing), page_url: '' }, existing).page_url)
      .toContain('cannot be cleared')
  })

  it('omits blank optional fields on create and sends empty text values to clear on edit', () => {
    const values = { ...findingToFormValues(existing), title: ' Revised ', description: '  ', evidence: ' ', page_url: existing.page_url ?? '' }
    expect(normalizeFindingCreateForm(values)).toEqual({ title: 'Revised', page_url: existing.page_url })
    expect(normalizeFindingUpdateForm({ ...values, status: 'dismissed' })).toEqual({
      title: 'Revised', description: '', evidence: '', page_url: existing.page_url, status: 'dismissed',
    })
  })
})
