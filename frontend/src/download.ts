function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

export async function downloadAuthenticatedFile(
  url: string,
  accessToken: string,
  fallbackMessage: string,
) {
  const response = await fetch(url, {
    headers: { Authorization: `Bearer ${accessToken}` },
  })
  if (!response.ok) {
    const body: unknown = await response.json().catch(() => null)
    const message = isRecord(body) && typeof body.detail === 'string'
      ? body.detail
      : fallbackMessage
    throw new Error(message)
  }
  const blob = await response.blob()
  const contentDisposition = response.headers.get('Content-Disposition') ?? ''
  const filename = contentDisposition.match(/filename="?([^";]+)"?/i)?.[1] ?? 'reporte'
  const objectUrl = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = objectUrl
  anchor.download = filename
  document.body.append(anchor)
  anchor.click()
  anchor.remove()
  window.setTimeout(() => URL.revokeObjectURL(objectUrl), 0)
}
