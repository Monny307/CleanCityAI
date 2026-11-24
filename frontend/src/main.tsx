import { StrictMode, useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Link, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import axios from "axios";
import * as L from "leaflet";
import "leaflet/dist/leaflet.css";

import "./styles.css";

const api = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000" });
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("cleancity_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

type User = { id: number; email: string; full_name: string; role: "admin" | "citizen" };
type Report = { id: number; category: string; description: string; latitude: number; longitude: number; status: string; severity: string; is_demo: boolean; image_url: string | null; created_at: string };

function Layout({ children }: { children: React.ReactNode }) {
  const user = JSON.parse(localStorage.getItem("cleancity_user") ?? "null") as User | null;
  const navigate = useNavigate();
  const logout = () => { localStorage.clear(); navigate("/"); };
  return <div className="app-shell">
    <header className="topbar">
      <Link to="/" className="brand"><span className="brand-mark">C</span> CleanCity <strong>AI</strong></Link>
      <nav>{user ? <>
        {user.role === "admin" ? <><Link to="/admin">Operations</Link><Link to="/admin/reports">Manage</Link><Link to="/admin/intelligence">Insights</Link><Link to="/admin/routes">Routes</Link></> : <Link to="/report">Report waste</Link>}
        <Link to="/reports">My reports</Link><Link to="/sources">Open data</Link>
        <button className="text-button" onClick={logout}>Sign out</button>
      </> : <Link className="nav-cta" to="/login">Sign in</Link>}</nav>
    </header>
    {children}
  </div>;
}

function Landing() {
  return <Layout><main className="shell">
    <section className="hero"><div className="hero-copy"><p className="eyebrow">SMART WASTE MANAGEMENT</p><h1>A cleaner city starts with better intelligence.</h1><p className="lede">Connect citizen reports, open data, and AI-powered operations to keep Phnom Penh moving toward a cleaner future.</p><div className="actions"><Link className="primary" to="/report">Report waste</Link><Link className="secondary" to="/login">Open dashboard</Link></div></div><div className="signal-card"><div className="card-top"><span>City operations</span><span className="live">PILOT</span></div><div className="metric"><strong>AI</strong><span>human-centered<br /><small>city operations</small></span></div><div className="bars"><span/><span/><span/><span/><span/><span/><span/></div><div className="card-foot"><span>Built for Phnom Penh</span><strong>24/7</strong></div></div></section>
    <section className="feature-grid"><Feature icon="◎" title="See the whole picture" text="Turn citizen reports and open geospatial data into a clear operational view."/><Feature icon="⌁" title="Prioritize what matters" text="Focus collection teams on hotspots with transparent, explainable scores."/><Feature icon="↗" title="Move more efficiently" text="Plan optimized collection routes with an honest demonstration mode." /></section>
  </main></Layout>;
}

function Feature({ icon, title, text }: { icon: string; title: string; text: string }) {
  return <article><span className="icon">{icon}</span><h2>{title}</h2><p>{text}</p></article>;
}

function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("admin@cleancity-ai.com");
  const [password, setPassword] = useState("CleanCityDemo2026!");
  const [error, setError] = useState("");
  const useAccount = (accountEmail: string) => { setEmail(accountEmail); setPassword("CleanCityDemo2026!"); setError(""); };
  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError("");
    try {
      const response = await api.post("/api/auth/login", { email, password });
      localStorage.setItem("cleancity_token", response.data.access_token);
      localStorage.setItem("cleancity_user", JSON.stringify(response.data.user));
      navigate(response.data.user.role === "admin" ? "/admin" : "/reports");
    } catch (requestError) {
      if (axios.isAxiosError(requestError) && requestError.response) {
        setError(`Sign in failed (${requestError.response.status}): ${requestError.response.data?.detail ?? "Invalid credentials"}`);
      } else {
        setError("Sign in failed: the API at http://127.0.0.1:8000 is not reachable.");
      }
    }
  };
  return <Layout><main className="centered"><form className="form-card" onSubmit={submit}><p className="eyebrow">WELCOME BACK</p><h1>Sign in</h1><p className="muted">Choose a development account or enter your own credentials.</p><div className="demo-accounts"><button type="button" onClick={() => useAccount("citizen@cleancity-ai.com")}><strong>Citizen demo</strong><small>citizen@cleancity-ai.com</small></button><button type="button" onClick={() => useAccount("admin@cleancity-ai.com")}><strong>Administrator demo</strong><small>admin@cleancity-ai.com</small></button></div><label>Email<input value={email} onChange={(event) => setEmail(event.target.value)} type="email" required /></label><label>Password<input value={password} onChange={(event) => setPassword(event.target.value)} type="password" required /></label>{error && <p className="error">{error}</p>}<button className="primary" type="submit">Continue</button></form></main></Layout>;
}

