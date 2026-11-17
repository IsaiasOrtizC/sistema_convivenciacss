import { useEffect, useMemo, useState, type FormEvent } from 'react'
import FollowUp from './FollowUp.tsx'
import { authenticatedFetch } from './authenticatedFetch'
import './FollowUp.css'
import './Notifications.css'

type NotificationItem = {
  id: number
  titulo: string
  mensaje: string
  icono: string
  fecha: string
  leida: boolean
  estado: string
  estado_etiqueta: string
  evento_tipo: string
  caso_id: number | null
  categoria_falta: string
  fecha_limite: string | null
  version_reglamento: number | null
  regla_operativa: boolean
  regla_evidencia: string
  regla_titulo_fuente: string
  regla_seccion_fuente: string
  regla_pagina_impresa: number | null
  regla_pagina_pdf: number | null
  historial: {
    fecha: string
    estado: string
    usuario: string
    motivo: string
  }[]
}

type NotificationsData = {
  notificaciones: NotificationItem[]
  puede_gestionar: boolean
  estados: { valor: string; etiqueta: string }[]
}

type NotificationsProps = {
  accessToken: string
  showFollowUp?: boolean
  onOpenCase?: (caseId: number) => void
}

type FilterMode = 'todas' | 'no_leidas' | 'con_caso'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function isNotificationsData(value: unknown): value is NotificationsData {
  return (
    isRecord(value) &&
    typeof value.puede_gestionar === 'boolean' &&
    Array.isArray(value.estados) &&
    value.estados.every(
      (estado: unknown) =>
        isRecord(estado) &&
        typeof estado.valor === 'string' &&
        typeof estado.etiqueta === 'string',
    ) &&
    Array.isArray(value.notificaciones) &&
    value.notificaciones.every(
      (notificacion: unknown) =>
        isRecord(notificacion) &&
        typeof notificacion.id === 'number' &&
        typeof notificacion.titulo === 'string' &&
        typeof notificacion.mensaje === 'string' &&
        typeof notificacion.icono === 'string' &&
        typeof notificacion.fecha === 'string' &&
        typeof notificacion.leida === 'boolean' &&
        typeof notificacion.estado === 'string' &&
        typeof notificacion.estado_etiqueta === 'string' &&
        typeof notificacion.evento_tipo === 'string' &&
        (typeof notificacion.caso_id === 'number' || notificacion.caso_id === null) &&
        typeof notificacion.categoria_falta === 'string' &&
        (typeof notificacion.fecha_limite === 'string' || notificacion.fecha_limite === null) &&
        (typeof notificacion.version_reglamento === 'number' || notificacion.version_reglamento === null) &&
        typeof notificacion.regla_operativa === 'boolean' &&
        typeof notificacion.regla_evidencia === 'string' &&
        typeof notificacion.regla_titulo_fuente === 'string' &&
        typeof notificacion.regla_seccion_fuente === 'string' &&
        (typeof notificacion.regla_pagina_impresa === 'number' || notificacion.regla_pagina_impresa === null) &&
        (typeof notificacion.regla_pagina_pdf === 'number' || notificacion.regla_pagina_pdf === null) &&
        Array.isArray(notificacion.historial) &&
        notificacion.historial.every(
          (cambio: unknown) =>
            isRecord(cambio) &&
            typeof cambio.fecha === 'string' &&
            typeof cambio.estado === 'string' &&
            typeof cambio.usuario === 'string' &&
            typeof cambio.motivo === 'string',
        ),
    )
  )
}

async function getErrorMessage(response: Response, fallback: string) {
  const body: unknown = await response.json().catch(() => null)
  if (isRecord(body) && typeof body.detail === 'string') return body.detail
  return fallback
}

async function loadNotifications(accessToken: string, signal?: AbortSignal) {
  const response = await authenticatedFetch(`${API_BASE_URL}/api/v1/notificaciones/`, {
    headers: { Authorization: `Bearer ${accessToken}` },
    signal,
  })
  if (!response.ok) {
    throw new Error(await getErrorMessage(response, 'No se pudieron cargar las notificaciones.'))
  }

  const body: unknown = await response.json()
  if (!isNotificationsData(body)) {
    throw new Error('El servidor devolvió notificaciones con formato inválido.')
  }
  return body
}

