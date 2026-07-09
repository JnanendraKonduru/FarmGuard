/* ═══════════════════════════════════════════════════════
   FarmGuard Dashboard JS — Multi-page logic
═══════════════════════════════════════════════════════ */

const ALL_CLASSES = ["person","dog","cat","bird","cow","horse","sheep","elephant","bear","zebra","deer","fox","rabbit"];
const ANIMAL_SET  = new Set(["dog","cat","bird","cow","horse","sheep","elephant","bear","zebra","deer","fox","rabbit"]);

let currentPage  = "overview";
let histPage     = 1;
let histLabel    = "";
let lastDetTotal = 0;
let snapshots    = [];

// ── Clock ──────────────────────────────────────────────────────────────────
function tick() {
  const now = new Date();
  const t = now.toLocaleTimeString("en-IN", { hour12: false });
  const d = now.toLocaleDateString("en-IN");
  document.getElementById("tbClock").textContent = t;
  document.getElementById("sysTime").textContent = d + " " + t;
}
tick();
setInterval(tick, 1000);

// ── Sidebar collapse ───────────────────────────────────────────────────────
const sidebar = document.getElementById("sidebar");
document.getElementById("sidebarToggle").addEventListener("click", () => {
  sidebar.classList.toggle("collapsed");
});

// ── Navigation ─────────────────────────────────────────────────────────────
const navItems  = document.querySelectorAll(".nav-item");
const pages     = document.querySelectorAll(".page");
const titles    = { overview:"Overview", camera:"Live Camera", snapshots:"Snapshots", analytics:"Analytics", settings:"Settings" };

function goTo(page) {
  currentPage = page;
  navItems.forEach(n => n.classList.toggle("active", n.dataset.page === page));
  pages.forEach(p => p.classList.toggle("active", p.id === `page-${page}`));
  document.getElementById("pageTitle").textContent = titles[page];
  document.getElementById("breadcrumb").textContent = `FarmGuard / ${titles[page]}`;
  if (page === "analytics") loadHistory(1);
  if (page === "snapshots") loadSnapshots();
  if (page === "settings")  loadSettings();
}

navItems.forEach(n => n.addEventListener("click", e => { e.preventDefault(); goTo(n.dataset.page); }));

// allow "go-btn" and "panel-link" elements to navigate
document.addEventListener("click", e => {
  const el = e.target.closest("[data-page]");
  if (el && !el.classList.contains("nav-item")) goTo(el.dataset.page);
});

// ── Status check ───────────────────────────────────────────────────────────
const sysDot = document.getElementById("sysDot");
const sysTxt = document.getElementById("sysTxt");

async function checkStatus() {
  try {
    const r = await fetch("/api/stats");
    if (r.ok) { sysDot.className = "sys-dot online"; sysTxt.textContent = "System online"; }
    else throw new Error();
  } catch {
    sysDot.className = "sys-dot offline"; sysTxt.textContent = "Offline";
  }
}
checkStatus();
setInterval(checkStatus, 10000);

// ── Stats / Overview ───────────────────────────────────────────────────────
async function loadStats() {
  try {
    const r = await fetch("/api/stats");
    const d = await r.json();

    // Stat cards
    document.getElementById("ovTotal").textContent  = d.total_detections ?? 0;
    document.getElementById("ovToday").textContent  = d.today_detections ?? 0;
    document.getElementById("ovAlerts").textContent = d.alerts_sent ?? 0;
    document.getElementById("ovLast").textContent   = d.last_detection ? d.last_detection.slice(0,19) : "None";

    // Cam sidebar
    document.getElementById("camToday").textContent  = d.today_detections ?? 0;
    document.getElementById("camAlerts").textContent = d.alerts_sent ?? 0;
    document.getElementById("camLast").textContent   = d.last_detection ? d.last_detection.slice(11,19) : "—";

    // Alert ping if new detection
    if (d.total_detections > lastDetTotal && lastDetTotal > 0) {
      triggerAlertPing(d.top_threats?.[0]?.label ?? "Unknown");
    }
    lastDetTotal = d.total_detections ?? 0;

    // Snapshot badge
    document.getElementById("snapBadge").textContent = d.total_detections ?? 0;

    // Threat bars (overview + analytics)
    renderThreatBars(d.top_threats ?? [], "ovThreatBars");
    renderThreatBars(d.top_threats ?? [], "anThreatBars");

  } catch(e) { console.warn("Stats error:", e); }
}

