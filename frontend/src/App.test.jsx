import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import { api } from './api'

vi.mock('./api', () => ({
  api: {
    listAssets: vi.fn(),
    listVulnerabilities: vi.fn(),
    createAsset: vi.fn(),
    updateAsset: vi.fn(),
    deleteAsset: vi.fn(),
    createVulnerability: vi.fn(),
    updateVulnerability: vi.fn(),
    deleteVulnerability: vi.fn(),
  },
}))

const assets = [
  {
    id: 1,
    name: 'web-01',
    asset_type: 'server',
    ip_address: '10.0.0.5',
    owner: 'platform-team',
    description: null,
    vulnerability_count: 1,
  },
]

const vulnerabilities = [
  {
    id: 9,
    title: 'Outdated OpenSSL',
    severity: 'critical',
    status: 'open',
    cve_id: 'CVE-2023-0286',
    asset_id: 1,
    asset_name: 'web-01',
    description: null,
  },
  {
    id: 10,
    title: 'Missing security headers',
    severity: 'low',
    status: 'resolved',
    cve_id: null,
    asset_id: 1,
    asset_name: 'web-01',
    description: null,
  },
]

/** Read a summary tile by its label, e.g. statFor('Open'). Scoped to the tiles
 *  because labels like "Open" also appear as status badges in the table. */
function statFor(label) {
  const tile = [...document.querySelectorAll('.stat')].find(
    (el) => el.querySelector('.stat-label').textContent === label,
  )
  return tile.querySelector('.stat-value').textContent
}

beforeEach(() => {
  vi.clearAllMocks()
  api.listAssets.mockResolvedValue(assets)
  api.listVulnerabilities.mockResolvedValue(vulnerabilities)
})

describe('App', () => {
  it('loads both resources on mount and reports the API as online', async () => {
    render(<App />)

    expect(await screen.findByText('Outdated OpenSSL')).toBeInTheDocument()
    expect(screen.getByText('API online')).toBeInTheDocument()
    expect(api.listAssets).toHaveBeenCalledTimes(1)
    expect(api.listVulnerabilities).toHaveBeenCalledTimes(1)
  })

  it('counts open and unresolved-critical findings in the summary tiles', async () => {
    render(<App />)
    await screen.findByText('Outdated OpenSSL')

    expect(statFor('Assets')).toBe('1')
    expect(statFor('Findings')).toBe('2')
    expect(statFor('Open')).toBe('1')
    expect(statFor('Critical unresolved')).toBe('1')
  })

  it('switches to the assets tab', async () => {
    render(<App />)
    await screen.findByText('Outdated OpenSSL')

    await userEvent.click(screen.getByRole('button', { name: 'Assets' }))

    expect(screen.getByRole('heading', { name: 'Add asset' })).toBeInTheDocument()
    expect(screen.getByText('platform-team')).toBeInTheDocument()
  })

  it('creates a finding and reloads the list', async () => {
    api.createVulnerability.mockResolvedValue({ id: 11 })
    render(<App />)
    await screen.findByText('Outdated OpenSSL')

    await userEvent.type(
      screen.getByPlaceholderText('SQL injection in login form'),
      'Open redirect',
    )
    await userEvent.click(screen.getByRole('button', { name: 'Add finding' }))

    await waitFor(() =>
      expect(api.createVulnerability).toHaveBeenCalledWith(
        expect.objectContaining({ title: 'Open redirect', severity: 'medium' }),
      ),
    )
    // A successful mutation refetches, so both list calls run a second time.
    await waitFor(() => expect(api.listVulnerabilities).toHaveBeenCalledTimes(2))
  })

  it('prefills the form when editing and sends the id through', async () => {
    api.updateVulnerability.mockResolvedValue({ id: 9 })
    render(<App />)
    await screen.findByText('Outdated OpenSSL')

    const row = screen.getByText('Outdated OpenSSL').closest('tr')
    await userEvent.click(within(row).getByRole('button', { name: 'Edit' }))

    expect(screen.getByRole('heading', { name: 'Edit finding' })).toBeInTheDocument()
    expect(screen.getByDisplayValue('Outdated OpenSSL')).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'Save changes' }))

    await waitFor(() =>
      expect(api.updateVulnerability).toHaveBeenCalledWith(
        9,
        expect.objectContaining({ title: 'Outdated OpenSSL' }),
      ),
    )
  })

  it('surfaces per-field validation errors from the server', async () => {
    const failure = Object.assign(new Error('Validation failed'), {
      details: { title: 'This field is required' },
    })
    api.createVulnerability.mockRejectedValue(failure)
    render(<App />)
    await screen.findByText('Outdated OpenSSL')

    await userEvent.click(screen.getByRole('button', { name: 'Add finding' }))

    expect(await screen.findByText('This field is required')).toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent('Validation failed')
  })

  it('asks for confirmation before deleting, and skips the call when declined', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(false)
    render(<App />)
    await screen.findByText('Outdated OpenSSL')

    const row = screen.getByText('Outdated OpenSSL').closest('tr')
    await userEvent.click(within(row).getByRole('button', { name: 'Delete' }))

    expect(window.confirm).toHaveBeenCalled()
    expect(api.deleteVulnerability).not.toHaveBeenCalled()
  })

  it('deletes once confirmed', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    api.deleteVulnerability.mockResolvedValue(null)
    render(<App />)
    await screen.findByText('Outdated OpenSSL')

    const row = screen.getByText('Outdated OpenSSL').closest('tr')
    await userEvent.click(within(row).getByRole('button', { name: 'Delete' }))

    await waitFor(() => expect(api.deleteVulnerability).toHaveBeenCalledWith(9))
  })

  it('shows an offline banner when the API cannot be reached', async () => {
    api.listAssets.mockRejectedValue(new Error('Cannot reach the API.'))
    api.listVulnerabilities.mockRejectedValue(new Error('Cannot reach the API.'))

    render(<App />)

    expect(await screen.findByText('API offline')).toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent('Cannot reach the API.')
  })
})
