import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
} from 'react'
import { authenticatedFetch } from './authenticatedFetch'
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

type AutocompleteSuggestion = {
  key: string
  categoria: 'Caso' | 'Estudiante' | 'Funcionario'
  titulo: string
  subtitulo: string
  relleno: string
  onSelect: () => void
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

  // Estado del desplegable de autocompletado
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const [activeIndex, setActiveIndex] = useState(-1)
  const skipNextFetchRef = useRef(false)
  const fieldWrapperRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const fetchResults = useCallback(
    async (termino: string, signal?: AbortSignal) => {
      setLoading(true)
      setError('')
      try {
        const params = new URLSearchParams({ q: termino })
        const response = await authenticatedFetch(`${API_BASE_URL}/api/v1/busqueda/?${params}`, {
          headers: { Authorization: `Bearer ${accessToken}` },
          signal,
        })
        if (!response.ok) throw new Error('No se pudo completar la búsqueda.')
        const body: unknown = await response.json()
        if (!isSearchResults(body)) throw new Error('El servidor devolvió resultados inválidos.')
        setResults(body)
        setDropdownOpen(true)
        setActiveIndex(-1)
      } catch (requestError) {
        if (requestError instanceof DOMException && requestError.name === 'AbortError') {
          return
        }
        setError(
          requestError instanceof TypeError
            ? 'No fue posible conectar con el servidor.'
            : requestError instanceof Error
              ? requestError.message
              : 'No se pudo completar la búsqueda.',
        )
      } finally {
        setLoading(false)
      }
    },
    [accessToken],
  )

  // Búsqueda predictiva con debounce de 250 ms al escribir
  useEffect(() => {
    if (skipNextFetchRef.current) {
      skipNextFetchRef.current = false
      return
    }

    const termino = query.trim()
    if (termino.length < 2) {
      setResults(null)
      setDropdownOpen(false)
      setActiveIndex(-1)
      setError('')
      return
    }

    const controller = new AbortController()
    const timer = window.setTimeout(() => {
      void fetchResults(termino, controller.signal)
    }, 250)

    return () => {
      window.clearTimeout(timer)
      controller.abort()
    }
  }, [query, fetchResults])

  // Cerrar el desplegable al hacer clic fuera del campo
  useEffect(() => {
    function handleOutsideClick(event: MouseEvent) {
      if (fieldWrapperRef.current && !fieldWrapperRef.current.contains(event.target as Node)) {
        setDropdownOpen(false)
        setActiveIndex(-1)
      }
    }
    document.addEventListener('mousedown', handleOutsideClick)
    return () => document.removeEventListener('mousedown', handleOutsideClick)
  }, [])

  // Lista plana de sugerencias para el desplegable y navegación con teclado
  const suggestions = useMemo<AutocompleteSuggestion[]>(() => {
    if (!results) return []
    const items: AutocompleteSuggestion[] = []

    for (const estudiante of results.estudiantes) {
      items.push({
        key: `est-${estudiante.id}`,
        categoria: 'Estudiante',
        titulo: estudiante.nombre_completo,
        subtitulo: estudiante.curso,
        relleno: estudiante.nombre_completo,
        onSelect: () => onOpenStudent(estudiante.id),
      })
    }

    for (const caso of results.casos) {
      items.push({
        key: `caso-${caso.id}`,
        categoria: 'Caso',
        titulo: `#${caso.id} · ${caso.titulo}`,
        subtitulo: `${caso.fecha} · ${caso.lugar}`,
        relleno: caso.titulo,
        onSelect: () => onOpenCase(caso.id),
      })
    }

    for (const usuario of results.usuarios) {
      items.push({
        key: `usr-${usuario.id}`,
        categoria: 'Funcionario',
        titulo: usuario.nombre_completo,
        subtitulo: `${usuario.rol} · ${usuario.correo}`,
        relleno: usuario.nombre_completo,
        onSelect: () => onOpenUser(usuario.id),
      })
    }

    return items
  }, [results, onOpenCase, onOpenStudent, onOpenUser])

  // Sugerencia inline (texto tenue) si la primera coincidencia empieza por el texto escrito
  const inlineSuggestion = useMemo(() => {
    if (!query || suggestions.length === 0) return ''
    const firstFill = suggestions[0].relleno
    if (firstFill.toLocaleLowerCase().startsWith(query.toLocaleLowerCase())) {
      return query + firstFill.slice(query.length)
    }
    return ''
  }, [query, suggestions])

  function applySuggestion(item: AutocompleteSuggestion) {
    skipNextFetchRef.current = true
    setQuery(item.relleno)
    setDropdownOpen(false)
    setActiveIndex(-1)
    item.onSelect()
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (!dropdownOpen || suggestions.length === 0) return

    if (event.key === 'ArrowDown') {
      event.preventDefault()
      const nextIndex = (activeIndex + 1) % suggestions.length
      setActiveIndex(nextIndex)
      skipNextFetchRef.current = true
      setQuery(suggestions[nextIndex].relleno)
    } else if (event.key === 'ArrowUp') {
      event.preventDefault()
      const prevIndex = activeIndex <= 0 ? suggestions.length - 1 : activeIndex - 1
      setActiveIndex(prevIndex)
      skipNextFetchRef.current = true
      setQuery(suggestions[prevIndex].relleno)
    } else if (event.key === 'Enter' && activeIndex >= 0) {
      event.preventDefault()
      applySuggestion(suggestions[activeIndex])
    } else if (event.key === 'Escape') {
      setDropdownOpen(false)
      setActiveIndex(-1)
    }
  }

  async function search(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const termino = query.trim()
    if (termino.length < 2) {
      setError('Escribe al menos dos caracteres para buscar.')
      setResults(null)
      setDropdownOpen(false)
      return
    }
    setDropdownOpen(false)
    await fetchResults(termino)
    setDropdownOpen(false)
  }

  return (
    <div className="dashboard-content global-search">
      <section className="dashboard-welcome">
        <p className="dashboard-eyebrow">Búsqueda global</p>
        <h1>Buscar en ConviData</h1>
        <p>Encuentra casos, estudiantes y funcionarios por nombre, correo o identificador.</p>
      </section>

      <section className="dashboard-panel global-search__panel--overflow">
        <form className="global-search__form" onSubmit={(event) => void search(event)}>
          <label htmlFor="global-search-query">Término de búsqueda</label>
          <div className="global-search__controls" ref={fieldWrapperRef}>
            <div className="global-search__autocomplete">
              {inlineSuggestion && (
                <input
                  aria-hidden="true"
                  className="global-search__ghost"
                  readOnly
                  tabIndex={-1}
                  type="text"
                  value={inlineSuggestion}
                />
              )}
              <input
                aria-autocomplete="list"
                aria-expanded={dropdownOpen}
                autoComplete="off"
                className="global-search__input"
                id="global-search-query"
                maxLength={100}
                onChange={(event) => setQuery(event.target.value)}
                onFocus={() => {
                  if (query.trim().length >= 2 && results) {
                    setDropdownOpen(true)
                  }
                }}
                onKeyDown={handleKeyDown}
                placeholder="Escribe nombre, correo o #caso…"
                ref={input