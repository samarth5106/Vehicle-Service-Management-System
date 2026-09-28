'use client'

import { useMemo, useState } from 'react'
import {
  ArrowUpRight,
  Bell,
  CalendarDays,
  CarFront,
  ChevronDown,
  CircleDollarSign,
  ClipboardCheck,
  Gauge,
  LayoutDashboard,
  Menu,
  MoreHorizontal,
  Package,
  Plus,
  Search,
  Settings,
  ShieldCheck,
  Sparkles,
  Users,
  Wrench,
  X,
} from 'lucide-react'

const navItems = [
  { label: 'Overview', icon: LayoutDashboard },
  { label: 'Customers', icon: Users },
  { label: 'Vehicles', icon: CarFront },
  { label: 'Service records', icon: ClipboardCheck },
  { label: 'Mechanics', icon: Wrench },
  { label: 'Parts inventory', icon: Package },
  { label: 'Invoices', icon: CircleDollarSign },
]

const serviceRows = [
  { id: 'SV-2408', vehicle: 'MH 12 RT 4821', customer: 'Aarav Mehta', mechanic: 'Rohan Shah', type: 'Full service', date: 'Today, 10:30 AM', status: 'In progress', amount: '₹4,850' },
  { id: 'SV-2407', vehicle: 'DL 08 CN 1190', customer: 'Ananya Kapoor', mechanic: 'Maya Iyer', type: 'Brake service', date: 'Today, 9:15 AM', status: 'Completed', amount: '₹2,420' },
  { id: 'SV-2406', vehicle: 'KA 05 MQ 7302', customer: 'Vikram Singh', mechanic: 'Dev Patel', type: 'Oil change', date: 'Yesterday, 4:40 PM', status: 'Scheduled', amount: '₹1,180' },
  { id: 'SV-2405', vehicle: 'TN 09 AX 6408', customer: 'Ishita Nair', mechanic: 'Rohan Shah', type: 'AC service', date: 'Yesterday, 2:20 PM', status: 'Completed', amount: '₹3,760' },
]

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    'In progress': 'status-blue',
    Completed: 'status-green',
    Scheduled: 'status-amber',
  }
  return <span className={`status-badge ${styles[status] || ''}`}><span className="status-dot" />{status}</span>
}

