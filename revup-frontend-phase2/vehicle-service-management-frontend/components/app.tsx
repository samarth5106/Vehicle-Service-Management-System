"use client"
import { useCallback, useEffect, useState } from "react"
import { api, ApiError } from "@/lib/api"

type Row = Record<string, any>
type Opt = { value: any; label: string }
type Field = { name: string; label: string; type?: string; required?: boolean; options?: string; editHidden?: boolean }
type Col = [string, string, ("inr" | "badge")?]

const inr = (n: any) => "₹" + Number(n ?? 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })
const NEXT: Record<string, string[]> = { Received: ["Diagnosing"], Diagnosing: ["In Progress", "Waiting for Parts"], "In Progress": ["Waiting for Parts", "Completed"], "Waiting for Parts": ["In Progress"], Completed: ["Delivered"], Delivered: [] }
const PAGES = ["Dashboard", "Customers", "Vehicles", "Service Records", "Mechanics", "Parts Inventory", "Invoices", "Reports"]
const OPTIONS: Record<string, [string, string, string]> = { customers: ["/api/customers", "customer_id", "name"], vehicles: ["/api/vehicles", "vehicle_id", "registration_no"], mechanics: ["/api/mechanics", "mechanic_id", "name"] }

function Cell({ v, kind }: { v: any; kind?: string }) {
  if (kind === "inr") return <>{inr(v)}</>
  if (kind === "badge") return <span className={`badge s-${String(v).split(" ")[0]}`}>{v}</span>
  return <>{v === null || v === undefined || v === "" ? "—" : String(v)}</>
}

function Table({ rows, cols, actions }: { rows: Row[]; cols: Col[]; actions?: (r: Row) => React.ReactNode }) {
  if (!rows.length) return <div className="empty">No records found.</div>
  return <table><thead><tr>{cols.map(c => <th key={c[0]}>{c[1]}</th>)}{actions && <th>Actions</th>}</tr></thead>
    <tbody>{rows.map((r, i) => <tr key={i}>{cols.map(c => <td key={c[0]}><Cell v={r[c[0]]} kind={c[2]} /></td>)}{actions && <td><div className="acts">{actions(r)}</div></td>}</tr>)}</tbody></table>
}

function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  return <div className="back"><div className="modal"><div className="head"><h2>{title}</h2><button className="btn sec sm" onClick={onClose}>Close</button></div>{children}</div></div>
}

function FormModal({ title, fields, row, onClose, onSaved, save }: { title: string; fields: Field[]; row?: Row; onClose: () => void; onSaved: (m: string) => void; save: (data: Row, changed: Row) => Promise<string> }) {
  const [vals, setVals] = useState<Row>(() => Object.fromEntries(fields.map(f => [f.name, row?.[f.name] ?? (f.type === "date" && !row ? new Date().toISOString().slice(0, 10) : "")])))
  const [opts, setOpts] = useState<Record<string, Opt[]>>({})
  const [err, setErr] = useState(""); const [fe, setFe] = useState<Record<string, string>>({}); const [busy, setBusy] = useState(false)
  useEffect(() => { fields.forEach(async f => { if (f.options) { const [p, k, l] = OPTIONS[f.options]; const d = await api<Row[]>(p).catch(() => []); setOpts(o => ({ ...o, [f.name]: d.map(x => ({ value: x[k], label: f.options === "vehicles" ? `${x.registration_no} - ${x.make} ${x.model}` : x[l] })) })) } }) }, [])
  async function submit(e: React.FormEvent) {
    e.preventDefault(); setBusy(true); setErr(""); setFe({})
    const changed = row ? Object.fromEntries(Object.entries(vals).filter(([k, v]) => String(v) !== String(row[k] ?? ""))) : vals
    try { onSaved(await save(vals, changed)) } catch (x) { const a = x as ApiError; setErr(a.message); setFe(a.fields || {}) } finally { setBusy(false) }
  }
  return <Modal title={title} onClose={onClose}><form onSubmit={submit}>
    {err && <div className="msg bad">{err}</div>}
    <div className="grid">{fields.filter(f => !(row && f.editHidden)).map(f => <label key={f.name}>{f.label}{f.required && " *"}
      {f.options ? <select value={vals[f.name]} onChange={e => setVals({ ...vals, [f.name]: e.target.value })}><option value="">Select…</option>{(opts[f.name] || []).map(o => <option key={o.value} value={o.value}>{o.label}</option>)}</select>
        : <input type={f.type || "text"} step={f.type === "number" ? "0.01" : undefined} value={vals[f.name]} onChange={e => setVals({ ...vals, [f.name]: e.target.value })} />}
      {fe[f.name] && <span className="e">{fe[f.name]}</span>}</label>)}</div>
    <div className="foot"><button type="button" className="btn sec" onClick={onClose}>Cancel</button><button className="btn" disabled={busy}>{busy ? "Saving…" : "Save"}</button></div></form></Modal>
}

