import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { ApiClientError } from '../../../api/errors'
import { archiveFinding, createFinding, listDiagnosticFindings, updateFinding } from '../findingService'
import type { DiagnosticStatus, Finding } from '../types'
import FindingsSection from './FindingsSection.vue'

vi.mock('../findingService', () => ({
  archiveFinding: vi.fn(),
  createFinding: vi.fn(),
  getFinding: vi.fn(),
  listDiagnosticFindings: vi.fn(),
  updateFinding: vi.fn(),
}))

const finding: Finding = {
  id: 71,
  diagnostic_id: 31,
  title: 'Contact form is hard to find',
  description: 'The contact link is below several unrelated sections.',
  page_url: 'https://example.com/contact',
  evidence: 'The main navigation has no contact link.',
  status: 'identified',
  created_at: '2026-11-10T12:00:00Z',
  updated_at: '2026-11-10T12:00:00Z',
}
const archivedFinding: Finding = { ...finding, id: 72, title: 'Old observation', status: 'archived' }
const mountSection = (diagnosticId = 31, diagnosticStatus: DiagnosticStatus = 'planned') => mount(FindingsSection, {
  props: { diagnosticId, diagnosticStatus },
})

function mockDialogMethods() {
  vi.spyOn(HTMLDialogElement.prototype, 'showModal').mockImplementation(function (this: HTMLDialogElement) {
    this.setAttribute('open', '')
  })
  vi.spyOn(HTMLDialogElement.prototype, 'close').mockImplementation(function (this: HTMLDialogElement) {
    this.removeAttribute('open')
  })
}

