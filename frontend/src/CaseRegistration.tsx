import { useEffect, useState, type FormEvent } from 'react'
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

type StudentDraft = {
  key: number
  estudiante_id: string
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
  const response = await fetch(`${API_BASE_URL}/api/v1/casos/formulario/`, {
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

  useEffect(() => {
    let active = true
    fetchOptions(accessToken)
      .then((result) => {
        if (active) setOptions(result)
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

  function updateStudent(key: number, patch: Partial<StudentDraft>) {
    setStudents((current) =>
      current.map((student) =>
        student.key === key ? { ...student, ...patch } : student,
      ),
    )
  }

  function selectStudent(key: number, selectedId: string) {
    const existing = options?.estudiantes.find((item) => String(item.id) === selectedId)
    if (!existing) {
      updateStudent(key, { ...emptyStudent(key) })
      return
    }
    updateStudent(key, {
      estudiante_id: selectedId,
      nombre: existing.nombre,
      apellido_paterno: existing.apellido_paterno,
      apellido_materno: existing.apellido_materno,
      numero_lista: existing.numero_lista === null ? '' : String(existing.numero_lista),
      curso_id: String(existing.curso_id),
    })
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

      const response = await fetch(`${API_BASE_URL}/api/v1/casos/nuevo/`, {
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
      setFecha('')
      setLugarId('')
      setDescripcion('')
      setTipoFalta('')
      setEvidencia(null)
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
        {error && <p className="form-error" role="alert">{error}</p>}
        {success && <p className="case-success" role="status">{success}</p>}
        {options && (
          <form className="case-registration-form" onSubmit={submit}>
            <label>
              Título
              <input
                maxLength={180}
                onChange={(event) => setTitulo(event.target.value)}
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
                required
                rows={5}
                value={descripcion}
              />
            </label>
            <fieldset className="case-students">
              <legend>Estudiantes involucrados</legend>
              {students.map((student, index) => (
                <div className="case-student" key={student.key}>
                  <div className="case-student__heading">
                    <strong>Estudiante {index + 1}</strong>
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
                  <label>
                    Seleccionar estudiante existente (opcional)
                    <select
                      onChange={(event) => selectStudent(student.key, event.target.value)}
                      value={student.estudiante_id}
                    >
                      <option value="">Ingreso manual</option>
                      {options.estudiantes.map((existing) => (
                        <option key={existing.id} value={existing.id}>
                          {existing.apellido_paterno} {existing.apellido_materno}, {existing.nombre}
                        </option>
                      ))}
                    </select>
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
                          estudiante_id: '', numero_lista: event.target.value,
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
              ))}
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
                type="file"
              />
            </label>
            <button className="button--quiet case-registration-form__submit" disabled={submitting} type="submit">
              {submitting ? 'Enviando…' : options.requiere_aprobacion ? 'Enviar a revisión' : 'Registrar caso'}
            </button>
          </form>
        )}
      </section>
    </div>
  )
}
