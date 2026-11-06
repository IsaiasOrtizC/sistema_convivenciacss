import { useCallback, useEffect, useState } from 'react'
import './TeacherCases.css'
import { downloadAuthenticatedFile } from './download'

type CourseCase = {
  caso_id: number
  titulo: string
  descripcion: string
  fecha: string | null
  lugar: string
  tipo_falta: string
  alumnos: string
}

type CourseData = {
  curso: { id: number; nombre: string }
  casos: CourseCase[]
  solicitudes: {
    id: number
    titulo: string
    fecha_evento: string
    estado: string
    lugar: string
    comentario_revision: string
    revisada_por: string
  }[]
}

type TeacherCasesProps = {
  accessToken: string
  onOpenCase: (caseId: number) => void
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function isCourseData(value: unknown): value is CourseData {
  return isRecord(value) &&
    isRecord(value.curso) &&
    typeof value.curso.id === 'number' &&
    typeof value.curso.nombre === 'string' &&
    Array.isArray(value.casos) &&
    value.casos.every((item: unknown) =>
      isRecord(item) &&
      typeof item.caso_id === 'number' &&
      typeof item.titulo === 'string' &&
      typeof item.descripcion === 'string' &&
      (typeof item.fecha === 'string' || item.fecha === null) &&
      typeof item.lugar === 'string' &&
      typeof item.tipo_falta === 'string' &&
      typeof item.alumnos === 'string',
    ) &&
    Array.isArray(value.solicitudes) &&
    value.solicitudes.every((item: unknown) =>
      isRecord(item) &&
      typeof item.id === 'number' &&
      typeof item.titulo === 'string' &&
      typeof item.fecha_evento === 'string' &&
      typeof item.estado === 'string' &&
      typeof item.lugar === 'string' &&
      typeof item.comentario_revision === 'string' &&
      typeof item.revisada_por === 'string',
    )
}

async function fetchCourseData(accessToken: string, query: URLSearchParams) {
  const response = await fetch(`${API_BASE_URL}/api/v1/mi-curso/?${query}`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  })
  if (!response.ok) throw new Error('No se pudo cargar el historial del curso.')
  const body: unknown = await response.json()
  if (!isCourseData(body)) throw new Error('El servidor devolvió datos del curso inválidos.')
  return body
}

