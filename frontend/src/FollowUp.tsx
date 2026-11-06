import { useEffect, useState, type FormEvent } from 'react'

type FollowUpAction = {
  id: number
  titulo: string
  estado: 'pendiente' | 'completada'
  estado_etiqueta: string
  responsable: string
  fecha_limite: string | null
  vencida: boolean
}

type FollowUpRow = {
  caso_id: number
  fecha_caso: string
  registrado_en: string | null
  tiene_evidencia: boolean
  estudiante_id: string
  estudiante_pk: number | null
  categoria: string
  estado: 'abierto' | 'solucionado'
  estado_etiqueta: string
  avance: number | null
  acciones: FollowUpAction[]
  historial: { fecha: string; estado: string; motivo: string }[]
}

type FollowUpData = {
  puede_gestionar: boolean
  filas: FollowUpRow[]
}

type FollowUpProps = {
  accessToken: string
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function isFollowUpData(value: unknown): value is FollowUpData {
  return (
    isRecord(value) &&
    typeof value.puede_gestionar === 'boolean' &&
    Array.isArray(value.filas) &&
    value.filas.every(
      (row: unknown) =>
        isRecord(row) &&
        typeof row.caso_id === 'number' &&
        typeof row.fecha_caso === 'string' &&
        (typeof row.registrado_en === 'string' || row.registrado_en === null) &&
        typeof row.tiene_evidencia === 'boolean' &&
        typeof row.estudiante_id === 'string' &&
        (typeof row.estudiante_pk === 'number' || row.estudiante_pk === null) &&
        typeof row.categoria === 'string' &&
        (row.estado === 'abierto' || row.estado === 'solucionado') &&
        typeof row.estado_etiqueta === 'string' &&
        (typeof row.avance === 'number' || row.avance === null) &&
        Array.isArray(row.acciones) &&
        row.acciones.every(
          (action: unknown) =>
            isRecord(action) &&
            typeof action.id === 'number' &&
            typeof action.titulo === 'string' &&
            (action.estado === 'pendiente' || action.estado === 'completada') &&
            typeof action.estado_etiqueta === 'string' &&
            typeof action.responsable === 'string' &&
            (typeof action.fecha_limite === 'string' || action.fecha_limite === null) &&
            typeof action.vencida === 'boolean',
        ) &&
        Array.isArray(row.historial) &&
        row.historial.every(
          (entry: unknown) =>
            isRecord(entry) &&
            typeof entry.fecha === 'string' &&
            typeof entry.estado === 'string' &&
            typeof entry.motivo === 'string',
        ),
    )
  )
}

async function errorMessage(response: Response, fallback: string) {
  const body: unknown = await response.json().catch(() => null)
  if (isRecord(body) && typeof body.detail === 'string') return body.detail
  return fallback
}

async function fetchFollowUps(accessToken: string, state: string) {
  const query = state ? `?estado=${encodeURIComponent(state)}` : ''
  const response = await fetch(`${API_BASE_URL}/api/v1/seguimiento/${query}`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  })
  if (!response.ok) {
    throw new Error(await errorMessage(response, 'No se pudo cargar el seguimiento.'))
  }
  const body: unknown = await response.json()
  if (!isFollowUpData(body)) {
    throw new Error('El servidor devolvió datos de seguimiento con formato inválido.')
  }
  return body
}

function dateLabel(value: string) {
  return new Intl.DateTimeFormat('es-CL', {
    dateStyle: 'medium',
    timeZone: 'UTC',
  }).format(new Date(value))
}

