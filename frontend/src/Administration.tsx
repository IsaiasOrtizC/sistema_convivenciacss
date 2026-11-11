import { useCallback, useEffect, useState, type FormEvent } from 'react'
import './Administration.css'

type AdminSection = 'users' | 'students' | 'history'

type AdminUser = {
  id: number
  nombre: string
  apellido_paterno: string
  apellido_materno: string
  correo: string
  rol_id: number
  rol: string
  curso_id: number | null
  curso: string
  activo: boolean
  bloqueado: boolean
  primer_ingreso: boolean
  ultimo_acceso: string | null
}

type AdminStudent = {
  id: number
  nombre: string
  apellido_paterno: string
  apellido_materno: string
  correo: string
  activo: boolean
  curso_id: number
  curso: string
  numero_lista: number | null
  identificador: string
}

type AdminHistoryItem = {
  id: number
  usuario_id: number | null
  usuario: string
  accion: string
  detalle: string
  fecha: string
}

type StudentImportHistory = {
  archivo: string
  realizado_en: string
  importador: string
  alumnos_agregados: string[]
  duplicados_detectados: string[]
  filas_omitidas: number
}

type Options = { id: number; nombre: string }

type AdministrationProps = {
  accessToken: string
  section: AdminSection
  onOpenCase: (caseId: number) => void
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function isOptions(value: unknown): value is Options[] {
  return Array.isArray(value) && value.every((item) =>
    isRecord(item) && typeof item.id === 'number' && typeof item.nombre === 'string',
  )
}

function isAdminUser(value: unknown): value is AdminUser {
  return isRecord(value) &&
    typeof value.id === 'number' &&
    typeof value.nombre === 'string' &&
    typeof value.apellido_paterno === 'string' &&
    typeof value.apellido_materno === 'string' &&
    typeof value.correo === 'string' &&
    typeof value.rol_id === 'number' &&
    typeof value.rol === 'string' &&
    (typeof value.curso_id === 'number' || value.curso_id === null) &&
    typeof value.curso === 'string' &&
    typeof value.activo === 'boolean' &&
    typeof value.bloqueado === 'boolean' &&
    typeof value.primer_ingreso === 'boolean' &&
    (typeof value.ultimo_acceso === 'string' || value.ultimo_acceso === null)
}

function isAdminStudent(value: unknown): value is AdminStudent {
  return isRecord(value) &&
    typeof value.id === 'number' &&
    typeof value.nombre === 'string' &&
    typeof value.apellido_paterno === 'string' &&
    typeof value.apellido_materno === 'string' &&
    typeof value.correo === 'string' &&
    typeof value.activo === 'boolean' &&
    typeof value.curso_id === 'number' &&
    typeof value.curso === 'string' &&
    (typeof value.numero_lista === 'number' || value.numero_lista === null) &&
    typeof value.identificador === 'string'
}

function isAdminHistory(value: unknown): value is AdminHistoryItem {
  return isRecord(value) &&
    typeof value.id === 'number' &&
    (typeof value.usuario_id === 'number' || value.usuario_id === null) &&
    typeof value.usuario === 'string' &&
    typeof value.accion === 'string' &&
    typeof value.detalle === 'string' &&
    typeof value.fecha === 'string'
}

function isStudentImportHistory(value: unknown): value is StudentImportHistory {
  return isRecord(value) &&
    typeof value.archivo === 'string' &&
    typeof value.realizado_en === 'string' &&
    typeof value.importador === 'string' &&
    Array.isArray(value.alumnos_agregados) &&
    value.alumnos_agregados.every((item) => typeof item === 'string') &&
    Array.isArray(value.duplicados_detectados) &&
    value.duplicados_detectados.every((item) => typeof item === 'string') &&
    typeof value.filas_omitidas === 'number'
}

async function getErrorMessage(response: Response, fallback: string) {
  const body: unknown = await response.json().catch(() => null)
  if (isRecord(body) && typeof body.detail === 'string') return body.detail
  return fallback
}

function authHeaders(token: string): HeadersInit {
  return { Authorization: ['Be', 'arer'].join('') + ' ' + token }
}

function formatDate(value: string | null) {
  if (!value) return 'Nunca'
  return new Intl.DateTimeFormat('es-CL', {
    dateStyle: 'medium',
    timeZone: 'UTC',
  }).format(new Date(value))
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat('es-CL', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

export default function Administration({
  accessToken,
  section,
  onOpenCase,
}: AdministrationProps) {
  const [users, setUsers] = useState<AdminUser[]>([])
  const [students, setStudents] = useState<AdminStudent[]>([])
  const [studentImports, setStudentImports] = useState<StudentImportHistory[]>([])
  const [history, setHistory] = useState<AdminHistoryItem[]>([])
  const [roles, setRoles] = useState<Options[]>([])
  const [courses, setCourses] = useState<Options[]>([])
  const [selected, setSelected] = useState<number[]>([])
  const [query, setQuery] = useState('')
  const [stateFilter, setStateFilter] = useState('')
  const [roleFilter, setRoleFilter] = useState('')
  const [accessDateFrom, setAccessDateFrom] = useState('')
  const [accessDateTo, setAccessDateTo] = useState('')
  const [studentCourseFilter, setStudentCourseFilter] = useState('')
  const [studentNumberFilter, setStudentNumberFilter] = useState('')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [totalPages, setTotalPages] = useState(1)
  const [actions, setActions] = useState<string[]>([])
  const [studentHistory, setStudentHistory] = useState<{
    estudiante: AdminStudent
    casos: { id: number; titulo: string; fecha: string | null; lugar: string; gravedad: string }[]
    puntaje_riesgo: number
    estado_texto: string
  } | null>(null)
  const [editingUser, setEditingUser] = useState<AdminUser | null>(null)
  const [editingStudent, setEditingStudent] = useState<AdminStudent | null>(null)
  const [userForm, setUserForm] = useState({
    nombre: '',
    apellido_paterno: '',
    apellido_materno: '',
    correo: '',
    rol_id: '',
    curso_id: '',
    contrasena: '',
  })
  const [studentForm, setStudentForm] = useState({
    nombre: '',
    apellido_paterno: '',
    apellido_materno: '',
    correo: '',
    curso_id: '',
    numero_lista: '',
  })
  const [upload, setUpload] = useState<File | null>(null)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)

  const loadData = useCallback(async (
    nextPage: number,
    nextQuery: string,
    nextStateFilter: string,
    nextCourseFilter: string,
    nextNumberFilter: string,
    nextRoleFilter: string,
    nextAccessDateFrom: string,
    nextAccessDateTo: string,
  ) => {
    const params = new URLSearchParams({ pagina: String(nextPage) })
    if (nextQuery.trim()) {
      params.set(
        section === 'users' ? 'nombre' : 'busqueda',
        nextQuery.trim(),
      )
    }
    if (nextStateFilter) {
      params.set(section === 'history' ? 'accion' : 'estado', nextStateFilter)
    }
    if (section === 'users') {
      if (nextRoleFilter) params.set('rol', nextRoleFilter)
      if (nextAccessDateFrom) params.set('fecha_desde', nextAccessDateFrom)
      if (nextAccessDateTo) params.set('fecha_hasta', nextAccessDateTo)
    }
    if (section === 'students') {
      if (nextCourseFilter) params.set('curso', nextCourseFilter)
      if (nextNumberFilter) params.set('numero_lista', nextNumberFilter)
    }
    const endpoint = section === 'users'
      ? `/api/v1/admin/usuarios/?${params}`
      : section === 'students'
        ? `/api/v1/admin/estudiantes/?${params}`
        : `/api/v1/admin/historial-usuarios/?${params}`
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        headers: authHeaders(accessToken),
      })
      if (!response.ok) throw new Error(await getErrorMessage(response, 'No se pudieron cargar los datos.'))
      const body: unknown = await response.json()
      if (!isRecord(body) || !Array.isArray(body.resultados)) {
        throw new Error('El servidor devolvió datos administrativos inválidos.')
      }
      if (section === 'users') {
        if (!body.resultados.every(isAdminUser) || !isOptions(body.roles) || !isOptions(body.cursos)) {
          throw new Error('El servidor devolvió usuarios u opciones con formato inválido.')
        }
        setUsers(body.resultados)
        setRoles(body.roles)
        setCourses(body.cursos)
      } else if (section === 'students') {
        if (!body.resultados.every(isAdminStudent) ||
          !isOptions(body.cursos) ||
          !Array.isArray(body.importaciones) ||
          !body.importaciones.every(isStudentImportHistory)) {
          throw new Error('El servidor devolvió estudiantes u opciones con formato inválido.')
        }
        setStudents(body.resultados)
        setCourses(body.cursos)
        setStudentImports(body.importaciones)
      } else {
        if (!body.resultados.every(isAdminHistory) ||
          !Array.isArray(body.acciones) ||
          !body.acciones.every((item) => typeof item === 'string')) {
          throw new Error('El servidor devolvió historial con formato inválido.')
        }
        setHistory(body.resultados)
        setActions(body.acciones)
      }
      setPage(typeof body.pagina === 'number' ? body.pagina : nextPage)
      setTotal(typeof body.total === 'number' ? body.total : 0)
      setTotalPages(typeof body.total_paginas === 'number' ? body.total_paginas : 1)
    } catch (requestError) {
      setError(
        requestError instanceof TypeError
          ? 'No fue posible conectar con el servidor.'
          : requestError instanceof Error
            ? requestError.message
            : 'No se pudieron cargar los datos.',
      )
    } finally {
      setLoading(false)
    }
  }, [
    accessToken,
    section,
  ])

  function loadCurrentData(
    nextPage = page,
    nextQuery = query,
    nextStateFilter = stateFilter,
    nextCourseFilter = studentCourseFilter,
    nextNumberFilter = studentNumberFilter,
    nextRoleFilter = roleFilter,
    nextAccessDateFrom = accessDateFrom,
    nextAccessDateTo = accessDateTo,
  ) {
    return loadData(
      nextPage,
      nextQuery,
      nextStateFilter,
      nextCourseFilter,
      nextNumberFilter,
      nextRoleFilter,
      nextAccessDateFrom,
      nextAccessDateTo,
    )
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadData(1, '', '', '', '', '', '', '')
    }, 0)
    return () => window.clearTimeout(timer)
  }, [loadData])

  async function sendRequest(path: string, method: string, body?: unknown) {
    const isForm = body instanceof FormData
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers: {
        ...authHeaders(accessToken),
        ...(body && !isForm ? { 'Content-Type': 'application/json' } : {}),
      },
      body: body ? (isForm ? body : JSON.stringify(body)) : undefined,
    })
    if (!response.ok) throw new Error(await getErrorMessage(response, 'No se pudo completar la acción.'))
    return response.status === 204 ? null : response.json() as Promise<unknown>
  }

  function startCreateUser() {
    setEditingUser(null)
    setUserForm({
      nombre: '',
      apellido_paterno: '',
      apellido_materno: '',
      correo: '',
      rol_id: '',
      curso_id: '',
      contrasena: '',
    })
  }

  function startEditUser(user: AdminUser) {
    setEditingUser(user)
    setUserForm({
      nombre: user.nombre,
      apellido_paterno: user.apellido_paterno,
      apellido_materno: user.apellido_materno,
      correo: user.correo,
      rol_id: String(user.rol_id),
      curso_id: user.curso_id ? String(user.curso_id) : '',
      contrasena: '',
    })
  }

  async function saveUser(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setBusy(true)
    setError('')
    setMessage('')
    try {
      const result = await sendRequest(
        editingUser
          ? `/api/v1/admin/usuarios/${editingUser.id}/`
          : '/api/v1/admin/usuarios/',
        editingUser ? 'PUT' : 'POST',
        userForm,
      )
      setEditingUser(null)
      startCreateUser()
      setMessage(isRecord(result) && typeof result.mensaje === 'string'
        ? result.mensaje
        : 'Los datos del usuario se guardaron.')
      await loadCurrentData(1, query, stateFilter)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'No se pudo guardar el usuario.')
    } finally {
      setBusy(false)
    }
  }

  async function userAction(user: AdminUser, action: 'estado' | 'desbloquear' | 'eliminar') {
    if (action === 'eliminar' && !window.confirm(`¿Eliminar la cuenta de ${user.nombre} ${user.apellido_paterno}?`)) return
    setBusy(true)
    setError('')
    setMessage('')
    try {
      if (action === 'eliminar') {
        await sendRequest(`/api/v1/admin/usuarios/${user.id}/`, 'DELETE')
      } else {
        await sendRequest(`/api/v1/admin/usuarios/${user.id}/`, 'PATCH', {
          accion: action,
          activo: action === 'estado' ? !user.activo : undefined,
        })
      }
      setMessage('La cuenta se actualizó correctamente.')
      await loadCurrentData(page, query, stateFilter)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'No se pudo actualizar la cuenta.')
    } finally {
      setBusy(false)
    }
  }

  async function bulkUsers(action: 'desactivar' | 'eliminar') {
    if (!selected.length) return
    if (!window.confirm(`¿${action === 'eliminar' ? 'Eliminar' : 'Desactivar'} ${selected.length} cuenta(s)?`)) return
    setBusy(true)
    setError('')
    try {
      const result = await sendRequest('/api/v1/admin/usuarios/acciones-masivas/', 'POST', {
        accion: action,
        usuarios: selected,
      })
      setSelected([])
      setMessage(isRecord(result) && typeof result.mensaje === 'string' ? result.mensaje : 'Acción masiva completada.')
      await loadCurrentData(page, query, stateFilter)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'No se pudo completar la acción masiva.')
    } finally {
      setBusy(false)
    }
  }

  function startCreateStudent() {
    setEditingStudent(null)
    setStudentForm({
      nombre: '',
      apellido_paterno: '',
      apellido_materno: '',
      correo: '',
      curso_id: '',
      numero_lista: '',
    })
  }

  function startEditStudent(student: AdminStudent) {
    setEditingStudent(student)
    setStudentForm({
      nombre: student.nombre,
      apellido_paterno: student.apellido_paterno,
      apellido_materno: student.apellido_materno,
      correo: student.correo,
      curso_id: String(student.curso_id),
      numero_lista: student.numero_lista === null ? '' : String(student.numero_lista),
    })
  }

  async function saveStudent(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      await sendRequest(
        editingStudent
          ? `/api/v1/admin/estudiantes/${editingStudent.id}/`
          : '/api/v1/admin/estudiantes/',
        editingStudent ? 'PUT' : 'POST',
        studentForm,
      )
      startCreateStudent()
      setMessage(editingStudent ? 'Estudiante actualizado.' : 'Estudiante registrado.')
      await loadCurrentData(1, query, stateFilter)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'No se pudo guardar al estudiante.')
    } finally {
      setBusy(false)
    }
  }

  async function toggleStudent(student: AdminStudent) {
    setBusy(true)
    setError('')
    try {
      await sendRequest(`/api/v1/admin/estudiantes/${student.id}/`, 'PATCH', {
        activo: !student.activo,
      })
      setMessage(`Estudiante ${student.activo ? 'desactivado' : 'activado'}.`)
      await loadCurrentData(page, query, stateFilter)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'No se pudo cambiar el estado.')
    } finally {
      setBusy(false)
    }
  }

  async function removeStudent(student: AdminStudent) {
    if (!window.confirm(`¿Quitar a ${student.nombre} ${student.apellido_paterno}? Se conservará su historial de casos.`)) return
    setBusy(true)
    setError('')
    try {
      await sendRequest(`/api/v1/admin/estudiantes/${student.id}/`, 'DELETE')
      setMessage('Estudiante quitado y desactivado; sus antecedentes se conservaron.')
      await loadCurrentData(page, query, stateFilter)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'No se pudo quitar al estudiante.')
    } finally {
      setBusy(false)
    }
  }

  async function viewStudent(student: AdminStudent) {
    setBusy(true)
    setError('')
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/admin/estudiantes/${student.id}/`,
        { headers: authHeaders(accessToken) },
      )
      if (!response.ok) throw new Error(await getErrorMessage(response, 'No se pudo cargar la ficha.'))
      const body: unknown = await response.json()
      if (!isRecord(body) || !isRecord(body.estudiante) || !Array.isArray(body.casos)) {
        throw new Error('El servidor devolvió una ficha de estudiante inválida.')
      }
      const studentData = body.estudiante
      if (!isAdminStudent(studentData) ||
        typeof body.puntaje_riesgo !== 'number' ||
        typeof body.estado_texto !== 'string' ||
        !body.casos.every((item: unknown) =>
          isRecord(item) &&
          typeof item.id === 'number' &&
          typeof item.titulo === 'string' &&
          (typeof item.fecha === 'string' || item.fecha === null) &&
          typeof item.lugar === 'string' &&
          typeof item.gravedad === 'string',
        )) {
        throw new Error('El servidor devolvió una ficha de estudiante inválida.')
      }
      setStudentHistory({
        estudiante: studentData,
        casos: body.casos,
        puntaje_riesgo: body.puntaje_riesgo,
        estado_texto: body.estado_texto,
      })
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'No se pudo cargar la ficha.')
    } finally {
      setBusy(false)
    }
  }

  async function importStudents(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!upload) {
      setError('Selecciona el archivo Excel que deseas importar.')
      return
    }
    const formData = new FormData()
    formData.append('archivo_excel', upload)
    setBusy(true)
    setError('')
    try {
      const result = await sendRequest('/api/v1/admin/estudiantes/importar/', 'POST', formData)
      setUpload(null)
      setMessage(isRecord(result) && typeof result.mensaje === 'string' ? result.mensaje : 'Importación procesada.')
      await loadCurrentData(1, query, stateFilter)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'No se pudo importar el archivo.')
    } finally {
      setBusy(false)
    }
  }

  const heading = section === 'users'
    ? 'Administración de usuarios'
    : section === 'students'
      ? 'Administración de estudiantes'
      : 'Historial de usuarios'
  const hasStudentFilters = Boolean(
    query.trim() || studentCourseFilter || studentNumberFilter || stateFilter,
  )

  return (
    <div className="dashboard-content administration">
      <section className="dashboard-welcome">
        <p className="dashboard-eyebrow">Administración</p>
        <h1>{heading}</h1>
        <p>Gestiona los registros institucionales con permisos de Administrador.</p>
      </section>
      {error && <p className="form-error" role="alert">{error}</p>}
      {message && <p className="administration__success" role="status">{message}</p>}

      {section === 'users' && (
        <>
          <section className="dashboard-panel administration__filters">
            <label>Buscar usuario<input value={query} onChange={(event) => setQuery(event.target.value)} onKeyDown={(event) => {
              if (event.key === 'Enter') void loadCurrentData(1, event.currentTarget.value, stateFilter)
            }} /></label>
            <label>Estado<select value={stateFilter} onChange={(event) => {
              setStateFilter(event.target.value)
              void loadCurrentData(1, query, event.target.value)
            }}><option value="">Todos</option><option value="activo">Activo</option><option value="inactivo">Inactivo</option><option value="bloqueado">Bloqueada</option></select></label>
            <label>Rol<select value={roleFilter} onChange={(event) => {
              setRoleFilter(event.target.value)
            }}><option value="">Todos</option>{roles.map((role) => <option key={role.id} value={role.id}>{role.nombre}</option>)}</select></label>
            <label>Último acceso desde<input type="date" value={accessDateFrom} onChange={(event) => setAccessDateFrom(event.target.value)} /></label>
            <label>Último acceso hasta<input type="date" value={accessDateTo} onChange={(event) => setAccessDateTo(event.target.value)} /></label>
            <button className="button--quiet" onClick={() => void loadCurrentData(1, query, stateFilter)} type="button">Buscar</button>
            <button className="administration__primary" onClick={startCreateUser} type="button">Nuevo usuario</button>
          </section>
          <form className="dashboard-panel administration__form" onSubmit={(event) => void saveUser(event)}>
            <h2>{editingUser ? `Editar ${editingUser.nombre} ${editingUser.apellido_paterno}` : 'Crear usuario'}</h2>
            <div className="administration__form-grid">
              <label>Nombres<input required value={userForm.nombre} onChange={(event) => setUserForm({ ...userForm, nombre: event.target.value })} /></label>
              <label>Apellido paterno<input required value={userForm.apellido_paterno} onChange={(event) => setUserForm({ ...userForm, apellido_paterno: event.target.value })} /></label>
              <label>Apellido materno<input required value={userForm.apellido_materno} onChange={(event) => setUserForm({ ...userForm, apellido_materno: event.target.value })} /></label>
              <label>Correo institucional<input required type="email" value={userForm.correo} onChange={(event) => setUserForm({ ...userForm, correo: event.target.value })} /></label>
              <label>Rol<select required value={userForm.rol_id} onChange={(event) => setUserForm({ ...userForm, rol_id: event.target.value })}><option value="">Selecciona un rol</option>{roles.map((role) => <option key={role.id} value={role.id}>{role.nombre}</option>)}</select></label>
              {roles.find((role) => String(role.id) === userForm.rol_id)?.nombre === 'Profesor Jefe' && (
                <label>Curso asignado<select required value={userForm.curso_id} onChange={(event) => setUserForm({ ...userForm, curso_id: event.target.value })}><option value="">Selecciona un curso</option>{courses.map((course) => <option key={course.id} value={course.id}>{course.nombre}</option>)}</select></label>
              )}
              {editingUser && <label>Nueva contraseña (opcional)<input minLength={12} type="password" value={userForm.contrasena} onChange={(event) => setUserForm({ ...userForm, contrasena: event.target.value })} /></label>}
            </div>
            <div className="administration__actions">
              <button className="administration__primary" disabled={busy} type="submit">{busy ? 'Guardando…' : editingUser ? 'Guardar usuario' : 'Crear y enviar contraseña'}</button>
              {editingUser && <button className="button--quiet" onClick={startCreateUser} type="button">Cancelar</button>}
            </div>
          </form>
          <section className="dashboard-panel">
            <div className="dashboard-panel__header"><h2>Funcionarios</h2><span>{total} usuarios</span></div>
            {selected.length > 0 && <div className="administration__actions">
              <button className="button--quiet" disabled={busy} onClick={() => void bulkUsers('desactivar')} type="button">Desactivar seleccionados</button>
              <button className="administration__danger" disabled={busy} onClick={() => void bulkUsers('eliminar')} type="button">Eliminar seleccionados</button>
            </div>}
            {loading ? <p role="status">Cargando usuarios…</p> : (
              <div className="dashboard-table-wrap"><table className="dashboard-table">
                <thead><tr><th>Sel.</th><th>Funcionario</th><th>Rol / curso</th><th>Acceso</th><th>Estado</th><th>Acciones</th></tr></thead>
                <tbody>{users.map((user) => <tr key={user.id}>
                  <td><input aria-label={`Seleccionar ${user.nombre}`} checked={selected.includes(user.id)} onChange={(event) => setSelected((current) => event.target.checked ? [...current, user.id] : current.filter((id) => id !== user.id))} type="checkbox" /></td>
                  <td>{user.nombre} {user.apellido_paterno} {user.apellido_materno}<small>{user.correo}</small></td>
                  <td>{user.rol}{user.curso && <small>{user.curso}</small>}</td>
                  <td>{formatDate(user.ultimo_acceso)}</td>
                  <td>{user.bloqueado ? 'Bloqueada' : user.activo ? 'Activa' : 'Inactiva'}{user.primer_ingreso && <small>Debe cambiar contraseña</small>}</td>
                  <td className="administration__row-actions">
                    <button className="button--quiet" disabled={busy} onClick={() => startEditUser(user)} type="button">Editar</button>
                    <button className="button--quiet" disabled={busy} onClick={() => void userAction(user, 'estado')} type="button">{user.activo ? 'Desactivar' : 'Activar'}</button>
                    {user.bloqueado && <button className="button--quiet" disabled={busy} onClick={() => void userAction(user, 'desbloquear')} type="button">Desbloquear</button>}
                    <button className="administration__danger" disabled={busy} onClick={() => void userAction(user, 'eliminar')} type="button">Eliminar</button>
                  </td>
                </tr>)}</tbody>
              </table></div>
            )}
            <Pagination page={page} totalPages={totalPages} busy={loading} onPage={(value) => void loadCurrentData(value, query, stateFilter)} />
          </section>
        </>
      )}

      {section === 'students' && (
        <>
          {studentHistory && (
            <section className="dashboard-panel administration__student-history">
              <button className="button--quiet" onClick={() => setStudentHistory(null)} type="button">Cerrar ficha</button>
              <h2>{studentHistory.estudiante.nombre} {studentHistory.estudiante.apellido_paterno}</h2>
              <p>{studentHistory.estudiante.identificador} · {studentHistory.estudiante.curso} · {studentHistory.estado_texto} · Puntaje {studentHistory.puntaje_riesgo}</p>
              <div className="dashboard-table-wrap"><table className="dashboard-table"><thead><tr><th>Caso</th><th>Fecha</th><th>Lugar</th><th>Gravedad</th></tr></thead><tbody>
                {studentHistory.casos.map((item) => <tr key={item.id}><td><button className="case-detail__link" onClick={() => onOpenCase(item.id)} type="button">{item.titulo} (#{item.id})</button></td><td>{formatDate(item.fecha)}</td><td>{item.lugar}</td><td>{item.gravedad}</td></tr>)}
                {!studentHistory.casos.length && <tr><td colSpan={4}>No hay casos asociados.</td></tr>}
              </tbody></table></div>
            </section>
          )}
          <section className="dashboard-panel administration__filters">
            <label>Buscar estudiante<input value={query} onChange={(event) => setQuery(event.target.value)} onKeyDown={(event) => {
              if (event.key === 'Enter') void loadCurrentData(1, event.currentTarget.value, stateFilter)
            }} /></label>
            <label>Curso<select value={studentCourseFilter} onChange={(event) => {
              setStudentCourseFilter(event.target.value)
              void loadCurrentData(1, query, stateFilter, event.target.value, studentNumberFilter)
            }}><option value="">Todos</option>{courses.map((course) => <option key={course.id} value={course.id}>{course.nombre}</option>)}</select></label>
            <label>N.º de lista<input min="0" type="number" value={studentNumberFilter} onChange={(event) => setStudentNumberFilter(event.target.value)} onKeyDown={(event) => {
              if (event.key === 'Enter') void loadCurrentData(1, query, stateFilter, studentCourseFilter, event.currentTarget.value)
            }} /></label>
            <label>Estado<select value={stateFilter} onChange={(event) => {
              setStateFilter(event.target.value)
              void loadCurrentData(1, query, event.target.value, studentCourseFilter, studentNumberFilter)
            }}><option value="">Todos</option><option value="activo">Activo</option><option value="inactivo">Inactivo</option></select></label>
            <button className="button--quiet" onClick={() => void loadCurrentData(1, query, stateFilter)} type="button">Buscar</button>
          </section>
          <form className="dashboard-panel administration__form" onSubmit={(event) => void saveStudent(event)}>
            <h2>{editingStudent ? 'Editar estudiante' : 'Registrar estudiante'}</h2>
            <div className="administration__form-grid">
              <label>Nombres<input required value={studentForm.nombre} onChange={(event) => setStudentForm({ ...studentForm, nombre: event.target.value })} /></label>
              <label>Apellido paterno<input required value={studentForm.apellido_paterno} onChange={(event) => setStudentForm({ ...studentForm, apellido_paterno: event.target.value })} /></label>
              <label>Apellido materno<input required value={studentForm.apellido_materno} onChange={(event) => setStudentForm({ ...studentForm, apellido_materno: event.target.value })} /></label>
              <label>Correo (opcional)<input type="email" value={studentForm.correo} onChange={(event) => setStudentForm({ ...studentForm, correo: event.target.value })} /></label>
              <label>Curso<select required value={studentForm.curso_id} onChange={(event) => setStudentForm({ ...studentForm, curso_id: event.target.value })}><option value="">Selecciona un curso</option>{courses.map((course) => <option key={course.id} value={course.id}>{course.nombre}</option>)}</select></label>
              <label>N.º de lista<input min="0" type="number" value={studentForm.numero_lista} onChange={(event) => setStudentForm({ ...studentForm, numero_lista: event.target.value })} /></label>
            </div>
            <div className="administration__actions">
              <button className="administration__primary" disabled={busy} type="submit">{editingStudent ? 'Guardar estudiante' : 'Registrar estudiante'}</button>
              {editingStudent && <button className="button--quiet" onClick={startCreateStudent} type="button">Cancelar</button>}
            </div>
          </form>
          <form className="dashboard-panel administration__import" onSubmit={(event) => void importStudents(event)}>
            <h2>Importación desde Excel</h2>
            <p>Usa un archivo .xlsx con columnas: Nombres, apellido paterno, apellido materno, grado, paralelo y número de lista (opcional).</p>
            <div className="administration__actions">
              <input accept=".xlsx" onChange={(event) => setUpload(event.target.files?.[0] ?? null)} type="file" />
              <button className="button--quiet" disabled={busy || !upload} type="submit">Importar archivo</button>
            </div>
          </form>
          <section className="dashboard-panel">
          <div className="dashboard-panel__header"><h2>Últimas importaciones</h2><span>{studentImports.length} operaciones</span></div>
          {studentImports.length ? (
            <div className="dashboard-table-wrap"><table className="dashboard-table">
              <thead><tr><th>Fecha</th><th>Archivo / operador</th><th>Agregados</th><th>Duplicados / omitidos</th></tr></thead>
              <tbody>{studentImports.map((item) => (
                <tr key={`${item.realizado_en}-${item.archivo}`}>
                  <td>{formatDateTime(item.realizado_en)}</td>
                  <td>{item.archivo}<small>{item.importador}</small></td>
                  <td>
                    {item.alumnos_agregados.length}
                    {item.alumnos_agregados.length > 0 && (
                      <details><summary>Ver alumnos agregados</summary>{item.alumnos_agregados.map((name) => <small key={name}>{name}</small>)}</details>
                    )}
                  </td>
                  <td>
                    {item.duplicados_detectados.length} duplicados · {item.filas_omitidas} omitidos
                    {item.duplicados_detectados.length > 0 && (
                      <details><summary>Ver duplicados detectados</summary>{item.duplicados_detectados.map((name) => <small key={name}>{name}</small>)}</details>
                    )}
                  </td>
                </tr>
              ))}</tbody>
            </table></div>
          ) : <p className="dashboard-empty">Aún no se han importado alumnos.</p>}
          </section>
          <section className="dashboard-panel">
            <div className="dashboard-panel__header"><h2>Estudiantes</h2><span>{total} registros</span></div>
            {loading ? <p role="status">Cargando estudiantes…</p> : (
              <div className="dashboard-table-wrap"><table className="dashboard-table">
                <thead><tr><th>Estudiante</th><th>Identificador / lista</th><th>Curso</th><th>Estado</th><th>Acciones</th></tr></thead>
                <tbody>
                  {students.length ? students.map((student) => <tr key={student.id}>
                    <td>{student.nombre} {student.apellido_paterno} {student.apellido_materno}<small>{student.correo}</small></td>
                    <td>{student.identificador || 'Sin identificador'}<small>Lista: {student.numero_lista ?? '—'}</small></td>
                    <td>{student.curso}</td><td>{student.activo ? 'Activo' : 'Inactivo'}</td>
                    <td className="administration__row-actions">
                      <button className="button--quiet" disabled={busy} onClick={() => void viewStudent(student)} type="button">Ficha</button>
                      <button className="button--quiet" disabled={busy} onClick={() => startEditStudent(student)} type="button">Editar</button>
                      <button className="button--quiet" disabled={busy} onClick={() => void toggleStudent(student)} type="button">{student.activo ? 'Desactivar' : 'Activar'}</button>
                      <button className="administration__danger" disabled={busy} onClick={() => void removeStudent(student)} type="button">Quitar</button>
                    </td>
                  </tr>) : (
                    <tr><td className="dashboard-empty" colSpan={5} role="status">
                      {hasStudentFilters
                        ? 'No se encontraron alumnos con los filtros seleccionados.'
                        : 'No hay alumnos registrados.'}
                    </td></tr>
                  )}
                </tbody>
              </table></div>
            )}
            <Pagination page={page} totalPages={totalPages} busy={loading} onPage={(value) => void loadCurrentData(value, query, stateFilter)} />
          </section>
        </>
      )}

      {section === 'history' && (
        <>
          <section className="dashboard-panel administration__filters">
            <label>Buscar en historial<input value={query} onChange={(event) => setQuery(event.target.value)} onKeyDown={(event) => {
              if (event.key === 'Enter') void loadCurrentData(1, event.currentTarget.value, stateFilter)
            }} /></label>
            <label>Acción<select value={stateFilter} onChange={(event) => {
              setStateFilter(event.target.value)
              void loadCurrentData(1, query, event.target.value)
            }}><option value="">Todas</option>{actions.map((action) => <option key={action} value={action}>{action}</option>)}</select></label>
            <button className="button--quiet" onClick={() => void loadCurrentData(1, query, stateFilter)} type="button">Buscar</button>
          </section>
          <section className="dashboard-panel">
            <div className="dashboard-panel__header"><h2>Auditoría de acciones</h2><span>{total} registros</span></div>
            {loading ? <p role="status">Cargando historial…</p> : (
              <div className="dashboard-table-wrap"><table className="dashboard-table">
                <thead><tr><th>Fecha</th><th>Usuario</th><th>Acción</th><th>Detalle</th></tr></thead>
                <tbody>{history.map((item) => <tr key={item.id}><td>{formatDateTime(item.fecha)}</td><td>{item.usuario}</td><td>{item.accion}</td><td>{item.detalle}</td></tr>)}</tbody>
              </table></div>
            )}
            <Pagination page={page} totalPages={totalPages} busy={loading} onPage={(value) => void loadCurrentData(value, query, stateFilter)} />
          </section>
        </>
      )}
    </div>
  )
}

function Pagination({
  page,
  totalPages,
  busy,
  onPage,
}: {
  page: number
  totalPages: number
  busy: boolean
  onPage: (page: number) => void
}) {
  return (
    <div className="dashboard-pagination">
      <span>Pagina {page} de {totalPages}</span>
      <div>
        <button className="button--quiet" disabled={page <= 1 || busy} onClick={() => onPage(page - 1)} type="button">Anterior</button>
        <button className="button--quiet" disabled={page >= totalPages || busy} onClick={() => onPage(page + 1)} type="button">Siguiente</button>
      </div>
    </div>
  )
}