function ReportForm() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ category: "household", description: "", latitude: "11.5564", longitude: "104.9282", severity: "medium" });
  const [image, setImage] = useState<File | null>(null);
  const [preview, setPreview] = useState("");
  const [message, setMessage] = useState("");
  const [locationStatus, setLocationStatus] = useState("Using the default Phnom Penh preview");
  const [locating, setLocating] = useState(false);
  const mapElement = useRef<HTMLDivElement | null>(null);
  const mapInstance = useRef<L.Map | null>(null);
  const markerInstance = useRef<L.Marker | null>(null);
  const useCurrentLocation = () => {
    if (!navigator.geolocation) {
      setLocationStatus("Geolocation is not supported by this browser");
      return;
    }
    setLocating(true);
    setLocationStatus("Finding your location…");
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const latitude = position.coords.latitude;
        const longitude = position.coords.longitude;
        if (latitude < 11.4 || latitude > 11.7 || longitude < 104.7 || longitude > 105.1) {
          setLocationStatus("You are outside the Phnom Penh pilot area");
          setLocating(false);
          return;
        }
        setForm((current) => ({ ...current, latitude: latitude.toFixed(6), longitude: longitude.toFixed(6) }));
        setLocationStatus("Current location added");
        setLocating(false);
      },
      (error) => {
        setLocationStatus(error.code === 1 ? "Location permission was denied" : "Could not determine your location");
        setLocating(false);
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 },
    );
  };
  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    const body = new FormData();
    body.append("category", form.category);
    body.append("description", form.description);
    body.append("latitude", form.latitude);
    body.append("longitude", form.longitude);
    body.append("severity", form.severity);
    if (image) body.append("image", image);
    try {
      await api.post("/api/reports", body);
      setMessage("Report submitted successfully.");
      setTimeout(() => navigate("/reports"), 900);
    } catch (requestError) {
      setMessage(axios.isAxiosError(requestError) ? `Could not submit: ${requestError.response?.data?.detail ?? "Invalid report"}` : "Could not submit report.");
    }
  };
  const chooseImage = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] ?? null;
    setImage(file);
    setPreview(file ? URL.createObjectURL(file) : "");
  };
  const latitude = Number(form.latitude);
  const longitude = Number(form.longitude);
  useEffect(() => {
    if (!mapElement.current || mapInstance.current) return;
    const map = L.map(mapElement.current).setView([latitude, longitude], 14);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(map);
    const marker = L.marker([latitude, longitude], { draggable: true }).addTo(map);
    const updatePosition = (point: L.LatLng) => {
      if (point.lat < 11.4 || point.lat > 11.7 || point.lng < 104.7 || point.lng > 105.1) {
        setLocationStatus("Selected location is outside the Phnom Penh pilot area");
        return;
      }
      setForm((current) => ({ ...current, latitude: point.lat.toFixed(6), longitude: point.lng.toFixed(6) }));
      setLocationStatus("Marker position adjusted");
    };
    marker.on("dragend", () => updatePosition(marker.getLatLng()));
    map.on("click", (event: L.LeafletMouseEvent) => {
      marker.setLatLng(event.latlng);
      updatePosition(event.latlng);
    });
    mapInstance.current = map;
    markerInstance.current = marker;
    return () => {
      map.remove();
      mapInstance.current = null;
      markerInstance.current = null;
    };
  }, []);
  useEffect(() => {
    if (mapInstance.current && markerInstance.current) {
      markerInstance.current.setLatLng([latitude, longitude]);
      mapInstance.current.setView([latitude, longitude], mapInstance.current.getZoom());
    }
  }, [latitude, longitude]);
  return <Layout><main className="page"><div className="page-heading"><p className="eyebrow">CITIZEN REPORTING</p><h1>Report a waste problem</h1><p className="muted">Help collection teams understand what is happening on the ground.</p></div><form className="form-card wide" onSubmit={submit}><div className="form-grid"><label>Waste category<select value={form.category} onChange={(event) => setForm({ ...form, category: event.target.value })}>{["household", "plastic", "food", "construction", "illegal_dumping", "mixed", "other"].map((item) => <option key={item}>{item}</option>)}</select></label><label>Severity<select value={form.severity} onChange={(event) => setForm({ ...form, severity: event.target.value })}><option>low</option><option>medium</option><option>high</option></select></label></div><label>Description<textarea required minLength={5} value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} placeholder="What did you see?" /></label><label className="upload-label">Waste photograph<input type="file" accept="image/jpeg,image/png,image/webp" onChange={chooseImage}/><span>Choose a JPEG, PNG, or WebP image up to 5 MB</span></label>{preview && <img className="upload-preview" src={preview} alt="Waste report preview"/>}<div className="location-card"><div className="location-heading"><div><p className="eyebrow">REPORT LOCATION</p><strong>{locationStatus}</strong></div><button type="button" className="location-button" onClick={useCurrentLocation} disabled={locating}>{locating ? "Locating…" : "Use my current location"}</button></div><div ref={mapElement} className="osm-preview" /><div className="location-footer"><small>{latitude.toFixed(6)}, {longitude.toFixed(6)}</small><a href={`https://www.openstreetmap.org/?mlat=${latitude}&mlon=${longitude}#map=16/${latitude}/${longitude}`} target="_blank" rel="noreferrer">Open map</a></div></div>{message && <p className={message.startsWith("Could") ? "error" : "success"}>{message}</p>}<button className="primary" type="submit">Submit report</button></form></main></Layout>;
}

