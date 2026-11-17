import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
} from 'react'
import { authenticatedFetch } from './authenticatedFetch'
import './CaseRegistration.css'

type CaseRegistrationOptions = {
  lugares: { id: number; nombre: string }[]
  cursos: { id: number; nombre: string }[]
  estudiantes: {
    id: number
    nombre: string
    apellido_paterno: string
    apellido_materno: string
    numero_lista: number | null
    curso_id: number
  }[]
  requiere_aprobacion: boolean
  fecha_hoy: string
}

type StudentOption = CaseRegistrationOptions['estudiantes'][number]

type StudentDraft = {
  key: number
  estudiante_id: string
  search_query: string
  nombre: string
  apellido_paterno: string
  apellido_materno: string
  numero_lista: string
  curso_id: string
}

type RegistrationProps = {
  accessToken: string
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

function normalizeText(text: string): string {
  return text
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim()
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function isOptions(value: unknown): value is CaseRegistrationOptions {
  return (
    isRecord(value) &&
    Array.isArray(value.lugares) &&
    value.lugares.every((item: unknown) =>
      isRecord(item) && typeof item.id === 'number' && typeof item.nombre === 'string',
    ) &&
    Array.isArray(value.cursos) &&
    value.cursos.every((item: unknown) =>
      isRecord(item) && typeof item.id === 'number' && typeof item.nombre === 'string',
    ) &&
    Array.isArray(value.estudiantes) &&
    value.estudiantes.every((item: unknown) =>
      isRecord(item) &&
      typeof item.id === 'number' &&
      typeof item.nombre === 'string' &&
      typeof item.apellido_paterno === 'string' &&
      typeof item.apellido_materno === 'string' &&
      (typeof item.numero_lista === 'number' || item.numero_lista === null) &&
      typeof item.curso_id === 'number',
    ) &&
    typeof value.requiere_aprobacion === 'boolean' &&
    typeof value.fecha_hoy === 'string'
  )
}

async function getErrorMessage(response: Response, fallback: string) {
  const body: unknown = await response.json().catch(() => null)
  if (isRecord(body) && typeof body.detail === 'string') return body.detail
  return fallback
}

async function fetchOptions(accessToken: string) {
  const response = await authenticatedFetch(`${API_BASE_URL}/api/v1/casos/formulario/`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  })
  if (!response.ok) {
    throw new Error(await getErrorMessage(response, 'No se pudieron cargar los datos del formulario.'))
  }
  const body: unknown = await response.json()
  if (!isOptions(body)) {
    throw new Error('El servidor devolvió datos de formulario con formato inválido.')
  }
  return body
}

function emptyStudent(key: number): StudentDraft {
  return {
    key,
    estudiante_id: '',
    search_query: '',
    nombre: '',
    apellido_paterno: '',
    apellido_materno: '',
    numero_lista: '',
    curso_id: '',
  }
}

export default function CaseRegistration({ accessToken }: RegistrationProps) {
  const [options, setOptions] = useState<CaseRegistrationOptions | null>(null)
  const [students, setStudents] = useState<StudentDraft[]>([emptyStudent(1)])
  const [nextKey, setNextKey] = useState(2)
  const [titulo, setTitulo] = useState('')
  const [fecha, setFecha] = useState('')
  const [lugarId, setLugarId] = useState('')
  const [descripcion, setDescripcion] = useState('')
  const [tipoFalta, setTipoFalta] = useState('')
  const [evidencia, setEvidencia] = useState<File | null>(null)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  // Control del desplegable de autocompletado por tarjeta de estudiante
  const [openStudentKey, setOpenStudentKey] = useState<number | null>(null)
  const [highlightedIndex, setHighlightedIndex] = useState<number>(-1)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    let active = true
    fetchOptions(accessToken)
      .then((result) => {
        if (!active) return
        setOptions(result)
        setFecha((prev) => prev || result.fecha_hoy)
      })
      .catch((requestError: unknown) => {
        if (!active) return
        setError(
          requestError instanceof TypeError
            ? 'No fue posible conectar con el servidor.'
            : requestError instanceof Error
              ? requestError.message
              : 'No se pudieron cargar los datos del formulario.',
        )
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [accessToken])

  // Mapa rápido de curso_id -> nombre de curso
  const cursosMap = useMemo(() => {
    const map = new Map<number, string>()
    options?.cursos.forEach((curso) => map.set(curso.id, curso.nombre))
    return map
  }, [options])

  // IDs de estudiantes ya seleccionados en otras tarjetas para evitar duplicados en el mismo caso
  const selectedIds = useMemo(
    () => new Set(students.map((s) => s.estudiante_id).filter(Boolean)),
    [students],
  )

  function getMatchingStudents(student: StudentDraft): StudentOption[] {
    if (!options) return []
    const term = normalizeText(student.search_query)
    if (!term) return []

    return options.estudiantes
      .filter((existing) => {
        if (
          selectedIds.has(String(existing.id)) &&
          String(existing.id) !== student.estudiante_id
        ) {
          return false
        }
        const fullName = normalizeText(
          `${existing.nombre} ${existing.apellido_paterno} ${existing.apellido_materno}`,
        )
        const reverseName = normalizeText(
          `${existing.apellido_paterno} ${existing.apellido_materno} ${existing.nombre}`,
        )
        const courseName = normalizeText(cursosMap.get(existing.curso_id) ?? '')
        return (
          fullName.includes(term) ||
          reverseName.includes(term) ||
          courseName.includes(term)
        )
      })
      .slice(0, 8)
  }

  function updateStudent(key: number, patch: Partial<StudentDraft>) {
    setStudents((current) =>
      current.map((student) =>
        student.key === key ? { ...student, ...patch } : student,
      ),
    )
  }

  function applySelectedStudent(key: number, existing: StudentOption) {
    const label = `${existing.nombre} ${existing.apellido_paterno} ${existing.apellido_materno}`.trim()
    updateStudent(key, {
      estudiante_id: String(existing.id),
      search_query: label,
      nombre: existing.nombre,
      apellido_paterno: existing.apellido_paterno,
      apellido_materno: existing.apellido_materno,
      numero_lista: existing.numero_lista === null ? '' : String(existing.numero_lista),
      curso_id: String(existing.curso_id),
    })
    setOpenStudentKey(null)
    setHighlightedIndex(-1)
  }

  function handleAutocompleteKeyDown(
    event: KeyboardEvent<HTMLInputElement>,
    student: StudentDraft,
    matches: StudentOption[],
  ) {
    if (openStudentKey !== student.key || matches.length === 0) return

    if (event.key === 'ArrowDown') {
      event.preventDefault()
      setHighlightedIndex((prev) => (prev + 1) % matches.length)
    } else if (event.key === 'ArrowUp') {
      event.preventDefault()
      setHighlightedIndex((prev) => (prev <= 0 ? matches.length - 1 : prev - 1))
    } else if (event.key === 'Enter' && highlightedIndex >= 0) {
      event.preventDefault()
      applySelectedStudent(student.key, matches[highlightedIndex])
    } else if (event.key === 'Escape') {
      setOpenStudentKey(null)
      setHighlightedIndex(-1)
    }
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setSuccess('')
    setSubmitting(true)

    try {
      const payload = {
        titulo,
        fecha,
        lugar_id: lugarId,
        descripcion,
        tipo_falta: tipoFalta,
        estudiantes: students.map((student) => ({
          estudiante_id: student.estudiante_id || null,
          nombre: student.nombre,
          apellido_paterno: student.apellido_paterno,
          apellido_materno: student.apellido_materno,
          numero_lista: student.numero_lista || null,
          curso_id: student.curso_id,
        })),
      }
      const body = new FormData()
      body.append('datos', JSON.stringify(payload))
      if (evidencia) body.append('evidencia_foto', evidencia)

      const response = await authenticatedFetch(`${API_BASE_URL}/api/v1/casos/nuevo/`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${accessToken}` },
        body,
      })
      if (!response.ok) {
        throw new Error(await getErrorMessage(response, 'No se pudo registrar el caso.'))
      }

      const result: unknown = await response.json()
      if (!isRecord(result) || typeof result.mensaje !== 'string') {
        throw new Error('El servidor devolvió una respuesta de registro inválida.')
      }
      setSuccess(result.mensaje)
      setTitulo('')
      setFecha(options?.fecha_hoy ?? '')
      setLugarId('')
      setDescripcion('')
      setTipoFalta('')
      setEvidencia(null)
      if (fileInputRef.current) fileInputRef.current.value = ''
      setStudents([emptyStudent(nextKey)])
      setNextKey(nextKey + 1)
    } catch (requestError) {
      setError(
        requestError instanceof TypeError
          ? 'No fue posible conectar con el servidor.'
          : requestError instanceof Error
            ? requestError.message
            : 'No se pudo registrar el caso.',
      )
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="dashboard-content">
      <section className="dashboard-welcome">
        <p className="dashboard-eyebrow">Gestión de casos</p>
        <h1>Registrar caso</h1>
        <p>
          {options?.requiere_aprobacion
            ? 'El reporte será enviado a revisión antes de incorporarse al historial.'
            : 'Registra los antecedentes del incidente y sus estudiantes involucrados.'}
        </p>
      </section>

      <section className="dashboard-panel">
        {loading && <p className="dashboard-empty" role="status">Cargando formulario…</p>}
        {error && <p className="case-error" role="alert">{error}</p>}
        {success && <p className="case-success" role="status">{success}</p>}
        {options && (
          <form className="case-registration-form" onSubmit={submit}>
            <label>
              Título
              <input
                maxLength={180}
                onChange={(event) => setTitulo(event.target.value)}
                placeholder="Ej. Altercado en patio durante recreo"
                required
                value={titulo}
              />
            </label>
            <div className="case-registration-form__grid">
              <label>
                Fecha del incidente
                <input
                  max={options.fecha_hoy}
                  onChange={(event) => setFecha(event.target.value)}
                  required
                  type="date"
                  value={fecha}
                />
              </label>
              <label>
                Lugar
                <select
                  onChange={(event) => setLugarId(event.target.value)}
                  required
                  value={lugarId}
                >
                  <option value="">Selecciona un lugar</option>
                  {options.lugares.map((lugar) => (
                    <option key={lugar.id} value={lugar.id}>{lugar.nombre}</option>
                  ))}
                </select>
              </label>
            </div>
            <label>
              Descripción
              <textarea
                onChange={(event) => setDescripcion(event.target.value)}
                placeholder="Describe detalladamente los hechos ocurridos…"
                required
                rows={5}
                value={descripcion}
              />
            </label>
            <fieldset className="case-students">
              <legend>Estudiantes involucrados</legend>
              {students.map((student, index) => {
                const matches = getMatchingStudents(student)
                const isDropdownOpen =
                  openStudentKey === student.key && student.search_query.trim().length > 0

                return (
                  <div className="case-student" key={student.key}>
                    <div className="case-student__heading">
                      <strong>
                        Estudiante {index + 1}
                        {student.estudiante_id && (
                          <span className="case-student__linked-badge"> · Vinculado</span>
                        )}
                      </strong>
                      {students.length > 1 && (
                        <button
                          className="button--quiet"
                          onClick={() =>
                            setStudents((current) =>
                              current.filter((entry) => entry.key !== student.key),
                            )
                          }
                          type="button"
                        >
                          Quitar
                        </button>
                      )}
                    </div>

                    <label className="case-student__search-label">
                      Buscar y rellenar estudiante existente (opcional)
                      <div className="case-student__autocomplete">
                        <input
                          aria-autocomplete="list"
                          aria-expanded={isDropdownOpen}
                          autoComplete="off"
                          onBlur={() => {
                            window.setTimeout(() => {
                              setOpenStudentKey((prev) =>
                                prev === student.key ? null : prev,
                              )
                            }, 150)
                          }}
                          onChange={(event) => {
                            const value = event.target.value
                            updateStudent(student.key, {
                              search_query: value,
                              ...(value === '' ? { estudiante_id: '' } : {}),
                            })
                            setOpenStudentKey(student.key)
                            setHighlightedIndex(0)
                          }}
                          onFocus={() => {
                            if (student.search_query.trim().length > 0) {
                              setOpenStudentKey(student.key)
                            }
                          }}
                          onKeyDown={(event) =>
                            handleAutocompleteKeyDown(event, student, matches)
                          }
                          placeholder="Escribe nombre, apellido o curso para autocompletar…"
                          role="combobox"
                          type="text"
                          value={student.search_query}
                        />
                        {student.search_query && (
                          <button
                            aria-label="Limpiar selección de estudiante"
                            className="case-student__clear"
                            onClick={() => {
                              updateStudent(student.key, emptyStudent(student.key))
                              setOpenStudentKey(null)
                            }}
                            type="button"
                          >
                            ✕
                          </button>
                        )}

                        {isDropdownOpen && (
                          <div className="case-student__dropdown" role="listbox">
                            {matches.length > 0 ? (
                              matches.map((match, matchIdx) => (
                                <button
                                  aria-selected={matchIdx === highlightedIndex}
                                  className={`case-student__dropdown-item${
                                    matchIdx === highlightedIndex ? ' is-active' : ''
                                  }`}
                                  key={match.id}
                                  onMouseDown={(event) => {
                                    event.preventDefault()
                                    applySelectedStudent(student.key, match)
                                  }}
                                  onMouseEnter={() => setHighlightedIndex(matchIdx)}
                                  role="option"
                                  type="button"
                                >
                                  <span>
                                    <strong>
                                      {match.apellido_paterno} {match.apellido_materno}, {match.nombre}
                                    </strong>
                                    {match.numero_lista !== null && (
                                      <small> · Lista #{match.numero_lista}</small>
                                    )}
                                  </span>
                                  <span className="case-student__course-tag">
                                    {cursosMap.get(match.curso_id) ?? 'Sin curso'}
                                  </span>
                                </button>
                              ))
                            ) : (
                              <div className="case-student__dropdown-empty">
                                Sin coincidencias. Completa los campos manualmente abajo.
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </label>

                    <div className="case-registration-form__grid case-registration-form__grid--student">
                      <label>
                        Nombre
                        <input
                          onChange={(event) => updateStudent(student.key, {
                            estudiante_id: '', nombre: event.target.value,
                          })}
                          required
                          value={student.nombre}
                        />
                      </label>
                      <label>
                        Apellido paterno
                        <input
                          onChange={(event) => updateStudent(student.key, {
                            estudiante_id: '', apellido_paterno: event.target.value,
                          })}
                          required
                          value={student.apellido_paterno}
                        />
                      </label>
                      <label>
                        Apellido materno
                        <input
                          onChange={(event) => updateStudent(student.key, {
                            estudiante_id: '', apellido_materno: event.target.value,
                          })}
                          value={student.apellido_materno}
                        />
                      </label>
                      <label>
                        Número de lista
                        <input
                          min="0"
                          onChange={(event) => updateStudent(student.key, {
                            numero_lista: event.target.value,
                          })}
                          type="number"
                          value={student.numero_lista}
                        />
                      </label>
                      <label>
                        Curso
                        <select
                          onChange={(event) => updateStudent(student.key, {
                            estudiante_id: '', curso_id: event.target.value,
                          })}
                          required
                          value={student.curso_id}
                        >
                          <option value="">Selecciona un curso</option>
                          {options.cursos.map((curso) => (
                            <option key={curso.id} value={curso.id}>{curso.nombre}</option>
                          ))}
                        </select>
                      </label>
                    </div>
                  </div>
                )
              })}
              <button
                className="button--quiet"
                onClick={() => {
                  setStudents((current) => [...current, emptyStudent(nextKey)])
                  setNextKey((current) => current + 1)
                }}
                type="button"
              >
                Agregar estudiante
              </button>
            </fieldset>
            <fieldset className="case-severity">
              <legend>Clasificación de gravedad</legend>
              {['Leve', 'Grave', 'Gravísima'].map((severity) => (
                <label key={severity}>
                  <input
                    checked={tipoFalta === severity}
                    name="tipo_falta"
                    onChange={() => setTipoFalta(severity)}
                    required={!tipoFalta}
                    type="radio"
                    value={severity}
                  />
                  {severity}
                </label>
              ))}
            </fieldset>
            <label>
              Evidencia (opcional; máximo 20 MB)
              <input
                accept=".pdf,.doc,.docx,.xls,.xlsx,.txt,.png,.jpg,.jpeg"
                onChange={(event) => setEvidencia(event.target.files?.[0] ?? null)}
                ref={fileInputRef}
                type="file"
              />
            </label>
            <button
              className="button--quiet case-registration-form__submit"
              disabled={submitting}
              type="submit"
            >
              {submitting ? 'Enviando…' : options.requiere_aprobacion ? 'Enviar a revisión' : 'Registrar caso'}
            </button>
          </form>
        )}
      </section>
    </div>
  )
}