function formatDate(value: string) {
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return value
  return new Intl.DateTimeFormat('es-CL', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(parsed)
}

export default function Notifications({
  accessToken,
  showFollowUp = true,
  onOpenCase,
}: NotificationsProps) {
  const [data, setData] = useState<NotificationsData | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [pendingId, setPendingId] = useState<number | null>(null)
  const [reasons, setReasons] = useState<Record<number, string>>({})
  const [selectedStates, setSelectedStates] = useState<Record<number, string>>({})
  const [filterMode, setFilterMode] = useState<FilterMode>('todas')

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    loadNotifications(accessToken, controller.signal)
      .then((notifications) => {
        setData(notifications)
      })
      .catch((requestError: unknown) => {
        if (requestError instanceof DOMException && requestError.name === 'AbortError') return
        setError(
          requestError instanceof TypeError
            ? 'No fue posible conectar con el servidor.'
            : requestError instanceof Error
              ? requestError.message
              : 'No se pudieron cargar las notificaciones.',
        )
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })
    return () => {
      controller.abort()
    }
  }, [accessToken])

  const unreadCount = useMemo(
    () => data?.notificaciones.filter((item) => !item.leida).length ?? 0,
    [data],
  )

  const filteredNotifications = useMemo(() => {
    if (!data) return []
    if (filterMode === 'no_leidas') {
      return data.notificaciones.filter((item) => !item.leida)
    }
    if (filterMode === 'con_caso') {
      return data.notificaciones.filter((item) => item.caso_id !== null)
    }
    return data.notificaciones
  }, [data, filterMode])

  async function refresh(silent = false) {
    setError('')
    if (!silent) setLoading(true)
    try {
      setData(await loadNotifications(accessToken))
    } catch (requestError) {
      setError(
        requestError instanceof TypeError
          ? 'No fue posible conectar con el servidor.'
          : requestError instanceof Error
            ? requestError.message
            : 'No se pudieron cargar las notificaciones.',
      )
    } finally {
      if (!silent) setLoading(false)
    }
  }

  async function sendAction(
    id: number,
    action: { accion: 'leer' } | { accion: 'estado'; estado: string; motivo: string },
  ) {
    setPendingId(id)
    setError('')
    try {
      const response = await authenticatedFetch(`${API_BASE_URL}/api/v1/notificaciones/${id}/`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(action),
      })
      if (!response.ok) {
        throw new Error(await getErrorMessage(response, 'No se pudo actualizar la notificación.'))
      }

      if (action.accion === 'leer') {
        setData((current) =>
          current
            ? {
                ...current,
                notificaciones: current.notificaciones.map((item) =>
                  item.id === id ? { ...item, leida: true } : item,
                ),
              }
            : current,
        )
      } else {
        await refresh(true)
        setReasons((current) => ({ ...current, [id]: '' }))
        setSelectedStates((current) => {
          const next = { ...current }
          delete next[id]
          return next
        })
      }
    } catch (requestError) {
      setError(
        requestError instanceof TypeError
          ? 'No fue posible conectar con el servidor.'
          : requestError instanceof Error
            ? requestError.message
            : 'No se pudo actualizar la notificación.',
      )
    } finally {
      setPendingId(null)
    }
  }

  function handleStatusSubmit(event: FormEvent<HTMLFormElement>, item: NotificationItem) {
    event.preventDefault()
    const estado = selectedStates[item.id] ?? item.estado
    const motivo = (reasons[item.id] ?? '').trim()
    if (!motivo) return
    void sendAction(item.id, {
      accion: 'estado',
      estado,
      motivo,
    })
  }

  return (
    <div className="dashboard-content">
      <section className="dashboard-welcome">
        <p className="dashboard-eyebrow">Centro de alertas</p>
        <h1>Notificaciones</h1>
        <p>
          Revisa las alertas de convivencia y el historial de sus estados
          {unreadCount > 0 ? ` (${unreadCount} sin leer)` : ''}.
        </p>
      </section>

      <section className="dashboard-panel" aria-label="Bandeja de notificaciones">
        <div className="dashboard-panel__header">
          <div>
            <h2>Actividad reciente</h2>
            {data && data.notificaciones.length > 0 && (
              <div className="notification-filters" role="group" aria-label="Filtrar notificaciones">
                <button
                  aria-pressed={filterMode === 'todas'}
                  className="button--quiet"
                  onClick={() => setFilterMode('todas')}
                  type="button"
                >
                  Todas ({data.notificaciones.length})
                </button>
                <button
                  aria-pressed={filterMode === 'no_leidas'}
                  className="button--quiet"
                  onClick={() => setFilterMode('no_leidas')}
                  type="button"
                >
                  No leídas ({unreadCount})
                </button>
                <button
                  aria-pressed={filterMode === 'con_caso'}
                  className="button--quiet"
                  onClick={() => setFilterMode('con_caso')}
                  type="button"
                >
                  Con caso
                </button>
              </div>
            )}
          </div>
          <button className="button--quiet" disabled={loading} onClick={() => void refresh()} type="button">
            Actualizar
          </button>
        </div>

        {error && <p className="form-error" role="alert">{error}</p>}
        {loading && <p className="dashboard-empty" role="status">Cargando notificaciones…</p>}

        {!loading && filteredNotifications.length === 0 && (
          <p className="dashboard-empty">
            {filterMode === 'no_leidas'
              ? 'No tienes notificaciones sin leer.'
              : filterMode === 'con_caso'
                ? 'No hay notificaciones vinculadas a casos.'
                : 'No tienes notificaciones pendientes en este momento.'}
          </p>
        )}

        {filteredNotifications.map((item) => {
          const currentSelectedState = selectedStates[item.id] ?? item.estado
          const isManaging = pendingId === item.id

          return (
            <article
              className={`notification-card${item.leida ? '' : ' notification-card--unread'}`}
              key={item.id}
            >
              <div className="notification-card__icon" aria-hidden="true">{item.icono}</div>
              <div className="notification-card__body">
                <div className="notification-card__heading">
                  <h3>{item.titulo}</h3>
                  {!item.leida && <span className="case-id">Nueva</span>}
                </div>

                {item.caso_id !== null && (
                  <p className="notification-card__meta">
                    {onOpenCase ? (
                      <button
                        className="case-detail__link"
                        onClick={() => onOpenCase(item.caso_id!)}
                        type="button"
                      >
                        Caso #{item.caso_id}
                      </button>
                    ) : (
                      `Caso #${item.caso_id}`
                    )}
                    {item.categoria_falta && ` · ${item.categoria_falta}`}
                  </p>
                )}

                <p>{item.mensaje}</p>

                {item.regla_operativa && (
                  <details className="notification-card__evidence">
                    <summary>Ver evidencia y referencia del Reglamento</summary>
                    <blockquote>{item.regla_evidencia}</blockquote>
                    <p>
                      {item.regla_titulo_fuente} · {item.regla_seccion_fuente}
                      {item.regla_pagina_impresa !== null && ` · Página impresa ${item.regla_pagina_impresa}`}
                      {item.regla_pagina_pdf !== null && ` · Página PDF ${item.regla_pagina_pdf}`}
                      {item.version_reglamento !== null && ` · Versión ${item.version_reglamento}`}
                    </p>
                  </details>
                )}

                <p className="notification-card__meta">
                  {formatDate(item.fecha)} · {item.estado_etiqueta}
                  {item.fecha_limite && ` · Límite: ${item.fecha_limite}`}
                </p>

                {item.historial.length > 0 && (
                  <details className="notification-card__history">
                    <summary>Historial de cambios ({item.historial.length})</summary>
                    {item.historial.map((change, index) => (
                      <p key={`${change.fecha}-${index}`}>
                        {formatDate(change.fecha)} · {change.estado}
                        {change.usuario && ` · ${change.usuario}`}
                        {change.motivo && ` · ${change.motivo}`}
                      </p>
                    ))}
                  </details>
                )}

                {!item.leida && (
                  <button
                    className="button--quiet"
                    disabled={isManaging}
                    onClick={() => void sendAction(item.id, { accion: 'leer' })}
                    type="button"
                  >
                    Marcar como leída
                  </button>
                )}

                {data?.puede_gestionar && (
                  <form
                    className="notification-card__manage"
                    onSubmit={(event) => handleStatusSubmit(event, item)}
                  >
                    <label>
                      Estado
                      <select
                        name="estado"
                        onChange={(event) =>
                          setSelectedStates((current) => ({
                            ...current,
                            [item.id]: event.target.value,
                          }))
                        }
                        value={currentSelectedState}
                      >
                        {data.estados.map((estado) => (
                          <option key={estado.valor} value={estado.valor}>
                            {estado.etiqueta}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Motivo del cambio
                      <input
                        maxLength={500}
                        onChange={(event) =>
                          setReasons((current) => ({ ...current, [item.id]: event.target.value }))
                        }
                        placeholder="Describe brevemente la gestión o resolución…"
                        required
                        value={reasons[item.id] ?? ''}
                      />
                    </label>
                    <button
                      className="button--quiet"
                      disabled={isManaging || !(reasons[item.id] ?? '').trim()}
                      type="submit"
                    >
                      {isManaging ? 'Guardando…' : 'Guardar estado'}
                    </button>
                  </form>
                )}
              </div>
            </article>
          )
        })}
      </section>

      {showFollowUp && <FollowUp accessToken={accessToken} />}
    </div>
  )
}