type Cfg = { title: string; sub: string; path: string; cols: Col[]; fields: Field[]; add: string; idKey: string; filter?: [string, string[]] }
const CFG: Record<string, Cfg> = {
  "Customers": { title: "Customers", sub: "Owners whose vehicles are serviced at the center.", path: "/api/customers", idKey: "customer_id", add: "Register Customer",
    cols: [["customer_id", "ID"], ["name", "Name"], ["phone", "Phone"], ["email", "Email"], ["address", "Address"]],
    fields: [{ name: "name", label: "Name", required: true }, { name: "phone", label: "Phone (10 digits)", required: true }, { name: "email", label: "Email", type: "email" }, { name: "address", label: "Address" }] },
  "Vehicles": { title: "Vehicles", sub: "Every vehicle belongs to a registered customer.", path: "/api/vehicles", idKey: "vehicle_id", add: "Register Vehicle",
    cols: [["registration_no", "Reg. No."], ["make", "Make"], ["model", "Model"], ["manufacturing_year", "Year"], ["customer_name", "Owner"]],
    fields: [{ name: "customer_id", label: "Owner", options: "customers", required: true }, { name: "registration_no", label: "Registration No.", required: true }, { name: "make", label: "Make", required: true }, { name: "model", label: "Model", required: true }, { name: "manufacturing_year", label: "Manufacturing Year", type: "number" }] },
  "Service Records": { title: "Service Records", sub: "Service jobs from vehicle arrival to delivery.", path: "/api/services", idKey: "service_id", add: "New Service Job",
    filter: ["status", ["Received", "Diagnosing", "In Progress", "Waiting for Parts", "Completed", "Delivered"]],
    cols: [["service_id", "Job"], ["service_date", "Date"], ["registration_no", "Vehicle"], ["customer_name", "Customer"], ["service_type", "Service"], ["mechanic_name", "Mechanic"], ["labor_cost", "Labour", "inr"], ["status", "Status", "badge"]],
    fields: [{ name: "vehicle_id", label: "Vehicle", options: "vehicles", required: true, editHidden: true }, { name: "mechanic_id", label: "Mechanic", options: "mechanics", required: true }, { name: "service_date", label: "Date", type: "date", required: true }, { name: "service_type", label: "Service Type", required: true }, { name: "labor_cost", label: "Labour Cost (₹)", type: "number" }, { name: "description", label: "Problem / Description" }] },
  "Mechanics": { title: "Mechanics", sub: "Workshop staff who are assigned to service jobs.", path: "/api/mechanics", idKey: "mechanic_id", add: "Add Mechanic",
    cols: [["mechanic_id", "ID"], ["name", "Name"], ["phone", "Phone"], ["specialization", "Specialization"]],
    fields: [{ name: "name", label: "Name", required: true }, { name: "phone", label: "Phone" }, { name: "specialization", label: "Specialization" }] },
  "Parts Inventory": { title: "Parts Inventory", sub: "Stock reduces automatically when a part is used in a service.", path: "/api/parts", idKey: "part_id", add: "Add Part",
    cols: [["part_name", "Part"], ["quantity_in_stock", "In Stock"], ["unit_price", "Unit Price", "inr"]],
    fields: [{ name: "part_name", label: "Part Name", required: true }, { name: "quantity_in_stock", label: "Quantity in Stock", type: "number", required: true }, { name: "unit_price", label: "Unit Price (₹)", type: "number", required: true }] },
  "Invoices": { title: "Invoices", sub: "Generated from completed jobs. Amounts are calculated, never typed.", path: "/api/invoices", idKey: "invoice_id", add: "", filter: ["payment_status", ["Unpaid", "Paid"]],
    cols: [["invoice_id", "Invoice"], ["invoice_date", "Date"], ["registration_no", "Vehicle"], ["customer_name", "Customer"], ["parts_amount", "Parts", "inr"], ["labor_amount", "Labour", "inr"], ["tax_amount", "GST 18%", "inr"], ["total_amount", "Total", "inr"], ["payment_status", "Payment", "badge"]], fields: [] },
}

