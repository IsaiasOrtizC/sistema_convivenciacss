import { useEffect, useState, type FormEvent } from 'react'
import FollowUp from './FollowUp.tsx'
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
}

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

async function loadNotifications(accessToken: string) {
  const response = await fetch(`${API_BASE_URL}/api/v1/notificaciones/`, {
    headers: { Authorization: `Bearer ${accessToken}` },
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
  return new Intl.DateTimeFormat('es-CL', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

export default function Notifications({
  accessToken,
  showFollowUp = true,
}: NotificationsProps) {
  const [data, setData] = useState<NotificationsData | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [pendingId, setPendingId] = useState<number | null>(null)
  const [reasons, setReasons] = useState<Record<number, string>>({})

  useEffect(() => {
    let active = true
    loadNotifications(accessToken)
      .then((notifications) => {
        if (active) setData(notifications)
      })
      .catch((requestError: unknown) => {
        if (!active) return
        setError(
          requestError instanceof TypeError
            ? 'No fue posible conectar con el servidor.'
            : requestError instanceof Error
              ? requestError.message
              : 'No se pudieron cargar las notificaciones.',
        )
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [accessToken])

  async function refresh() {
    setError('')
    setLoading(true)
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
      setLoading(false)
    }
  }

  async function sendAction(
    id: number,
    action: { accion: 'leer' } | { accion: 'estado'; estado: string; motivo: string },
  ) {
    setPendingId(id)
    setError('')
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/notificaciones/${id}/`, {
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
      await refresh()
      setReasons((current) => ({ ...current, [id]: '' }))
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
    const formData = new FormData(event.currentTarget)
    const estado = formData.get('estado')
    if (typeof estado !== 'string') return
    void sendAction(item.id, {
      accion: 'estado',
      estado,
      motivo: reasons[item.id] ?? '',
    })
  }

  return (
    <div className="dashboard-content">
      <section className="dashboard-welcome">
        <p className="dashboard-eyebrow">Centro de alertas</p>
        <h1>Notificaciones</h1>
        <p>Revisa las alertas de convivencia y el historial de sus estados.</p>
      </section>

      <section className="dashboard-panel" aria-label="Bandeja de notificaciones">
        <div className="dashboard-panel__header">
          <h2>Actividad reciente</h2>
          <button className="button--quiet" disabled={loading} onClick={() => void refresh()} type="button">
            Actualizar
          </button>
        </div>
        {error && <p className="form-error" role="alert">{error}</p>}
        {loading && <p className="dashboard-empty" role="status">Cargando notificaciones…</p>}
        {!loading && data?.notificaciones.length === 0 && (
          <p className="dashboard-empty">No tienes notificaciones pendientes en este momento.</p>
        )}
        {data?.notificaciones.map((item) => (
          <article className={`notification-card${item.leida ? '' : ' notification-card--unread'}`} key={item.id}>
            <div className="notification-card__icon" aria-hidden="true">{item.icono}</div>
            <div className="notification-card__body">
              <div className="notification-card__heading">
                <h3>{item.titulo}</h3>
                {!item.leida && <span className="case-id">Nueva</span>}
              </div>
              {item.caso_id !== null && (
                <p className="notification-card__meta">
                  Caso #{item.caso_id} · {item.categoria_falta}
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
                  disabled={pendingId === item.id}
                  onClick={() => void sendAction(item.id, { accion: 'leer' })}
                  type="button"
                >
                  Marcar como leída
                </button>
              )}
              {data?.puede_gestionar && (
                <form className="notification-card__manage" onSubmit={(event) => handleStatusSubmit(event, item)}>
                  <label>
                    Estado
                    <select defaultValue={item.estado} name="estado">
                      {data.estados.map((estado) => (
                        <option key={estado.valor} value={estado.valor}>{estado.etiqueta}</option>
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
                      required
                      value={reasons[item.id] ?? ''}
                    />
                  </label>
                  <button className="button--quiet" disabled={pendingId === item.id} type="submit">
                    Guardar estado
                  </button>
                </form>
              )}
            </div>
          </article>
        ))}
      </section>
      {showFollowUp && <FollowUp accessToken={accessToken} />}
    </div>
  )
}
