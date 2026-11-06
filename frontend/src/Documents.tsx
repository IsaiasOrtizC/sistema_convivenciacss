import { useCallback, useEffect, useState, type FormEvent } from 'react'
import './Documents.css'

type Rule = {
  id: number
  titulo: string
  categoria_falta: string
  activador: string
  umbral_casos: number | null
  umbral_anotaciones: number | null
  conducta_condicion: string
  unidad_umbral: string
  cantidad_minima: number | null
  estado_cantidad: string
  accion_requerida: string
  medida_asociada: string
  tipo_medida: string
  duracion_minima_dias: number | null
  duracion_maxima_dias: number | null
  unidad_duracion: string
  condiciones: string
  excepciones: string
  requiere_citacion_apoderado: boolean
  solo_presentacion: boolean
  plazo_dias: number | null
  plazo_desde: string
  responsable_rol: string
  evidencia_textual: string
  referencia_origen: string
  titulo_fuente: string
  version_fuente: string
  seccion_fuente: string
  pagina_impresa: number | null
  pagina_pdf: number | null
  pagina_impresa_hasta: number | null
  pagina_pdf_hasta: number | null
  estado: string
  puede_activarse: boolean
}

type DocumentItem = {
  id: number
  tipo: string
  titulo: string
  archivo_url: string
  fecha_subida: string
  subido_por: string
  estado_procesamiento: string
  error_procesamiento: string
  numero_paginas: number | null
}

type VersionItem = {
  id: number
  documento_id: number
  documento_titulo: string
  numero: number
  estado: string
  creada_en: string
  reglas: Rule[]
  puede_activar: boolean
}

type DocumentsData = {
  documentos: DocumentItem[]
  versiones: VersionItem[]
  puede_administrar: boolean
  limite_pdf_mb: number
  opciones: {
    estados_regla: { valor: string; etiqueta: string }[]
    activadores: { valor: string; etiqueta: string }[]
    tipos_medida: { valor: string; etiqueta: string }[]
    roles_responsables: { valor: string; etiqueta: string }[]
    referencias_plazo: { valor: string; etiqueta: string }[]
  }
}

type RuleForm = {
  titulo: string
  categoria_falta: string
  activador: string
  umbral_casos: string
  umbral_anotaciones: string
  accion_requerida: string
  tipo_medida: string
  estado: string
  plazo_dias: string
  plazo_desde: string
  responsable_rol: string
  requiere_citacion_apoderado: boolean
}

type DocumentsProps = { accessToken: string }

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function isRule(value: unknown): value is Rule {
  return isRecord(value) &&
    typeof value.id === 'number' &&
    typeof value.titulo === 'string' &&
    typeof value.categoria_falta === 'string' &&
    typeof value.activador === 'string' &&
    (typeof value.umbral_casos === 'number' || value.umbral_casos === null) &&
    (typeof value.umbral_anotaciones === 'number' || value.umbral_anotaciones === null) &&
    typeof value.conducta_condicion === 'string' &&
    typeof value.unidad_umbral === 'string' &&
    (typeof value.cantidad_minima === 'number' || value.cantidad_minima === null) &&
    typeof value.estado_cantidad === 'string' &&
    typeof value.accion_requerida === 'string' &&
    typeof value.medida_asociada === 'string' &&
    typeof value.tipo_medida === 'string' &&
    (typeof value.duracion_minima_dias === 'number' || value.duracion_minima_dias === null) &&
    (typeof value.duracion_maxima_dias === 'number' || value.duracion_maxima_dias === null) &&
    typeof value.unidad_duracion === 'string' &&
    typeof value.condiciones === 'string' &&
    typeof value.excepciones === 'string' &&
    typeof value.requiere_citacion_apoderado === 'boolean' &&
    typeof value.solo_presentacion === 'boolean' &&
    (typeof value.plazo_dias === 'number' || value.plazo_dias === null) &&
    typeof value.plazo_desde === 'string' &&
    typeof value.responsable_rol === 'string' &&
    typeof value.evidencia_textual === 'string' &&
    typeof value.referencia_origen === 'string' &&
    typeof value.titulo_fuente === 'string' &&
    typeof value.version_fuente === 'string' &&
    typeof value.seccion_fuente === 'string' &&
    (typeof value.pagina_impresa === 'number' || value.pagina_impresa === null) &&
    (typeof value.pagina_pdf === 'number' || value.pagina_pdf === null) &&
    (typeof value.pagina_impresa_hasta === 'number' || value.pagina_impresa_hasta === null) &&
    (typeof value.pagina_pdf_hasta === 'number' || value.pagina_pdf_hasta === null) &&
    typeof value.estado === 'string' &&
    typeof value.puede_activarse === 'boolean'
}

