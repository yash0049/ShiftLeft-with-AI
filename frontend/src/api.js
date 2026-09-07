const BASE = import.meta.env.VITE_API_BASE_URL ?? ''

class ApiError extends Error {
  constructor(message, details) {
    super(message)
    this.name = 'ApiError'
    this.details = details ?? null
  }
}

async function request(path, options = {}) {
  let response
  try {
    response = await fetch(`${BASE}${path}`, {
      headers: options.body ? { 'Content-Type': 'application/json' } : undefined,
      ...options,
    })
  } catch {
    throw new ApiError('Cannot reach the API. Is the Flask server running?')
  }

  if (response.status === 204) return null

  const payload = await response.json().catch(() => null)

  if (!response.ok) {
    const message = payload?.error ?? `Request failed (${response.status})`
    throw new ApiError(message, payload?.details)
  }

  return payload
}

const body = (data) => JSON.stringify(data)

export const api = {
  health: () => request('/health'),

  listAssets: () => request('/api/assets').then((r) => r.assets),
  createAsset: (data) => request('/api/assets', { method: 'POST', body: body(data) }),
  updateAsset: (id, data) =>
    request(`/api/assets/${id}`, { method: 'PUT', body: body(data) }),
  deleteAsset: (id) => request(`/api/assets/${id}`, { method: 'DELETE' }),

  listVulnerabilities: () =>
    request('/api/vulnerabilities').then((r) => r.vulnerabilities),
  createVulnerability: (data) =>
    request('/api/vulnerabilities', { method: 'POST', body: body(data) }),
  updateVulnerability: (id, data) =>
    request(`/api/vulnerabilities/${id}`, { method: 'PUT', body: body(data) }),
  deleteVulnerability: (id) => request(`/api/vulnerabilities/${id}`, { method: 'DELETE' }),
}

export { ApiError }
