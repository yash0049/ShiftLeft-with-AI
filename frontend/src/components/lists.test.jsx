import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import AssetList from './AssetList'
import VulnerabilityList from './VulnerabilityList'

const asset = {
  id: 1,
  name: 'web-01',
  asset_type: 'server',
  ip_address: '10.0.0.5',
  owner: 'platform-team',
  description: 'Public nginx reverse proxy',
  vulnerability_count: 2,
}

const vuln = {
  id: 9,
  title: 'SQL injection in login form',
  severity: 'critical',
  status: 'in_progress',
  cve_id: 'CVE-2024-1234',
  asset_id: 1,
  asset_name: 'web-01',
  description: null,
}

describe('AssetList', () => {
  it('prompts to add one when empty', () => {
    render(<AssetList assets={[]} onEdit={() => {}} onDelete={() => {}} />)
    expect(screen.getByText(/no assets yet/i)).toBeInTheDocument()
  })

  it('renders the asset with its finding count', () => {
    render(<AssetList assets={[asset]} onEdit={() => {}} onDelete={() => {}} />)

    expect(screen.getByText('web-01')).toBeInTheDocument()
    expect(screen.getByText('server')).toBeInTheDocument()
    expect(screen.getByText('10.0.0.5')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
  })

  it('shows an em dash where optional fields are missing', () => {
    const bare = { ...asset, ip_address: null, owner: null, description: null }
    render(<AssetList assets={[bare]} onEdit={() => {}} onDelete={() => {}} />)

    expect(screen.getAllByText('—')).toHaveLength(2)
  })

  it('hands the whole asset back to its callbacks', async () => {
    const onEdit = vi.fn()
    const onDelete = vi.fn()
    render(<AssetList assets={[asset]} onEdit={onEdit} onDelete={onDelete} />)

    await userEvent.click(screen.getByRole('button', { name: 'Edit' }))
    await userEvent.click(screen.getByRole('button', { name: 'Delete' }))

    expect(onEdit).toHaveBeenCalledWith(asset)
    expect(onDelete).toHaveBeenCalledWith(asset)
  })
})

describe('VulnerabilityList', () => {
  it('says so when there is nothing to show', () => {
    render(
      <VulnerabilityList vulnerabilities={[]} onEdit={() => {}} onDelete={() => {}} />,
    )
    expect(screen.getByText(/no findings recorded yet/i)).toBeInTheDocument()
  })

  it('renders severity and status as labelled badges', () => {
    render(
      <VulnerabilityList
        vulnerabilities={[vuln]}
        onEdit={() => {}}
        onDelete={() => {}}
      />,
    )

    expect(screen.getByText('critical')).toHaveClass('severity-critical')
    // in_progress is shown in its human-readable form.
    expect(screen.getByText('In progress')).toHaveClass('status-in_progress')
    expect(screen.getByText('CVE-2024-1234')).toBeInTheDocument()
    expect(screen.getByText('web-01')).toBeInTheDocument()
  })

  it('marks a finding with no asset as unassigned', () => {
    const orphan = { ...vuln, asset_id: null, asset_name: null }
    render(
      <VulnerabilityList
        vulnerabilities={[orphan]}
        onEdit={() => {}}
        onDelete={() => {}}
      />,
    )

    expect(screen.getByText('unassigned')).toBeInTheDocument()
  })
})
