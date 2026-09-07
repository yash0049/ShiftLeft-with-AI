import { useCallback, useEffect, useMemo, useState } from 'react'
import { api } from './api'
import AssetForm from './components/AssetForm'
import AssetList from './components/AssetList'
import VulnerabilityForm from './components/VulnerabilityForm'
import VulnerabilityList from './components/VulnerabilityList'
import './App.css'

export default function App() {
  const [tab, setTab] = useState('vulnerabilities')
  const [assets, setAssets] = useState([])
  const [vulnerabilities, setVulnerabilities] = useState([])

  const [editingAsset, setEditingAsset] = useState(null)
  const [editingVuln, setEditingVuln] = useState(null)

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [fieldErrors, setFieldErrors] = useState(null)
  const [apiOnline, setApiOnline] = useState(null)

  const refresh = useCallback(async () => {
    try {
      const [nextAssets, nextVulns] = await Promise.all([
        api.listAssets(),
        api.listVulnerabilities(),
      ])
      setAssets(nextAssets)
      setVulnerabilities(nextVulns)
      setApiOnline(true)
      setError(null)
    } catch (err) {
      setError(err.message)
      setApiOnline(false)
    } finally {
      setLoading(false)
    }
  }, [])

  // Load on mount. refresh() only sets state after awaiting the API, so this is a
  // genuine external-system sync rather than the cascading render the rule guards against.
  useEffect(() => {
    // eslint-disable-next-line react/set-state-in-effect
    refresh()
  }, [refresh])

  /** Run a mutation, refresh on success, and surface field errors on failure. */
  const mutate = useCallback(
    async (action) => {
      setError(null)
      setFieldErrors(null)
      try {
        await action()
        await refresh()
        return true
      } catch (err) {
        setError(err.message)
        setFieldErrors(err.details ?? null)
        return false
      }
    },
    [refresh],
  )

  const saveAsset = (form) =>
    mutate(() =>
      editingAsset ? api.updateAsset(editingAsset.id, form) : api.createAsset(form),
    ).then((ok) => {
      if (ok) setEditingAsset(null)
      return ok
    })

  const saveVulnerability = (form) =>
    mutate(() =>
      editingVuln ? api.updateVulnerability(editingVuln.id, form) : api.createVulnerability(form),
    ).then((ok) => {
      if (ok) setEditingVuln(null)
      return ok
    })

  function deleteAsset(asset) {
    const extra =
      asset.vulnerability_count > 0
        ? ` and its ${asset.vulnerability_count} finding(s)`
        : ''
    if (!confirm(`Delete "${asset.name}"${extra}?`)) return
    mutate(() => api.deleteAsset(asset.id)).then(() => {
      setEditingAsset((current) => (current?.id === asset.id ? null : current))
    })
  }

  function deleteVulnerability(vuln) {
    if (!confirm(`Delete "${vuln.title}"?`)) return
    mutate(() => api.deleteVulnerability(vuln.id)).then(() => {
      setEditingVuln((current) => (current?.id === vuln.id ? null : current))
    })
  }

  const openCount = useMemo(
    () => vulnerabilities.filter((v) => v.status === 'open').length,
    [vulnerabilities],
  )
  const criticalCount = useMemo(
    () =>
      vulnerabilities.filter(
        (v) => v.severity === 'critical' && v.status !== 'resolved',
      ).length,
    [vulnerabilities],
  )

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <h1>SecureTrack</h1>
          <p className="subtitle">Asset and vulnerability tracker</p>
        </div>
        <div className={`api-status ${apiOnline ? 'online' : 'offline'}`}>
          <span className="dot" />
          {apiOnline === null ? 'connecting' : apiOnline ? 'API online' : 'API offline'}
        </div>
      </header>

      <section className="stats">
        <div className="stat">
          <span className="stat-value">{assets.length}</span>
          <span className="stat-label">Assets</span>
        </div>
        <div className="stat">
          <span className="stat-value">{vulnerabilities.length}</span>
          <span className="stat-label">Findings</span>
        </div>
        <div className="stat">
          <span className="stat-value">{openCount}</span>
          <span className="stat-label">Open</span>
        </div>
        <div className="stat">
          <span className="stat-value danger-text">{criticalCount}</span>
          <span className="stat-label">Critical unresolved</span>
        </div>
      </section>

      {error && (
        <div className="banner error" role="alert">
          {error}
          <button onClick={refresh}>Retry</button>
        </div>
      )}

      <nav className="tabs">
        <button
          className={tab === 'vulnerabilities' ? 'tab active' : 'tab'}
          onClick={() => setTab('vulnerabilities')}
        >
          Vulnerabilities
        </button>
        <button
          className={tab === 'assets' ? 'tab active' : 'tab'}
          onClick={() => setTab('assets')}
        >
          Assets
        </button>
      </nav>

      {loading ? (
        <p className="empty">Loading…</p>
      ) : tab === 'assets' ? (
        <div className="layout">
          <AssetForm
            key={editingAsset?.id ?? 'new-asset'}
            editing={editingAsset}
            fieldErrors={fieldErrors}
            onSubmit={saveAsset}
            onCancel={() => {
              setEditingAsset(null)
              setFieldErrors(null)
            }}
          />
          <AssetList assets={assets} onEdit={setEditingAsset} onDelete={deleteAsset} />
        </div>
      ) : (
        <div className="layout">
          <VulnerabilityForm
            key={editingVuln?.id ?? 'new-vuln'}
            editing={editingVuln}
            assets={assets}
            fieldErrors={fieldErrors}
            onSubmit={saveVulnerability}
            onCancel={() => {
              setEditingVuln(null)
              setFieldErrors(null)
            }}
          />
          <VulnerabilityList
            vulnerabilities={vulnerabilities}
            onEdit={setEditingVuln}
            onDelete={deleteVulnerability}
          />
        </div>
      )}
    </div>
  )
}
