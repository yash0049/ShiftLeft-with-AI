import { useState } from 'react'
import { ASSET_TYPES } from '../constants'

const EMPTY = {
  name: '',
  asset_type: 'server',
  ip_address: '',
  owner: '',
  description: '',
}

function toFormState(asset) {
  if (!asset) return EMPTY
  return {
    name: asset.name ?? '',
    asset_type: asset.asset_type ?? 'server',
    ip_address: asset.ip_address ?? '',
    owner: asset.owner ?? '',
    description: asset.description ?? '',
  }
}

export default function AssetForm({ editing, onSubmit, onCancel, fieldErrors }) {
  // App gives this form a key derived from `editing`, so switching rows remounts it
  // and this initializer reloads the fields.
  const [form, setForm] = useState(() => toFormState(editing))
  const [saving, setSaving] = useState(false)

  const update = (field) => (event) =>
    setForm((prev) => ({ ...prev, [field]: event.target.value }))

  async function handleSubmit(event) {
    event.preventDefault()
    setSaving(true)
    try {
      const saved = await onSubmit(form)
      if (saved && !editing) setForm(EMPTY)
    } finally {
      setSaving(false)
    }
  }

  return (
    <form className="card form" onSubmit={handleSubmit}>
      <h3>{editing ? `Edit ${editing.name}` : 'Add asset'}</h3>

      <label>
        <span className="label-text">
          Name <span className="required">*</span>
        </span>
        <input
          value={form.name}
          onChange={update('name')}
          placeholder="web-01"
          autoComplete="off"
        />
        {fieldErrors?.name && <span className="field-error">{fieldErrors.name}</span>}
      </label>

      <label>
        Type
        <select value={form.asset_type} onChange={update('asset_type')}>
          {ASSET_TYPES.map((type) => (
            <option key={type} value={type}>
              {type}
            </option>
          ))}
        </select>
      </label>

      <div className="form-row">
        <label>
          IP address
          <input
            value={form.ip_address}
            onChange={update('ip_address')}
            placeholder="10.0.0.5"
            autoComplete="off"
          />
        </label>

        <label>
          Owner
          <input
            value={form.owner}
            onChange={update('owner')}
            placeholder="platform-team"
            autoComplete="off"
          />
        </label>
      </div>

      <label>
        Description
        <textarea value={form.description} onChange={update('description')} rows={2} />
      </label>

      <div className="form-actions">
        <button type="submit" className="primary" disabled={saving}>
          {saving ? 'Saving…' : editing ? 'Save changes' : 'Add asset'}
        </button>
        {editing && (
          <button type="button" onClick={onCancel}>
            Cancel
          </button>
        )}
      </div>
    </form>
  )
}