function renderThreatBars(threats, containerId) {
  const el = document.getElementById(containerId);
  if (!el) return;
  if (!threats.length) { el.innerHTML = `<div class="empty">No detections yet</div>`; return; }
  const max = threats[0].count;
  el.innerHTML = threats.map(t => {
    const cls = t.label === "person" ? "person" : ANIMAL_SET.has(t.label) ? "dog" : "";
    const pct = Math.round((t.count / max) * 100);
    return `<div class="threat-row">
      <span class="threat-lbl">${t.label}</span>
      <div class="threat-bar-wrap"><div class="threat-bar ${cls}" style="width:${pct}%"></div></div>
      <span class="threat-cnt">${t.count}</span>
    </div>`;
  }).join("");
}

loadStats();
setInterval(loadStats, 7000);

// ── Recent events (overview + camera sidebar) ──────────────────────────────
async function loadRecentEvents() {
  try {
    const r = await fetch("/api/detections?page=1&limit=8");
    const d = await r.json();
    renderEventList(d.data ?? [], "ovEventList");
    renderEventList(d.data ?? [], "camEventList");
  } catch {}
}

function renderEventList(rows, containerId) {
  const el = document.getElementById(containerId);
  if (!el) return;
  if (!rows.length) { el.innerHTML = `<div class="empty">No detections yet</div>`; return; }
  el.innerHTML = rows.map(row => {
    const dotClass = row.label === "person" ? "person" : ANIMAL_SET.has(row.label) ? "animal" : "other";
    const conf = (row.confidence * 100).toFixed(0) + "%";
    const ts   = row.timestamp ? row.timestamp.slice(11,19) : "—";
    return `<div class="event-item">
      <span class="event-dot ${dotClass}"></span>
      <span class="event-label">${row.label}</span>
      <span class="event-conf">${conf}</span>
      <span class="event-time">${ts}</span>
    </div>`;
  }).join("");
}

loadRecentEvents();
setInterval(loadRecentEvents, 7000);

// ── Alert ping + toast ─────────────────────────────────────────────────────
function triggerAlertPing(label) {
  const ping = document.getElementById("alertPing");
  ping.classList.add("active");
  setTimeout(() => ping.classList.remove("active"), 3000);
  showToast(`⚠ ${label.charAt(0).toUpperCase()+label.slice(1)} detected!`, "orange");

  // flash threat banner on camera page
  const banner    = document.getElementById("threatBanner");
  const bannerLbl = document.getElementById("bannerLabel");
  if (banner) {
    bannerLbl.textContent = label.toUpperCase();
    banner.classList.add("show");
    setTimeout(() => banner.classList.remove("show"), 4000);
  }
}

function showToast(msg, type = "orange") {
  const wrap = document.getElementById("toastWrap");
  const t = document.createElement("div");
  t.className = `toast ${type === "green" ? "green" : type === "blue" ? "blue" : ""}`;
  const now = new Date().toLocaleTimeString("en-IN", { hour12: false });
  t.innerHTML = `<span class="toast-ico">${type==="green"?"✓":"⚠"}</span><span class="toast-txt">${msg}</span><span class="toast-time">${now}</span>`;
  wrap.appendChild(t);
  setTimeout(() => t.remove(), 5000);
}

// ── Camera page ────────────────────────────────────────────────────────────
async function updateCamLabel() {
  try {
    const r = await fetch("/api/settings");
    const s = await r.json();
    const src = s.camera_source ?? "0";
    const lbl = src === "0" ? "Camera 0 — Webcam" : src;
    document.getElementById("camSrc").textContent = lbl;
    document.getElementById("camFooterMeta").textContent = "Source: " + lbl;
  } catch {}
}
updateCamLabel();

