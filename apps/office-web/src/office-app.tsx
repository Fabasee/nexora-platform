import { useCallback, useEffect, useMemo, useState } from "react";
import {
  getAuth,
  onAuthStateChanged,
  signInWithEmailAndPassword,
  signOut,
  type User,
} from "firebase/auth";
import { initializeApp, getApps } from "firebase/app";

type EntryType = "application" | "module" | "platform_service";
type PortfolioEntry = {
  id: string;
  key: string;
  name: string;
  entry_type: EntryType;
  category: string;
  description: string;
  parent: { key: string; name: string; entry_type: EntryType } | null;
  lifecycle_status: string;
  decision_status: "confirmed" | "candidate";
  priority: string;
  delivery_model: string;
  activation_product_key: string | null;
  module_count: number;
  sort_order: number;
  created_at: string;
  updated_at: string;
  modules?: Array<{
    key: string;
    name: string;
    category: string;
    lifecycle_status: string;
    decision_status: string;
    priority: string;
    delivery_model: string;
  }>;
};
type PortfolioPage = { count: number; limit: number; offset: number; results: PortfolioEntry[] };
type AuditEvent = { id: string; entry_key: string; entry_name: string; action: "created" | "updated"; source: "admin" | "manifest"; actor_label: string; changes: Record<string, { before: string | null; after: string | null }>; occurred_at: string };
type AuditPage = { count: number; limit: number; offset: number; results: AuditEvent[] };
type AccessProfile = { user_id: string; roles: string[]; permissions: string[] };
type SecurityEvent = { id: string; user_id: string; event_type: string; occurred_at: string; provider: string; source_ip: string | null; user_agent: string; request_id: string };
type SecurityEventPage = { count: number; limit: number; offset: number; results: SecurityEvent[] };
type Summary = {
  total_entries: number;
  applications: number;
  modules: number;
  platform_services: number;
  by_lifecycle_status: Record<string, number>;
  by_decision_status: Record<string, number>;
  by_priority: Record<string, number>;
};

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY as string | undefined,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN as string | undefined,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID as string | undefined,
  appId: import.meta.env.VITE_FIREBASE_APP_ID as string | undefined,
};
const apiBase = ((import.meta.env.VITE_API_BASE_URL as string | undefined) || "/api/v1").replace(/\/$/, "");
const firebaseReady = Boolean(firebaseConfig.apiKey && firebaseConfig.authDomain && firebaseConfig.projectId && firebaseConfig.appId);
const firebaseApp = firebaseReady
  ? (getApps()[0] ?? initializeApp(firebaseConfig))
  : null;
const auth = firebaseApp ? getAuth(firebaseApp) : null;