function isDocumentsData(value: unknown): value is DocumentsData {
  if (
    !isRecord(value) ||
    typeof value.puede_administrar !== 'boolean' ||
    typeof value.limite_pdf_mb !== 'number' ||
    !isRecord(value.opciones)
  ) return false

  const opciones = value.opciones
  return Array.isArray(value.documentos) &&
    value.documentos.every((item: unknown) =>
      isRecord(item) &&
      typeof item.id === 'number' &&
      typeof item.tipo === 'string' &&
      typeof item.titulo === 'string' &&
      typeof item.archivo_url === 'string' &&
      typeof item.fecha_subida === 'string' &&
      typeof item.subido_por === 'string' &&
      typeof item.estado_procesamiento === 'string' &&
      typeof item.error_procesamiento === 'string' &&
      (typeof item.numero_paginas === 'number' || item.numero_paginas === null),
    ) &&
    Array.isArray(value.versiones) &&
    value.versiones.every((item: unknown) =>
      isRecord(item) &&
      typeof item.id === 'number' &&
      typeof item.documento_id === 'number' &&
      typeof item.documento_titulo === 'string' &&
      typeof item.numero === 'number' &&
      typeof item.estado === 'string' &&
      typeof item.creada_en === 'string' &&
      typeof item.puede_activar === 'boolean' &&
      Array.isArray(item.reglas) &&
      item.reglas.every(isRule),
    ) &&
    ['estados_regla', 'activadores', 'tipos_medida', 'roles_responsables', 'referencias_plazo']
      .every((key) => Array.isArray(opciones[key]) &&
        opciones[key].every((item) =>
          isRecord(item) && typeof item.valor === 'string' && typeof item.etiqueta === 'string',
        ))
}

async function getErrorMessage(response: Response, fallback: string) {
  const body: unknown = await response.json().catch(() => null)
  if (isRecord(body) && typeof body.detail === 'string') return body.detail
  return fallback
}

async function fetchDocuments(accessToken: string): Promise<DocumentsData> {
  const response = await fetch(`${API_BASE_URL}/api/v1/documentos/`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  })
  if (!response.ok) throw new Error(await getErrorMessage(response, 'No se pudieron cargar los documentos.'))
  const body: unknown = await response.json()
  if (!isDocumentsData(body)) throw new Error('El servidor devolvió datos de documentos inválidos.')
  return body
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('es-CL', {
    dateStyle: 'medium',
    timeZone: 'UTC',
  }).format(new Date(value))
}

function emptyRuleForm(): RuleForm {
  return {
    titulo: '',
    categoria_falta: '',
    activador: 'manual',
    umbral_casos: '',
    umbral_anotaciones: '',
    accion_requerida: '',
    tipo_medida: 'no_clasificada',
    estado: 'pendiente',
    plazo_dias: '',
    plazo_desde: 'sin_definir',
    responsable_rol: '',
    requiere_citacion_apoderado: false,
  }
}