document.getElementById("fsBtn")?.addEventListener("click", () => {
  const frame = document.getElementById("feedFrame");
  if (frame.requestFullscreen) frame.requestFullscreen();
});

// ── Snapshots ──────────────────────────────────────────────────────────────
async function loadSnapshots() {
  const grid = document.getElementById("snapGrid");
  grid.innerHTML = `<div class="empty">Loading…</div>`;
  try {
    const r = await fetch("/api/snapshots");
    const d = await r.json();
    snapshots = d.snapshots ?? [];
    renderSnapshots(snapshots);
  } catch { grid.innerHTML = `<div class="empty">Could not load snapshots.</div>`; }
}

function renderSnapshots(list) {
  const grid  = document.getElementById("snapGrid");
  const count = document.getElementById("snapCount");
  count.textContent = `${list.length} snapshot${list.length !== 1 ? "s" : ""}`;
  if (!list.length) { grid.innerHTML = `<div class="empty">No snapshots yet — they appear here when FarmGuard detects threats.</div>`; return; }
  grid.innerHTML = list.map(s =>
    `<div class="snap-thumb" onclick="openLightbox('${s.url}','${s.filename}')">
       <img src="${s.url}" alt="${s.filename}" loading="lazy"/>
       <div class="snap-cap">${s.filename}</div>
     </div>`
  ).join("");
}

document.getElementById("snapSearch").addEventListener("input", e => {
  const q = e.target.value.toLowerCase();
  renderSnapshots(q ? snapshots.filter(s => s.filename.toLowerCase().includes(q)) : snapshots);
});

function openLightbox(url, name) {
  document.getElementById("lbImg").src = url;
  document.getElementById("lbName").textContent = name;
  document.getElementById("lightbox").classList.add("open");
}
function closeLightbox() {
  document.getElementById("lightbox").classList.remove("open");
}
document.getElementById("lbClose").onclick = closeLightbox;
document.getElementById("lbBg").onclick    = closeLightbox;
document.addEventListener("keydown", e => { if (e.key === "Escape") closeLightbox(); });

// ── Analytics / History ────────────────────────────────────────────────────
async function loadHistory(page = 1) {
  histPage = page;
  try {
    const r = await fetch(`/api/detections?page=${page}&limit=30&label=${encodeURIComponent(histLabel)}`);
    const d = await r.json();
    renderHistory(d);
    renderClassLegend();
  } catch { document.getElementById("histBody").innerHTML = `<tr><td colspan="6" class="empty">Failed to load</td></tr>`; }
}

function renderHistory(d) {
  const tbody = document.getElementById("histBody");
  if (!d.data?.length) {
    tbody.innerHTML = `<tr><td colspan="6" class="empty">No records found.</td></tr>`;
  } else {
    tbody.innerHTML = d.data.map(row => {
      const isP = row.label === "person";
      const isA = ANIMAL_SET.has(row.label);
      const pillCls = isP ? "person" : isA ? "animal" : "default";
      const snapCell = row.snapshot
        ? `<a class="snap-link" href="/snapshots/${row.snapshot}" target="_blank">View</a>`
        : `<span style="color:var(--txt-muted)">—</span>`;
      return `<tr>
        <td>${row.id}</td>
        <td>${row.timestamp?.slice(0,19) ?? "—"}</td>
        <td><span class="label-pill ${pillCls}">${row.label}</span></td>
        <td>${(row.confidence * 100).toFixed(1)}%</td>
        <td class="${row.alerted ? "alerted-y" : "alerted-n"}">${row.alerted ? "✓ Yes" : "—"}</td>
        <td>${snapCell}</td>
      </tr>`;
    }).join("");
  }

  const pages = Math.max(1, Math.ceil((d.total ?? 0) / 30));
  const pg    = document.getElementById("pagination");
  pg.innerHTML = pages <= 1 ? "" :
    Array.from({length: Math.min(pages, 10)}, (_,i) =>
      `<button class="pg-btn ${i+1===histPage?"on":""}" onclick="loadHistory(${i+1})">${i+1}</button>`
    ).join("");
}