async function apiRequest<T>(user: User, path: string): Promise<T> {
  if (!apiBase) throw new Error("VITE_API_BASE_URL belum dikonfigurasi.");
  const token = await user.getIdToken();
  const response = await fetch(`${apiBase}/office/${path}`, {
    headers: { Accept: "application/json", Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    if (response.status === 401) throw new Error("Sesi tidak valid. Silakan masuk kembali.");
    if (response.status === 403) throw new Error("Akses ditolak. Akun harus terverifikasi dan memiliki hak staf Nexora Office.");
    if (response.status === 404) throw new Error("Data portofolio tidak ditemukan.");
    throw new Error(`Permintaan gagal (HTTP ${response.status}).`);
  }
  return response.json() as Promise<T>;
}

const label = (value: string) => value.replaceAll("_", " ").replace(/\b\w/g, (char) => char.toUpperCase());

export function OfficeApp() {
  const [user, setUser] = useState<User | null>(null);
  const [authReady, setAuthReady] = useState(!auth);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loginBusy, setLoginBusy] = useState(false);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [entries, setEntries] = useState<PortfolioEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [auditTotal, setAuditTotal] = useState(0);
  const [accessProfile, setAccessProfile] = useState<AccessProfile | null>(null);
  const [securityEvents, setSecurityEvents] = useState<SecurityEvent[]>([]);
  const [securityEventTotal, setSecurityEventTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [type, setType] = useState("");
  const [lifecycle, setLifecycle] = useState("");
  const [decision, setDecision] = useState("");
  const [selected, setSelected] = useState<PortfolioEntry | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    if (!auth) return;
    return onAuthStateChanged(auth, (nextUser) => {
      setUser(nextUser);
      setAuthReady(true);
      setError(null);
      setSummary(null);
      setEntries([]);
    });
  }, []);

  const loadDashboard = useCallback(async (activeUser: User) => {
    setBusy(true);
    setError(null);
    try {
      const params = new URLSearchParams({ limit: "100", offset: "0" });
      if (search.trim()) params.set("search", search.trim());
      if (type) params.set("entry_type", type);
      if (lifecycle) params.set("lifecycle_status", lifecycle);
      if (decision) params.set("decision_status", decision);
      const profile = await apiRequest<AccessProfile>(activeUser, "access/me/");
      setAccessProfile(profile);
      if (profile.permissions.includes("portfolio.view")) {
        const [nextSummary, page] = await Promise.all([
          apiRequest<Summary>(activeUser, "summary/"),
          apiRequest<PortfolioPage>(activeUser, `portfolio/?${params.toString()}`),
        ]);
        setSummary(nextSummary);
        setEntries(page.results);
        setTotal(page.count);
      } else {
        setSummary(null);
        setEntries([]);
        setTotal(0);
      }
      if (profile.permissions.includes("audit.view")) {
        const audit = await apiRequest<AuditPage>(activeUser, "audit/?limit=20&offset=0");
        setAuditEvents(audit.results);
        setAuditTotal(audit.count);
      } else {
        setAuditEvents([]);
        setAuditTotal(0);
      }
      if (profile.permissions.includes("security.view")) {
        const security = await apiRequest<SecurityEventPage>(activeUser, "access/security-events/?limit=20&offset=0");
        setSecurityEvents(security.results);
        setSecurityEventTotal(security.count);
      } else {
        setSecurityEvents([]);
        setSecurityEventTotal(0);
      }
      setNotice(null);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Dashboard tidak dapat dimuat.");
    } finally {
      setBusy(false);
    }
  }, [search, type, lifecycle, decision]);

  useEffect(() => {
    if (user) void loadDashboard(user);
  }, [user, loadDashboard]);

  const openEntry = useCallback(async (entry: PortfolioEntry) => {
    if (!user) return;
    setSelected(entry);
    try {
      const detail = await apiRequest<PortfolioEntry>(user, `portfolio/${encodeURIComponent(entry.key)}/`);
      setSelected(detail);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Detail gagal dimuat.");
    }
  }, [user]);

  const grouped = useMemo(() => entries.reduce<Record<string, PortfolioEntry[]>>((groups, entry) => {
    const group = entry.parent?.name ?? (entry.entry_type === "platform_service" ? "Platform services" : "Independent applications");
    (groups[group] ??= []).push(entry);
    return groups;
  }, {}), [entries]);

  async function handleLogin(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!auth) return;
    setLoginBusy(true);
    setError(null);
    try {
      const credential = await signInWithEmailAndPassword(auth, email.trim(), password);
      if (!credential.user.emailVerified) {
        await signOut(auth);
        setError("Email belum diverifikasi. Verifikasi email terlebih dahulu, lalu masuk kembali.");
      } else {
        setPassword("");
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Login gagal.");
    } finally {
      setLoginBusy(false);
    }
  }

  if (!authReady) return <div className="boot-screen">Memeriksa sesi Nexora…</div>;

  if (!firebaseReady || !auth) {
    return <div className="boot-screen"><section className="login-card"><div className="brand-lockup"><span className="brand-symbol">N</span><div><b>NEXORA OFFICE</b><small>INTERNAL OPERATIONS</small></div></div><h1>Konfigurasi belum lengkap</h1><p>Isi variabel Firebase Web dan API pada file <code>.env</code> berdasarkan environment deployment. Jangan masukkan service-account key atau secret server ke aplikasi web.</p></section></div>;
  }

  if (!user) {
    return (
      <div className="login-shell">
        <div className="login-aside">
          <div className="brand-lockup"><span className="brand-symbol">N</span><div><b>NEXORA OFFICE</b><small>INTERNAL OPERATIONS</small></div></div>
          <div className="login-message"><span className="eyebrow">NEXORA UNIVERSAL PLATFORM</span><h1>One platform.<br />Clear oversight.</h1><p>Internal workspace untuk mengelola portofolio produk, struktur modul, dan arah pengembangan ekosistem Nexora.</p></div>
          <span className="aside-foot">PRIVATE ACCESS · AUTHORIZED STAFF ONLY</span>
        </div>
        <main className="login-main">
          <form className="login-card" onSubmit={handleLogin}>
            <span className="eyebrow">SECURE SIGN IN</span><h2>Selamat datang</h2><p>Masuk menggunakan akun staf Nexora yang telah diberikan akses.</p>
            {error && <div className="alert error">{error}</div>}
            <label>Email staf<input autoComplete="username" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required /></label>
            <label>Password<input autoComplete="current-password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} required /></label>
            <button className="button primary full" disabled={loginBusy}>{loginBusy ? "Memeriksa…" : "Masuk ke Office"}</button>
            <small className="login-hint">Akun tidak dapat didaftarkan dari halaman ini. Hubungi administrator untuk mendapatkan akses.</small>
          </form>
        </main>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-lockup"><span className="brand-symbol">N</span><div><b>NEXORA OFFICE</b><small>INTERNAL OPERATIONS</small></div></div>
        <div className="nav-caption">WORKSPACE</div>
        <div className="nav-item active"><span>▦</span> Portfolio overview</div>
        <div className="nav-item muted"><span>◈</span> Product architecture <em>Soon</em></div>
        <div className="nav-item muted"><span>⌁</span> Operations <em>Soon</em></div>
        <div className="nav-item muted"><span>◉</span> Security & access <em>Soon</em></div>
        <div className="sidebar-bottom"><div className="user-chip"><span className="user-avatar">{(user.email?.[0] ?? "S").toUpperCase()}</span><div><b>{user.email}</b><small>{accessProfile?.roles.map(label).join(" · ") || "Role not loaded"}</small></div></div><button className="button ghost full" onClick={() => void signOut(auth)}>Keluar</button></div>
      </aside>
      <main className="main-content">
        <header className="topbar"><div><span className="breadcrumb">Workspace / <b>Portfolio overview</b></span><h1>Product portfolio</h1><p>Kelola visibilitas struktur dan status ekosistem Nexora.</p></div><button className="button secondary" onClick={() => void loadDashboard(user)} disabled={busy}>↻ <span>Refresh data</span></button></header>
        {error && <div className="alert error">{error}</div>}
        {notice && <div className="alert">{notice}</div>}
        {summary && <section className="metric-grid">
          <Metric label="Total entries" value={summary.total_entries} detail="Seluruh portofolio terdaftar" icon="▦" />
          <Metric label="Applications" value={summary.applications} detail="Produk dan aplikasi induk" icon="◫" />
          <Metric label="Modules" value={summary.modules} detail="Fitur dalam aplikasi induk" icon="◈" />
          <Metric label="Platform services" value={summary.platform_services} detail="Layanan bersama ekosistem" icon="⌘" />
        </section>}
        {accessProfile?.permissions.includes("portfolio.view") && <section className="panel">
          <div className="panel-heading"><div><h2>Portfolio registry</h2><p>{total} entri sesuai filter · Data dari registry pusat</p></div><span className="readonly-tag">READ ONLY</span></div>
          <div className="filters">
            <input aria-label="Cari portofolio" placeholder="Cari nama, key, deskripsi…" value={search} onChange={(event) => setSearch(event.target.value)} />
            <select aria-label="Jenis entri" value={type} onChange={(event) => setType(event.target.value)}><option value="">Semua jenis</option><option value="application">Application</option><option value="module">Module</option><option value="platform_service">Platform service</option></select>
            <select aria-label="Status pengembangan" value={lifecycle} onChange={(event) => setLifecycle(event.target.value)}><option value="">Semua status</option><option value="in_development">In development</option><option value="planned">Planned</option><option value="research">Research</option><option value="proposed">Proposed</option><option value="live">Live</option><option value="paused">Paused</option></select>
            <select aria-label="Status keputusan" value={decision} onChange={(event) => setDecision(event.target.value)}><option value="">Confirmed + candidate</option><option value="confirmed">Confirmed</option><option value="candidate">Candidate</option></select>
          </div>
          {busy && <div className="loading-line">Memuat data portofolio…</div>}
          {!busy && entries.length === 0 && <div className="empty-state">Tidak ada entri yang cocok dengan filter saat ini.</div>}
          {!busy && Object.entries(grouped).map(([group, items]) => <div className="portfolio-group" key={group}>
            <div className="group-title">{group}<span>{items.length}</span></div>
            <div className="table-wrap"><table><thead><tr><th>PRODUCT / MODULE</th><th>TYPE</th><th>DEVELOPMENT</th><th>DECISION</th><th>PRIORITY</th><th></th></tr></thead><tbody>
              {items.map((entry) => <tr key={entry.key} onClick={() => void openEntry(entry)} tabIndex={0} onKeyDown={(event) => { if (event.key === "Enter") void openEntry(entry); }}>
                <td><div className="entry-name">{entry.name}</div><div className="entry-key">{entry.key}</div></td><td><span className="type-label">{label(entry.entry_type)}</span></td><td><Status value={entry.lifecycle_status} /></td><td><Status value={entry.decision_status} /></td><td><span className="priority-label">{label(entry.priority)}</span></td><td className="arrow-cell">→</td>
              </tr>)}
            </tbody></table></div>
          </div>)}
        </section>}
        {accessProfile?.permissions.includes("audit.view") && <section className="panel audit-panel">
          <div className="panel-heading"><div><h2>Audit &amp; governance</h2><p>{auditTotal} aktivitas tercatat · Menampilkan 20 aktivitas terbaru</p></div><span className="readonly-tag">APPEND ONLY</span></div>
          {auditEvents.length === 0 ? <div className="empty-state">Belum ada aktivitas perubahan portofolio.</div> : <div className="table-wrap"><table><thead><tr><th>TIME</th><th>ENTRY</th><th>EVENT</th><th>SOURCE</th><th>ACTOR</th><th>CHANGES</th></tr></thead><tbody>
            {auditEvents.map((event) => <tr key={event.id}>
              <td>{new Date(event.occurred_at).toLocaleString()}</td>
              <td><div className="entry-name">{event.entry_name}</div><div className="entry-key">{event.entry_key}</div></td>
              <td><Status value={event.action} /></td>
              <td>{label(event.source)}</td>
              <td>{event.actor_label || "System / automation"}</td>
              <td><details className="audit-change-details">
                <summary>{Object.keys(event.changes).length} field(s)</summary>
                <div className="audit-change-list">
                  {Object.entries(event.changes).map(([field, values]) => <div className="audit-change" key={field}>
                    <b>{label(field)}</b>
                    <span className="audit-before">{values.before ?? "—"}</span>
                    <span className="audit-arrow">→</span>
                    <span className="audit-after">{values.after ?? "—"}</span>
                  </div>)}
                </div>
              </details></td>
            </tr>)}
          </tbody></table></div>}
        </section>}
        {accessProfile?.permissions.includes("security.view") && <section className="panel audit-panel">
          <div className="panel-heading"><div><h2>Security activity</h2><p>{securityEventTotal} event tercatat · Menampilkan 20 event terbaru</p></div><span className="readonly-tag">SECURITY</span></div>
          {securityEvents.length === 0 ? <div className="empty-state">Belum ada aktivitas keamanan.</div> : <div className="table-wrap"><table><thead><tr><th>TIME</th><th>ACCOUNT</th><th>EVENT</th><th>PROVIDER</th><th>IP ADDRESS</th><th>REQUEST ID</th></tr></thead><tbody>
            {securityEvents.map((event) => <tr key={event.id}>
              <td>{new Date(event.occurred_at).toLocaleString()}</td>
              <td><span className="entry-key">{event.user_id}</span></td>
              <td><Status value={event.event_type} /></td>
              <td>{event.provider || "—"}</td>
              <td>{event.source_ip || "—"}</td>
              <td><span className="entry-key">{event.request_id || "—"}</span></td>
            </tr>)}
          </tbody></table></div>}
        </section>}
        <footer className="page-footer">NEXORA OFFICE <span>•</span> Internal portfolio workspace <span>•</span> Role-based access</footer>
      </main>
      {selected && <div className="drawer-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) setSelected(null); }}><aside className="detail-drawer"><div className="drawer-head"><span className="eyebrow">PORTFOLIO DETAIL</span><button className="close-button" onClick={() => setSelected(null)} aria-label="Tutup detail">×</button></div><span className="detail-type">{label(selected.entry_type)}</span><h2>{selected.name}</h2><code>{selected.key}</code><p className="detail-description">{selected.description || "Belum ada deskripsi."}</p><div className="detail-grid"><div><small>Development</small><b>{label(selected.lifecycle_status)}</b></div><div><small>Decision</small><b>{label(selected.decision_status)}</b></div><div><small>Priority</small><b>{label(selected.priority)}</b></div><div><small>Delivery model</small><b>{label(selected.delivery_model)}</b></div></div>{selected.parent && <div className="detail-section"><small>PARENT APPLICATION</small><b>{selected.parent.name}</b><code>{selected.parent.key}</code></div>}<div className="detail-section"><small>CHILD MODULES · {selected.modules?.length ?? selected.module_count}</small>{selected.modules?.length ? selected.modules.map((module) => <div className="module-row" key={module.key}><b>{module.name}</b><span>{label(module.lifecycle_status)} · {label(module.decision_status)}</span></div>) : <p className="muted-copy">Tidak ada modul langsung.</p>}</div><div className="detail-section"><small>RUNTIME PRODUCT LINK</small><p className="muted-copy">{selected.activation_product_key ?? "Belum dihubungkan ke runtime product."}</p></div></aside></div>}
    </div>
  );
}

function Metric({ label, value, detail, icon }: { label: string; value: number; detail: string; icon: string }) {
  return <article className="metric-card"><div className="metric-top"><span>{label}</span><i>{icon}</i></div><strong>{value.toString().padStart(2, "0")}</strong><small>{detail}</small></article>;
}

function Status({ value }: { value: string }) {
  return <span className={`status status-${value}`}><i />{label(value)}</span>;
}
