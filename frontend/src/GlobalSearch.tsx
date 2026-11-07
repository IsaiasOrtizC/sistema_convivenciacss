import { useState, type FormEvent } from 'react'
import './GlobalSearch.css'

type SearchResults = {
  estudiantes: { id: number; nombre_completo: string; curso: string }[]
  casos: { id: number; titulo: string; fecha: string; lugar: string }[]
  usuarios: { id: number; nombre_completo: string; correo: string; rol: string }[]
}

type GlobalSearchProps = {
  accessToken: string
  onOpenCase: (caseId: number) => void
  onOpenStudent: (studentId: number) => void
  onOpenUser: (userId: number) => void
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function isSearchResults(value: unknown): value is SearchResults {
  if (!isRecord(value)) return false
  return ['estudiantes', 'casos', 'usuarios'].every((key) =>
    Array.isArray(value[key]) &&
    value[key].every((item: unknown) =>
      isRecord(item) &&
      typeof item.id === 'number' &&
      (key === 'estudiantes'
        ? typeof item.nombre_completo === 'string' && typeof item.curso === 'string'
        : key === 'casos'
          ? typeof item.titulo === 'string' && typeof item.fecha === 'string' && typeof item.lugar === 'string'
          : typeof item.nombre_completo === 'string' && typeof item.correo === 'string' && typeof item.rol === 'string'),
    ),
  )
}

export default function GlobalSearch({
  accessToken,
  onOpenCase,
  onOpenStudent,
  onOpenUser,
}: GlobalSearchProps) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResults | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function search(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (query.trim().length < 2) {
      setError('Escribe al menos dos caracteres para buscar.')
      setResults(null)
      return
    }
    setLoading(true)
    setError('')
    try {
      const params = new URLSearchParams({ q: query.trim() })
      const response = await fetch(`${API_BASE_URL}/api/v1/busqueda/?${params}`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      })
      if (!response.ok) throw new Error('No se pudo completar la búsqueda.')
      const body: unknown = await response.json()
      if (!isSearchResults(body)) throw new Error('El servidor devolvió resultados inválidos.')
      setResults(body)
    } catch (requestError) {
      setError(requestError instanceof TypeError
        ? 'No fue posible conectar con el servidor.'
        : requestError instanceof Error
          ? requestError.message
          : 'No se pudo completar la búsqueda.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="dashboard-content global-search">
      <section className="dashboard-welcome">
        <p className="dashboard-eyebrow">Búsqueda global</p>
        <h1>Buscar en ConviData</h1>
        <p>Encuentra casos, estudiantes y funcionarios por nombre, correo o identificador.</p>
      </section>
      <section className="dashboard-panel">
        <form className="global-search__form" onSubmit={(event) => void search(event)}>
          <label htmlFor="global-search-query">Término de búsqueda</label>
          <div>
            <input id="global-search-query" maxLength={100} value={query} onChange={(event) => setQuery(event.target.value)} />
            <button className="button--primary" disabled={loading} type="submit">{loading ? 'Buscando…' : 'Buscar'}</button>
          </div>
        </form>
        {error && <p className="form-error" role="alert">{error}</p>}
      </section>

      {results && (
        <>
          <section className="dashboard-panel">
            <div className="dashboard-panel__header"><h2>Casos</h2><span>{results.casos.length}</span></div>
            {results.casos.length ? <ul className="global-search__results">{results.casos.map((caso) => (
              <li key={caso.id}>
                <button className="case-detail__link" onClick={() => onOpenCase(caso.id)} type="button">#{caso.id} · {caso.titulo}</button>
                <span>{caso.fecha} · {caso.lugar}</span>
              </li>
            ))}</ul> : <p className="dashboard-empty">No se encontraron casos.</p>}
          </section>
          <section className="dashboard-panel">
            <div className="dashboard-panel__header"><h2>Estudiantes</h2><span>{results.estudiantes.length}</span></div>
            {results.estudiantes.length ? <ul className="global-search__results">{results.estudiantes.map((estudiante) => (
              <li key={estudiante.id}>
                <strong>{estudiante.nombre_completo}</strong>
                <span>{estudiante.curso}</span>
                <button className="case-detail__link" onClick={() => onOpenStudent(estudiante.id)} type="button">
                  Ver historial de casos
                </button>
              </li>
            ))}</ul> : <p className="dashboard-empty">No se encontraron estudiantes.</p>}
          </section>
          <section className="dashboard-panel">
            <div className="dashboard-panel__header"><h2>Funcionarios</h2><span>{results.usuarios.length}</span></div>
            {results.usuarios.length ? <ul className="global-search__results">{results.usuarios.map((usuario) => (
              <li key={usuario.id}>
                <strong>{usuario.nombre_completo}</strong>
                <span>{usuario.correo} · {usuario.rol}</span>
                <button className="case-detail__link" onClick={() => onOpenUser(usuario.id)} type="button">
                  Ver casos registrados
                </button>
              </li>
            ))}</ul> : <p className="dashboard-empty">No se encontraron funcionarios.</p>}
          </section>
        </>
      )}
    </div>
  )
}