function PartsModal({ job, onClose, notify }: { job: Row; onClose: () => void; notify: (m: string, bad?: boolean) => void }) {
  const [used, setUsed] = useState<Row[]>([]); const [parts, setParts] = useState<Row[]>([]); const [pid, setPid] = useState(""); const [qty, setQty] = useState("1"); const [err, setErr] = useState("")
  const locked = !!job.invoice_id || ["Received", "Delivered"].includes(job.status)
  const load = useCallback(async () => { setUsed(await api(`/api/services/${job.service_id}/parts`)); setParts(await api("/api/parts")) }, [job.service_id])
  useEffect(() => { load() }, [load])
  const run = async (fn: () => Promise<any>) => { setErr(""); try { const r = await fn(); notify(r.message); await load() } catch (e) { setErr((e as Error).message) } }
  const total = used.reduce((s, u) => s + u.line_total, 0)
  return <Modal title={`Parts used: Job #${job.service_id} (${job.registration_no})`} onClose={onClose}>
    {err && <div className="msg bad">{err}</div>}
    {locked && <div className="msg bad">{job.invoice_id ? "Invoice generated: parts are locked." : `Parts can't be edited while the job is ${job.status}.`}</div>}
    <Table rows={used} cols={[["part_name", "Part"], ["quantity", "Qty"], ["unit_price", "Unit Price", "inr"], ["line_total", "Total", "inr"]]}
      actions={u => <button className="btn sec sm" disabled={locked} onClick={() => run(() => api(`/api/services/${job.service_id}/parts/${u.part_id}`, { method: "DELETE" }))}>Remove</button>} />
    <p>Parts total: <b>{inr(total)}</b></p>
    {!locked && <div className="tools" style={{ marginTop: 12 }}><select style={{ width: 240 }} value={pid} onChange={e => setPid(e.target.value)}><option value="">Select part…</option>{parts.map(p => <option key={p.part_id} value={p.part_id}>{p.part_name} ({p.quantity_in_stock} in stock, {inr(p.unit_price)})</option>)}</select>
      <input type="number" min="1" style={{ width: 80 }} value={qty} onChange={e => setQty(e.target.value)} />
      <button className="btn" onClick={() => run(() => api(`/api/services/${job.service_id}/parts`, { method: "POST", body: JSON.stringify({ part_id: pid, quantity: qty }) }))}>Add Part</button></div>}
  </Modal>
}

function HistoryModal({ title, url, onClose }: { title: string; url: string; onClose: () => void }) {
  const [rows, setRows] = useState<Row[]>([])
  useEffect(() => { api<Row[]>(url).then(setRows) }, [url])
  return <Modal title={title} onClose={onClose}><Table rows={rows} cols={[["service_date", "Date"], ["registration_no", "Vehicle"], ["service_type", "Service"], ["mechanic_name", "Mechanic"], ["status", "Status", "badge"], ["invoice_id", "Invoice"]]} /></Modal>
}

