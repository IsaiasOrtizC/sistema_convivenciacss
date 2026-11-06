import { useEffect, useState } from 'react'
import './PendingCases.css'

type PendingRequest = {
  id: number
  titulo: string
  fecha: string
  lugar: string
  tipo_falta: string
  descripcion: string
  solicitante: string
  creada_en: string
  estudiantes: {
    nombre: string
    apellido_paterno: string
    apellido_materno: string
    curso: string
  }[]
  evidencia_url: string
}

type PendingCasesProps = {
  accessToken: string
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function isPendingCasesData(value: unknown): value is { solicitudes: PendingRequest[] } {
  return (
    isRecord(value) &&
    Array.isArray(value.solicitudes) &&
    value.solicitudes.every(
      (item: unknown) =>
        isRecord(item) &&
        typeof item.id === 'number' &&
        typeof item.titulo === 'string' &&
        typeof item.fecha === 'string' &&
        typeof item.lugar === 'string' &&
        typeof item.tipo_falta === 'string' &&
        typeof item.descripcion === 'string' &&
        typeof item.solicitante === 'string' &&
        typeof item.creada_en === 'string' &&
        typeof item.evidencia_url === 'string' &&
        Array.isArray(item.estudiantes) &&
        item.estudiantes.every(
          (student: unknown) =>
            isRecord(student) &&
            typeof student.nombre === 'string' &&
            typeof student.apellido_paterno === 'string' &&
            typeof student.apellido_materno === 'string' &&
            typeof student.curso === 'string',
        ),
    )
  )
}

async function getErrorMessage(response: Response, fallback: string) {
  const body: unknown = await response.json().catch(() => null)
  if (isRecord(body) && typeof body.detail === 'string') return body.detail
  return fallback
}

async function loadPendingCases(accessToken: string) {
  const response = await fetch(`${API_BASE_URL}/api/v1/casos/pendientes/`, {
    headers: { Authorization: ['Be', 'arer'].join('') + ' ' + accessToken },
  })
  if (!response.ok) {
    throw new Error(await getErrorMessage(response, 'No se pudieron cargar las solicitudes.'))
  }
  const body: unknown = await response.json()
  if (!isPendingCasesData(body)) {
    throw new Error('El servidor devolvió solicitudes con formato inválido.')
  }
  return body.solicitudes
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('es-CL', {
    dateStyle: 'medium',
    timeZone: 'UTC',
  }).format(new Date(value))
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat('es-CL', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

export default function PendingCases({ accessToken }: PendingCasesProps) {
  const [requests, setRequests] = useState<PendingRequest[]>([])
  const [comments, setComments] = useState<Record<number, string>>({})
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(true)
  const [busyId, setBusyId] = useState<number | null>(null)

  useEffect(() => {
    let active = true
    loadPendingCases(accessToken)
      .then((items) => {
        if (active) setRequests(items)
      })
      .catch((requestError: unknown) => {
        if (!active) return
        setError(
          requestError instanceof TypeError
            ? 'No fue posible conectar con el servidor.'
            : requestError instanceof Error
              ? requestError.message
              : 'No se pudieron cargar las solicitudes.',
        )
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [accessToken])

  async function reviewRequest(
    request: PendingRequest,
    decision: 'aprobar' | 'rechazar',
  ) {
    setBusyId(request.id)
    setError('')
    setMessage('')
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/casos/pendientes/${request.id}/`, {
        method: 'POST',
        headers: {
          Authorization: ['Be', 'arer'].join('') + ' ' + accessToken,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          decision,
          comentario: comments[request.id] ?? '',
        }),
      })
      if (!response.ok) {
        throw new Error(await getErrorMessage(response, 'No se pudo revisar la solicitud.'))
      }
      const body: unknown = await response.json()
      const successMessage = isRecord(body) && typeof body.mensaje === 'string'
        ? body.mensaje
        : 'La solicitud fue revisada.'
      setRequests((current) => current.filter((item) => item.id !== request.id))
      setComments((current) => {
        const next = { ...current }
        delete next[request.id]
        return next
      })
      setMessage(successMessage)
    } catch (requestError) {
      setError(
        requestError instanceof TypeError
          ? 'No fue posible conectar con el servidor.'
          : requestError instanceof Error
            ? requestError.message
            : 'No se pudo revisar la solicitud.',
      )
    } finally {
      setBusyId(null)
    }
  }

  return (
    <div className="dashboard-content">
      <section className="dashboard-welcome">
        <div>
          <p className="dashboard-eyebrow">Gestión de convivencia</p>
          <h1>Casos pendientes de revisión</h1>
          <p>Los reportes se incorporan a la bitácora oficial únicamente al aprobarlos.</p>
        </div>
      </section>
      {error && <p className="form-error" role="alert">{error}</p>}
      {message && <p className="pending-cases__success" role="status">{message}</p>}
      {loading && <p className="dashboard-empty" role="status">Cargando solicitudes…</p>}
      {!loading && requests.length === 0 && !error && (
        <section className="dashboard-panel">
          <p className="dashboard-empty">No hay casos pendientes de revisión.</p>
        </section>
      )}
      {requests.map((request) => (
        <section className="dashboard-panel pending-cases__card" key={request.id}>
          <div className="dashboard-panel__header">
            <div>
              <h2>{request.titulo}</h2>
              <p>
                Solicitud #{request.id} · Enviado por {request.solicitante}
                {' '}· {formatDateTime(request.creada_en)}
              </p>
            </div>
            <span className="case-id">En espera de revisión</span>
          </div>
          <dl className="pending-cases__details">
            <div><dt>Fecha del hecho</dt><dd>{formatDate(request.fecha)}</dd></div>
            <div><dt>Lugar</dt><dd>{request.lugar}</dd></div>
            <div><dt>Tipo de falta</dt><dd>{request.tipo_falta}</dd></div>
            <div><dt>Estudiantes</dt><dd>{request.estudiantes.map((student) =>
              `${student.nombre} ${student.apellido_paterno} ${student.apellido_materno} (${student.curso})`,
            ).join('; ')}</dd></div>
            <div className="pending-cases__description">
              <dt>Descripción</dt><dd>{request.descripcion}</dd>
            </div>
          </dl>
          {request.evidencia_url && (
            <p>
              <a href={request.evidencia_url} target="_blank" rel="noopener noreferrer">
                Abrir archivo adjunto
              </a>
            </p>
          )}
          <form
            className="pending-cases__review"
            onSubmit={(event) => {
              event.preventDefault()
              void reviewRequest(request, 'aprobar')
            }}
          >
            <label>
              Comentario de revisión (opcional)
              <textarea
                maxLength={2000}
                rows={3}
                value={comments[request.id] ?? ''}
                onChange={(event) => setComments((current) => ({
                  ...current,
                  [request.id]: event.target.value,
                }))}
              />
            </label>
            <div>
              <button className="button--quiet pending-cases__approve" disabled={busyId === request.id} type="submit">
                Aprobar y registrar caso
              </button>
              <button
                className="button--quiet"
                disabled={busyId === request.id}
                onClick={() => void reviewRequest(request, 'rechazar')}
                type="button"
              >
                Rechazar reporte
              </button>
            </div>
          </form>
        </section>
      ))}
    </div>
  )
}