export default function VehicleDashboard() {
  const [active, setActive] = useState('Overview')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [showToast, setShowToast] = useState(false)
  const [notice, setNotice] = useState('')
  const [notificationsOpen, setNotificationsOpen] = useState(false)

  const filteredRows = useMemo(() => serviceRows.filter((row) => Object.values(row).join(' ').toLowerCase().includes(query.toLowerCase())), [query])
  const searchResults = useMemo(() => {
    const term = query.trim().toLowerCase()
    if (!term) return { pages: [], records: [] }
    return {
      pages: navItems.filter(({ label }) => label.toLowerCase().includes(term)).map(({ label }) => label),
      records: serviceRows.filter((row) => Object.values(row).join(' ').toLowerCase().includes(term)),
    }
  }, [query])

  function addService() {
    setShowToast(true)
    window.setTimeout(() => setShowToast(false), 3000)
  }

  return (
    <div className="dashboard-shell">
      <aside className={`sidebar ${sidebarOpen ? 'sidebar-open' : ''}`}>
        <div className="brand-row">
          <div className="brand-mark"><Gauge size={22} strokeWidth={2.5} /></div>
          <div><strong>rev<span>up</span></strong><small>service studio</small></div>
          <button className="icon-button sidebar-close" onClick={() => setSidebarOpen(false)} aria-label="Close navigation"><X size={18} /></button>
        </div>
        <div className="sidebar-label">Workspace</div>
        <nav className="nav-list" aria-label="Main navigation">
          {navItems.map(({ label, icon: Icon }) => <button key={label} className={`nav-item ${active === label ? 'active' : ''}`} onClick={() => { setActive(label); setSidebarOpen(false) }}><Icon size={18} /><span>{label}</span>{label === 'Service records' && <span className="nav-count">8</span>}</button>)}
        </nav>
        <div className="sidebar-label sidebar-bottom-label">Manage</div>
        <nav className="nav-list"><button className={`nav-item ${active === 'Reports' ? 'active' : ''}`} onClick={() => { setActive('Reports'); setSidebarOpen(false) }}><ShieldCheck size={18} /><span>Reports</span></button><button className={`nav-item ${active === 'Settings' ? 'active' : ''}`} onClick={() => { setActive('Settings'); setSidebarOpen(false) }}><Settings size={18} /><span>Settings</span></button></nav>
        <div className="sidebar-footer"><div className="footer-icon"><Sparkles size={16} /></div><div><b>Pro workspace</b><small>All systems operational</small></div><span className="online-dot" /></div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <button className="icon-button mobile-menu" onClick={() => setSidebarOpen(true)} aria-label="Open navigation"><Menu size={20} /></button>
          <div className="breadcrumb"><span>Workspace</span><span>/</span><b>{active}</b></div>
          <div className="topbar-actions">
            <label className="search-box"><Search size={17} /><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search anything..." aria-label="Search dashboard" /><kbd>⌘ K</kbd></label>
            <div className="notification-wrap">
              <button className={`notification-button ${notificationsOpen ? 'active' : ''}`} onClick={() => setNotificationsOpen((open) => !open)} aria-label="Notifications" aria-expanded={notificationsOpen}><Bell size={19} /><i /></button>
              {notificationsOpen && <div className="notification-menu page-enter" role="dialog" aria-label="Notifications">
                <div className="notification-menu-heading"><div><b>Notifications</b><small>3 updates for your workspace</small></div><button className="text-button" onClick={() => setNotificationsOpen(false)}>Close <X size={13} /></button></div>
                <button className="notification-item" onClick={() => { setActive('Service records'); setNotificationsOpen(false) }}><span className="notification-dot blue" /><span><b>Service record updated</b><small>SV-2408 is now in progress.</small></span><time>2m</time></button>
                <button className="notification-item" onClick={() => { setActive('Parts inventory'); setNotificationsOpen(false) }}><span className="notification-dot amber" /><span><b>Low stock alert</b><small>Brake pads need replenishing.</small></span><time>18m</time></button>
                <button className="notification-item" onClick={() => { setActive('Invoices'); setNotificationsOpen(false) }}><span className="notification-dot green" /><span><b>Invoice paid</b><small>INV-1082 was settled successfully.</small></span><time>1h</time></button>
              </div>}
            </div>
            <div className="profile"><div className="avatar">CP</div><div className="profile-copy"><b>Chinmay Pande</b><small>Administrator</small></div><ChevronDown size={15} className="muted-icon" /></div>
          </div>
        </header>

        <section className="page-content">
          <div className="page-heading"><div><p className="eyebrow">MONDAY, 28 SEPTEMBER 2026</p><h1>{active === 'Overview' ? <>Good morning, Chinmay <span>✦</span></> : active}</h1><p className="heading-subtitle">{active === 'Overview' ? "Here's what's happening at your workshop today." : `Manage your ${active.toLowerCase()} in one clear workspace.`}</p></div><button className="primary-button" onClick={addService}><Plus size={17} /> New service</button></div>

          {query.trim() && <section className="panel search-results-panel page-enter" aria-live="polite"><div className="panel-heading"><div><h2>Search results</h2><p>Showing matches for “{query}”.</p></div><button className="text-button" onClick={() => setQuery('')}>Clear search <X size={14} /></button></div>{searchResults.pages.length === 0 && searchResults.records.length === 0 ? <p className="empty-state">No customers, vehicles, services, mechanics, parts, invoices, or pages matched your search.</p> : <div className="search-result-list">{searchResults.pages.map((label) => <button key={label} className="search-result" onClick={() => { setActive(label); setQuery('') }}><Search size={16} /><span><b>{label}</b><small>Open workspace page</small></span><ArrowUpRight size={15} /></button>)}{searchResults.records.map((row) => <button key={row.id} className="search-result" onClick={() => { setActive('Service records'); setQuery('') }}><ClipboardCheck size={16} /><span><b>{row.id} · {row.vehicle}</b><small>{row.customer} · {row.type}</small></span><ArrowUpRight size={15} /></button>)}</div>}</section>}

          {active !== 'Overview' && <section className="panel workspace-view page-enter">{active === 'Reports' ? <><div className="panel-heading"><div><h2>Reports & insights</h2><p>Understand workshop performance at a glance.</p></div><button className="primary-button" onClick={() => setNotice('Report export queued')}><ArrowUpRight size={16} /> Export report</button></div><div className="report-grid"><div className="report-card"><span>Monthly revenue</span><strong>₹8.42L</strong><div className="report-bars"><i style={{height:'48%'}} /><i style={{height:'72%'}} /><i style={{height:'58%'}} /><i style={{height:'88%'}} /><i style={{height:'76%'}} /><i style={{height:'100%'}} /></div></div><div className="report-card"><span>Jobs completed</span><strong>186</strong><div className="report-ring"><b>86%</b></div></div><div className="report-card"><span>Customer retention</span><strong>94.6%</strong><p className="report-up">+8.4% this month</p></div></div></> : active === 'Settings' ? <><div className="panel-heading"><div><h2>Workspace settings</h2><p>Make RevUp fit the way your workshop works.</p></div><button className="primary-button" onClick={() => setNotice('Settings saved')}><ShieldCheck size={16} /> Save changes</button></div><div className="settings-list"><label><span><b>Workshop notifications</b><small>Get alerts when jobs change status.</small></span><input type="checkbox" defaultChecked /></label><label><span><b>Daily performance digest</b><small>Receive a summary each morning.</small></span><input type="checkbox" defaultChecked /></label><label><span><b>Compact data tables</b><small>Show more records in less space.</small></span><input type="checkbox" /></label></div></> : <><div className="panel-heading"><div><h2>{active}</h2><p>{active === 'Service records' ? 'Track every job from intake to completion.' : `Your ${active.toLowerCase()} workspace is ready.`}</p></div><button className="primary-button" onClick={addService}><Plus size={16} /> Add {active === 'Parts inventory' ? 'part' : active === 'Invoices' ? 'invoice' : active === 'Customers' ? 'customer' : active === 'Vehicles' ? 'vehicle' : 'record'}</button></div><div className="workspace-cards"><div><strong>{active === 'Customers' ? '1,248' : active === 'Vehicles' ? '486' : active === 'Mechanics' ? '18' : active === 'Parts inventory' ? '324' : active === 'Invoices' ? '₹8.42L' : '32'}</strong><span>Active {active.toLowerCase()}</span></div><div><strong>12.8%</strong><span>Growth this month</span></div><div><strong>Live</strong><span>System status</span></div></div></>}</section>}

          {active === 'Overview' && <><div className="hero-strip"><div className="hero-copy"><div className="hero-pill"><span className="hero-pulse" /> WORKSHOP PULSE</div><h2>Keep every ride<br /><em>moving forward.</em></h2><p>Track your team, vehicles and service health from one calm, clear workspace.</p><button className="hero-link" onClick={() => setActive('Service records')}>View service schedule <ArrowUpRight size={15} /></button></div><div className="hero-image"><img src="https://images.unsplash.com/photo-1486006920555-c77dcf18193c?auto=format&fit=crop&w=1200&q=85" alt="Mechanic working on a car in a bright workshop" /><div className="hero-image-overlay" /></div><div className="hero-stat"><span>Today&apos;s completion</span><strong>86%</strong><div className="mini-progress"><i /></div><small>+12.4% vs last week</small></div></div>

          <div className="section-heading"><div><h2>At a glance</h2><p>A live snapshot of your operations.</p></div><button className="date-filter"><CalendarDays size={16} /> This month <ChevronDown size={14} /></button></div>
          <div className="stats-grid">
            <div className="stat-card"><div className="stat-top"><span className="stat-icon blue"><Users size={18} /></span><span className="trend-up">+12.8% <ArrowUpRight size={13} /></span></div><strong>1,248</strong><span>Active customers</span><div className="sparkline blue-line" /></div>
            <div className="stat-card"><div className="stat-top"><span className="stat-icon purple"><CarFront size={18} /></span><span className="trend-up">+8.2% <ArrowUpRight size={13} /></span></div><strong>486</strong><span>Vehicles serviced</span><div className="sparkline purple-line" /></div>
            <div className="stat-card"><div className="stat-top"><span className="stat-icon orange"><Wrench size={18} /></span><span className="trend-up">+4.6% <ArrowUpRight size={13} /></span></div><strong>32</strong><span>Active services</span><div className="sparkline orange-line" /></div>
            <div className="stat-card"><div className="stat-top"><span className="stat-icon green"><CircleDollarSign size={18} /></span><span className="trend-up">+18.4% <ArrowUpRight size={13} /></span></div><strong>₹8.42L</strong><span>Revenue this month</span><div className="sparkline green-line" /></div>
          </div>

          <div className="content-grid"><div className="panel services-panel"><div className="panel-heading"><div><h2>Recent service records</h2><p>Stay on top of what&apos;s in the bay.</p></div><button className="text-button" onClick={() => setActive('Service records')}>View all <ArrowUpRight size={14} /></button></div><div className="table-wrap"><table><thead><tr><th>Service ID</th><th>Vehicle</th><th>Customer</th><th>Service type</th><th>Status</th><th>Amount</th><th /></tr></thead><tbody>{filteredRows.map((row) => <tr key={row.id}><td><b className="id-text">{row.id}</b></td><td><div className="vehicle-cell"><span className="vehicle-mini"><CarFront size={15} /></span><b>{row.vehicle}</b></div></td><td>{row.customer}</td><td>{row.type}</td><td><StatusBadge status={row.status} /></td><td><b>{row.amount}</b></td><td><button className="more-button" aria-label={`More options for ${row.id}`}><MoreHorizontal size={18} /></button></td></tr>)}</tbody></table></div></div><div className="panel schedule-panel"><div className="panel-heading"><div><h2>Today&apos;s schedule</h2><p>4 appointments on deck.</p></div><button className="more-button"><MoreHorizontal size={18} /></button></div><div className="timeline"><div className="timeline-item current"><time>10:30</time><div className="timeline-line"><span /></div><div><b>Full service</b><p>BMW M4 · Aarav Mehta</p></div></div><div className="timeline-item"><time>12:00</time><div className="timeline-line"><span /></div><div><b>Oil &amp; filter change</b><p>Honda City · Neha Rao</p></div></div><div className="timeline-item"><time>14:30</time><div className="timeline-line"><span /></div><div><b>Brake inspection</b><p>Royal Enfield · Kabir Jain</p></div></div><div className="timeline-item"><time>16:00</time><div className="timeline-line"><span /></div><div><b>AC diagnostics</b><p>Skoda Kushaq · Zoya Ali</p></div></div></div><button className="schedule-button" onClick={() => setActive('Service records')}>Open full schedule <ArrowUpRight size={14} /></button></div></div>

</>}
        </section>
      </main>
      {(showToast || notice) && <div className="toast"><span className="toast-check">✓</span><div><b>{notice || 'Ready to add a service'}</b><small>{notice ? 'Your workspace is up to date.' : 'Connect your backend to create records.'}</small></div><button onClick={() => { setShowToast(false); setNotice('') }} aria-label="Dismiss notification"><X size={16} /></button></div>}
    </div>
  )
}