export default function TeacherCases({ accessToken, onOpenCase }: TeacherCasesProps) {
  const [data, setData] = useState<CourseData | null>(null)
  const [gravedad, setGravedad] = useState('')
  const [desde, setDesde] = useState('')
  const [hasta, setHasta] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [downloading, setDownloading] = useState(false)

  const loadCases = useCallback(async () => {
    setLoading(true)
    setError('')
    const query = new URLSearchParams()
    if (gravedad) query.set('gravedad', gravedad)
    if (desde) query.set('fecha_desde', desde)
    if (hasta) query.set('fecha_hasta', hasta)
    try {
      setData(await fetchCourseData(accessToken, query))
    } catch (requestError) {
      setError(
        requestError instanceof TypeError
          ? 'No fue posible conectar con el servidor.'
          : requestError instanceof Error
            ? requestError.message
            : 'No se pudo cargar el historial del curso.',
      )
    } finally {
      setLoading(false)
    }
  }, [accessToken, desde, gravedad, hasta])

  useEffect(() => {
    let active = true
    fetchCourseData(accessToken, new URLSearchParams())
      .then((body) => {
        if (active) setData(body)
      })
      .catch((requestError: unknown) => {
        if (!active) return
        setError(
          requestError instanceof TypeError
            ? 'No fue posible conectar con el servidor.'
            : requestError instanceof Error
              ? requestError.message
              : 'No se pudo cargar el historial del curso.',
        )
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [accessToken])

  async function exportCases(format: 'pdf' | 'xlsx') {
    setDownloading(true)
    setError('')
    const query = new URLSearchParams()
    if (gravedad) query.set('gravedad', gravedad)
    if (desde) query.set('fecha_desde', desde)
    if (hasta) query.set('fecha_hasta', hasta)
    const suffix = query.size ? `?${query}` : ''
    try {
      await downloadAuthenticatedFile(
        `${API_BASE_URL}/api/v1/mi-curso/exportar/${format}/${suffix}`,
        accessToken,
        'No se pudo exportar el historial del curso.',
      )
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'No se pudo exportar el historial del curso.')
    } finally {
      setDownloading(false)
    }
  }

  return (
    <div className="dashboard-content">
      <section className="dashboard-welcome">
        <p className="dashboard-eyebrow">Profesor Jefe</p>
        <h1>{data ? `Casos de ${data.curso.nombre}` : 'Mi curso'}</h1>
        <p>Consulta los casos vinculados a los estudiantes de tu curso y el estado de tus reportes.</p>
      </section>

      <section className="dashboard-panel" aria-labelledby="course-cases-title">
        <div className="dashboard-panel__header">
          <h2 id="course-cases-title">Historial de casos</h2>
          <div className="teacher-cases__header-actions">
            <span>{data?.casos.length ?? 0} casos</span>
            <button className="button--quiet" disabled={loading || downloading} onClick={() => void exportCases('pdf')} type="button">PDF</button>
            <button className="button--quiet" disabled={loading || downloading} onClick={() => void exportCases('xlsx')} type="button">Excel</button>
          </div>
        </div>
        <form className="teacher-cases__filters" onSubmit={(event) => {
          event.preventDefault()
          void loadCases()
        }}>
          <label>Gravedad
            <select value={gravedad} onChange={(event) => setGravedad(event.target.value)}>
              <option value="">Todas</option>
              <option value="Leve">Leve</option>
              <option value="Grave">Grave</option>
              <option value="Gravísima">Gravísima</option>
            </select>
          </label>
          <label>Desde<input type="date" value={desde} onChange={(event) => setDesde(event.target.value)} /></label>
          <label>Hasta<input type="date" value={hasta} onChange={(event) => setHasta(event.target.value)} /></label>
          <button className="button--primary" disabled={loading} type="submit">Aplicar filtros</button>
        </form>
        {error && <p className="form-error" role="alert">{error}</p>}
        {loading && <p className="dashboard-empty" role="status">Cargando casos…</p>}
        {!loading && data?.casos.length ? (
          <div className="dashboard-table-wrap">
            <table className="dashboard-table">
              <thead><tr><th>Caso</th><th>Fecha</th><th>Lugar</th><th>Gravedad</th><th>Estudiantes</th></tr></thead>
              <tbody>{data.casos.map((caso) => (
                <tr key={caso.caso_id}>
                  <td>
                    <button className="case-detail__link" onClick={() => onOpenCase(caso.caso_id)} type="button">
                      #{caso.caso_id} · {caso.titulo}
                    </button>
                    <small>{caso.descripcion}</small>
                  </td>
                  <td>{caso.fecha ? new Intl.DateTimeFormat('es-CL', { dateStyle: 'medium', timeZone: 'UTC' }).format(new Date(caso.fecha)) : 'Sin fecha'}</td>
                  <td>{caso.lugar || 'No especificado'}</td>
                  <td>{caso.tipo_falta}</td>
                  <td>{caso.alumnos}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        ) : !loading && <p className="dashboard-empty">No hay casos que coincidan con los filtros.</p>}
      </section>

      <section className="dashboard-panel">
        <div className="dashboard-panel__header"><h2>Mis reportes</h2><span>{data?.solicitudes.length ?? 0}</span></div>
        {data?.solicitudes.length ? (
          <div className="dashboard-table-wrap">
            <table className="dashboard-table">
              <thead><tr><th>Reporte</th><th>Fecha del evento</th><th>Lugar</th><th>Estado</th><th>Revisión</th></tr></thead>
              <tbody>{data.solicitudes.map((solicitud) => (
                <tr key={solicitud.id}>
                  <td>{solicitud.titulo}</td>
                  <td>{solicitud.fecha_evento}</td>
                  <td>{solicitud.lugar}</td>
                  <td>{solicitud.estado}</td>
                  <td>{solicitud.comentario_revision || solicitud.revisada_por || 'Sin comentarios'}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        ) : <p className="dashboard-empty">Aún no has enviado reportes.</p>}
      </section>
    </div>
  )
}