function Resource({ name, notify }: { name: string; notify: (m: string, bad?: boolean) => void }) {
  const c = CFG[name]; const [rows, setRows] = useState<Row[]>([]); const [q, setQ] = useState(""); const [flt, setFlt] = useState("")
  const [form, setForm] = useState<Row | "new" | null>(null); const [modal, setModal] = useState<React.ReactNode>(null); const [loading, setLoading] = useState(true)
  const load = useCallback(async () => {
    setLoading(true); const p = new URLSearchParams(); if (q) p.set("q", q); if (flt && c.filter) p.set(c.filter[0], flt)
    try { setRows(await api(`${c.path}?${p}`)) } catch (e) { notify((e as Error).message, true) } finally { setLoading(false) }
  }, [c, q, flt, notify])
  useEffect(() => { const t = setTimeout(load, 200); return () => clearTimeout(t) }, [load])
  const act = async (fn: () => Promise<any>) => { try { notify((await fn()).message); load() } catch (e) { notify((e as Error).message, true) } }
  const put = (url: string, body: Row) => api(url, { method: "PUT", body: JSON.stringify(body) })
  const actions = (r: Row) => <>
    {c.fields.length > 0 && <button className="btn sec sm" onClick={() => setForm(r)}>Edit</button>}
    {name === "Customers" && <button className="btn sec sm" onClick={() => setModal(<HistoryModal title={`Service history: ${r.name}`} url={`/api/customers/${r.customer_id}/history`} onClose={() => setModal(null)} />)}>History</button>}
    {name === "Vehicles" && <button className="btn sec sm" onClick={() => setModal(<HistoryModal title={`Service history: ${r.registration_no}`} url={`/api/vehicles/${r.vehicle_id}/history`} onClose={() => setModal(null)} />)}>History</button>}
    {name === "Service Records" && <>
      {NEXT[r.status].map(s => <button key={s} className="btn sm" onClick={() => act(() => put(`/api/services/${r.service_id}`, { status: s }))}>→ {s}</button>)}
      {!["Received", "Delivered"].includes(r.status) && <button className="btn sec sm" onClick={() => setModal(<PartsModal job={r} notify={notify} onClose={() => { setModal(null); load() }} />)}>Parts</button>}
      {r.status === "Completed" && !r.invoice_id && <button className="btn sm" onClick={() => act(() => api("/api/invoices", { method: "POST", body: JSON.stringify({ service_id: r.service_id }) }))}>Generate Invoice</button>}</>}
    {name === "Invoices" && <button className="btn sm" onClick={() => act(() => put(`/api/invoices/${r.invoice_id}/payment`, { payment_status: r.payment_status === "Paid" ? "Unpaid" : "Paid" }))}>Mark {r.payment_status === "Paid" ? "Unpaid" : "Paid"}</button>}</>
  return <>
    <div className="head"><div><h1>{c.title}</h1><p>{c.sub}</p></div><div className="tools">
      <input placeholder="Search…" value={q} onChange={e => setQ(e.target.value)} />
      {c.filter && <select value={flt} onChange={e => setFlt(e.target.value)}><option value="">All</option>{c.filter[1].map(s => <option key={s}>{s}</option>)}</select>}
      {c.add && <button className="btn" onClick={() => setForm("new")}>+ {c.add}</button>}</div></div>
    <div className="panel">{loading && !rows.length ? <div className="empty">Loading…</div> : <Table rows={rows} cols={c.cols} actions={actions} />}</div>
    {form && <FormModal title={form === "new" ? c.add : `Edit ${c.title.replace(/s$/, "")}`} fields={c.fields} row={form === "new" ? undefined : form} onClose={() => setForm(null)}
      save={async (all, changed) => { const r = form === "new" ? await api(c.path, { method: "POST", body: JSON.stringify(all) }) : await put(`${c.path}/${form[c.idKey]}`, changed); return r.message }}
      onSaved={m => { setForm(null); notify(m); load() }} />}
    {modal}</>
}

