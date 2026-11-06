import { useState, type FormEvent } from 'react'
import './AccountSettings.css'

type AccountProfile = {
  id: number
  nombre: string
  apellido_paterno: string
  apellido_materno: string
  correo: string
  rol: string
}

type AccountSettingsProps = {
  accessToken: string
  profile: AccountProfile
  section: 'profile' | 'settings'
  onProfileUpdated: (profile: AccountProfile) => void
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

async function getErrorMessage(response: Response, fallback: string) {
  const body: unknown = await response.json().catch(() => null)
  if (isRecord(body) && typeof body.detail === 'string') return body.detail
  return fallback
}

export default function AccountSettings({
  accessToken,
  profile,
  section,
  onProfileUpdated,
}: AccountSettingsProps) {
  const [nombre, setNombre] = useState(profile.nombre)
  const [apellidoPaterno, setApellidoPaterno] = useState(profile.apellido_paterno)
  const [apellidoMaterno, setApellidoMaterno] = useState(profile.apellido_materno)
  const [correo, setCorreo] = useState(profile.correo)
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [saving, setSaving] = useState(false)

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setMessage('')
    setSaving(true)
    try {
      if (section === 'profile') {
        const response = await fetch(`${API_BASE_URL}/api/v1/me/`, {
          method: 'PATCH',
          headers: {
            Authorization: ['Be', 'arer'].join('') + ' ' + accessToken,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            nombre,
            apellido_paterno: apellidoPaterno,
            apellido_materno: apellidoMaterno,
            correo,
          }),
        })
        if (!response.ok) throw new Error(await getErrorMessage(response, 'No se pudo actualizar el perfil.'))
        const body: unknown = await response.json()
        if (!isRecord(body) ||
          typeof body.id !== 'number' ||
          typeof body.nombre !== 'string' ||
          typeof body.apellido_paterno !== 'string' ||
          typeof body.apellido_materno !== 'string' ||
          typeof body.correo !== 'string' ||
          typeof body.rol !== 'string') {
          throw new Error('El servidor devolvió datos de perfil inválidos.')
        }
        onProfileUpdated({
          id: body.id,
          nombre: body.nombre,
          apellido_paterno: body.apellido_paterno,
          apellido_materno: body.apellido_materno,
          correo: body.correo,
          rol: body.rol,
        })
        setMessage('Tus datos personales se actualizaron correctamente.')
      } else {
        if (newPassword !== confirmPassword) {
          throw new Error('La confirmación no coincide con la nueva contraseña.')
        }
        const response = await fetch(`${API_BASE_URL}/api/v1/me/`, {
          method: 'PUT',
          headers: {
            Authorization: ['Be', 'arer'].join('') + ' ' + accessToken,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            contrasena_actual: currentPassword,
            contrasena_nueva: newPassword,
          }),
        })
        if (!response.ok) throw new Error(await getErrorMessage(response, 'No se pudo cambiar la contraseña.'))
        setCurrentPassword('')
        setNewPassword('')
        setConfirmPassword('')
        setMessage('La contraseña se cambió correctamente.')
      }
    } catch (requestError) {
      setError(
        requestError instanceof TypeError
          ? 'No fue posible conectar con el servidor.'
          : requestError instanceof Error
            ? requestError.message
            : 'No se pudo guardar la configuración.',
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="dashboard-content account-settings">
      <section className="dashboard-welcome">
        <p className="dashboard-eyebrow">Mi cuenta</p>
        <h1>{section === 'profile' ? 'Datos personales' : 'Configuración de seguridad'}</h1>
        <p>{profile.nombre} {profile.apellido_paterno} · {profile.rol}</p>
      </section>
      {error && <p className="form-error" role="alert">{error}</p>}
      {message && <p className="account-settings__success" role="status">{message}</p>}
      <form className="dashboard-panel account-settings__form" onSubmit={(event) => void submit(event)}>
        {section === 'profile' ? (
          <>
            <label>Nombres<input required value={nombre} onChange={(event) => setNombre(event.target.value)} /></label>
            <label>Apellido paterno<input required value={apellidoPaterno} onChange={(event) => setApellidoPaterno(event.target.value)} /></label>
            <label>Apellido materno<input required value={apellidoMaterno} onChange={(event) => setApellidoMaterno(event.target.value)} /></label>
            <label>Correo institucional<input required type="email" value={correo} onChange={(event) => setCorreo(event.target.value)} /></label>
          </>
        ) : (
          <>
            <label>Contraseña actual<input autoComplete="current-password" minLength={1} required type="password" value={currentPassword} onChange={(event) => setCurrentPassword(event.target.value)} /></label>
            <label>Nueva contraseña<input autoComplete="new-password" minLength={12} required type="password" value={newPassword} onChange={(event) => setNewPassword(event.target.value)} /></label>
            <label>Confirmar nueva contraseña<input autoComplete="new-password" minLength={12} required type="password" value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} /></label>
            <p className="account-settings__hint">Usa al menos 12 caracteres. Tu contraseña no se almacena en el navegador.</p>
          </>
        )}
        <button className="account-settings__submit" disabled={saving} type="submit">
          {saving ? 'Guardando…' : section === 'profile' ? 'Guardar perfil' : 'Cambiar contraseña'}
        </button>
      </form>
    </div>
  )
}
