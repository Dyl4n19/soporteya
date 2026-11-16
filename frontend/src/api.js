const BASE = import.meta.env.VITE_API_URL || '/api'

function cookie(name) {
  return document.cookie.split('; ').find(x => x.startsWith(`${name}=`))?.split('=').slice(1).join('=') || ''
}

export async function api(path, options = {}) {
  const method = options.method || 'GET'
  const headers = { ...(options.body ? { 'Content-Type': 'application/json' } : {}), ...options.headers }
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) headers['X-CSRFToken'] = decodeURIComponent(cookie('csrftoken'))
  const response = await fetch(`${BASE}${path}`, { credentials: 'include', ...options, method, headers })
  if (response.status === 204) return null
  const data = await response.json().catch(() => ({ message: 'Respuesta inválida del servidor' }))
  if (!response.ok) throw Object.assign(new Error(data.message || 'Error'), { status: response.status, field: data.field })
  return data
}

export async function ensureCsrf() { return api('/auth/csrf/') }

