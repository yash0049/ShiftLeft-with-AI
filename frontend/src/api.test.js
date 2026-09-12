import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError, api } from './api'

function mockResponse(status, payload) {
  global.fetch.mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: async () => payload,
  })
}

describe('api client', () => {
  beforeEach(() => {
    global.fetch = vi.fn()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('unwraps the assets array from the envelope', async () => {
    mockResponse(200, { assets: [{ id: 1, name: 'web-01' }] })

    await expect(api.listAssets()).resolves.toEqual([{ id: 1, name: 'web-01' }])
    expect(global.fetch).toHaveBeenCalledWith('/api/assets', { headers: undefined })
  })

  it('unwraps the vulnerabilities array from the envelope', async () => {
    mockResponse(200, { vulnerabilities: [{ id: 7, title: 'Weak TLS' }] })

    await expect(api.listVulnerabilities()).resolves.toEqual([
      { id: 7, title: 'Weak TLS' },
    ])
  })

  it('sends JSON headers and a serialized body on create', async () => {
    mockResponse(201, { id: 2, name: 'db-01' })

    await api.createAsset({ name: 'db-01' })

    expect(global.fetch).toHaveBeenCalledWith('/api/assets', {
      headers: { 'Content-Type': 'application/json' },
      method: 'POST',
      body: '{"name":"db-01"}',
    })
  })

  it('targets the right URL and verb on update', async () => {
    mockResponse(200, { id: 5, status: 'resolved' })

    await api.updateVulnerability(5, { status: 'resolved' })

    expect(global.fetch).toHaveBeenCalledWith('/api/vulnerabilities/5', {
      headers: { 'Content-Type': 'application/json' },
      method: 'PUT',
      body: '{"status":"resolved"}',
    })
  })

  it('returns null for 204 responses without parsing a body', async () => {
    const json = vi.fn()
    global.fetch.mockResolvedValue({ ok: true, status: 204, json })

    await expect(api.deleteAsset(3)).resolves.toBeNull()
    expect(json).not.toHaveBeenCalled()
  })

  it('raises the server error message and keeps per-field details', async () => {
    mockResponse(400, {
      error: 'Validation failed',
      details: { title: 'This field is required' },
    })

    const error = await api.createVulnerability({}).catch((e) => e)

    expect(error).toBeInstanceOf(ApiError)
    expect(error.message).toBe('Validation failed')
    expect(error.details).toEqual({ title: 'This field is required' })
  })

  it('falls back to the status code when the body carries no error text', async () => {
    mockResponse(500, null)

    await expect(api.listAssets()).rejects.toThrow('Request failed (500)')
  })

  it('reports an unreachable API rather than surfacing the fetch failure', async () => {
    global.fetch.mockRejectedValue(new TypeError('Failed to fetch'))

    await expect(api.listAssets()).rejects.toThrow(
      'Cannot reach the API. Is the Flask server running?',
    )
  })
})