function MyReports() {
  const [reports, setReports] = useState<Report[]>([]);
  useEffect(() => { api.get<Report[]>("/api/reports").then((response) => setReports(response.data)).catch(() => setReports([])); }, []);
  return <Layout><main className="page"><div className="page-heading"><p className="eyebrow">YOUR REPORTS</p><h1>Track reports</h1><p className="muted">Follow each report from submission to collection.</p></div><div className="table-card">{reports.length === 0 ? <Empty text="No reports yet. Submit the first one."/> : <table><thead><tr><th>Report</th><th>Category</th><th>Severity</th><th>Status</th><th>Date</th></tr></thead><tbody>{reports.map((report) => <tr key={report.id}><td>#{report.id}</td><td>{report.category}</td><td><span className={`badge ${report.severity}`}>{report.severity}</span></td><td><span className={`badge ${report.status}`}>{report.status.replace("_", " ")}</span></td><td>{new Date(report.created_at).toLocaleDateString()}</td></tr>)}</tbody></table>}</div></main></Layout>;
}

function AdminDashboard() {
  const [summary, setSummary] = useState<Record<string, number> | null>(null);
  const [reports, setReports] = useState<Report[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const load = async () => {
    setRefreshing(true);
    try {
      const [summaryResponse, reportsResponse] = await Promise.all([
        api.get("/api/dashboard/summary"),
        api.get<Report[]>("/api/reports"),
      ]);
      setSummary(summaryResponse.data);
      setReports(reportsResponse.data);
    } finally {
      setRefreshing(false);
    }
  };
  useEffect(() => {
    load();
    const timer = window.setInterval(load, 5000);
    const refreshVisible = () => { if (document.visibilityState === "visible") load(); };
    document.addEventListener("visibilitychange", refreshVisible);
    return () => {
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", refreshVisible);
    };
  }, []);
  const cards = [["total_reports", "Total reports"], ["pending_reports", "Pending reports"], ["critical_hotspots", "Critical hotspots"], ["completed_collections", "Completed"]]; 
  return <Layout><main className="page"><div className="page-heading row"><div><p className="eyebrow">OPERATIONS CENTER</p><h1>Good morning, team.</h1><p className="muted">A live view of Phnom Penh waste operations.</p></div><div className="heading-actions"><button className="secondary" type="button" onClick={load} disabled={refreshing}>{refreshing ? "Refreshing…" : "Refresh"}</button><Link className="primary" to="/report">＋ New report</Link></div></div><div className="kpi-grid">{cards.map(([key, label]) => <div className="kpi" key={key}><span>{label}</span><strong>{summary?.[key] ?? "—"}</strong><small>from connected reports</small></div>)}</div><div className="dashboard-grid"><div className="table-card"><div className="card-title"><h2>Recent reports</h2><Link to="/admin/reports">View all</Link></div>{reports.length === 0 ? <Empty text="Connect the API and seed demo data to populate reports."/> : <table><thead><tr><th>ID</th><th>Category</th><th>Location</th><th>Status</th></tr></thead><tbody>{reports.slice(0, 7).map((report) => <tr key={report.id}><td>#{report.id}</td><td>{report.category}</td><td>{report.latitude.toFixed(3)}, {report.longitude.toFixed(3)}</td><td><span className={`badge ${report.status}`}>{report.status.replace("_", " ")}</span></td></tr>)}</tbody></table>}</div><div className="map-panel"><div className="card-title"><h2>Report map</h2><span className="live">LIVE DATA</span></div><div className="map-grid">{reports.slice(0, 12).map((report) => <span key={report.id} title={report.category} className={report.severity} style={{ left: `${20 + ((report.longitude - 104.88) * 400)}px`, top: `${25 + ((11.6 - report.latitude) * 380)}px` }}>●</span>)}</div><p className="map-caption">Report locations update automatically every five seconds.</p></div></div></main></Layout>;
}

function AdminReports() {
  const [reports, setReports] = useState<Report[]>([]);
  const load = () => api.get<Report[]>("/api/reports").then((response) => setReports(response.data));
  useEffect(() => { load().catch(() => undefined); }, []);
  const update = async (id: number, status: string) => { await api.patch(`/api/reports/${id}/status`, { status }); load(); };
  return <Layout><main className="page"><div className="page-heading"><p className="eyebrow">REPORT MANAGEMENT</p><h1>Review incoming reports</h1><p className="muted">Update lifecycle status so citizens and collection teams stay aligned.</p></div><div className="table-card"><table><thead><tr><th>Report</th><th>Category</th><th>Severity</th><th>Status</th><th>Action</th></tr></thead><tbody>{reports.map((report) => <tr key={report.id}><td>#{report.id}<br/><small>{report.description}</small></td><td>{report.category}</td><td><span className={`badge ${report.severity}`}>{report.severity}</span></td><td><span className={`badge ${report.status}`}>{report.status.replace("_", " ")}</span></td><td><select value={report.status} onChange={(event) => update(report.id, event.target.value)}><option value="pending">Pending</option><option value="under_review">Under review</option><option value="scheduled">Scheduled</option><option value="collected">Collected</option><option value="rejected">Rejected</option></select></td></tr>)}</tbody></table>{reports.length === 0 && <Empty text="No reports available."/>}</div></main></Layout>;
}

function Intelligence() {
  const [hotspots, setHotspots] = useState<{ latitude: number; longitude: number; report_count: number; high_severity_count: number }[]>([]);
  const [priorities, setPriorities] = useState<{ report_id: number; score: number; level: string; reasons: string[] }[]>([]);
  useEffect(() => { Promise.all([api.get("/api/hotspots"), api.get("/api/priorities")]).then(([hotspotResponse, priorityResponse]) => { setHotspots(hotspotResponse.data); setPriorities(priorityResponse.data); }).catch(() => undefined); }, []);
  return <Layout><main className="page"><div className="page-heading"><p className="eyebrow">INTELLIGENCE</p><h1>Hotspots & priorities</h1><p className="muted">DBSCAN clusters and transparent weighted scores from connected reports.</p></div><div className="dashboard-grid"><div className="table-card"><div className="card-title"><h2>Detected hotspots</h2><span className="live">DBSCAN</span></div>{hotspots.length ? <table><thead><tr><th>Location</th><th>Reports</th><th>High severity</th></tr></thead><tbody>{hotspots.map((hotspot, index) => <tr key={index}><td>{hotspot.latitude.toFixed(4)}, {hotspot.longitude.toFixed(4)}</td><td>{hotspot.report_count}</td><td>{hotspot.high_severity_count}</td></tr>)}</tbody></table> : <Empty text="At least two nearby reports are required to confirm a hotspot."/>}</div><div className="table-card"><div className="card-title"><h2>Ranked priorities</h2><span className="live">0–100</span></div>{priorities.length ? <table><thead><tr><th>Report</th><th>Score</th><th>Level</th></tr></thead><tbody>{priorities.slice(0, 8).map((priority) => <tr key={priority.report_id}><td>#{priority.report_id}</td><td><strong>{priority.score}</strong></td><td><span className={`badge ${priority.level}`}>{priority.level}</span></td></tr>)}</tbody></table> : <Empty text="No active locations."/>}</div></div></main></Layout>;
}

function RoutesPage() {
  const [points, setPoints] = useState<{ id: number; name: string; latitude: number; longitude: number; priority_score: number }[]>([]);
  const [selected, setSelected] = useState<number[]>([]);
  const [startPointId, setStartPointId] = useState<number | null>(null);
  const [result, setResult] = useState<{ stop_ids: number[]; optimized_distance_km: number; distance_saved_percent: number; method: string; route_geometry: number[][] | null; road_network_available: boolean; routing_disclaimer: string } | null>(null);
  const routeMapElement = useRef<HTMLDivElement | null>(null);
  const routeMapInstance = useRef<L.Map | null>(null);
  const routeLayers = useRef<L.LayerGroup | null>(null);
  useEffect(() => {
    api.get("/api/routes").then((response) => {
      setPoints(response.data);
      const initial = response.data.slice(0, 4).map((point: { id: number }) => point.id);
      setSelected(initial);
      setStartPointId(initial[0] ?? null);
    });
  }, []);
  useEffect(() => {
    if (!routeMapElement.current || routeMapInstance.current) return;
    const map = L.map(routeMapElement.current).setView([11.5564, 104.9282], 12);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(map);
    routeMapInstance.current = map;
    routeLayers.current = L.layerGroup().addTo(map);
    return () => {
      map.remove();
      routeMapInstance.current = null;
      routeLayers.current = null;
    };
  }, []);
  const optimize = async () => {
    const response = await api.post("/api/routes/optimize", {
      collection_point_ids: selected,
      start_point_id: startPointId,
    });
    setResult(response.data);
  };
  useEffect(() => {
    if (!routeMapInstance.current || !routeLayers.current) return;
    routeLayers.current.clearLayers();
    const selectedPoints = selected
      .map((id) => points.find((point) => point.id === id))
      .filter((point): point is { id: number; name: string; latitude: number; longitude: number; priority_score: number } => Boolean(point));
    const ordered = result
      ? result.stop_ids.map((id) => selectedPoints.find((point) => point.id === id)).filter((point): point is { id: number; name: string; latitude: number; longitude: number; priority_score: number } => Boolean(point))
      : selectedPoints;
    ordered.forEach((point, index) => {
      const marker = L.marker([point.latitude, point.longitude], {
        icon: L.divIcon({
          className: "route-marker",
          html: `<span>${index + 1}</span>`,
          iconSize: [34, 34],
          iconAnchor: [17, 34],
        }),
      }).bindPopup(`<strong>${point.name}</strong><br/>Priority: ${point.priority_score}`);
      routeLayers.current?.addLayer(marker);
    });
    if (ordered.length > 1) {
      const roadGeometry = result?.road_network_available && result.route_geometry
        ? result.route_geometry.map(([longitude, latitude]) => [latitude, longitude])
        : ordered.map((point) => [point.latitude, point.longitude]);
      const line = L.polyline(roadGeometry as L.LatLngExpression[], {
        color: "#16a36a",
        weight: 5,
        opacity: 0.85,
      });
      routeLayers.current?.addLayer(line);
      routeMapInstance.current.fitBounds(line.getBounds(), { padding: [30, 30] });
    }
  }, [points, selected, result]);
  const togglePoint = (pointId: number, checked: boolean) => {
    const nextSelected = checked ? [...selected, pointId] : selected.filter((id) => id !== pointId);
    setSelected(nextSelected);
    if (!nextSelected.includes(startPointId ?? -1)) setStartPointId(nextSelected[0] ?? null);
  };
  return <Layout><main className="page"><div className="page-heading"><p className="eyebrow">COLLECTION ROUTES</p><h1>Plan the collector route</h1><p className="muted">Choose collection points, select where the run begins, and follow the optimized road route on the map.</p></div><div className="route-layout"><div className="form-card route-controls"><div className="point-list">{points.map((point) => <label key={point.id} className="point"><input type="checkbox" checked={selected.includes(point.id)} onChange={(event) => togglePoint(point.id, event.target.checked)}/><span><strong>{point.name}</strong><small>{point.latitude.toFixed(4)}, {point.longitude.toFixed(4)}</small></span><b>{point.priority_score}</b></label>)}</div><label className="start-point">Starting collection point<select value={startPointId ?? ""} disabled={selected.length === 0} onChange={(event) => setStartPointId(Number(event.target.value))}>{selected.map((id) => { const point = points.find((item) => item.id === id); return point ? <option key={id} value={id}>{point.name}</option> : null; })}</select></label><button className="primary" disabled={selected.length < 2} onClick={optimize}>Generate optimized route</button>{result && <div className="result-card"><p className="eyebrow">{result.road_network_available ? "ROAD ROUTE" : "DEMONSTRATION RESULT"}</p><h2>{result.optimized_distance_km} km</h2><p>{result.distance_saved_percent}% distance saved against selected order.</p><small>{result.routing_disclaimer}</small></div>}</div><div className="route-map-card"><div className="card-title"><h2>Collector map</h2><span className="live">{result ? "OPTIMIZED ORDER" : "SELECTED POINTS"}</span></div><div ref={routeMapElement} className="route-map" /></div></div></main></Layout>;
}

function Sources() {
  const [sources, setSources] = useState<{ name: string; url: string; purpose: string; license: string; status: string }[]>([]);
  useEffect(() => { api.get("/api/open-data/sources").then((response) => setSources(response.data)); }, []);
  return <Layout><main className="page"><div className="page-heading"><p className="eyebrow">OPEN DATA</p><h1>Sources we build on</h1><p className="muted">Transparent inputs for trustworthy city intelligence.</p></div><div className="source-grid">{sources.map((source) => <article className="source-card" key={source.name}><div className="source-icon">↗</div><h2>{source.name}</h2><p>{source.purpose}</p><a href={source.url} target="_blank" rel="noreferrer">Visit source</a><small>{source.license} · {source.status}</small></article>)}</div></main></Layout>;
}

function Empty({ text }: { text: string }) { return <div className="empty"><span>○</span><p>{text}</p></div>; }

function Protected({ children, admin = false }: { children: React.ReactNode; admin?: boolean }) {
  const user = JSON.parse(localStorage.getItem("cleancity_user") ?? "null") as User | null;
  if (!user || (admin && user.role !== "admin")) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function App() { return <BrowserRouter><Routes><Route path="/" element={<Landing/>}/><Route path="/login" element={<Login/>}/><Route path="/report" element={<Protected><ReportForm/></Protected>}/><Route path="/reports" element={<Protected><MyReports/></Protected>}/><Route path="/admin" element={<Protected admin><AdminDashboard/></Protected>}/><Route path="/admin/reports" element={<Protected admin><AdminReports/></Protected>}/><Route path="/admin/intelligence" element={<Protected admin><Intelligence/></Protected>}/><Route path="/admin/routes" element={<Protected admin><RoutesPage/></Protected>}/><Route path="/sources" element={<Sources/>}/></Routes></BrowserRouter>; }

createRoot(document.getElementById("root")!).render(<StrictMode><App /></StrictMode>);