describe('findings section', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(listDiagnosticFindings).mockResolvedValue([finding])
  })
  afterEach(() => vi.restoreAllMocks())

  it('shows loading, empty, and populated states', async () => {
    vi.mocked(listDiagnosticFindings).mockReturnValueOnce(new Promise(() => {}))
    const loading = mountSection()
    expect(loading.get('[role="status"]').text()).toContain('Loading findings')
    loading.unmount()

    vi.mocked(listDiagnosticFindings).mockResolvedValueOnce([])
    const empty = mountSection()
    await flushPromises()
    expect(empty.text()).toContain('No findings yet')

    vi.mocked(listDiagnosticFindings).mockResolvedValueOnce([finding])
    const populated = mountSection()
    await flushPromises()
    expect(populated.text()).toContain(finding.title)
    expect(populated.text()).toContain(finding.description)
    expect(populated.text()).toContain(finding.page_url)
    expect(populated.text()).toContain(finding.evidence)
    expect(populated.text()).toContain('Identified')
    expect(populated.text()).toContain('Created Nov 10, 2026')
  })

  it('hides archived findings by default and displays them when included', async () => {
    vi.mocked(listDiagnosticFindings).mockResolvedValue([finding, archivedFinding])
    const wrapper = mountSection()
    await flushPromises()
    expect(wrapper.text()).not.toContain('Old observation')
    await wrapper.get('input[type="checkbox"]').setValue(true)
    expect(wrapper.text()).toContain('Old observation')
    expect(wrapper.find('.finding-card--archived').exists()).toBe(true)
    expect(wrapper.find('.finding-card--archived').text()).toContain('Archived')
    expect(wrapper.find('.finding-card--archived').text()).not.toContain('Edit')
  })

  it('creates a finding under the diagnostic path with the selected details', async () => {
    mockDialogMethods()
    const created = { ...finding, id: 73, title: 'New observation', description: null, page_url: null, evidence: null }
    vi.mocked(createFinding).mockResolvedValue(created)
    const wrapper = mountSection(31, 'completed')
    await flushPromises()
    await wrapper.get('button').trigger('click')
    await wrapper.get('#finding-title').setValue(' New observation ')
    await wrapper.get('dialog form').trigger('submit')
    await flushPromises()
    expect(createFinding).toHaveBeenCalledWith(31, { title: 'New observation' })
    expect(wrapper.text()).toContain('New observation')
    expect(wrapper.text()).toContain('Finding created.')
  })

  it('shows server validation errors, retains inputs, and prevents duplicate submissions', async () => {
    mockDialogMethods()
    let finish!: (value: Finding) => void
    vi.mocked(createFinding).mockReturnValue(new Promise((resolve) => { finish = resolve }))
    const wrapper = mountSection()
    await flushPromises()
    await wrapper.get('button').trigger('click')
    await wrapper.get('#finding-title').setValue('Entered title')
    await wrapper.get('dialog form').trigger('submit')
    await wrapper.get('dialog form').trigger('submit')
    expect(createFinding).toHaveBeenCalledTimes(1)
    expect(wrapper.text()).toContain('Saving…')
    finish(finding)
    await flushPromises()
    wrapper.unmount()

    vi.mocked(listDiagnosticFindings).mockResolvedValue([finding])
    vi.mocked(createFinding).mockRejectedValue(new ApiClientError('Invalid title', 422, [
      { location: ['body', 'title'], message: 'Title is required.' },
    ]))
    const failed = mountSection()
    await flushPromises()
    await failed.get('button').trigger('click')
    await failed.get('#finding-title').setValue('Keep this title')
    await failed.get('dialog form').trigger('submit')
    await flushPromises()
    expect(failed.text()).toContain('Title is required.')
    expect((failed.get('#finding-title').element as HTMLInputElement).value).toBe('Keep this title')
  })

  it('edits finding fields and sends empty strings to clear description and evidence', async () => {
    mockDialogMethods()
    vi.mocked(updateFinding).mockResolvedValue({ ...finding, description: '', evidence: '', status: 'reviewed' })
    const wrapper = mountSection()
    await flushPromises()
    await wrapper.get('.finding-actions button.button--secondary').trigger('click')
    await wrapper.get('#finding-description').setValue('')
    await wrapper.get('#finding-evidence').setValue('')
    await wrapper.get('#finding-status').setValue('reviewed')
    await wrapper.get('dialog form').trigger('submit')
    await flushPromises()
    expect(updateFinding).toHaveBeenCalledWith(71, {
      title: finding.title, description: '', page_url: finding.page_url, evidence: '', status: 'reviewed',
    })
    expect(wrapper.text()).toContain('Finding updated.')
  })

  it('confirms archive, supports cancel, and keeps the archived record available', async () => {
    mockDialogMethods()
    vi.mocked(archiveFinding).mockResolvedValue({ ...finding, status: 'archived' })
    const wrapper = mountSection()
    await flushPromises()
    await wrapper.get('.finding-actions button.button--danger').trigger('click')
    const dialog = wrapper.get('dialog[aria-labelledby="finding-archive-title"]')
    expect(dialog.attributes('open')).toBeDefined()
    await dialog.get('button.button--secondary').trigger('click')
    expect(archiveFinding).not.toHaveBeenCalled()

    await wrapper.get('.finding-actions button.button--danger').trigger('click')
    await wrapper.get('dialog[aria-labelledby="finding-archive-title"] button.button--danger').trigger('click')
    await flushPromises()
    expect(archiveFinding).toHaveBeenCalledWith(71)
    expect(wrapper.text()).not.toContain(finding.title)
    await wrapper.get('input[type="checkbox"]').setValue(true)
    expect(wrapper.text()).toContain(finding.title)
    expect(wrapper.find('.finding-card--archived').exists()).toBe(true)
  })

  it('keeps archive confirmation open and reports API failures', async () => {
    mockDialogMethods()
    vi.mocked(archiveFinding).mockRejectedValue(new ApiClientError('Archive failed', 409))
    const wrapper = mountSection()
    await flushPromises()
    await wrapper.get('.finding-actions button.button--danger').trigger('click')
    await wrapper.get('dialog[aria-labelledby="finding-archive-title"] button.button--danger').trigger('click')
    await flushPromises()
    expect(wrapper.get('dialog[aria-labelledby="finding-archive-title"]').attributes('open')).toBeDefined()
    expect(wrapper.get('[role="alert"]').text()).toContain('Archive failed')
  })

  it('makes all findings read-only and hides creation for archived diagnostics', async () => {
    vi.mocked(listDiagnosticFindings).mockResolvedValue([finding, archivedFinding])
    const wrapper = mountSection(31, 'archived')
    await flushPromises()
    await wrapper.get('input[type="checkbox"]').setValue(true)
    expect(wrapper.text()).toContain('read-only records')
    expect(wrapper.text()).not.toContain('Add finding')
    expect(wrapper.find('.finding-actions').exists()).toBe(false)
  })

  it('ignores findings from a previous diagnostic when requests resolve out of order', async () => {
    let resolve31!: (items: Finding[]) => void
    let resolve32!: (items: Finding[]) => void
    vi.mocked(listDiagnosticFindings).mockImplementation((id) => new Promise((resolve) => {
      if (id === 31) resolve31 = resolve
      else resolve32 = resolve
    }))
    const wrapper = mountSection(31)
    await wrapper.setProps({ diagnosticId: 32 })
    const current = { ...finding, id: 82, diagnostic_id: 32, title: 'Current diagnostic finding' }
    resolve32([current])
    await flushPromises()
    resolve31([finding])
    await flushPromises()
    expect(wrapper.text()).toContain('Current diagnostic finding')
    expect(wrapper.text()).not.toContain(finding.title)
  })

  it('ignores a create response from the previous diagnostic after navigation', async () => {
    mockDialogMethods()
    let resolveCreate!: (value: Finding) => void
    vi.mocked(createFinding).mockReturnValue(new Promise((resolve) => { resolveCreate = resolve }))
    vi.mocked(listDiagnosticFindings).mockResolvedValue([])
    const wrapper = mountSection(31)
    await flushPromises()
    await wrapper.get('button').trigger('click')
    await wrapper.get('#finding-title').setValue('Old diagnostic finding')
    await wrapper.get('dialog[aria-labelledby="finding-form-title"] form').trigger('submit')
    await wrapper.setProps({ diagnosticId: 32 })
    await flushPromises()
    resolveCreate({ ...finding, title: 'Old diagnostic finding' })
    await flushPromises()
    expect(wrapper.text()).not.toContain('Old diagnostic finding')
    expect(createFinding).toHaveBeenCalledWith(31, { title: 'Old diagnostic finding' })
  })
})
