const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

export const SESSION_EXPIRED_EVENT = 'convidata:session-expired'

let accessToken: string | null = null
let refreshToken: string | null = null
let sessionVersion = 0
let refreshPromise: { version: number; promise: Promise<string | null> } | null = null

interface RefreshResponse {
  access: string
  refresh?: string
}

function isAccessResponse(value: unknown): value is RefreshResponse {
  return (
    typeof value === 'object' &&
    value !== null &&
    'access' in value &&
    typeof value.access === 'string' &&
    (!('refresh' in value) || typeof value.refresh === 'string')
  )
}

export function setAuthTokens(access: string, refresh: string) {
  sessionVersion += 1
  accessToken = access
  refreshToken = refresh
  refreshPromise = null
}

export function clearAuthTokens() {
  sessionVersion += 1
  accessToken = null
  refreshToken = null
  refreshPromise = null
}

export function hasAuthTokens(): boolean {
  return Boolean(accessToken || refreshToken)
}

function resolveUrl(input: RequestInfo | URL): RequestInfo | URL {
  if (typeof input === 'string' && input.startsWith('/') && API_BASE_URL) {
    return `${API_BASE_URL}${input}`
  }
  return input
}

function getCsrfToken(): string | null {
  if (typeof document === 'undefined') return null
  const meta = document.querySelector<HTMLMetaElement>('meta[name="csrf-token"]')?.content?.trim()
  if (meta && meta !== 'NOTPROVIDED') return meta

  const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/)
  return match ? decodeURIComponent(match[1]) : null
}

function isMutatingMethod(method?: string): boolean {
  const normalized = (method ?? 'GET').toUpperCase()
  return normalized !== 'GET' && normalized !== 'HEAD' && normalized !== 'OPTIONS'
}

function sessionExpiredResponse() {
  return new Response(
    JSON.stringify({
      detail: 'Tu sesión expiró. Inicia sesión nuevamente.',
      code: 'session_expired',
    }),
    {
      status: 401,
      headers: { 'Content-Type': 'application/json' },
    },
  )
}

async function refreshAccessToken(
  expiredToken: string,
  version: number,
): Promise<string | null> {
  if (version !== sessionVersion) return null
  if (accessToken && accessToken !== expiredToken) return accessToken
  if (!refreshToken) return null

  if (refreshPromise?.version === version) {
    return refreshPromise.promise
  }

  const tokenToRefresh = refreshToken
  const promise = (async () => {
    let response: Response
    try {
      response = await fetch(`${API_BASE_URL}/api/auth/token/refresh/`, {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh: tokenToRefresh }),
      })
    } catch {
      throw new Error('No fue posible renovar la sesión. Verifica tu conexión.')
    }

    if (response.status === 401 || response.status === 403) {
      return null
    }
    if (!response.ok) {
      throw new Error('No se pudo renovar la sesión. Inténtalo nuevamente.')
    }

    const body: unknown = await response.json()
    if (!isAccessResponse(body)) {
      throw new Error('El servidor devolvió una respuesta de renovación inválida.')
    }
    if (version !== sessionVersion || tokenToRefresh !== refreshToken) return null

    accessToken = body.access
    if (body.refresh) {
      refreshToken = body.refresh
    }
    return accessToken
  })()

  refreshPromise = { version, promise }
  try {
    return await promise
  } finally {
    if (refreshPromise?.promise === promise) refreshPromise = null
  }
}

function requestWithToken(
  input: RequestInfo | URL,
  init: RequestInit,
  token: string | null,
) {
  const target = input instanceof Request ? input.clone() : resolveUrl(input)
  const requestHeaders = target instanceof Request ? target.headers : undefined
  const headers = new Headers(requestHeaders)
  new Headers(init.headers).forEach((value, key) => headers.set(key, value))

  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  const method = init.method ?? (target instanceof Request ? target.method : 'GET')
  if (isMutatingMethod(method) && !headers.has('X-CSRFToken')) {
    const csrfToken = getCsrfToken()
    if (csrfToken) {
      headers.set('X-CSRFToken', csrfToken)
    }
  }

  return fetch(target, {
    credentials: 'same-origin',
    ...init,
    headers,
  })
}

export async function authenticatedFetch(
  input: RequestInfo | URL,
  init: RequestInit = {},
): Promise<Response> {
  const token = accessToken
  if (!token) {
    return requestWithToken(input, init, null)
  }

  const version = sessionVersion
  const response = await requestWithToken(input, init, token)
  if (response.status !== 401) return response

  const refreshedToken = await refreshAccessToken(token, version)
  if (!refreshedToken) {
    if (version !== sessionVersion) return response
    clearAuthTokens()
    window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT))
    return sessionExpiredResponse()
  }

  const retriedResponse = await requestWithToken(input, init, refreshedToken)
  if (retriedResponse.status !== 401) return retriedResponse

  if (version === sessionVersion) {
    clearAuthTokens()
    window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT))
    return sessionExpiredResponse()
  }
  return retriedResponse
}