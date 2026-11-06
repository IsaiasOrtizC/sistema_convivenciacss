import { useEffect, useState } from 'react'
import './Statistics.css'
import { downloadAuthenticatedFile } from './download'

type StatisticsFilters = {
  gravedad: string
  curso: string
  zona: string
  fecha_desde: string
  fecha_hasta: string
}

type StatisticsData = {
  total_casos: number
  curso_top: string
  tipo_caso_top: string
  zona_top: string
  variacion_pct: number
  gravedad_labels: string[]
  gravedad_data: number[]
  cursos_labels: string[]
  cursos_data: number[]
  zonas_labels: string[]
  zonas_data: number[]
  meses_labels: string[]
  mensual_data: number[]
  tabla_datos: {
    caso_id: number
    titulo: string
    fecha: string | null
    cursos: string
    zona: string
    gravedad: string
  }[]
  filtros: StatisticsFilters
  cursos_opciones: { id: number; nombre: string }[]
  zonas_opciones: { id: number; nombre: string }[]
}

type StatisticsProps = {
  accessToken: string
}

type ChartType = 'bar' | 'line' | 'pie'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')
const CURRENT_YEAR = new Date().getFullYear()
const DEFAULT_FILTERS: StatisticsFilters = {
  gravedad: '',
  curso: '',
  zona: '',
  fecha_desde: `${CURRENT_YEAR}-01-01`,
  fecha_hasta: `${CURRENT_YEAR}-12-31`,
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function isNumberArray(value: unknown): value is number[] {
  return Array.isArray(value) && value.every((item) => typeof item === 'number')
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === 'string')
}

function isStatisticsData(value: unknown): value is StatisticsData {
  return (
    isRecord(value) &&
    typeof value.total_casos === 'number' &&
    typeof value.curso_top === 'string' &&
    typeof value.tipo_caso_top === 'string' &&
    typeof value.zona_top === 'string' &&
    typeof value.variacion_pct === 'number' &&
    isStringArray(value.gravedad_labels) &&
    isNumberArray(value.gravedad_data) &&
    isStringArray(value.cursos_labels) &&
    isNumberArray(value.cursos_data) &&
    isStringArray(value.zonas_labels) &&
    isNumberArray(value.zonas_data) &&
    isStringArray(value.meses_labels) &&
    isNumberArray(value.mensual_data) &&
    Array.isArray(value.tabla_datos) &&
    value.tabla_datos.every(
      (row: unknown) =>
        isRecord(row) &&
        typeof row.caso_id === 'number' &&
        typeof row.titulo === 'string' &&
        (typeof row.fecha === 'string' || row.fecha === null) &&
        typeof row.cursos === 'string' &&
        typeof row.zona === 'string' &&
        typeof row.gravedad === 'string',
    ) &&
    isRecord(value.filtros) &&
    typeof value.filtros.gravedad === 'string' &&
    typeof value.filtros.curso === 'string' &&
    typeof value.filtros.zona === 'string' &&
    typeof value.filtros.fecha_desde === 'string' &&
    typeof value.filtros.fecha_hasta === 'string' &&
    Array.isArray(value.cursos_opciones) &&
    value.cursos_opciones.every(
      (item: unknown) =>
        isRecord(item) &&
        typeof item.id === 'number' &&
        typeof item.nombre === 'string',
    ) &&
    Array.isArray(value.zonas_opciones) &&
    value.zonas_opciones.every(
      (item: unknown) =>
        isRecord(item) &&
        typeof item.id === 'number' &&
        typeof item.nombre === 'string',
    )
  )
}

async function errorMessage(response: Response, fallback: string) {
  const body: unknown = await response.json().catch(() => null)
  if (isRecord(body) && typeof body.detail === 'string') return body.detail
  return fallback
}

async function fetchStatistics(
  accessToken: string,
  filters: StatisticsFilters,
): Promise<StatisticsData> {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.set(key, value)
  })
  const query = params.size > 0 ? `?${params}` : ''
  const response = await fetch(`${API_BASE_URL}/api/v1/estadisticas/${query}`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  })
  if (!response.ok) {
    throw new Error(await errorMessage(response, 'No se pudieron cargar las estadísticas.'))
  }
  const body: unknown = await response.json()
  if (!isStatisticsData(body)) {
    throw new Error('El servidor devolvió datos de estadísticas con formato inválido.')
  }
  return body
}

