import { StrictMode, Suspense } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Suspense fallback={<div className="app-loading" role="status" aria-live="polite">Cargando sección…</div>}>
      <App />
    </Suspense>
  </StrictMode>,
)
