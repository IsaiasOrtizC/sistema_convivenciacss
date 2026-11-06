import { useState, type FormEvent } from 'react'
import Administration from './Administration.tsx'
import AccountSettings from './AccountSettings.tsx'
import CaseDetail from './CaseDetail.tsx'
import CaseRegistration from './CaseRegistration.tsx'
import Documents from './Documents.tsx'
import TeacherCases from './TeacherCases.tsx'
import GlobalSearch from './GlobalSearch.tsx'
import Notifications from './Notifications.tsx'
import PendingCases from './PendingCases.tsx'
import Statistics from './Statistics.tsx'
import './App.css'

type TokenResponse = {
  access: string
}

type UserProfile = {
  id: number
  nombre: string
  apellido_paterno: string
  apellido_materno: string
  correo: string
  rol: string
}

type DashboardCase = {
  id: number
  titulo: string
  fecha: string | null
  lugar: string
}

type DashboardData = {
  metricas: {
    total_casos: number
    casos_leves: number
    casos_graves: number
    casos_gravisimas: number
  }
  periodo: {
    casos: number
    curso_mas_incidentes: string
    tipo_falta_frecuente: string
    zona_mas_conflictos: string
    variacion: number
    zonas: { nombre: string; total: number }[]
  }
  casos: {
    resultados: DashboardCase[]
    pagina: number
    total_paginas: number
    total: number
    tiene_anterior: boolean
    tiene_siguiente: boolean
  }
}

type CaseHistoryFilters = {
  q: string
  curso: string
  gravedad: string
  fecha_desde: string
  fecha_hasta: string
}

type CaseHistoryData = {
  resultados: {
    id: number
    titulo: string
    descripcion: string
    lugar: string
    fecha: string | null
    usuario_id: number | null
  }[]
  pagina: number
  total_paginas: number
  total: number
  tiene_anterior: boolean
  tiene_siguiente: boolean
  cursos: { id: number; nombre: string }[]
  mostrar_contador: boolean
}