function renderClassLegend() {
  fetch("/api/settings").then(r=>r.json()).then(s => {
    const classes = s.detection_classes ?? ALL_CLASSES;
    const colors  = { person: "var(--red)", dog: "var(--orange)", cat: "var(--orange)", bird: "var(--blue)" };
    document.getElementById("classLegend").innerHTML = classes.map(c =>
      `<div class="cl-row"><span class="cl-dot" style="background:${colors[c]??'var(--green)'}"></span><span class="cl-name">${c}</span></div>`
    ).join("");
  }).catch(()=>{});
}

let histTimer;
document.getElementById("histSearch").addEventListener("input", e => {
  clearTimeout(histTimer);
  histTimer = setTimeout(() => { histLabel = e.target.value.trim(); loadHistory(1); }, 350);
});

document.getElementById("clearBtn").addEventListener("click", async () => {
  if (!confirm("Delete ALL detection records? Cannot be undone.")) return;
  await fetch("/api/clear_detections", { method: "POST" });
  loadHistory(1);
  loadStats();
  showToast("All records cleared", "blue");
});

// ── Settings ───────────────────────────────────────────────────────────────
async function loadSettings() {
  try {
    const r = await fetch("/api/settings");
    const s = await r.json();

    document.getElementById("setCamera").value   = s.camera_source ?? "0";
    document.getElementById("setConf").value      = s.confidence_threshold ?? 0.5;
    document.getElementById("confDisp").textContent = parseFloat(s.confidence_threshold ?? 0.5).toFixed(2);
    document.getElementById("setAlertCD").value  = s.alert_cooldown_minutes ?? 2;
    document.getElementById("setCallCD").value   = s.call_cooldown_minutes  ?? 5;
    document.getElementById("setTelegram").checked = !!s.telegram_alerts;
    document.getElementById("setVoice").checked    = !!s.voice_calls;
    document.getElementById("setSound").checked    = !!s.sound_alarm;

    const active = s.detection_classes ?? [];
    const grid   = document.getElementById("classChips");
    grid.innerHTML = ALL_CLASSES.map(c =>
      `<span class="chip ${active.includes(c)?"on":""}" data-cls="${c}">${c}</span>`
    ).join("");
    grid.querySelectorAll(".chip").forEach(ch => ch.addEventListener("click", () => ch.classList.toggle("on")));
  } catch(e) { console.warn("Settings load error:", e); }
}

document.getElementById("setConf").addEventListener("input", e => {
  document.getElementById("confDisp").textContent = parseFloat(e.target.value).toFixed(2);
});

document.getElementById("saveBtn").addEventListener("click", async () => {
  const activeClasses = [...document.querySelectorAll(".chip.on")].map(c => c.dataset.cls);
  const payload = {
    camera_source:          document.getElementById("setCamera").value.trim(),
    confidence_threshold:   parseFloat(document.getElementById("setConf").value),
    alert_cooldown_minutes: parseInt(document.getElementById("setAlertCD").value),
    call_cooldown_minutes:  parseInt(document.getElementById("setCallCD").value),
    telegram_alerts:        document.getElementById("setTelegram").checked,
    voice_calls:            document.getElementById("setVoice").checked,
    sound_alarm:            document.getElementById("setSound").checked,
    detection_classes:      activeClasses,
  };
  try {
    const r = await fetch("/api/settings", { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(payload) });
    if (r.ok) {
      const msg = document.getElementById("saveMsg");
      msg.textContent = "✓ Settings saved";
      setTimeout(() => msg.textContent = "", 3000);
      showToast("Settings saved successfully", "green");
      updateCamLabel();
    }
  } catch(e) { console.error("Save failed:", e); }
});