function StatChart({
  title,
  labels,
  values,
  type,
}: {
  title: string
  labels: string[]
  values: number[]
  type: ChartType
}) {
  const max = Math.max(1, ...values)
  const total = values.reduce((sum, value) => sum + value, 0)
  const colors = ['#7b1a1a', '#d4a017', '#4d9de0', '#57b786', '#df8050', '#7950a1', '#5b7c85', '#c94d4d']
  let accumulated = 0
  const pieStops = values.map((value, index) => {
    const start = total ? (accumulated / total) * 100 : 0
    accumulated += value
    const end = total ? (accumulated / total) * 100 : 0
    return `${colors[index % colors.length]} ${start}% ${end}%`
  }).join(', ')
  const pieBackground = total
    ? `conic-gradient(${pieStops})`
    : 'conic-gradient(var(--border) 0% 100%)'
  const points = values.map((value, index) => {
    const x = values.length < 2 ? 50 : (index / (values.length - 1)) * 100
    const y = 90 - (value / max) * 80
    return `${x},${y}`
  }).join(' ')
  return (
    <article className={`stat-chart stat-chart--${type}`}>
      <h2>{title}</h2>
      {labels.length === 0 && <p className="dashboard-empty">Sin datos para mostrar.</p>}
      {type === 'pie' && labels.length > 0 && (
        <div className="stat-pie-layout">
          <div
            aria-label={`${title}: ${labels.map((label, index) => `${label}, ${values[index] ?? 0}`).join('; ')}`}
            className="stat-pie"
            role="img"
            style={{ background: pieBackground }}
          />
          <div className="stat-pie-legend">
            {labels.map((label, index) => (
              <div key={`${label}-${index}`}>
                <span
                  aria-hidden="true"
                  className="stat-pie-legend__swatch"
                  style={{ backgroundColor: colors[index % colors.length] }}
                />
                <span>{label}</span>
                <strong>{values[index] ?? 0}</strong>
                <small>{total ? `${Math.round(((values[index] ?? 0) / total) * 100)}%` : '0%'}</small>
              </div>
            ))}
          </div>
        </div>
      )}
      {type === 'line' && labels.length > 0 && (
        <>
          <svg
            aria-label={`${title}: ${labels.map((label, index) => `${label}, ${values[index] ?? 0}`).join('; ')}`}
            className="stat-line-chart"
            preserveAspectRatio="none"
            role="img"
            viewBox="0 0 100 100"
          >
            <polyline points={points} />
            {values.map((value, index) => {
              const x = values.length < 2 ? 50 : (index / (values.length - 1)) * 100
              const y = 90 - (value / max) * 80
              return <circle cx={x} cy={y} key={`${labels[index]}-${index}`} r="1.6" />
            })}
          </svg>
          <div className="stat-line-labels">
            {labels.map((label, index) => (
              <span key={`${label}-${index}`} title={`${label}: ${values[index] ?? 0}`}>
                {label}
              </span>
            ))}
          </div>
        </>
      )}
      {type === 'bar' && labels.map((label, index) => {
        const value = values[index] ?? 0
        const width = `${(value / max) * 100}%`
        return (
          <div className="stat-chart__row" key={`${label}-${index}`}>
            <span className="stat-chart__label">{label}</span>
            <div className="stat-chart__track">
              <span className="stat-chart__bar" style={{ width }} />
            </div>
            <strong>{value}</strong>
          </div>
        )
      })}
    </article>
  )
}

function formatDate(value: string | null) {
  if (!value) return 'Sin fecha'
  return new Intl.DateTimeFormat('es-CL', {
    dateStyle: 'medium',
    timeZone: 'UTC',
  }).format(new Date(value))
}

