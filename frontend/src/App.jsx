import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { Link, Navigate, Route, Routes, useLocation, useNavigate, useParams } from 'react-router-dom'
import { api, ensureCsrf } from './api'

const AuthContext = createContext(null)
const useAuth = () => useContext(AuthContext)

function AuthProvider({ children }) {
  const [user, setUser] = useState(undefined)
  useEffect(() => { ensureCsrf().then(() => api('/auth/me/')).then(setUser).catch(() => setUser(null)) }, [])
  const value = useMemo(() => ({ user, async login(username, password) { await ensureCsrf(); setUser(await api('/auth/login/', { method: 'POST', body: JSON.stringify({ username, password }) })) }, async logout() { await api('/auth/logout/', { method: 'POST' }); setUser(null) } }), [user])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

function Login() {
  const { user, login } = useAuth(); const nav = useNavigate(); const [form, setForm] = useState({ username: '', password: '' }); const [error, setError] = useState(''); const [loading, setLoading] = useState(false)
  if (user) return <Navigate to="/" />
  async function submit(e) { e.preventDefault(); setLoading(true); setError(''); try { await login(form.username, form.password); nav('/') } catch (e) { setError(e.message) } finally { setLoading(false) } }
  return <main className="login-shell"><section className="login-card"><div className="brand-mark">SY</div><h1>SoporteYa</h1><p>Centro de gestión de soporte TI</p><form onSubmit={submit}><label>Usuario<input required value={form.username} onChange={e => setForm({ ...form, username: e.target.value })} /></label><label>Contraseña<input required type="password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} /></label>{error && <div className="alert error">{error}</div>}<button disabled={loading}>{loading ? 'Ingresando…' : 'Ingresar'}</button></form></section></main>
}

function Protected({ children }) { const { user } = useAuth(); if (user === undefined) return <div className="center">Cargando sesión…</div>; return user ? children : <Navigate to="/login" /> }

function Layout({ children }) {
  const { user, logout } = useAuth(); const loc = useLocation()
  const links = [['/', 'Resumen'], ['/tickets', 'Tickets'], ['/empresas', 'Empresas'], ['/categorias', 'Categorías'], ['/tecnicos', 'Técnicos'], ...(user.role === 'SUPERVISOR' ? [['/reporte', 'Reporte SLA']] : [])]
  return <div className="app-shell"><aside><div className="logo"><span>SY</span><div><strong>SoporteYa</strong><small>Mesa de ayuda TI</small></div></div><nav>{links.map(([to, label]) => <Link key={to} className={loc.pathname === to ? 'active' : ''} to={to}>{label}</Link>)}</nav><div className="profile"><strong>{user.name || user.username}</strong><small>{user.role}</small><button className="ghost" onClick={logout}>Cerrar sesión</button></div></aside><main className="content">{children}</main></div>
}

function Dashboard() {
  const { user } = useAuth()
  const [tickets, setTickets] = useState([]); useEffect(() => { api('/tickets/?page_size=100').then(x => setTickets(x.results || x)).catch(() => {}) }, [])
  const count = state => tickets.filter(t => t.estado === state).length
  return <><header><div><p className="eyebrow">Panel operativo</p><h1>Resumen de soporte</h1><p>Visión rápida de la carga y el estado de atención.</p></div>{user.role === 'SUPERVISOR' && <Link className="button" to="/tickets/nuevo">Nuevo ticket</Link>}</header><section className="stats">{[['Abiertos', count('ABIERTO')], ['En progreso', count('EN_PROGRESO')], ['Resueltos', count('RESUELTO')], ['Total', tickets.length]].map(([x, n]) => <article key={x}><small>{x}</small><strong>{n}</strong></article>)}</section><section className="panel"><h2>Tickets recientes</h2><TicketTable rows={tickets.slice(0, 6)} /></section></>
}

function TicketTable({ rows }) { return <div className="table-wrap"><table><thead><tr><th>ID</th><th>Título</th><th>Empresa</th><th>Prioridad</th><th>Estado</th><th></th></tr></thead><tbody>{rows.map(t => <tr key={t.id_ticket}><td>#{t.id_ticket}</td><td>{t.titulo}</td><td>{t.empresa_nombre}</td><td><span className={`badge ${t.prioridad.toLowerCase()}`}>{t.prioridad}</span></td><td>{t.estado.replace('_', ' ')}</td><td><Link to={`/tickets/${t.id_ticket}`}>Ver</Link></td></tr>)}</tbody></table>{!rows.length && <p className="empty">No hay registros.</p>}</div> }

function Tickets() {
  const { user } = useAuth()
  const [data, setData] = useState({ results: [] })
  const [q, setQ] = useState('')
  const [estado, setEstado] = useState('')
  const [error, setError] = useState('')
  useEffect(() => { api(`/tickets/?search=${encodeURIComponent(q)}&estado=${estado}`).then(setData).catch(e => setError(e.message)) }, [q, estado])
  return <><header><div><p className="eyebrow">Operación principal</p><h1>Tickets</h1></div>{user.role === 'SUPERVISOR' && <Link className="button" to="/tickets/nuevo">Crear ticket</Link>}</header>{error && <div className="alert error">{error}</div>}<div className="filters"><input placeholder="Buscar…" value={q} onChange={e => setQ(e.target.value)} /><select value={estado} onChange={e => setEstado(e.target.value)}><option value="">Todos los estados</option>{['ABIERTO','ASIGNADO','EN_PROGRESO','RESUELTO','CERRADO'].map(x => <option key={x}>{x}</option>)}</select></div><section className="panel"><TicketTable rows={data.results || data} /></section></>
}

function TicketForm() {
  const nav = useNavigate()
  const { id } = useParams()
  const { user } = useAuth()
  const [opts, setOpts] = useState({ empresas: [], categorias: [], tecnicos: [] })
  const [form, setForm] = useState({ empresa_id: '', categoria_id: '', tecnico_id: '', titulo: '', descripcion: '', prioridad: 'MEDIA', comentarios: [''] })
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  useEffect(() => {
    Promise.all([api('/empresas/?page_size=100'), api('/categorias/?page_size=100'), api('/tecnicos/?activo=true&page_size=100')])
      .then(([a, b, c]) => setOpts({ empresas: a.results || a, categorias: b.results || b, tecnicos: c.results || c }))
      .catch(e => setError(e.message))
    if (id) api(`/tickets/${id}/`).then(ticket => {
      if (ticket.estado !== 'ABIERTO') { nav(`/tickets/${id}`, { replace: true }); return }
      setForm({ empresa_id: ticket.empresa_id, categoria_id: ticket.categoria_id, tecnico_id: ticket.tecnico_id || '', titulo: ticket.titulo, descripcion: ticket.descripcion, prioridad: ticket.prioridad, comentarios: [''] })
    }).catch(e => setError(e.message))
  }, [id, nav])
  if (user.role !== 'SUPERVISOR') return <Navigate to="/tickets" />
  async function save(e) {
    e.preventDefault(); setSaving(true); setError('')
    try {
      const body = { ...form, empresa_id: +form.empresa_id, categoria_id: +form.categoria_id, tecnico_id: form.tecnico_id ? +form.tecnico_id : null, comentarios: form.comentarios.filter(x => x.trim()).map(texto => ({ texto })) }
      const ticket = await api(id ? `/tickets/${id}/` : '/tickets/', { method: id ? 'PUT' : 'POST', body: JSON.stringify(body) })
      nav(`/tickets/${ticket.id_ticket}`)
    } catch (e) { setError(e.message) } finally { setSaving(false) }
  }
  return <><header><div><p className="eyebrow">{id ? 'Edición y asignación' : 'Nueva solicitud'}</p><h1>{id ? `Editar ticket #${id}` : 'Crear ticket'}</h1></div></header><section className="panel form-panel"><form onSubmit={save}><div className="grid two"><Select label="Empresa" items={opts.empresas} valueKey="id_empresa" labelKey="razon_social" value={form.empresa_id} onChange={v => setForm({ ...form, empresa_id: v })} /><Select label="Categoría" items={opts.categorias} valueKey="id_categoria" labelKey="nombre" value={form.categoria_id} onChange={v => setForm({ ...form, categoria_id: v })} /><Select label="Técnico (opcional)" items={opts.tecnicos} valueKey="id_tecnico" labelKey="nombre" value={form.tecnico_id} required={false} onChange={v => setForm({ ...form, tecnico_id: v })} /><label>Prioridad<select value={form.prioridad} onChange={e => setForm({ ...form, prioridad: e.target.value })}>{['BAJA','MEDIA','ALTA','CRITICA'].map(x => <option key={x}>{x}</option>)}</select></label></div><label>Título<input minLength="5" maxLength="150" required value={form.titulo} onChange={e => setForm({ ...form, titulo: e.target.value })} /></label><label>Descripción<textarea minLength="10" required rows="5" value={form.descripcion} onChange={e => setForm({ ...form, descripcion: e.target.value })} /></label><h2>{id ? 'Agregar comentarios' : 'Comentarios iniciales'}</h2>{form.comentarios.map((text, index) => <label key={index}>Comentario {index + 1}<textarea minLength="2" maxLength="4000" value={text} onChange={e => setForm({ ...form, comentarios: form.comentarios.map((value, i) => i === index ? e.target.value : value) })} /></label>)}<button className="secondary" type="button" onClick={() => setForm({ ...form, comentarios: [...form.comentarios, ''] })}>Agregar otro comentario</button>{error && <div className="alert error">{error}</div>}<div className="actions"><Link className="button secondary" to={id ? `/tickets/${id}` : '/tickets'}>Cancelar</Link><button disabled={saving}>{saving ? 'Guardando…' : 'Guardar ticket'}</button></div></form></section></>
}

function Select({label,items,valueKey,labelKey,value,onChange,required=true}) { return <label>{label}<select required={required} value={value} onChange={e=>onChange(e.target.value)}><option value="">Seleccione…</option>{items.map(x=><option key={x[valueKey]} value={x[valueKey]}>{x[labelKey]}</option>)}</select></label> }

function TicketDetail() {
  const { id } = useParams()
  const { user } = useAuth()
  const nav = useNavigate()
  const [t, setT] = useState(null)
  const [text, setText] = useState('')
  const [editing, setEditing] = useState(null)
  const [editText, setEditText] = useState('')
  const [error, setError] = useState('')
  const load = () => api(`/tickets/${id}/`).then(setT).catch(e => setError(e.message))
  useEffect(() => { load() }, [id])
  async function mutate(path, method, body) {
    setError('')
    try { await api(`/tickets/${id}/${path}`, { method, ...(body ? { body: JSON.stringify(body) } : {}) }); await load(); return true }
    catch (e) { setError(e.message); return false }
  }
  async function comment(e) { e.preventDefault(); if (await mutate('comentarios/', 'POST', { texto: text })) setText('') }
  async function saveComment(e) { e.preventDefault(); if (await mutate(`comentarios/${editing}/`, 'PUT', { texto: editText })) setEditing(null) }
  async function removeTicket() {
    if (!confirm('¿Eliminar este ticket abierto y sus comentarios?')) return
    try { await api(`/tickets/${id}/`, { method: 'DELETE' }); nav('/tickets') } catch (e) { setError(e.message) }
  }
  if (!t) return <div className="center">{error || 'Cargando…'}</div>
  const supervisor = user.role === 'SUPERVISOR'
  const next = { ABIERTO: ['ASIGNADO'], ASIGNADO: ['EN_PROGRESO'], EN_PROGRESO: ['RESUELTO'], RESUELTO: ['CERRADO','EN_PROGRESO'], CERRADO: [] }[t.estado]
  return <><header><div><p className="eyebrow">Ticket #{t.id_ticket}</p><h1>{t.titulo}</h1><p>{t.empresa_nombre} · {t.categoria_nombre}</p></div><span className={`badge ${t.prioridad.toLowerCase()}`}>{t.prioridad}</span></header>{error && <div className="alert error">{error}</div>}<div className="detail-grid"><section className="panel"><h2>Detalle</h2><p>{t.descripcion}</p><dl><div><dt>Estado</dt><dd>{t.estado}</dd></div><div><dt>Técnico</dt><dd>{t.tecnico_nombre || 'Sin asignar'}</dd></div><div><dt>SLA</dt><dd>{t.horas_sla} horas</dd></div></dl>{supervisor && t.estado === 'ABIERTO' && <div className="actions"><Link className="button secondary" to={`/tickets/${id}/editar`}>Editar / asignar técnico</Link><button className="danger" onClick={removeTicket}>Eliminar ticket</button></div>}<div className="actions">{next.filter(state => state !== 'ASIGNADO' || t.tecnico_id).map(state => <button key={state} onClick={() => mutate('estado/', 'POST', { estado: state })}>Pasar a {state.replaceAll('_', ' ')}</button>)}</div></section><section className="panel"><h2>Comentarios</h2><div className="timeline">{t.comentarios.map(c => <article key={c.numero}><strong>{c.autor}</strong><small>{new Date(c.fecha).toLocaleString()}</small>{editing === c.numero ? <form onSubmit={saveComment}><textarea minLength="2" maxLength="4000" required value={editText} onChange={e => setEditText(e.target.value)} /><div className="actions"><button>Guardar comentario</button><button className="secondary" type="button" onClick={() => setEditing(null)}>Cancelar</button></div></form> : <p>{c.texto}</p>}{supervisor && t.estado !== 'CERRADO' && editing !== c.numero && <div className="actions"><button className="link" onClick={() => { setEditing(c.numero); setEditText(c.texto) }}>Editar</button><button className="link danger" onClick={() => { if (confirm('¿Eliminar este comentario?')) mutate(`comentarios/${c.numero}/`, 'DELETE') }}>Eliminar</button></div>}</article>)}</div>{t.estado !== 'CERRADO' && <form onSubmit={comment}><textarea minLength="2" maxLength="4000" required value={text} onChange={e => setText(e.target.value)} placeholder="Agregar comentario…" /><button>Comentar</button></form>}</section></div></>
}

const masterConfig={empresas:{title:'Empresas',fields:[['rut','RUT'],['razon_social','Razón social'],['plan','Plan'],['activo','Activo']],defaults:{rut:'',razon_social:'',plan:'BASICO',activo:true}},categorias:{title:'Categorías',fields:[['nombre','Nombre'],['horas_sla','Horas SLA'],['activo','Activo']],defaults:{nombre:'',horas_sla:8,activo:true}},tecnicos:{title:'Técnicos',fields:[['rut','RUT'],['nombre','Nombre'],['email','Correo'],['activo','Activo']],defaults:{rut:'',nombre:'',email:'',activo:true}}}
function Masters({type}) { const cfg=masterConfig[type]; const {user}=useAuth(); const [rows,setRows]=useState([]); const [form,setForm]=useState(cfg.defaults); const [editing,setEditing]=useState(null); const [error,setError]=useState(''); const load=()=>api(`/${type}/?page_size=100`).then(x=>setRows(x.results||x)); useEffect(()=>{setForm(cfg.defaults);setEditing(null);load()},[type]); async function save(e){e.preventDefault();try{const path=editing?`/${type}/${editing}/`:`/${type}/`;await api(path,{method:editing?'PUT':'POST',body:JSON.stringify(form)});setForm(cfg.defaults);setEditing(null);load()}catch(e){setError(e.message)}} function edit(r){const id=r[`id_${type==='categorias'?'categoria':type==='empresas'?'empresa':'tecnico'}`];setEditing(id);setForm(Object.fromEntries(cfg.fields.map(([f])=>[f,r[f]])))} async function del(r){const id=r[`id_${type==='categorias'?'categoria':type==='empresas'?'empresa':'tecnico'}`];if(confirm('¿Eliminar este registro?')){try{await api(`/${type}/${id}/`,{method:'DELETE'});load()}catch(e){setError(e.message)}}} return <><header><div><p className="eyebrow">Mantenedor</p><h1>{cfg.title}</h1></div></header>{error&&<div className="alert error">{error}</div>}<div className="master-grid"><section className="panel"><table><thead><tr>{cfg.fields.map(([,l])=><th>{l}</th>)}{user.role==='SUPERVISOR'&&<th/>}</tr></thead><tbody>{rows.map((r,i)=><tr key={i}>{cfg.fields.map(([f])=><td>{typeof r[f]==='boolean'?(r[f]?'Sí':'No'):r[f]}</td>)}{user.role==='SUPERVISOR'&&<td><button className="link" onClick={()=>edit(r)}>Editar</button> <button className="link danger" onClick={()=>del(r)}>Eliminar</button></td>}</tr>)}</tbody></table></section>{user.role==='SUPERVISOR'&&<section className="panel form-panel"><h2>{editing?'Editar':'Nuevo registro'}</h2><form onSubmit={save}>{cfg.fields.map(([f,l])=>f==='activo'?<label className="check"><input type="checkbox" checked={form[f]} onChange={e=>setForm({...form,[f]:e.target.checked})}/>{l}</label>:f==='plan'?<label>{l}<select value={form[f]} onChange={e=>setForm({...form,[f]:e.target.value})}><option>BASICO</option><option>PREMIUM</option></select></label>:<label>{l}<input required type={f==='horas_sla'?'number':f==='email'?'email':'text'} value={form[f]} onChange={e=>setForm({...form,[f]:f==='horas_sla'?+e.target.value:e.target.value})}/></label>)}<button>{editing?'Guardar cambios':'Crear'}</button></form></section>}</div></> }

function Report() { const [data,setData]=useState(null); useEffect(()=>{api('/reportes/soporte/').then(setData)},[]); if(!data)return <div className="center">Calculando reporte…</div>; return <><header><div><p className="eyebrow">Indicadores SLA</p><h1>Reporte operativo</h1></div></header><div className="detail-grid"><section className="panel"><h2>Tickets vencidos</h2><TicketTable rows={data.tickets_vencidos.map(x=>({...x,empresa_nombre:x.empresa,prioridad:'ALTA'}))}/></section><section className="panel"><h2>Promedio de resolución</h2>{data.promedio_resolucion_por_tecnico.map(x=><div className="metric-row"><span>{x.tecnico}</span><strong>{x.horas_promedio} h</strong></div>)}</section></div></> }

function AppRoutes(){return <Routes><Route path="/login" element={<Login/>}/><Route path="*" element={<Protected><Layout><Routes><Route path="/" element={<Dashboard/>}/><Route path="/tickets" element={<Tickets/>}/><Route path="/tickets/nuevo" element={<TicketForm/>}/><Route path="/tickets/:id/editar" element={<TicketForm/>}/><Route path="/tickets/:id" element={<TicketDetail/>}/><Route path="/empresas" element={<Masters type="empresas"/>}/><Route path="/categorias" element={<Masters type="categorias"/>}/><Route path="/tecnicos" element={<Masters type="tecnicos"/>}/><Route path="/reporte" element={<Report/>}/></Routes></Layout></Protected>}/></Routes>}
export default function App(){return <AuthProvider><AppRoutes/></AuthProvider>}