const EMPTY_CASE_FILTERS: CaseHistoryFilters = {
  q: '',
  curso: '',
  gravedad: '',
  fecha_desde: '',
  fecha_hasta: '',
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

async function getErrorMessage(response: Response, fallback: string) {
  const body: unknown = await response.json().catch(() => null)

  if (
    typeof body === 'object' &&
    body !== null &&
    'detail' in body &&
    typeof body.detail === 'string'
  ) {
    return body.detail
  }

  return fallback
}

function isDashboardData(value: unknown): value is DashboardData {
  if (!isRecord(value) || !isRecord(value.metricas) || !isRecord(value.periodo) || !isRecord(value.casos)) {
    return false
  }

  const { metricas, periodo, casos } = value
  return (
    typeof metricas.total_casos === 'number' &&
    typeof metricas.casos_leves === 'number' &&
    typeof metricas.casos_graves === 'number' &&
    typeof metricas.casos_gravisimas === 'number' &&
    typeof periodo.casos === 'number' &&
    typeof periodo.curso_mas_incidentes === 'string' &&
    typeof periodo.tipo_falta_frecuente === 'string' &&
    typeof periodo.zona_mas_conflictos === 'string' &&
    typeof periodo.variacion === 'number' &&
    Array.isArray(periodo.zonas) &&
    periodo.zonas.every(
      (zona: unknown) =>
        isRecord(zona) &&
        typeof zona.nombre === 'string' &&
        typeof zona.total === 'number',
    ) &&
    Array.isArray(casos.resultados) &&
    casos.resultados.every(
      (caso: unknown) =>
        isRecord(caso) &&
        typeof caso.id === 'number' &&
        typeof caso.titulo === 'string' &&
        (typeof caso.fecha === 'string' || caso.fecha === null) &&
        typeof caso.lugar === 'string',
    ) &&
    typeof casos.pagina === 'number' &&
    typeof casos.total_paginas === 'number' &&
    typeof casos.total === 'number' &&
    typeof casos.tiene_anterior === 'boolean' &&
    typeof casos.tiene_siguiente === 'boolean'
  )
}

async function fetchDashboard(accessToken: string, page = 1): Promise<DashboardData> {
  const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/?pagina=${page}`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  })

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response, 'No se pudo cargar el panel de convivencia.'),
    )
  }

  const body: unknown = await response.json()
  if (!isDashboardData(body)) {
    throw new Error('El servidor devolvió datos de dashboard con formato inválido.')
  }

  return body
}

function isCaseHistoryData(value: unknown): value is CaseHistoryData {
  return (
    isRecord(value) &&
    Array.isArray(value.resultados) &&
    value.resultados.every(
      (caso: unknown) =>
        isRecord(caso) &&
        typeof caso.id === 'number' &&
        typeof caso.titulo === 'string' &&
        typeof caso.descripcion === 'string' &&
        typeof caso.lugar === 'string' &&
        (typeof caso.fecha === 'string' || caso.fecha === null) &&
        (typeof caso.usuario_id === 'number' || caso.usuario_id === null),
    ) &&
    typeof value.pagina === 'number' &&
    typeof value.total_paginas === 'number' &&
    typeof value.total === 'number' &&
    typeof value.tiene_anterior === 'boolean' &&
    typeof value.tiene_siguiente === 'boolean' &&
    Array.isArray(value.cursos) &&
    value.cursos.every(
      (curso: unknown) =>
        isRecord(curso) &&
        typeof curso.id === 'number' &&
        typeof curso.nombre === 'string',
    ) &&
    typeof value.mostrar_contador === 'boolean'
  )
}

async function fetchCaseHistory(
  accessToken: string,
  page: number,
  filters: CaseHistoryFilters,
): Promise<CaseHistoryData> {
  const params = new URLSearchParams({ pagina: String(page) })
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.set(key, value)
  })

  const response = await fetch(`${API_BASE_URL}/api/v1/casos/?${params}`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  })

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response, 'No se pudo cargar el historial de casos.'),
    )
  }

  const body: unknown = await response.json()
  if (!isCaseHistoryData(body)) {
    throw new Error('El servidor devolvió datos de casos con formato inválido.')
  }

  return body
}

function isTokenResponse(value: unknown): value is TokenResponse {
  return (
    typeof value === 'object' &&
    value !== null &&
    'access' in value &&
    typeof value.access === 'string'
  )
}

function isUserProfile(value: unknown): value is UserProfile {
  return (
    typeof value === 'object' &&
    value !== null &&
    'id' in value &&
    typeof value.id === 'number' &&
    'nombre' in value &&
    typeof value.nombre === 'string' &&
    'apellido_paterno' in value &&
    typeof value.apellido_paterno === 'string' &&
    'apellido_materno' in value &&
    typeof value.apellido_materno === 'string' &&
    'correo' in value &&
    typeof value.correo === 'string' &&
    'rol' in value &&
    typeof value.rol === 'string'
  )
}

function App() {
  const [correo, setCorreo] = useState('')
  const [contrasena, setContrasena] = useState('')
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [accessToken, setAccessToken] = useState<string | null>(null)
  const [dashboard, setDashboard] = useState<DashboardData | null>(null)
  const [dashboardError, setDashboardError] = useState('')
  const [isDashboardLoading, setIsDashboardLoading] = useState(false)
  const [activeSection, setActiveSection] = useState<
    | 'dashboard'
    | 'cases'
    | 'case-detail'
    | 'notifications'
    | 'register'
    | 'statistics'
    | 'pending-cases'
    | 'admin-users'
    | 'admin-students'
    | 'admin-history'
    | 'profile'
    | 'settings'
    | 'documents'
    | 'teacher-cases'
    | 'search'
  >('dashboard')
  const [selectedCaseId, setSelectedCaseId] = useState<number | null>(null)
  const [caseHistory, setCaseHistory] = useState<CaseHistoryData | null>(null)
  const [caseFilters, setCaseFilters] = useState(EMPTY_CASE_FILTERS)
  const [caseHistoryError, setCaseHistoryError] = useState('')
  const [isCaseHistoryLoading, setIsCaseHistoryLoading] = useState(false)
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setIsSubmitting(true)

    try {
      const tokenResponse = await fetch(`${API_BASE_URL}/api/auth/token/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ correo, contrasena }),
      })

      if (!tokenResponse.ok) {
        throw new Error(
          await getErrorMessage(tokenResponse, 'No se pudo iniciar sesión. Revisa tus credenciales.'),
        )
      }

      const tokenBody: unknown = await tokenResponse.json()
      if (!isTokenResponse(tokenBody)) {
        throw new Error('El servidor devolvió una respuesta de autenticación inválida.')
      }

      const profileResponse = await fetch(`${API_BASE_URL}/api/v1/me/`, {
        headers: { Authorization: `Bearer ${tokenBody.access}` },
      })

      if (!profileResponse.ok) {
        throw new Error(
          await getErrorMessage(profileResponse, 'No se pudo cargar el perfil del usuario.'),
        )
      }

      const profileBody: unknown = await profileResponse.json()
      if (!isUserProfile(profileBody)) {
        throw new Error('El servidor devolvió un perfil con formato inválido.')
      }

      const dashboardBody = profileBody.rol === 'Profesor Jefe'
        ? null
        : await fetchDashboard(tokenBody.access)
      setAccessToken(tokenBody.access)
      setProfile(profileBody)
      setDashboard(dashboardBody)
      setActiveSection(profileBody.rol === 'Profesor Jefe' ? 'teacher-cases' : 'dashboard')
      setContrasena('')
    } catch (requestError) {
      setError(
        requestError instanceof TypeError
          ? 'No fue posible conectar con el servidor. Verifica que Django esté ejecutándose.'
          : requestError instanceof Error
            ? requestError.message
            : 'Ocurrió un error al iniciar sesión.',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  function handleLogout() {
    setAccessToken(null)
    setProfile(null)
    setDashboard(null)
    setDashboardError('')
    setCaseHistory(null)
    setCaseHistoryError('')
    setCaseFilters(EMPTY_CASE_FILTERS)
    setActiveSection('dashboard')
    setCorreo('')
    setContrasena('')
    setError('')
  }

  async function handleDashboardPage(page: number) {
    if (!accessToken) return

    setIsDashboardLoading(true)
    setDashboardError('')
    try {
      setDashboard(await fetchDashboard(accessToken, page))
    } catch (requestError) {
      setDashboardError(
        requestError instanceof TypeError
          ? 'No fue posible conectar con el servidor.'
          : requestError instanceof Error
            ? requestError.message
            : 'No se pudo actualizar el panel.',
      )
    } finally {
      setIsDashboardLoading(false)
    }
  }

  async function handleCaseHistoryPage(
    page: number,
    filters: CaseHistoryFilters = caseFilters,
  ) {
    if (!accessToken) return

    setIsCaseHistoryLoading(true)
    setCaseHistoryError('')
    try {
      setCaseHistory(await fetchCaseHistory(accessToken, page, filters))
    } catch (requestError) {
      setCaseHistoryError(
        requestError instanceof TypeError
          ? 'No fue posible conectar con el servidor.'
          : requestError instanceof Error
            ? requestError.message
            : 'No se pudo actualizar el historial de casos.',
      )
    } finally {
      setIsCaseHistoryLoading(false)
    }
  }

  function canViewStatistics() {
    return ['Administrador', 'Inspector', 'PConvivencia'].includes(profile?.rol ?? '')
  }

  function canViewNotifications() {
    return ['Administrador', 'Inspector', 'PConvivencia', 'Profesor Jefe'].includes(profile?.rol ?? '')
  }

  function canReviewCases() {
    return ['Administrador', 'Inspector', 'PConvivencia'].includes(profile?.rol ?? '')
  }

  const pendingCasesNavigation = canReviewCases() && (
    <button
      className="button--quiet"
      aria-current={activeSection === 'pending-cases' ? 'page' : undefined}
      onClick={() => setActiveSection('pending-cases')}
      type="button"
    >
      Revisar casos
    </button>
  )

  const administrationNavigation = profile?.rol === 'Administrador' && (
    <>
      <button className="button--quiet" onClick={() => setActiveSection('admin-users')} type="button">
        Usuarios
      </button>
      <button className="button--quiet" onClick={() => setActiveSection('admin-students')} type="button">
        Estudiantes
      </button>
      <button className="button--quiet" onClick={() => setActiveSection('admin-history')} type="button">
        Auditoría
      </button>
    </>
  )

  const documentsNavigation = (
    <button className="button--quiet" onClick={() => setActiveSection('documents')} type="button">
      Documentos
    </button>
  )

  const notificationsNavigation = canViewNotifications() && (
    <button className="button--quiet" onClick={() => setActiveSection('notifications')} type="button">
      Notificaciones
    </button>
  )

  const searchNavigation = profile?.rol !== 'Profesor Jefe' && (
    <button className="button--quiet" onClick={() => setActiveSection('search')} type="button">
      Buscar
    </button>
  )

  const accountNavigation = (
    <>
      <button className="button--quiet" onClick={() => setActiveSection('profile')} type="button">
        Mi perfil
      </button>
      <button className="button--quiet" onClick={() => setActiveSection('settings')} type="button">
        Configuración
      </button>
      {notificationsNavigation}
      {searchNavigation}
      {documentsNavigation}
    </>
  )

  if (profile && accessToken && profile.rol === 'Profesor Jefe') {
    const accountSection = activeSection === 'profile' || activeSection === 'settings'
    return (
      <main className="dashboard-page">
        <header className="dashboard-topbar">
          <div className="dashboard-brand">
            <img src="/Insignia.png" alt="" width="42" height="42" />
            <div>
              <span className="dashboard-brand__name">ConviData</span>
              <span className="dashboard-brand__caption">Registro de convivencia escolar</span>
            </div>
          </div>
          <nav className="dashboard-navigation" aria-label="Navegación principal">
            <button
              className="button--quiet"
              aria-current={activeSection === 'teacher-cases' ? 'page' : undefined}
              onClick={() => setActiveSection('teacher-cases')}
              type="button"
            >
              Mi curso
            </button>
            <button
              className="button--quiet"
              aria-current={activeSection === 'register' ? 'page' : undefined}
              onClick={() => setActiveSection('register')}
              type="button"
            >
              Registrar caso
            </button>
            <button
              className="button--quiet"
              aria-current={activeSection === 'documents' ? 'page' : undefined}
              onClick={() => setActiveSection('documents')}
              type="button"
            >
              Documentos
            </button>
            <button
              className="button--quiet"
              aria-current={activeSection === 'profile' ? 'page' : undefined}
              onClick={() => setActiveSection('profile')}
              type="button"
            >
              Mi perfil
            </button>
            <button
              className="button--quiet"
              aria-current={activeSection === 'settings' ? 'page' : undefined}
              onClick={() => setActiveSection('settings')}
              type="button"
            >
              Configuración
            </button>
            {notificationsNavigation}
          </nav>
          <div className="dashboard-account">
            <span>{profile.nombre} {profile.apellido_paterno}</span>
            <span className="dashboard-account__role">{profile.rol}</span>
            <button className="button--quiet" onClick={handleLogout} type="button">
              Cerrar sesión
            </button>
          </div>
        </header>
        {activeSection === 'teacher-cases' ? (
          <TeacherCases
            accessToken={accessToken}
            onOpenCase={(caseId) => {
              setSelectedCaseId(caseId)
              setActiveSection('case-detail')
            }}
          />
        ) : activeSection === 'case-detail' && selectedCaseId !== null ? (
          <CaseDetail
            accessToken={accessToken}
            caseId={selectedCaseId}
            onBack={() => setActiveSection('teacher-cases')}
          />
        ) : activeSection === 'documents' ? (
          <Documents accessToken={accessToken} />
        ) : activeSection === 'notifications' ? (
          <Notifications accessToken={accessToken} showFollowUp={false} />
        ) : accountSection ? (
          <AccountSettings
            accessToken={accessToken}
            profile={profile}
            section={activeSection}
            onProfileUpdated={setProfile}
          />
        ) : <CaseRegistration accessToken={accessToken} />}
      </main>
    )
  }

  if (profile && accessToken && dashboard) {
    if (activeSection === 'search') {
      return (
        <main className="dashboard-page">
          <header className="dashboard-topbar">
            <div className="dashboard-brand">
              <img src="/Insignia.png" alt="" width="42" height="42" />
              <div>
                <span className="dashboard-brand__name">ConviData</span>
                <span className="dashboard-brand__caption">Panel de convivencia escolar</span>
              </div>
            </div>
            <nav className="dashboard-navigation" aria-label="Navegación principal">
              <button className="button--quiet" onClick={() => setActiveSection('dashboard')} type="button">Panel</button>
              <button className="button--quiet" onClick={() => setActiveSection('cases')} type="button">Casos</button>
              {pendingCasesNavigation}
              {administrationNavigation}
              {accountNavigation}
              {canViewNotifications() && (
                <button className="button--quiet" onClick={() => setActiveSection('notifications')} type="button">Notificaciones</button>
              )}
              {canViewStatistics() && (
                <button className="button--quiet" onClick={() => setActiveSection('statistics')} type="button">Estadísticas</button>
              )}
            </nav>
            <div className="dashboard-account">
              <span>{profile.nombre} {profile.apellido_paterno}</span>
              <span className="dashboard-account__role">{profile.rol}</span>
              <button className="button--quiet" onClick={handleLogout} type="button">Cerrar sesión</button>
            </div>
          </header>
          <GlobalSearch
            accessToken={accessToken}
            onOpenCase={(caseId) => {
              setSelectedCaseId(caseId)
              setActiveSection('case-detail')
            }}
          />
        </main>
      )
    }

    if (activeSection === 'documents') {
      return (
        <main className="dashboard-page">
          <header className="dashboard-topbar">
            <div className="dashboard-brand">
              <img src="/Insignia.png" alt="" width="42" height="42" />
              <div>
                <span className="dashboard-brand__name">ConviData</span>
                <span className="dashboard-brand__caption">Panel de convivencia escolar</span>
              </div>
            </div>
            <nav className="dashboard-navigation" aria-label="Navegación principal">
              <button className="button--quiet" onClick={() => setActiveSection('dashboard')} type="button">Panel</button>
              <button className="button--quiet" onClick={() => setActiveSection('cases')} type="button">Casos</button>
              {pendingCasesNavigation}
              {administrationNavigation}
              {accountNavigation}
              {canViewNotifications() && (
                <button className="button--quiet" onClick={() => setActiveSection('notifications')} type="button">Notificaciones</button>
              )}
              {canViewStatistics() && (
                <button className="button--quiet" onClick={() => setActiveSection('statistics')} type="button">Estadísticas</button>
              )}
            </nav>
            <div className="dashboard-account">
              <span>{profile.nombre} {profile.apellido_paterno}</span>
              <span className="dashboard-account__role">{profile.rol}</span>
              <button className="button--quiet" onClick={handleLogout} type="button">Cerrar sesión</button>
            </div>
          </header>
          <Documents accessToken={accessToken} />
        </main>
      )
    }

    if (activeSection === 'profile' || activeSection === 'settings') {
      return (
        <main className="dashboard-page">
          <header className="dashboard-topbar">
            <div className="dashboard-brand">
              <img src="/Insignia.png" alt="" width="42" height="42" />
              <div>
                <span className="dashboard-brand__name">ConviData</span>
                <span className="dashboard-brand__caption">Panel de convivencia escolar</span>
              </div>
            </div>
            <nav className="dashboard-navigation" aria-label="Navegación principal">
              <button className="button--quiet" onClick={() => setActiveSection('dashboard')} type="button">Panel</button>
              {administrationNavigation}
              <button className="button--quiet" onClick={() => setActiveSection('profile')} type="button">Mi perfil</button>
              <button className="button--quiet" onClick={() => setActiveSection('settings')} type="button">Configuración</button>
              {searchNavigation}
              {documentsNavigation}
            </nav>
            <div className="dashboard-account">
              <span>{profile.nombre} {profile.apellido_paterno}</span>
              <span className="dashboard-account__role">{profile.rol}</span>
              <button className="button--quiet" onClick={handleLogout} type="button">Cerrar sesión</button>
            </div>
          </header>
          <AccountSettings
            key={activeSection}
            accessToken={accessToken}
            profile={profile}
            section={activeSection}
            onProfileUpdated={setProfile}
          />
        </main>
      )
    }

    if (
      activeSection === 'admin-users' ||
      activeSection === 'admin-students' ||
      activeSection === 'admin-history'
    ) {
      const adminSection = activeSection === 'admin-users'
        ? 'users'
        : activeSection === 'admin-students'
          ? 'students'
          : 'history'
      return (
        <main className="dashboard-page">
          <header className="dashboard-topbar">
            <div className="dashboard-brand">
              <img src="/Insignia.png" alt="" width="42" height="42" />
              <div>
                <span className="dashboard-brand__name">ConviData</span>
                <span className="dashboard-brand__caption">Panel de convivencia escolar</span>
              </div>
            </div>
            <nav className="dashboard-navigation" aria-label="Navegación principal">
              <button className="button--quiet" onClick={() => setActiveSection('dashboard')} type="button">Panel</button>
              <button className="button--quiet" onClick={() => {
                setActiveSection('cases')
                void handleCaseHistoryPage(1)
              }} type="button">Casos</button>
              {pendingCasesNavigation}
              {administrationNavigation}
              {accountNavigation}
              {canViewNotifications() && (
                <button className="button--quiet" onClick={() => setActiveSection('notifications')} type="button">Notificaciones</button>
              )}
              <button className="button--quiet" onClick={() => setActiveSection('register')} type="button">Registrar</button>
              {canViewStatistics() && (
                <button className="button--quiet" onClick={() => setActiveSection('statistics')} type="button">Estadísticas</button>
              )}
            </nav>
            <div className="dashboard-account">
              <span>{profile.nombre} {profile.apellido_paterno}</span>
              <span className="dashboard-account__role">{profile.rol}</span>
              <button className="button--quiet" onClick={handleLogout} type="button">Cerrar sesión</button>
            </div>
          </header>
          <Administration
            key={activeSection}
            accessToken={accessToken}
            section={adminSection}
            onOpenCase={(caseId) => {
              setSelectedCaseId(caseId)
              setActiveSection('case-detail')
            }}
          />
        </main>
      )
    }

    if (activeSection === 'pending-cases') {
      return (
        <main className="dashboard-page">
          <header className="dashboard-topbar">
            <div className="dashboard-brand">
              <img src="/Insignia.png" alt="" width="42" height="42" />
              <div>
                <span className="dashboard-brand__name">ConviData</span>
                <span className="dashboard-brand__caption">Panel de convivencia escolar</span>
              </div>
            </div>
            <nav className="dashboard-navigation" aria-label="Navegación principal">
              <button className="button--quiet" onClick={() => setActiveSection('dashboard')} type="button">
                Panel
              </button>
              <button className="button--quiet" onClick={() => {
                setActiveSection('cases')
                void handleCaseHistoryPage(1)
              }} type="button">
                Casos
              </button>
              {pendingCasesNavigation}
              {administrationNavigation}
              {accountNavigation}
              {canViewNotifications() && (
                <button className="button--quiet" onClick={() => setActiveSection('notifications')} type="button">
                  Notificaciones
                </button>
              )}
              <button className="button--quiet" onClick={() => setActiveSection('register')} type="button">
                Registrar
              </button>
              {canViewStatistics() && (
                <button className="button--quiet" onClick={() => setActiveSection('statistics')} type="button">
                  Estadísticas
                </button>
              )}
            </nav>
            <div className="dashboard-account">
              <span>{profile.nombre} {profile.apellido_paterno}</span>
              <span className="dashboard-account__role">{profile.rol}</span>
              <button className="button--quiet" onClick={handleLogout} type="button">
                Cerrar sesión
              </button>
            </div>
          </header>
          <PendingCases accessToken={accessToken} />
        </main>
      )
    }

    if (activeSection === 'case-detail' && selectedCaseId !== null) {
      return (
        <main className="dashboard-page">
          <header className="dashboard-topbar">
            <div className="dashboard-brand">
              <img src="/Insignia.png" alt="" width="42" height="42" />
              <div>
                <span className="dashboard-brand__name">ConviData</span>
                <span className="dashboard-brand__caption">Panel de convivencia escolar</span>
              </div>
            </div>
            <nav className="dashboard-navigation" aria-label="Navegación principal">
              <button className="button--quiet" onClick={() => setActiveSection('dashboard')} type="button">Panel</button>
              <button className="button--quiet" onClick={() => {
                setActiveSection('cases')
                void handleCaseHistoryPage(1)
              }} type="button">Casos</button>
              {pendingCasesNavigation}
              {administrationNavigation}
              {accountNavigation}
              {canViewNotifications() && (
                <button className="button--quiet" onClick={() => setActiveSection('notifications')} type="button">Notificaciones</button>
              )}
              <button className="button--quiet" onClick={() => setActiveSection('register')} type="button">Registrar</button>
              {canViewStatistics() && (
                <button className="button--quiet" onClick={() => setActiveSection('statistics')} type="button">Estadísticas</button>
              )}
            </nav>
            <div className="dashboard-account">
              <span>{profile.nombre} {profile.apellido_paterno}</span>
              <span className="dashboard-account__role">{profile.rol}</span>
              <button className="button--quiet" onClick={handleLogout} type="button">Cerrar sesión</button>
            </div>
          </header>
          <CaseDetail
            key={selectedCaseId}
            accessToken={accessToken}
            caseId={selectedCaseId}
            onBack={() => {
              setActiveSection('cases')
              void handleCaseHistoryPage(1)
            }}
          />
        </main>
      )
    }

    if (activeSection === 'statistics') {
      return (
        <main className="dashboard-page">
          <header className="dashboard-topbar">
            <div className="dashboard-brand">
              <img src="/Insignia.png" alt="" width="42" height="42" />
              <div>
                <span className="dashboard-brand__name">ConviData</span>
                <span className="dashboard-brand__caption">Panel de convivencia escolar</span>
              </div>
            </div>
            <nav className="dashboard-navigation" aria-label="Navegación principal">
              <button
                className="button--quiet"
                onClick={() => setActiveSection('dashboard')}
                type="button"
              >
                Panel
              </button>
              <button
                className="button--quiet"
                onClick={() => {
                  setActiveSection('cases')
                  void handleCaseHistoryPage(1)
                }}
                type="button"
              >
                Casos
              </button>
              {pendingCasesNavigation}
              {administrationNavigation}
              {accountNavigation}
              {canViewNotifications() && (
                <button
                  className="button--quiet"
                  onClick={() => setActiveSection('notifications')}
                  type="button"
                >
                  Notificaciones
                </button>
              )}
              <button
                className="button--quiet"
                onClick={() => setActiveSection('register')}
                type="button"
              >
                Registrar
              </button>
              <button className="button--quiet" aria-current="page" type="button">
                Estadísticas
              </button>
            </nav>
            <div className="dashboard-account">
              <span>{profile.nombre} {profile.apellido_paterno}</span>
              <span className="dashboard-account__role">{profile.rol}</span>
              <button className="button--quiet" onClick={handleLogout} type="button">
                Cerrar sesión
              </button>
            </div>
          </header>
          <Statistics accessToken={accessToken} />
        </main>
      )
    }

    if (activeSection === 'register') {
      return (
        <main className="dashboard-page">
          <header className="dashboard-topbar">
            <div className="dashboard-brand">
              <img src="/Insignia.png" alt="" width="42" height="42" />
              <div>
                <span className="dashboard-brand__name">ConviData</span>
                <span className="dashboard-brand__caption">Panel de convivencia escolar</span>
              </div>
            </div>
            <nav className="dashboard-navigation" aria-label="Navegación principal">
              <button
                className="button--quiet"
                onClick={() => setActiveSection('dashboard')}
                type="button"
              >
                Panel
              </button>
              <button
                className="button--quiet"
                onClick={() => {
                  setActiveSection('cases')
                  void handleCaseHistoryPage(1)
                }}
                type="button"
              >
                Casos
              </button>
              {pendingCasesNavigation}
              {administrationNavigation}
              {accountNavigation}
              {canViewNotifications() && (
                <button
                  className="button--quiet"
                  onClick={() => setActiveSection('notifications')}
                  type="button"
                >
                  Notificaciones
                </button>
              )}
              <button className="button--quiet" aria-current="page" type="button">
                Registrar
              </button>
            </nav>
            <div className="dashboard-account">
              <span>{profile.nombre} {profile.apellido_paterno}</span>
              <span className="dashboard-account__role">{profile.rol}</span>
              <button className="button--quiet" onClick={handleLogout} type="button">
                Cerrar sesión
              </button>
            </div>
          </header>
          <CaseRegistration accessToken={accessToken} />
        </main>
      )
    }

    if (activeSection === 'notifications') {
      return (
        <main className="dashboard-page">
          <header className="dashboard-topbar">
            <div className="dashboard-brand">
              <img src="/Insignia.png" alt="" width="42" height="42" />
              <div>
                <span className="dashboard-brand__name">ConviData</span>
                <span className="dashboard-brand__caption">Panel de convivencia escolar</span>
              </div>
            </div>
            <nav className="dashboard-navigation" aria-label="Navegación principal">
              <button
                className="button--quiet"
                onClick={() => setActiveSection('dashboard')}
                type="button"
              >
                Panel
              </button>
              <button
                className="button--quiet"
                onClick={() => setActiveSection('cases')}
                type="button"
              >
                Casos
              </button>
              {pendingCasesNavigation}
              {administrationNavigation}
              {accountNavigation}
              <button
                className="button--quiet"
                onClick={() => setActiveSection('register')}
                type="button"
              >
                Registrar
              </button>
              <button className="button--quiet" aria-current="page" type="button">
                Notificaciones
              </button>
              {canViewStatistics() && (
                <button
                  className="button--quiet"
                  onClick={() => setActiveSection('statistics')}
                  type="button"
                >
                  Estadísticas
                </button>
              )}
            </nav>
            <div className="dashboard-account">
              <span>{profile.nombre} {profile.apellido_paterno}</span>
              <span className="dashboard-account__role">{profile.rol}</span>
              <button className="button--quiet" onClick={handleLogout} type="button">
                Cerrar sesión
              </button>
            </div>
          </header>
          <Notifications accessToken={accessToken} />
        </main>
      )
    }

    if (activeSection === 'cases') {
      return (
        <main className="dashboard-page">
          <header className="dashboard-topbar">
            <div className="dashboard-brand">
              <img src="/Insignia.png" alt="" width="42" height="42" />
              <div>
                <span className="dashboard-brand__name">ConviData</span>
                <span className="dashboard-brand__caption">Panel de convivencia escolar</span>
              </div>
            </div>
            <nav className="dashboard-navigation" aria-label="Navegación principal">
              <button
                className="button--quiet"
                onClick={() => setActiveSection('dashboard')}
                type="button"
              >
                Panel
              </button>
              <button className="button--quiet" aria-current="page" type="button">
                Casos
              </button>
              {pendingCasesNavigation}
              {administrationNavigation}
              {accountNavigation}
              {canViewNotifications() && (
                <button
                  className="button--quiet"
                  onClick={() => setActiveSection('notifications')}
                  type="button"
                >
                  Notificaciones
                </button>
              )}
              <button
                className="button--quiet"
                onClick={() => setActiveSection('register')}
                type="button"
              >
                Registrar
              </button>
              {canViewStatistics() && (
                <button
                  className="button--quiet"
                  onClick={() => setActiveSection('statistics')}
                  type="button"
                >
                  Estadísticas
                </button>
              )}
            </nav>
            <div className="dashboard-account">
              <span>{profile.nombre} {profile.apellido_paterno}</span>
              <span className="dashboard-account__role">{profile.rol}</span>
              <button className="button--quiet" onClick={handleLogout} type="button">
                Cerrar sesión
              </button>
            </div>
          </header>

          <div className="dashboard-content">
            <section className="dashboard-welcome">
              <p className="dashboard-eyebrow">Gestión de casos</p>
              <h1>Historial de casos</h1>
              <p>Busca y filtra los casos registrados en el establecimiento.</p>
            </section>

            <section className="dashboard-panel" aria-label="Filtros de casos">
              <form
                className="case-filters"
                onSubmit={(event) => {
                  event.preventDefault()
                  void handleCaseHistoryPage(1)
                }}
              >
                <label>
                  Búsqueda
                  <input
                    onChange={(event) =>
                      setCaseFilters({ ...caseFilters, q: event.target.value })
                    }
                    value={caseFilters.q}
                    type="search"
                  />
                </label>
                <label>
                  Curso
                  <select
                    onChange={(event) =>
                      setCaseFilters({ ...caseFilters, curso: event.target.value })
                    }
                    value={caseFilters.curso}
                  >
                    <option value="">Todos</option>
                    {caseHistory?.cursos.map((curso) => (
                      <option key={curso.id} value={curso.id}>{curso.nombre}</option>
                    ))}
                  </select>
                </label>
                <label>
                  Gravedad
                  <select
                    onChange={(event) =>
                      setCaseFilters({ ...caseFilters, gravedad: event.target.value })
                    }
                    value={caseFilters.gravedad}
                  >
                    <option value="">Todas</option>
                    <option value="Leve">Leve</option>
                    <option value="Grave">Grave</option>
                    <option value="Gravísima">Gravísima</option>
                  </select>
                </label>
                <label>
                  Desde
                  <input
                    onChange={(event) =>
                      setCaseFilters({ ...caseFilters, fecha_desde: event.target.value })
                    }
                    value={caseFilters.fecha_desde}
                    type="date"
                  />
                </label>
                <label>
                  Hasta
                  <input
                    onChange={(event) =>
                      setCaseFilters({ ...caseFilters, fecha_hasta: event.target.value })
                    }
                    value={caseFilters.fecha_hasta}
                    type="date"
                  />
                </label>
                <div className="case-filter-actions">
                  <button className="button--quiet" disabled={isCaseHistoryLoading} type="submit">
                    {isCaseHistoryLoading ? 'Buscando…' : 'Filtrar'}
                  </button>
                  <button
                    className="button--quiet"
                    disabled={isCaseHistoryLoading}
                    onClick={() => {
                      setCaseFilters(EMPTY_CASE_FILTERS)
                      void handleCaseHistoryPage(1, EMPTY_CASE_FILTERS)
                    }}
                    type="button"
                  >
                    Limpiar
                  </button>
                </div>
              </form>
            </section>

            <section className="dashboard-panel" aria-labelledby="case-history-title">
              <div className="dashboard-panel__header">
                <h2 id="case-history-title">Casos registrados</h2>
                {caseHistory?.mostrar_contador && (
                  <span>{caseHistory.total.toLocaleString('es-CL')} registros</span>
                )}
              </div>
              {caseHistoryError && <p className="form-error" role="alert">{caseHistoryError}</p>}
              {!caseHistory && isCaseHistoryLoading && (
                <p className="dashboard-empty" role="status">Cargando casos…</p>
              )}
              {caseHistory && caseHistory.resultados.length > 0 && (
                <div className="dashboard-table-wrap">
                  <table className="dashboard-table">
                    <thead>
                      <tr><th>ID</th><th>Título</th><th>Descripción</th><th>Fecha</th><th>Lugar</th></tr>
                    </thead>
                    <tbody>
                      {caseHistory.resultados.map((caso) => (
                        <tr key={caso.id}>
                          <td>
                            <button
                              className="case-detail__link"
                              onClick={() => {
                                setSelectedCaseId(caso.id)
                                setActiveSection('case-detail')
                              }}
                              type="button"
                            >
                              #{caso.id}
                            </button>
                          </td>
                          <td>
                            <button
                              className="case-detail__link"
                              onClick={() => {
                                setSelectedCaseId(caso.id)
                                setActiveSection('case-detail')
                              }}
                              type="button"
                            >
                              {caso.titulo}
                            </button>
                          </td>
                          <td>{caso.descripcion}</td>
                          <td>
                            {caso.fecha
                              ? new Intl.DateTimeFormat('es-CL', {
                                  dateStyle: 'medium',
                                  timeZone: 'UTC',
                                }).format(new Date(caso.fecha))
                              : 'Sin fecha'}
                          </td>
                          <td>{caso.lugar}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              {caseHistory && caseHistory.resultados.length === 0 && (
                <p className="dashboard-empty">No hay casos que coincidan con los filtros.</p>
              )}
              {caseHistory && (
                <div className="dashboard-pagination">
                  <span>
                    Página {caseHistory.pagina} de {caseHistory.total_paginas}
                    {caseHistory.mostrar_contador && ` · ${caseHistory.total} casos`}
                  </span>
                  <div>
                    <button
                      className="button--quiet"
                      disabled={!caseHistory.tiene_anterior || isCaseHistoryLoading}
                      onClick={() => void handleCaseHistoryPage(caseHistory.pagina - 1)}
                      type="button"
                    >
                      Anterior
                    </button>
                    <button
                      className="button--quiet"
                      disabled={!caseHistory.tiene_siguiente || isCaseHistoryLoading}
                      onClick={() => void handleCaseHistoryPage(caseHistory.pagina + 1)}
                      type="button"
                    >
                      Siguiente
                    </button>
                  </div>
                </div>
              )}
            </section>
          </div>
        </main>
      )
    }

    const metricCards = [
      { label: 'Total de casos', value: dashboard.metricas.total_casos, tone: 'total', note: 'Registros acumulados' },
      { label: 'Faltas leves', value: dashboard.metricas.casos_leves, tone: 'leve', note: 'Clasificación leve' },
      { label: 'Faltas graves', value: dashboard.metricas.casos_graves, tone: 'grave', note: 'Clasificación grave' },
      { label: 'Faltas gravísimas', value: dashboard.metricas.casos_gravisimas, tone: 'gravísima', note: 'Clasificación gravísima' },
    ]
    const maxZoneCount = Math.max(1, ...dashboard.periodo.zonas.map((zone) => zone.total))

    return (
      <main className="dashboard-page">
        <header className="dashboard-topbar">
          <div className="dashboard-brand">
            <img src="/Insignia.png" alt="" width="42" height="42" />
            <div>
              <span className="dashboard-brand__name">ConviData</span>
              <span className="dashboard-brand__caption">Panel de convivencia escolar</span>
            </div>
          </div>
          <nav className="dashboard-navigation" aria-label="Navegación principal">
            <button className="button--quiet" aria-current="page" type="button">
              Panel
            </button>
            <button
              className="button--quiet"
              onClick={() => {
                setActiveSection('cases')
                void handleCaseHistoryPage(1)
              }}
              type="button"
            >
              Casos
            </button>
            {pendingCasesNavigation}
            {administrationNavigation}
            {accountNavigation}
            <button
              className="button--quiet"
              onClick={() => setActiveSection('register')}
              type="button"
            >
              Registrar
            </button>
            {canViewStatistics() && (
              <button
                className="button--quiet"
                onClick={() => setActiveSection('statistics')}
                type="button"
              >
                Estadísticas
              </button>
            )}
            <button
              className="button--quiet"
              onClick={() => setActiveSection('notifications')}
              type="button"
            >
              Notificaciones
            </button>
          </nav>
          <div className="dashboard-account">
            <span>{profile.nombre} {profile.apellido_paterno}</span>
            <span className="dashboard-account__role">{profile.rol}</span>
            <button className="button--quiet" onClick={handleLogout} type="button">
              Cerrar sesión
            </button>
          </div>
        </header>

        <div className="dashboard-content">
          <section className="dashboard-welcome">
            <div>
              <p className="dashboard-eyebrow">ConviData</p>
              <h1>Panel de Convivencia Escolar</h1>
              <p>
                Bienvenido(a), <strong>{profile.nombre} {profile.apellido_paterno}</strong>
                {' '}· Bitácora oficial digitalizada
              </p>
            </div>
          </section>

          <section className="dashboard-metrics" aria-label="Resumen de casos">
            {metricCards.map((card) => (
              <article className={`dashboard-metric dashboard-metric--${card.tone}`} key={card.label}>
                <span className="dashboard-metric__label">{card.label}</span>
                <strong className="dashboard-metric__value">
                  {card.value.toLocaleString('es-CL')}
                </strong>
                <span className="dashboard-metric__note">{card.note}</span>
              </article>
            ))}
          </section>

          <section className="dashboard-panel" aria-labelledby="zones-title">
            <div className="dashboard-panel__header">
              <h2 id="zones-title">Incidentes por Zona del Establecimiento</h2>
              <span>Últimos 30 días</span>
            </div>
            {dashboard.periodo.zonas.length ? (
              <div className="zone-chart">
                {dashboard.periodo.zonas.map((zone) => (
                  <div className="zone-chart__row" key={zone.nombre}>
                    <span className="zone-chart__label">{zone.nombre}</span>
                    <div className="zone-chart__track">
                      <span
                        className="zone-chart__bar"
                        style={{ width: `${(zone.total / maxZoneCount) * 100}%` }}
                      />
                    </div>
                    <strong className="zone-chart__value">{zone.total}</strong>
                  </div>
                ))}
              </div>
            ) : (
              <p className="dashboard-empty">Sin incidentes registrados en los últimos 30 días.</p>
            )}
          </section>

          <section className="dashboard-panel" aria-labelledby="period-title">
            <div className="dashboard-panel__header">
              <h2 id="period-title">Resumen de los últimos 30 días</h2>
              <span>Comparado con los 30 días anteriores</span>
            </div>
            <div className="period-summary-grid">
              <div><span>Total de casos</span><strong>{dashboard.periodo.casos}</strong></div>
              <div><span>Curso con más incidentes</span><strong>{dashboard.periodo.curso_mas_incidentes}</strong></div>
              <div><span>Tipo de falta más frecuente</span><strong>{dashboard.periodo.tipo_falta_frecuente}</strong></div>
              <div><span>Zona con más conflictos</span><strong>{dashboard.periodo.zona_mas_conflictos}</strong></div>
              <div>
                <span>Variación del período</span>
                <strong>{dashboard.periodo.variacion}%</strong>
                <small>Respecto a los 30 días anteriores</small>
              </div>
            </div>
          </section>

          <section className="dashboard-panel" aria-labelledby="cases-title">
            <div className="dashboard-panel__header">
              <h2 id="cases-title">Listado de casos</h2>
              <span>{dashboard.casos.total.toLocaleString('es-CL')} registros</span>
            </div>
            {dashboardError && <p className="form-error" role="alert">{dashboardError}</p>}
            {dashboard.casos.resultados.length ? (
              <div className="dashboard-table-wrap">
                <table className="dashboard-table">
                  <thead>
                    <tr><th>ID</th><th>Caso / Título</th><th>Fecha</th><th>Lugar</th></tr>
                  </thead>
                  <tbody>
                    {dashboard.casos.resultados.map((incident) => (
                      <tr key={incident.id}>
                        <td><span className="case-id">#{incident.id}</span></td>
                        <td>{incident.titulo}</td>
                        <td>
                          {incident.fecha
                            ? new Intl.DateTimeFormat('es-CL', {
                                dateStyle: 'medium',
                                timeZone: 'UTC',
                              }).format(new Date(incident.fecha))
                            : 'Sin fecha'}
                        </td>
                        <td>{incident.lugar}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="dashboard-empty">No existen casos registrados en el sistema actualmente.</p>
            )}
            <div className="dashboard-pagination">
              <span>
                Página {dashboard.casos.pagina} de {dashboard.casos.total_paginas}
                {' '}· {dashboard.casos.total} casos
              </span>
              <div>
                <button
                  className="button--quiet"
                  disabled={!dashboard.casos.tiene_anterior || isDashboardLoading}
                  onClick={() => handleDashboardPage(dashboard.casos.pagina - 1)}
                  type="button"
                >
                  Anterior
                </button>
                <button
                  className="button--quiet"
                  disabled={!dashboard.casos.tiene_siguiente || isDashboardLoading}
                  onClick={() => handleDashboardPage(dashboard.casos.pagina + 1)}
                  type="button"
                >
                  {isDashboardLoading ? 'Cargando…' : 'Siguiente'}
                </button>
              </div>
            </div>
          </section>
        </div>
      </main>
    )
  }

  return (
    <main className="login-shell">
      <section className="panel-brand" aria-label="Presentación institucional">
        <div className="brand-content">
          <div className="logo-wrap">
            <img
              src="/Insignia.png"
              alt="Insignia Colegio San Sebastián"
              width="164"
              height="164"
            />
          </div>
          <p className="brand-school">Colegio San Sebastián</p>
          <h1 className="brand-name">Convi<span>Data</span></h1>
          <div className="brand-sep" />
          <p className="brand-tagline">
            Plataforma institucional de gestión y seguimiento de casos de
            convivencia escolar.
          </p>
          <div className="brand-status">
            <span className="brand-status-dot" />
            Plataforma institucional
          </div>
        </div>
      </section>

      <section className="panel-form" aria-labelledby="login-title">
        <div className="form-container">
          <div className="form-header">
            <p className="form-eyebrow">Acceso al sistema</p>
            <h2 className="form-title" id="login-title">Bienvenido/a</h2>
            <p className="form-sub">
              Ingresa con tu correo institucional para continuar.
            </p>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="field">
              <label htmlFor="correo">Correo institucional</label>
              <div className="input-wrap">
                <svg className="input-icon" aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 8l9 6 9-6M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                <input
                  autoComplete="email"
                  id="correo"
                  name="correo"
                  onChange={(event) => setCorreo(event.target.value)}
                  placeholder="usuario@melipilla.cl"
                  required
                  type="email"
                  value={correo}
                />
              </div>
            </div>

            <div className="field">
              <label htmlFor="contrasena">Contraseña</label>
              <div className="input-wrap">
                <svg className="input-icon" aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="4" y="10" width="16" height="11" rx="2" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8 10V7a4 4 0 018 0v3" />
                </svg>
                <input
                  autoComplete="current-password"
                  id="contrasena"
                  name="contrasena"
                  onChange={(event) => setContrasena(event.target.value)}
                  placeholder="••••••••"
                  required
                  type="password"
                  value={contrasena}
                />
              </div>
            </div>

            {error && <p className="form-error" role="alert">{error}</p>}

            <button className="btn-primary" disabled={isSubmitting} type="submit">
              {isSubmitting ? 'Verificando…' : 'Ingresar'}
            </button>
          </form>

          <div className="link-area">
            <span className="link-switch">¿Olvidó su contraseña?</span>
          </div>

          <div className="security-note">
            <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="4" y="10" width="16" height="11" rx="2" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M8 10V7a4 4 0 018 0v3" />
            </svg>
            Acceso protegido para personal autorizado
          </div>
        </div>

        <p className="form-footer">© 2026 ConviData · Colegio San Sebastián</p>
      </section>
    </main>
  )
}

export default App
