import { useEffect, useState, type FormEvent } from 'react'
import './CaseDetail.css'
import { downloadAuthenticatedFile } from './download'

type CaseStudent = {
  id: number
  nombre: string
  apellido_paterno: string
  apellido_materno: string
  numero_lista: number | null
  curso_id: number
  curso: string
  tipo_falta: string
}

type CaseDetailData = {
  id: number
  titulo: string
  descripcion: string
  fecha: string | null
  lugar_id: number
  lugar: string
  evidencia_url: string
  creado_por: string
  estudiantes: CaseStudent[]
  puede_editar: boolean
  puede_eliminar: boolean
  lugares: { id: number; nombre: string }[]
  cursos: { id: number; nombre: string }[]
  gravedades: { valor: string; etiqueta: string }[]
}

type CaseDetailProps = {
  accessToken: string
  caseId: number
  initialEditing?: boolean
  onBack: () => void
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function isCaseDetail(value: unknown): value is CaseDetailData {
  return (
    isRecord(value) &&
    typeof value.id === 'number' &&
    typeof value.titulo === 'string' &&
    typeof value.descripcion === 'string' &&
    (typeof value.fecha === 'string' || value.fecha === null) &&
    typeof value.lugar_id === 'number' &&
    typeof value.lugar === 'string' &&
    typeof value.evidencia_url === 'string' &&
    typeof value.creado_por === 'string' &&
    typeof value.puede_editar === 'boolean' &&
    typeof value.puede_eliminar === 'boolean' &&
    Array.isArray(value.estudiantes) &&
    value.estudiantes.every((item: unknown) =>
      isRecord(item) &&
      typeof item.id === 'number' &&
      typeof item.nombre === 'string' &&
      typeof item.apellido_paterno === 'string' &&
      typeof item.apellido_materno === 'string' &&
      (typeof item.numero_lista === 'number' || item.numero_lista === null) &&
      typeof item.curso_id === 'number' &&
      typeof item.curso === 'string' &&
      typeof item.tipo_falta === 'string',
    ) &&
    Array.isArray(value.lugares) &&
    value.lugares.every((item: unknown) =>
      isRecord(item) && typeof item.id === 'number' && typeof item.nombre === 'string',
    ) &&
    Array.isArray(value.cursos) &&
    value.cursos.every((item: unknown) =>
      isRecord(item) && typeof item.id === 'number' && typeof item.nombre === 'string',
    ) &&
    Array.isArray(value.gravedades) &&
    value.gravedades.every((item: unknown) =>
      isRecord(item) && typeof item.valor === 'string' && typeof item.etiqueta === 'string',
    )
  )
}

async function getErrorMessage(response: Response, fallback: string) {
  const body: unknown = await response.json().catch(() => null)
  if (isRecord(body) && typeof body.detail === 'string') return body.detail
  return fallback
}

function formatDate(value: string | null) {
  if (!value) return 'Sin fecha'
  return new Intl.DateTimeFormat('es-CL', {
    dateStyle: 'medium',
    timeZone: 'UTC',
  }).format(new Date(value))
}

export default function CaseDetail({
  accessToken,
  caseId,
  initialEditing = false,
  onBack,
}: CaseDetailProps) {
  const [data, setData] = useState<CaseDetailData | null>(null)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [placeId, setPlaceId] = useState('')
  const [severity, setSeverity] = useState('')
  const [students, setStudents] = useState<CaseStudent[]>([])
  const [editing, setEditing] = useState(false)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  useEffect(() => {
    let active = true
    fetch(`${API_BASE_URL}/api/v1/casos/${caseId}/`, {
      headers: { Authorization: ['Be', 'arer'].join('') + ' ' + accessToken },
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(await getErrorMessage(response, 'No se pudo cargar el caso.'))
        }
        const body: unknown = await response.json()
        if (!isCaseDetail(body)) throw new Error('El servidor devolvió datos de caso inválidos.')
        return body
      })
      .then((body) => {
        if (!active) return
        setData(body)
        setTitle(body.titulo)
        setDescription(body.descripcion)
        setPlaceId(String(body.lugar_id))
        setStudents(body.estudiantes)
        setSeverity(body.estudiantes[0]?.tipo_falta ?? 'Leve')
        setEditing(initialEditing && body.puede_editar)
        setError(initialEditing && !body.puede_editar ? 'No tienes permiso para editar este caso.' : '')
      })
      .catch((requestError: unknown) => {
        if (!active) return
        setError(
          requestError instanceof TypeError
            ? 'No fue posible conectar con el servidor.'
            : requestError instanceof Error
              ? requestError.message
              : 'No se pudo cargar el caso.',
        )
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [accessToken, caseId, initialEditing])

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!data) return
    setSaving(true)
    setError('')
    setMessage('')
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/casos/${caseId}/`, {
        method: 'PUT',
        headers: {
          Authorization: ['Be', 'arer'].join('') + ' ' + accessToken,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          titulo: title,
          descripcion: description,
          lugar_id: placeId,
          tipo_falta: severity,
          estudiantes: students.map((student) => ({
            id: student.id,
            nombre: student.nombre,
            apellido_paterno: student.apellido_paterno,
            apellido_materno: student.apellido_materno,
            curso_id: student.curso_id,
          })),
        }),
      })
      if (!response.ok) {
        throw new Error(await getErrorMessage(response, 'No se pudo guardar el caso.'))
      }
      const updatedResponse = await fetch(`${API_BASE_URL}/api/v1/casos/${caseId}/`, {
        headers: { Authorization: ['Be', 'arer'].join('') + ' ' + accessToken },
      })
      if (!updatedResponse.ok) {
        throw new Error(await getErrorMessage(updatedResponse, 'El caso se guardó, pero no se pudo recargar.'))
      }
      const updatedBody: unknown = await updatedResponse.json()
      if (!isCaseDetail(updatedBody)) {
        throw new Error('El caso se guardó, pero el servidor devolvió datos inválidos.')
      }
      setData(updatedBody)
      setStudents(updatedBody.estudiantes)
      setTitle(updatedBody.titulo)
      setDescription(updatedBody.descripcion)
      setPlaceId(String(updatedBody.lugar_id))
      setSeverity(updatedBody.estudiantes[0]?.tipo_falta ?? 'Leve')
      setEditing(false)
      setMessage('Los cambios del caso se guardaron correctamente.')
    } catch (requestError) {
      setError(
        requestError instanceof TypeError
          ? 'No fue posible conectar con el servidor.'
          : requestError instanceof Error
            ? requestError.message
            : 'No se pudo guardar el caso.',
      )
    } finally {
      setSaving(false)
    }
  }

  async function deleteCase() {
    if (!window.confirm(`¿Eliminar definitivamente el caso #${caseId}?`)) return
    setSaving(true)
    setError('')
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/casos/${caseId}/`, {
        method: 'DELETE',
        headers: { Authorization: ['Be', 'arer'].join('') + ' ' + accessToken },
      })
      if (!response.ok) {
        throw new Error(await getErrorMessage(response, 'No se pudo eliminar el caso.'))
      }
      onBack()
    } catch (requestError) {
      setError(
        requestError instanceof TypeError
          ? 'No fue posible conectar con el servidor.'
          : requestError instanceof Error
            ? requestError.message
            : 'No se pudo eliminar el caso.',
      )
    } finally {
      setSaving(false)
    }
  }

  async function exportCase(format: 'pdf' | 'xlsx') {
    setDownloading(true)
    setError('')
    try {
      await downloadAuthenticatedFile(
        `${API_BASE_URL}/api/v1/casos/${caseId}/exportar/${format}/`,
        accessToken,
        'No se pudo exportar el caso.',
      )
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'No se pudo exportar el caso.')
    } finally {
      setDownloading(false)
    }
  }

  function updateStudent(id: number, field: keyof CaseStudent, value: string) {
    setStudents((current) => current.map((student) => {
      if (student.id !== id) return student
      if (field === 'curso_id') {
        const course = data?.cursos.find((item) => item.id === Number(value))
        return { ...student, curso_id: Number(value), curso: course?.nombre ?? '' }
      }
      return { ...student, [field]: value }
    }))
  }

  if (loading) {
    return <div className="dashboard-content"><p role="status">Cargando caso…</p></div>
  }
  if (!data) {
    return (
      <div className="dashboard-content">
        <button className="button--quiet" onClick={onBack} type="button">Volver a casos</button>
        {error && <p className="form-error" role="alert">{error}</p>}
      </div>
    )
  }

  return (
    <div className="dashboard-content">
      <button className="button--quiet case-detail__back" onClick={onBack} type="button">
        Volver al historial
      </button>
      <section className="dashboard-welcome case-detail__hero">
        <p className="dashboard-eyebrow">Detalle del caso #{data.id}</p>
        <h1>{data.titulo}</h1>
        <p>{formatDate(data.fecha)} · {data.lugar}</p>
      </section>
      {error && <p className="form-error" role="alert">{error}</p>}
      {message && <p className="case-detail__success" role="status">{message}</p>}

      {editing ? (
        <form className="dashboard-panel case-detail__form" onSubmit={(event) => void save(event)}>
          <label>
            Título
            <input maxLength={180} required value={title} onChange={(event) => setTitle(event.target.value)} />
          </label>
          <label>
            Descripción
            <textarea required rows={5} value={description} onChange={(event) => setDescription(event.target.value)} />
          </label>
          <label>
            Lugar
            <select value={placeId} onChange={(event) => setPlaceId(event.target.value)}>
              {data.lugares.map((place) => <option key={place.id} value={place.id}>{place.nombre}</option>)}
            </select>
          </label>
          <label>
            Tipo de falta
            <select value={severity} onChange={(event) => setSeverity(event.target.value)}>
              {data.gravedades.map((item) => <option key={item.valor} value={item.valor}>{item.etiqueta}</option>)}
            </select>
          </label>
          <h2>Estudiantes involucrados</h2>
          {students.map((student) => (
            <fieldset className="case-detail__student" key={student.id}>
              <legend>{student.nombre} {student.apellido_paterno}</legend>
              <label>
                Nombre
                <input required value={student.nombre} onChange={(event) => updateStudent(student.id, 'nombre', event.target.value)} />
              </label>
              <label>
                Apellido paterno
                <input required value={student.apellido_paterno} onChange={(event) => updateStudent(student.id, 'apellido_paterno', event.target.value)} />
              </label>
              <label>
                Apellido materno
                <input required value={student.apellido_materno} onChange={(event) => updateStudent(student.id, 'apellido_materno', event.target.value)} />
              </label>
              <label>
                Curso
                <select value={student.curso_id} onChange={(event) => updateStudent(student.id, 'curso_id', event.target.value)}>
                  {data.cursos.map((course) => <option key={course.id} value={course.id}>{course.nombre}</option>)}
                </select>
              </label>
              {students.length > 1 && (
                <button
                  className="button--quiet"
                  onClick={() => setStudents((current) => current.filter((item) => item.id !== student.id))}
                  type="button"
                >
                  Quitar estudiante del caso
                </button>
              )}
            </fieldset>
          ))}
          <div className="case-detail__actions">
            <button className="case-detail__save" disabled={saving} type="submit">
              {saving ? 'Guardando…' : 'Guardar cambios'}
            </button>
            <button className="button--quiet" disabled={saving} onClick={() => setEditing(false)} type="button">
              Cancelar
            </button>
          </div>
        </form>
      ) : (
        <>
          <section className="dashboard-panel">
            <div className="dashboard-panel__header"><h2>Descripción</h2></div>
            <p className="case-detail__description">{data.descripcion}</p>
            <p><strong>Registrado por:</strong> {data.creado_por}</p>
            <p><strong>Clasificación:</strong> {data.estudiantes[0]?.tipo_falta ?? 'No especificada'}</p>
            {data.evidencia_url && (
              <p><a href={data.evidencia_url} target="_blank" rel="noopener noreferrer">Abrir evidencia adjunta</a></p>
            )}
          </section>
          <section className="dashboard-panel case-detail__students">
            <div className="dashboard-panel__header"><h2>Estudiantes involucrados</h2></div>
            <div className="dashboard-table-wrap">
              <table className="dashboard-table">
                <thead><tr><th>Estudiante</th><th>N.º de lista</th><th>Curso</th><th>Gravedad</th></tr></thead>
                <tbody>{data.estudiantes.map((student) => (
                  <tr key={student.id}>
                    <td>{student.nombre} {student.apellido_paterno} {student.apellido_materno}</td>
                    <td>{student.numero_lista ?? '—'}</td>
                    <td>{student.curso}</td>
                    <td>{student.tipo_falta}</td>
                  </tr>
                ))}</tbody>
              </table>
            </div>
          </section>
          <div className="case-detail__actions">
            <button className="button--quiet" disabled={downloading} onClick={() => void exportCase('pdf')} type="button">
              {downloading ? 'Preparando…' : 'Descargar PDF'}
            </button>
            <button className="button--quiet" disabled={downloading} onClick={() => void exportCase('xlsx')} type="button">
              Descargar Excel
            </button>
            {data.puede_editar && (
              <button className="case-detail__save" onClick={() => setEditing(true)} type="button">
                Editar caso
              </button>
            )}
            {data.puede_eliminar && (
              <button className="case-detail__delete" disabled={saving} onClick={() => void deleteCase()} type="button">
                Eliminar caso
              </button>
            )}
          </div>
        </>
      )}
    </div>
  )
}