function Dashboard({ go }: { go: (p: string) => void }) {
  const [d, setD] = useState<Row | null>(null); const [err, setErr] = useState("")
  useEffect(() => { api("/api/dashboard").then(setD).catch(e => setErr(e.message)) }, [])
  if (err) return <div className="msg bad">{err}</div>
  if (!d) return <div className="empty">Loading…</div>
  const cards: [string, any, string][] = [["Customers", d.customers, "Customers"], ["Vehicles", d.vehicles, "Vehicles"], ["Vehicles Under Service", d.vehicles_under_service, "Service Records"], ["Pending Jobs", d.pending_jobs, "Service Records"], ["Completed Services", d.completed_services, "Service Records"], ["Mechanics", d.mechanics, "Mechanics"], ["Low-Stock Parts", d.low_stock_parts, "Parts Inventory"], ["Unpaid Invoices", d.unpaid_invoices, "Invoices"], ["Revenue (Paid)", inr(d.revenue), "Invoices"], ["Outstanding", inr(d.outstanding), "Invoices"]]
  return <><div className="head"><div><h1>Dashboard</h1><p>Manage customers, vehicles, service jobs, parts and invoices.</p></div></div>
    <div className="flow">Customer → Vehicle → Service Job → Mechanic → Parts → Invoice → Payment → Service History</div>
    <div className="cards">{cards.map(([l, v, p]) => <button key={l} className="card" onClick={() => go(p)}><strong>{v}</strong><span>{l}</span></button>)}</div>
    <div className="panel"><h2 style={{ marginBottom: 8 }}>Recent Service Jobs</h2><Table rows={d.recent_services} cols={[["service_id", "Job"], ["service_date", "Date"], ["registration_no", "Vehicle"], ["customer_name", "Customer"], ["service_type", "Service"], ["mechanic_name", "Mechanic"], ["status", "Status", "badge"]]} /></div></>
}

const REPORTS: [string, string, Col[]][] = [
  ["services-by-status", "Services by Status", [["status", "Status", "badge"], ["jobs", "Jobs"]]],
  ["mechanic-workload", "Mechanic Workload", [["name", "Mechanic"], ["specialization", "Specialization"], ["active_jobs", "Active Jobs"], ["total_jobs", "Total Jobs"]]],
  ["parts-usage", "Parts Inventory & Usage", [["part_name", "Part"], ["quantity_in_stock", "In Stock"], ["total_used", "Total Used"]]],
  ["low-stock", "Low-Stock Parts", [["part_name", "Part"], ["quantity_in_stock", "In Stock"]]],
  ["revenue-by-date", "Revenue by Date (Paid)", [["payment_date", "Date"], ["invoices", "Invoices"], ["revenue", "Revenue", "inr"]]],
  ["payment-summary", "Paid vs Unpaid Invoices", [["payment_status", "Payment", "badge"], ["invoices", "Invoices"], ["amount", "Amount", "inr"]]],
]

function Reports() {
  const [data, setData] = useState<Record<string, Row[]>>({})
  useEffect(() => { REPORTS.forEach(([k]) => api<Row[]>(`/api/reports/${k}`).then(r => setData(d => ({ ...d, [k]: r })))) }, [])
  return <><div className="head"><div><h1>Reports</h1><p>Vehicle and customer service history are on the Vehicles and Customers pages (History button).</p></div></div>
    <div className="two">{REPORTS.map(([k, t, cols]) => <div className="panel" key={k}><h2 style={{ marginBottom: 8 }}>{t}</h2><Table rows={data[k] || []} cols={cols} /></div>)}</div></>
}

export default function App() {
  const [page, setPage] = useState("Dashboard"); const [msg, setMsg] = useState<{ t: string; bad: boolean } | null>(null)
  const notify = useCallback((t: string, bad = false) => { setMsg({ t, bad }); setTimeout(() => setMsg(null), 4000) }, [])
  return <div className="shell"><aside className="side"><div className="brand"><img src="/icon.svg" alt="RevUp" /><div><b>RevUp</b><small>Vehicle Service Management</small></div></div>
    <nav className="nav">{PAGES.map(p => <button key={p} className={page === p ? "on" : ""} onClick={() => setPage(p)}>{p}</button>)}</nav></aside>
    <main className="main">{msg && <div className={`msg ${msg.bad ? "bad" : "ok"}`}>{msg.t}</div>}
      {page === "Dashboard" ? <Dashboard key={page} go={setPage} /> : page === "Reports" ? <Reports /> : <Resource key={page} name={page} notify={notify} />}</main></div>
}
