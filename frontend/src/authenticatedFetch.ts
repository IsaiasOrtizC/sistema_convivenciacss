const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

export const ACCESS_TOKEN_KEY = 'convidata_access_token'
export const REFRESH_TOKEN_KEY = 'convidata_refresh_token'

let refreshPromise: Promise<string | null> | null = null

async function refreshAccessToken(): Promise<string | null> {
  const refresh = window.localStorage.getItem(REFRESH_TOKEN_KEY)
  if (!refresh) return null

  try {
    const response = await fetch(`${API_BASE_URL}/api/auth/token/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
    })
    if (!response.ok) return null

    const data: unknown = await response.json()
    if (
      typeof data === 'object' &&
      data !== null &&
      'access' in data &&
      typeof data.access === 'string'
    ) {
      window.localStorage.setItem(ACCESS_TOKEN_KEY, data.access)
      if ('refresh' in data && typeof data.refresh === 'string') {
        window.localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh)
      }
      return data.access
    }
    return null
  } catch {
    return null
  }
}

export async function authenticatedFetch(
  input: RequestInfo | URL,
  init: RequestInit = {},
): Promise<Response> {
  const storedAccess = window.localStorage.getItem(ACCESS_TOKEN_KEY)
  const headers = new Headers(init.headers)
  if (storedAccess) {
    headers.set('Authorization', `Bearer ${storedAccess}`)
  }

  let response = await fetch(input, { ...init, headers })

  if (response.status === 401) {
    if (!refreshPromise) {
      refreshPromise = refreshAccessToken().finally(() => {
        refreshPromise = null
      })
    }
    const newAccess = await refreshPromise
    if (newAccess) {
      headers.set('Authorization', `Bearer ${newAccess}`)
      response = await fetch(input, { ...init, headers })
    }
  }

  return response
}