export default function FollowUp({ accessToken }: FollowUpProps) {
  const [filter, setFilter] = useState('')
  const [data, setData] = useState<FollowUpData | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [pendingId, setPendingId] = useState<number | null>(null)
  const [reasons, setReasons] = useState<Record<string, string>>({})

  useEffect(() => {
    let active = true
    fetchFollowUps(accessToken, filter)
      .then((result) => {
        if (active) setData(result)
      })
      .catch((requestError: unknown) => {
        if (!active) return
        setError(
          requestError instanceof TypeError
            ? 'No fue posible conectar con el servidor.'
            : requestError instanceof Error
              ? requestError.message
              : 'No se pudo cargar el seguimiento.',
        )
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [accessToken, filter])

  async function refresh() {
    setError('')
    setLoading(true)
    try {
      setData(await fetchFollowUps(accessToken, filter))
    } catch (requestError) {
      setError(
        requestError instanceof TypeError
          ? 'No fue posible conectar con el servidor.'
          : requestError instanceof Error
            ? requestError.message
            : 'No se pudo cargar el seguimiento.',
      )
    } finally {
      setLoading(false)
    }
  }

  async function update(
    key: string,
    url: string,
    payload: Record<string, string>,
  ) {
    setPendingId(Number(key.split(':')[0]))
    setError('')
    try {
      const response = await fetch(`${API_BASE_URL}${url}`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      })
      if (!response.ok) {
        throw new Error(await errorMessage(response, 'No se pudo guardar el cambio.'))
      }
      await refresh()
      setReasons((current) => ({ ...current, [key]: '' }))
    } catch (requestError) {
      setError(
        requestError instanceof TypeError
          ? 'No fue posible conectar con el servidor.'
          : requestError instanceof Error
            ? requestError.message
            : 'No se pudo guardar el cambio.',
      )
    } finally {
      setPendingId(null)
    }
  }

  function submitAction(event: FormEvent<HTMLFormElement>, action: FollowUpAction) {
    event.preventDefault()
    const formData = new FormData(event.currentTarget)
    const estado = formData.get('estado')
    if (typeof estado !== 'string') return
    const key = `${action.id}:accion`
    void update(key, `/api/v1/seguimiento/acciones/${action.id}/`, {
      estado,
      motivo: reasons[key] ?? '',
    })
  }

  function submitClose(event: FormEvent<HTMLFormElement>, row: FollowUpRow) {
    event.preventDefault()
    if (row.estudiante_pk === null) return
    const key = `${row.caso_id}:cierre:${row.estudiante_pk}`
    void update(
      key,
      `/api/v1/seguimiento/casos/${row.caso_id}/estudiantes/${row.estudiante_pk}/cerrar/`,
      { motivo: reasons[key] ?? '' },
    )
  }

  return (
    <section className="dashboard-panel follow-up-panel" aria-labelledby="follow-up-heading">
      <div className="dashboard-panel__header">
        <div>
          <h2 id="follow-up-heading">Seguimiento de casos</h2>
          <p>Acciones pendientes, responsables, plazos e historial.</p>
        </div>
        <label className="follow-up-filter">
          Estado
          <select
            onChange={(event) => {
              setLoading(true)
              setFilter(event.target.value)
            }}
            value={filter}
          >
            <option value="">Todos</option>
            <option value="abierto">En seguimiento</option>
            <option value="solucionado">Solucionado</option>
          </select>
        </label>
      </div>
      {error && <p className="form-error" role="alert">{error}</p>}
      {loading && <p className="dashboard-empty" role="status">Cargando seguimiento…</p>}
      {!loading && data?.filas.length === 0 && (
        <p className="dashboard-empty">No se encontraron casos de seguimiento.</p>
      )}
      {data?.filas.map((row) => (
        <article className="follow-up-card" key={`${row.caso_id}-${row.estudiante_pk ?? 'sin-estudiante'}`}>
          <div className="follow-up-card__header">
            <h3>Caso #{row.caso_id}</h3>
            <span>{row.estado_etiqueta}</span>
          </div>
          <div className="follow-up-card__meta">
            <span>Estudiante: {row.estudiante_id}</span>
            <span>Tipo/categoría: {row.categoria}</span>
            <span>Fecha: {dateLabel(row.fecha_caso)}</span>
            {row.tiene_evidencia && <span>Hay evidencia asociada al caso.</span>}
            {row.avance !== null
              ? <span>Acciones completadas: {row.avance}%</span>
              : <span>No hay acciones requeridas configuradas.</span>}
          </div>
          <section className="follow-up-actions">
            <h4>Acciones requeridas</h4>
            {row.acciones.length === 0 && <p>No hay acciones requeridas vinculadas a reglas aprobadas.</p>}
            {row.acciones.map((action) => {
              const key = `${action.id}:accion`
              return (
                <article className="follow-up-action" key={action.id}>
                  <strong>{action.titulo}</strong>
                  <span>Estado: {action.estado_etiqueta}</span>
                  <span>Responsable: {action.responsable}</span>
                  {action.fecha_limite && (
                    <span className={action.vencida ? 'follow-up-overdue' : ''}>
                      Fecha límite: {dateLabel(action.fecha_limite)}
                      {action.vencida && ' · Vencida'}
                    </span>
                  )}
                  {data?.puede_gestionar && (
                    <form onSubmit={(event) => submitAction(event, action)}>
                      <select defaultValue={action.estado} name="estado">
                        <option value="pendiente">Pendiente</option>
                        <option value="completada">Completada</option>
                      </select>
                      <input
                        maxLength={500}
                        onChange={(event) =>
                          setReasons((current) => ({ ...current, [key]: event.target.value }))
                        }
                        placeholder="Motivo del cambio"
                        required
                        value={reasons[key] ?? ''}
                      />
                      <button className="button--quiet" disabled={pendingId === action.id} type="submit">
                        Guardar acción
                      </button>
                    </form>
                  )}
                </article>
              )
            })}
          </section>
          {row.historial.length > 0 && (
            <details className="follow-up-history">
              <summary>Historial de seguimiento</summary>
              {row.historial.map((entry, index) => (
                <p key={`${entry.fecha}-${index}`}>
                  {dateLabel(entry.fecha)} · {entry.estado} · {entry.motivo}
                </p>
              ))}
            </details>
          )}
          {data?.puede_gestionar && row.estado !== 'solucionado' && row.estudiante_pk !== null && (
            <form className="follow-up-close" onSubmit={(event) => submitClose(event, row)}>
              <label>
                Motivo del cierre
                <input
                  maxLength={1000}
                  onChange={(event) =>
                    setReasons((current) => ({
                      ...current,
                      [`${row.caso_id}:cierre:${row.estudiante_pk}`]: event.target.value,
                    }))
                  }
                  required
                  value={reasons[`${row.caso_id}:cierre:${row.estudiante_pk}`] ?? ''}
                />
              </label>
              <button
                className="button--quiet"
                disabled={pendingId === row.caso_id}
                type="submit"
              >
                Cerrar seguimiento
              </button>
            </form>
          )}
        </article>
      ))}
    </section>
  )
}