export default function Statistics({ accessToken }: StatisticsProps) {
  const [filters, setFilters] = useState<StatisticsFilters>({ ...DEFAULT_FILTERS })
  const [data, setData] = useState<StatisticsData | null>(null)
  const [chartType, setChartType] = useState<ChartType>('bar')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [downloading, setDownloading] = useState(false)

  useEffect(() => {
    let active = true
    const timer = window.setTimeout(() => {
      setLoading(true)
      setError('')
      fetchStatistics(accessToken, filters)
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
                : 'No se pudieron cargar las estadísticas.',
          )
        })
        .finally(() => {
          if (active) setLoading(false)
        })
    }, 250)
    return () => {
      active = false
      window.clearTimeout(timer)
    }
  }, [accessToken, filters])

  function updateFilter(key: keyof StatisticsFilters, value: string) {
    setFilters((current) => ({ ...current, [key]: value }))
  }

  function clearFilters() {
    setFilters({ ...DEFAULT_FILTERS })
  }

  async function exportStatistics(format: 'pdf' | 'xlsx') {
    setDownloading(true)
    setError('')
    const params = new URLSearchParams()
    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.set(key, value)
    })
    try {
      await downloadAuthenticatedFile(
        `${API_BASE_URL}/api/v1/estadisticas/exportar/${format}/?${params}`,
        accessToken,
        'No se pudieron exportar las estadísticas.',
      )
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'No se pudieron exportar las estadísticas.')
    } finally {
      setDownloading(false)
    }
  }

  const variationTone =
    data && data.variacion_pct > 0
      ? 'positive'
      : data && data.variacion_pct < 0
        ? 'negative'
        : 'neutral'

  return (
    <div className="dashboard-content statistics-page">
      <section className="dashboard-welcome">
        <p className="dashboard-eyebrow">Análisis de convivencia</p>
        <h1>Estadísticas</h1>
        <p>Explora tendencias de casos según período, curso, zona y gravedad.</p>
      </section>

      <section className="dashboard-panel" aria-label="Filtros de estadísticas">
        <form className="statistics-filters" onSubmit={(event) => event.preventDefault()}>
          <label>
            Gravedad
            <select onChange={(event) => updateFilter('gravedad', event.target.value)} value={filters.gravedad}>
              <option value="">Todas</option>
              <option value="Leve">Leve</option>
              <option value="Grave">Grave</option>
              <option value="Gravísima">Gravísima</option>
            </select>
          </label>
          <label>
            Curso
            <select onChange={(event) => updateFilter('curso', event.target.value)} value={filters.curso}>
              <option value="">Todos</option>
              {data?.cursos_opciones.map((course) => (
                <option key={course.id} value={course.id}>{course.nombre}</option>
              ))}
            </select>
          </label>
          <label>
            Zona
            <select onChange={(event) => updateFilter('zona', event.target.value)} value={filters.zona}>
              <option value="">Todas</option>
              {data?.zonas_opciones.map((zone) => (
                <option key={zone.id} value={zone.id}>{zone.nombre}</option>
              ))}
            </select>
          </label>
          <label>
            Desde
            <input onChange={(event) => updateFilter('fecha_desde', event.target.value)} type="date" value={filters.fecha_desde} />
          </label>
          <label>
            Hasta
            <input onChange={(event) => updateFilter('fecha_hasta', event.target.value)} type="date" value={filters.fecha_hasta} />
          </label>
          <div className="statistics-filter-actions">
            <button className="button--quiet" disabled={loading} onClick={clearFilters} type="button">
              Limpiar
            </button>
            <span aria-live="polite">{loading ? 'Actualizando…' : 'Los gráficos se actualizan automáticamente.'}</span>
          </div>
        </form>
      </section>

      {error && <p className="form-error" role="alert">{error}</p>}
      {loading && <p className="dashboard-empty" role="status">Actualizando estadísticas…</p>}
      {data && (
        <>
          <section className="statistics-kpis" aria-label="Resumen estadístico">
            <article><span>Total de casos</span><strong>{data.total_casos}</strong></article>
            <article><span>Curso con más incidentes</span><strong>{data.curso_top}</strong></article>
            <article><span>Tipo más frecuente</span><strong>{data.tipo_caso_top}</strong></article>
            <article><span>Zona con más incidentes</span><strong>{data.zona_top}</strong></article>
            <article className={`statistics-kpi--${variationTone}`}>
              <span>Variación frente al año anterior</span>
              <strong>{data.variacion_pct > 0 ? '▲ ' : data.variacion_pct < 0 ? '▼ ' : '→ '}
                {Math.abs(data.variacion_pct)}%
              </strong>
            </article>
          </section>

          <div className="statistics-chart-types" aria-label="Tipo de visualización">
            {([
              ['bar', 'Barras'],
              ['line', 'Tendencia'],
              ['pie', 'Distribución'],
            ] as const).map(([type, label]) => (
              <button
                aria-pressed={chartType === type}
                className="button--quiet"
                key={type}
                onClick={() => setChartType(type)}
                type="button"
              >
                {label}
              </button>
            ))}
            <button className="button--quiet" disabled={downloading} onClick={() => void exportStatistics('pdf')} type="button">
              {downloading ? 'Preparando…' : 'Exportar PDF'}
            </button>
            <button className="button--quiet" disabled={downloading} onClick={() => void exportStatistics('xlsx')} type="button">
              Exportar Excel
            </button>
          </div>

          <section className="statistics-charts" aria-label="Gráficos estadísticos">
            <StatChart title="Casos por gravedad" labels={data.gravedad_labels} values={data.gravedad_data} type={chartType} />
            <StatChart title="Casos por curso" labels={data.cursos_labels} values={data.cursos_data} type={chartType} />
            <StatChart title="Casos por zona" labels={data.zonas_labels} values={data.zonas_data} type={chartType} />
            <StatChart
              title={chartType === 'pie' ? 'Casos por mes' : 'Evolución mensual'}
              labels={data.meses_labels}
              values={data.mensual_data}
              type={chartType}
            />
          </section>

          <section className="dashboard-panel" aria-labelledby="statistics-table-title">
            <div className="dashboard-panel__header">
              <h2 id="statistics-table-title">Detalle de casos según filtros</h2>
              <span>{data.tabla_datos.length} registros</span>
            </div>
            <div className="dashboard-table-wrap">
              <table className="dashboard-table">
                <thead>
                  <tr><th>ID</th><th>Título</th><th>Fecha</th><th>Curso(s)</th><th>Zona</th><th>Gravedad</th></tr>
                </thead>
                <tbody>
                  {data.tabla_datos.map((row) => (
                    <tr key={row.caso_id}>
                      <td><span className="case-id">#{row.caso_id}</span></td>
                      <td>{row.titulo}</td>
                      <td>{formatDate(row.fecha)}</td>
                      <td>{row.cursos}</td>
                      <td>{row.zona}</td>
                      <td>{row.gravedad}</td>
                    </tr>
                  ))}
                  {data.tabla_datos.length === 0 && (
                    <tr><td className="statistics-empty-row" colSpan={6}>No hay casos que coincidan con los filtros.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </div>
  )
}