export default function Documents({ accessToken }: DocumentsProps) {
  const [data, setData] = useState<DocumentsData | null>(null)
  const [tipo, setTipo] = useState('Reglamento')
  const [titulo, setTitulo] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [manualVersion, setManualVersion] = useState<number | null>(null)
  const [manualTitle, setManualTitle] = useState('')
  const [manualEvidence, setManualEvidence] = useState('')
  const [manualPage, setManualPage] = useState('')
  const [editingRule, setEditingRule] = useState<Rule | null>(null)
  const [ruleForm, setRuleForm] = useState<RuleForm>(emptyRuleForm())
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)

  const loadDocuments = useCallback(async () => {
    setData(await fetchDocuments(accessToken))
  }, [accessToken])

  useEffect(() => {
    let active = true
    fetchDocuments(accessToken)
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
              : 'No se pudieron cargar los documentos.',
        )
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [accessToken])

  async function refresh() {
    setError('')
    try {
      await loadDocuments()
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'No se pudieron actualizar los documentos.')
    }
  }

  async function uploadDocument(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!file) {
      setError('Selecciona el PDF que deseas subir.')
      return
    }
    const formData = new FormData()
    formData.append('tipo_documento', tipo)
    formData.append('titulo', titulo)
    formData.append('archivo', file)
    setBusy(true)
    setError('')
    setMessage('')
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/documentos/`, {
        method: 'POST',
        headers: { Authorization: ['Be', 'arer'].join('') + ' ' + accessToken },
        body: formData,
      })
      if (!response.ok) throw new Error(await getErrorMessage(response, 'No se pudo procesar el documento.'))
      const body: unknown = await response.json()
      setMessage(isRecord(body) && typeof body.mensaje === 'string' ? body.mensaje : 'Documento procesado.')
      setFile(null)
      setTitulo('')
      await refresh()
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'No se pudo subir el documento.')
    } finally {
      setBusy(false)
    }
  }

  async function documentAction(document: DocumentItem, action: 'reprocesar' | 'eliminar') {
    if (action === 'eliminar' && !window.confirm(`¿Eliminar «${document.titulo}» y sus versiones?`)) return
    setBusy(true)
    setError('')
    setMessage('')
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/documentos/${document.id}/`, {
        method: action === 'eliminar' ? 'DELETE' : 'POST',
        headers: {
          Authorization: ['Be', 'arer'].join('') + ' ' + accessToken,
          ...(action === 'reprocesar' ? { 'Content-Type': 'application/json' } : {}),
        },
        body: action === 'reprocesar' ? JSON.stringify({ accion: action }) : undefined,
      })
      if (!response.ok) throw new Error(await getErrorMessage(response, 'No se pudo completar la acción.'))
      const body: unknown = await response.json()
      setMessage(isRecord(body) && typeof body.mensaje === 'string' ? body.mensaje : 'La acción fue completada.')
      await refresh()
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'No se pudo completar la acción.')
    } finally {
      setBusy(false)
    }
  }

  async function createManualRule(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (manualVersion === null) return
    setBusy(true)
    setError('')
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/documentos/versiones/${manualVersion}/reglas/`, {
        method: 'POST',
        headers: {
          Authorization: ['Be', 'arer'].join('') + ' ' + accessToken,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          titulo: manualTitle,
          evidencia_textual: manualEvidence,
          pagina: manualPage ? Number(manualPage) : null,
        }),
      })
      if (!response.ok) throw new Error(await getErrorMessage(response, 'No se pudo crear la propuesta.'))
      setManualVersion(null)
      setManualTitle('')
      setManualEvidence('')
      setManualPage('')
      setMessage('Propuesta de regla creada; completa sus campos antes de aprobarla.')
      await refresh()
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'No se pudo crear la propuesta.')
    } finally {
      setBusy(false)
    }
  }

  function startReview(rule: Rule) {
    setEditingRule(rule)
    setRuleForm({
      titulo: rule.titulo,
      categoria_falta: rule.categoria_falta,
      activador: rule.activador,
      umbral_casos: rule.umbral_casos === null ? '' : String(rule.umbral_casos),
      umbral_anotaciones: rule.umbral_anotaciones === null ? '' : String(rule.umbral_anotaciones),
      accion_requerida: rule.accion_requerida,
      tipo_medida: rule.tipo_medida,
      estado: rule.estado,
      plazo_dias: rule.plazo_dias === null ? '' : String(rule.plazo_dias),
      plazo_desde: rule.plazo_desde,
      responsable_rol: rule.responsable_rol,
      requiere_citacion_apoderado: rule.requiere_citacion_apoderado,
    })
  }

  async function reviewRule(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!editingRule) return
    setBusy(true)
    setError('')
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/documentos/reglas/${editingRule.id}/`, {
        method: 'PATCH',
        headers: {
          Authorization: ['Be', 'arer'].join('') + ' ' + accessToken,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(ruleForm),
      })
      if (!response.ok) throw new Error(await getErrorMessage(response, 'No se pudo guardar la revisión.'))
      setEditingRule(null)
      setMessage('La revisión de la regla quedó registrada.')
      await refresh()
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'No se pudo guardar la revisión.')
    } finally {
      setBusy(false)
    }
  }

  async function activateVersion(version: VersionItem) {
    if (!window.confirm(`¿Activar la versión ${version.numero} del reglamento?`)) return
    setBusy(true)
    setError('')
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/documentos/versiones/${version.id}/activar/`, {
        method: 'POST',
        headers: { Authorization: ['Be', 'arer'].join('') + ' ' + accessToken },
      })
      if (!response.ok) throw new Error(await getErrorMessage(response, 'No se pudo activar la versión.'))
      setMessage('La versión aprobada ahora está vigente.')
      await refresh()
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'No se pudo activar la versión.')
    } finally {
      setBusy(false)
    }
  }

  if (loading) {
    return <div className="dashboard-content"><p role="status">Cargando documentos…</p></div>
  }

  return (
    <div className="dashboard-content documents">
      <section className="dashboard-welcome">
        <p className="dashboard-eyebrow">Convivencia escolar</p>
        <h1>Documentos institucionales</h1>
        <p>Reglamentos, protocolos y propuestas de disposiciones para revisión.</p>
      </section>
      {error && <p className="form-error" role="alert">{error}</p>}
      {message && <p className="documents__success" role="status">{message}</p>}

      {data?.puede_administrar && (
        <form className="dashboard-panel documents__upload" onSubmit={(event) => void uploadDocument(event)}>
          <h2>Subir documento</h2>
          <div className="documents__form-grid">
            <label>Categoría<select value={tipo} onChange={(event) => setTipo(event.target.value)}><option value="Reglamento">Reglamento Interno</option><option value="Protocolo">Protocolo de Convivencia</option></select></label>
            <label>Título<input maxLength={150} value={titulo} onChange={(event) => setTitulo(event.target.value)} /></label>
            <label>Archivo PDF (máx. {data.limite_pdf_mb} MB)<input accept="application/pdf,.pdf" required type="file" onChange={(event) => setFile(event.target.files?.[0] ?? null)} /></label>
          </div>
          <button className="documents__primary" disabled={busy || !file} type="submit">{busy ? 'Procesando…' : 'Subir y procesar'}</button>
        </form>
      )}

      <section className="dashboard-panel">
        <div className="dashboard-panel__header"><h2>Reglamentos y protocolos</h2><span>{data?.documentos.length ?? 0} documentos</span></div>
        {data?.documentos.length ? (
          <div className="dashboard-table-wrap"><table className="dashboard-table">
            <thead><tr><th>Documento</th><th>Categoría</th><th>Procesamiento</th><th>Subido</th><th>Acciones</th></tr></thead>
            <tbody>{data.documentos.map((document) => <tr key={document.id}>
              <td><a href={document.archivo_url} target="_blank" rel="noopener noreferrer">{document.titulo}</a>{document.error_procesamiento && <small className="documents__error">{document.error_procesamiento}</small>}</td>
              <td>{document.tipo}</td>
              <td>{document.estado_procesamiento}{document.numero_paginas && <small>{document.numero_paginas} páginas</small>}</td>
              <td>{formatDate(document.fecha_subida)}<small>{document.subido_por}</small></td>
              <td className="documents__actions">
                {data.puede_administrar && document.estado_procesamiento === 'error' && <button className="button--quiet" disabled={busy} onClick={() => void documentAction(document, 'reprocesar')} type="button">Reprocesar</button>}
                {data.puede_administrar && <button className="documents__danger" disabled={busy} onClick={() => void documentAction(document, 'eliminar')} type="button">Eliminar</button>}
              </td>
            </tr>)}</tbody>
          </table></div>
        ) : <p className="dashboard-empty">No hay documentos institucionales cargados.</p>}
      </section>

      {data?.versiones.map((version) => (
        <section className="dashboard-panel documents__version" key={version.id}>
          <div className="dashboard-panel__header">
            <div><h2>{version.documento_titulo} · Versión {version.numero}</h2><p>{version.estado} · Creada {formatDate(version.creada_en)}</p></div>
            <div className="documents__actions">
              {data.puede_administrar && version.estado !== 'vigente' && <button className="button--quiet" onClick={() => {
                setManualVersion(version.id)
                setManualTitle('')
                setManualEvidence('')
                setManualPage('')
              }} type="button">Nueva propuesta</button>}
              {data.puede_administrar && version.puede_activar && version.estado !== 'vigente' && <button className="documents__primary" disabled={busy} onClick={() => void activateVersion(version)} type="button">Activar versión</button>}
            </div>
          </div>
          {manualVersion === version.id && (
            <form className="documents__rule-form" onSubmit={(event) => void createManualRule(event)}>
              <h3>Crear propuesta manual</h3>
              <label>Título<input maxLength={180} value={manualTitle} onChange={(event) => setManualTitle(event.target.value)} /></label>
              <label>Cita exacta del documento<textarea required rows={4} value={manualEvidence} onChange={(event) => setManualEvidence(event.target.value)} /></label>
              <label>Página<input min="1" type="number" value={manualPage} onChange={(event) => setManualPage(event.target.value)} /></label>
              <div className="documents__actions"><button className="documents__primary" disabled={busy} type="submit">Crear propuesta</button><button className="button--quiet" onClick={() => setManualVersion(null)} type="button">Cancelar</button></div>
            </form>
          )}
          {version.reglas.map((rule) => (
            <article className="documents__rule" key={rule.id}>
              <div className="documents__rule-heading">
                <h3>{rule.titulo}</h3>
                <span>{rule.estado}</span>
              </div>
              <p className="documents__evidence">{rule.evidencia_textual}</p>
              <dl className="documents__facts">
                <div><dt>Referencia</dt><dd>{rule.referencia_origen || 'Sin referencia'}</dd></div>
                <div><dt>Tipo de medida</dt><dd>{rule.tipo_medida}</dd></div>
                <div><dt>Categoría</dt><dd>{rule.categoria_falta || 'Sin clasificar'}</dd></div>
                <div><dt>Condición</dt><dd>{rule.conducta_condicion || rule.activador}</dd></div>
                <div><dt>Acción requerida</dt><dd>{rule.accion_requerida || rule.medida_asociada || 'Sin acción configurada'}</dd></div>
                {rule.condiciones && <div><dt>Condiciones</dt><dd>{rule.condiciones}</dd></div>}
                {rule.excepciones && <div><dt>Excepciones</dt><dd>{rule.excepciones}</dd></div>}
                {rule.solo_presentacion && <div><dt>Fuente</dt><dd>{rule.titulo_fuente} · {rule.version_fuente} · {rule.seccion_fuente} · páginas {rule.pagina_impresa ?? '—'} / PDF {rule.pagina_pdf ?? '—'}</dd></div>}
              </dl>
              {data.puede_administrar && version.estado !== 'vigente' && (
                <button className="button--quiet" onClick={() => startReview(rule)} type="button">Revisar propuesta</button>
              )}
              {editingRule?.id === rule.id && (
                <form className="documents__rule-form" onSubmit={(event) => void reviewRule(event)}>
                  <h3>Revisar propuesta</h3>
                  <label>Título<input maxLength={180} value={ruleForm.titulo} onChange={(event) => setRuleForm({ ...ruleForm, titulo: event.target.value })} /></label>
                  <label>Estado<select value={ruleForm.estado} onChange={(event) => setRuleForm({ ...ruleForm, estado: event.target.value })}>{data.opciones.estados_regla.map((option) => <option key={option.valor} value={option.valor}>{option.etiqueta}</option>)}</select></label>
                  <label>Tipo de medida<select value={ruleForm.tipo_medida} onChange={(event) => setRuleForm({ ...ruleForm, tipo_medida: event.target.value })}>{data.opciones.tipos_medida.map((option) => <option key={option.valor} value={option.valor}>{option.etiqueta}</option>)}</select></label>
                  <label>Categoría de falta<input maxLength={100} value={ruleForm.categoria_falta} onChange={(event) => setRuleForm({ ...ruleForm, categoria_falta: event.target.value })} /></label>
                  <label>Activador<select value={ruleForm.activador} onChange={(event) => setRuleForm({ ...ruleForm, activador: event.target.value })}>{data.opciones.activadores.map((option) => <option key={option.valor} value={option.valor}>{option.etiqueta}</option>)}</select></label>
                  <label>Umbral de casos<input min="1" max="10000" type="number" value={ruleForm.umbral_casos} onChange={(event) => setRuleForm({ ...ruleForm, umbral_casos: event.target.value })} /></label>
                  <label>Umbral de anotaciones<input min="1" max="10000" type="number" value={ruleForm.umbral_anotaciones} onChange={(event) => setRuleForm({ ...ruleForm, umbral_anotaciones: event.target.value })} /></label>
                  <label>Acción requerida<textarea rows={3} value={ruleForm.accion_requerida} onChange={(event) => setRuleForm({ ...ruleForm, accion_requerida: event.target.value })} /></label>
                  <label>Responsable<select value={ruleForm.responsable_rol} onChange={(event) => setRuleForm({ ...ruleForm, responsable_rol: event.target.value })}><option value="">Sin asignar</option>{data.opciones.roles_responsables.map((option) => <option key={option.valor} value={option.valor}>{option.etiqueta}</option>)}</select></label>
                  <label>Días de plazo<input min="0" max="3650" type="number" value={ruleForm.plazo_dias} onChange={(event) => setRuleForm({ ...ruleForm, plazo_dias: event.target.value })} /></label>
                  <label>Inicio del plazo<select value={ruleForm.plazo_desde} onChange={(event) => setRuleForm({ ...ruleForm, plazo_desde: event.target.value })}>{data.opciones.referencias_plazo.map((option) => <option key={option.valor} value={option.valor}>{option.etiqueta}</option>)}</select></label>
                  <label className="documents__checkbox"><input checked={ruleForm.requiere_citacion_apoderado} onChange={(event) => setRuleForm({ ...ruleForm, requiere_citacion_apoderado: event.target.checked })} type="checkbox" />Requiere citación de apoderado</label>
                  <div className="documents__actions"><button className="documents__primary" disabled={busy} type="submit">Guardar revisión</button><button className="button--quiet" onClick={() => setEditingRule(null)} type="button">Cancelar</button></div>
                </form>
              )}
            </article>
          ))}
          {!version.reglas.length && <p className="dashboard-empty">Esta versión aún no tiene propuestas de reglas.</p>}
        </section>
      ))}
    </div>
  )
}
