// NUVIO GROWTH BOT - Master Dashboard Application State & Router
let currentLang = localStorage.getItem("nuvio_lang") || "es";
let authToken = localStorage.getItem("nuvio_token") || "";
let currentUser = null;
let currentOrg = null;
let activeView = "overview";

// DOM Elements
const sidebarNav = document.getElementById("sidebarNav");
const langSelect = document.getElementById("langSelect");
const currentUserNameEl = document.getElementById("currentUserName");
const currentUserOrgEl = document.getElementById("currentUserOrg");
const toastContainer = document.getElementById("toastContainer");

// Toast Notification
function showToast(message, type = "info") {
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>${message}</span>`;
  toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// Authenticated API Fetch
async function apiRequest(endpoint, options = {}) {
  const headers = options.headers || {};
  if (authToken) {
    headers["Authorization"] = `Bearer ${authToken}`;
  }
  if (!headers["Content-Type"] && !(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  try {
    const res = await fetch(`/api/v1${endpoint}`, { credentials: "omit", ...options, headers });
    if (res.status === 401) {
      // Re-authenticate
      await autoLogin();
      return;
    }
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(data.detail || `Request failed with status ${res.status}`);
    }
    return data;
  } catch (err) {
    showToast(err.message, "danger");
    throw err;
  }
}

// Auto-Login with Seeded Credentials if no valid token
async function autoLogin() {
  try {
    const res = await fetch("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: "admin@nuviogrowth.com",
        password: "NuvioGrowth2026!"
      })
    });
    if (res.ok) {
      const data = await res.json();
      authToken = data.access_token;
      localStorage.setItem("nuvio_token", authToken);
      await loadCurrentUser();
      showToast("Sesión iniciada con éxito", "success");
    }
  } catch (e) {
    console.error("Auto login error:", e);
  }
}

async function loadCurrentUser() {
  try {
    currentUser = await apiRequest("/auth/me");
    const settingsData = await apiRequest("/settings");
    currentOrg = settingsData;
    if (currentUserNameEl) currentUserNameEl.textContent = currentUser.full_name;
    if (currentUserOrgEl) currentUserOrgEl.textContent = currentOrg.organization_name;
    if (currentUser.language && ["es", "en", "ht"].includes(currentUser.language)) {
      currentLang = currentUser.language;
      if (langSelect) langSelect.value = currentLang;
    }
  } catch (e) {
    console.error(e);
  }
}

// Navigation & View Routing
function switchView(viewName) {
  activeView = viewName;
  document.querySelectorAll(".view-section").forEach(sec => sec.classList.remove("active"));
  document.querySelectorAll(".nav-item").forEach(item => item.classList.remove("active"));

  const targetSec = document.getElementById(`view-${viewName}`);
  const targetNav = document.querySelector(`.nav-item[data-view="${viewName}"]`);

  if (targetSec) targetSec.classList.add("active");
  if (targetNav) targetNav.classList.add("active");

  window.location.hash = viewName;

  // View specific loaders
  if (viewName === "overview") loadOverview();
  else if (viewName === "social") loadSocialAccounts();
  else if (viewName === "queue") loadPublishingQueue();
  else if (viewName === "approvals") loadApprovals();
  else if (viewName === "media") loadMediaLibrary();
  else if (viewName === "calendar") loadCalendar();
  else if (viewName === "analytics") loadAnalytics();
  else if (viewName === "clients") loadClients();
  else if (viewName === "team") loadTeam();
  else if (viewName === "billing") loadBilling();
  else if (viewName === "settings") loadSettings();
}

// 1. OVERVIEW
async function loadOverview() {
  try {
    const summary = await apiRequest("/analytics/summary?days=30");
    const posts = await apiRequest("/posts");
    const accounts = await apiRequest("/social/accounts");

    document.getElementById("ov-accounts-count").textContent = summary.total_connected_accounts;
    document.getElementById("ov-followers-count").textContent = summary.total_followers.toLocaleString();
    document.getElementById("ov-impressions-count").textContent = summary.total_impressions.toLocaleString();
    document.getElementById("ov-engagement-rate").textContent = `${summary.total_engagement_rate}%`;

    // Render Overview Trend Chart
    const ovCanvas = document.getElementById("ov-timeline-canvas");
    if (ovCanvas && typeof NuvioChart !== "undefined") {
      const dataPoints = summary.timeline_impressions && summary.timeline_impressions.length > 0
        ? summary.timeline_impressions
        : [
            { date: "2026-11-01", value: 1200 },
            { date: "2026-11-03", value: 1850 },
            { date: "2026-11-05", value: 2400 },
            { date: "2026-11-07", value: 3100 },
            { date: "2026-11-09", value: 3950 }
          ];
      NuvioChart.renderLineChart(ovCanvas, dataPoints, {
        strokeColor: "#6366f1",
        gradientStart: "rgba(99, 102, 241, 0.4)"
      });
    }

    // Render Recent Posts Table
    const recentTbody = document.getElementById("ov-recent-posts-body");
    recentTbody.innerHTML = "";
    const slicePosts = (posts || []).slice(0, 5);
    if (slicePosts.length === 0) {
      recentTbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:24px;color:var(--text-dim);">No hay publicaciones creadas aún.</td></tr>`;
    } else {
      slicePosts.forEach(p => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td style="padding:12px;font-weight:600;color:var(--text-main);">${escapeHtml(p.title || p.content.slice(0, 30))}</td>
          <td style="padding:12px;">${renderPlatformPills(p.target_platforms)}</td>
          <td style="padding:12px;"><span class="status-badge status-${p.status}">${p.status.replace('_', ' ')}</span></td>
          <td style="padding:12px;color:var(--text-dim);font-size:0.8rem;">${p.scheduled_at ? formatDate(p.scheduled_at) : (p.published_at ? formatDate(p.published_at) : 'Borrador')}</td>
          <td style="padding:12px;text-align:right;">
            <button class="btn btn-secondary btn-sm" onclick="openPreviewPost(${p.id})">Ver</button>
          </td>
        `;
        recentTbody.appendChild(tr);
      });
    }

    // Render Connection Badges
    const statusWrap = document.getElementById("ov-conn-status-wrap");
    statusWrap.innerHTML = "";
    ["instagram", "facebook", "tiktok", "youtube"].forEach(plat => {
      const conn = accounts.find(a => a.platform === plat);
      const isConn = conn && conn.status === "connected";
      const div = document.createElement("div");
      div.className = "card-panel";
      div.style.padding = "14px";
      div.style.marginBottom = "0";
      div.innerHTML = `
        <div style="display:flex;align-items:center;justify-content:space-between;">
          <div style="display:flex;align-items:center;gap:10px;">
            <span class="platform-pill pill-${plat}">${plat}</span>
            <span style="font-size:0.85rem;font-weight:600;">${isConn ? conn.username : 'Sin conectar'}</span>
          </div>
          <span style="font-size:0.75rem;color:${isConn ? 'var(--success)' : 'var(--text-dim)'};font-weight:700;">
            ${isConn ? '● ACTIVO' : '○ NO CONECTADO'}
          </span>
        </div>
      `;
      statusWrap.appendChild(div);
    });

  } catch (e) {
    console.error(e);
  }
}

// 2. SOCIAL ACCOUNTS
async function loadSocialAccounts() {
  const container = document.getElementById("social-cards-grid");
  container.innerHTML = "<p>Cargando cuentas...</p>";
  try {
    const accounts = await apiRequest("/social/accounts");
    container.innerHTML = "";

    const platforms = [
      { id: "instagram", name: "Instagram Business", desc: "Meta Graph API v20.0" },
      { id: "facebook", name: "Facebook Pages", desc: "Meta Pages API" },
      { id: "tiktok", name: "TikTok Creator", desc: "TikTok for Developers Content Posting" },
      { id: "youtube", name: "YouTube Channel", desc: "Google YouTube Data API v3" }
    ];

    platforms.forEach(plat => {
      const conn = accounts.find(a => a.platform === plat.id);
      const card = document.createElement("div");
      card.className = "card-panel";
      card.style.display = "flex";
      card.style.flexDirection = "column";
      card.style.justifyContent = "space-between";

      if (conn) {
        card.innerHTML = `
          <div>
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
              <span class="platform-pill pill-${plat.id}">${plat.name}</span>
              <span class="status-badge status-published">Conectado</span>
            </div>
            <div style="display:flex;align-items:center;gap:12px;margin:16px 0;">
              <img src="${conn.profile_picture_url || 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=100'}" style="width:48px;height:48px;border-radius:50%;border:2px solid var(--border);">
              <div>
                <h4 style="font-size:0.95rem;font-weight:700;">${escapeHtml(conn.display_name || conn.username)}</h4>
                <p style="font-size:0.78rem;color:var(--text-dim);">@${escapeHtml(conn.username)}</p>
              </div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:12px;background:var(--bg-input);border-radius:8px;margin-bottom:16px;">
              <div>
                <span style="font-size:0.7rem;color:var(--text-muted);text-transform:uppercase;">Seguidores</span>
                <p style="font-size:1.1rem;font-weight:700;">${(conn.followers_count || 0).toLocaleString()}</p>
              </div>
              <div>
                <span style="font-size:0.7rem;color:var(--text-muted);text-transform:uppercase;">Publicaciones</span>
                <p style="font-size:1.1rem;font-weight:700;">${(conn.posts_count || 0).toLocaleString()}</p>
              </div>
            </div>
          </div>
          <div style="display:flex;gap:8px;">
            <button class="btn btn-secondary btn-sm" style="flex:1;" onclick="testAccountConn(${conn.id})">Probar API</button>
            <button class="btn btn-secondary btn-sm" style="flex:1;" onclick="syncAccountProfile(${conn.id})">Sincronizar</button>
            <button class="btn btn-danger btn-sm" onclick="disconnectAccount(${conn.id})">✕</button>
          </div>
        `;
      } else {
        card.innerHTML = `
          <div>
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
              <span class="platform-pill pill-${plat.id}">${plat.name}</span>
              <span class="status-badge status-draft">Desconectado</span>
            </div>
            <p style="font-size:0.82rem;color:var(--text-muted);margin:16px 0;">${plat.desc}. Conecta tu cuenta oficial para habilitar publicación programada y métricas.</p>
          </div>
          <div style="display:flex;gap:8px;">
            <button class="btn btn-primary btn-sm" style="flex:1;" onclick="startOAuthConnect('${plat.id}')">Conectar con OAuth</button>
            <button class="btn btn-secondary btn-sm" onclick="openManualConnectModal('${plat.id}')">Token</button>
          </div>
        `;
      }
      container.appendChild(card);
    });
  } catch (e) {
    console.error(e);
  }
}

async function startOAuthConnect(platform) {
  try {
    const res = await apiRequest(`/social/oauth/${platform}/url`);
    if (res && res.auth_url) {
      window.location.href = res.auth_url;
    }
  } catch (e) {
    console.error(e);
  }
}

async function testAccountConn(id) {
  try {
    const res = await apiRequest(`/social/accounts/${id}/test`, { method: "POST" });
    showToast(res.message, res.success ? "success" : "danger");
  } catch (e) {
    console.error(e);
  }
}

async function syncAccountProfile(id) {
  try {
    await apiRequest(`/social/accounts/${id}/sync`, { method: "POST" });
    showToast("Perfil de cuenta sincronizado", "success");
    loadSocialAccounts();
  } catch (e) {
    console.error(e);
  }
}

async function disconnectAccount(id) {
  if (!confirm("¿Deseas desconectar esta cuenta social de Nuvio Growth Bot?")) return;
  try {
    await apiRequest(`/social/accounts/${id}`, { method: "DELETE" });
    showToast("Cuenta desconectada", "info");
    loadSocialAccounts();
  } catch (e) {
    console.error(e);
  }
}

// 3. AI CONTENT STUDIO
let generatedProposals = [];

async function generateAIContent() {
  const btn = document.getElementById("ai-generate-btn");
  btn.disabled = true;
  btn.textContent = "Generando con IA...";

  const payload = {
    business_name: document.getElementById("ai-biz-name").value || "Nuvio Agency",
    industry: document.getElementById("ai-industry").value || "Marketing Digital",
    product_service: document.getElementById("ai-prod-service").value || "Gestión de Redes y Crecimiento",
    target_audience: document.getElementById("ai-audience").value || "Emprendedores y Marcas",
    social_network: document.getElementById("ai-platform").value || "instagram",
    language: document.getElementById("ai-language").value || currentLang,
    tone: document.getElementById("ai-tone").value || "professional",
    objective: document.getElementById("ai-objective").value || "brand_awareness",
    additional_notes: document.getElementById("ai-notes").value || "",
    variations_count: 3
  };

  try {
    const res = await apiRequest("/ai/generate", {
      method: "POST",
      body: JSON.stringify(payload)
    });
    generatedProposals = res.proposals || [];
    renderAIProposals();
    showToast("Propuestas generadas con éxito", "success");
  } catch (e) {
    console.error(e);
  } finally {
    btn.disabled = false;
    btn.textContent = "Generar Propuestas con IA";
  }
}

function renderAIProposals() {
  const container = document.getElementById("ai-proposals-container");
  container.innerHTML = "";

  if (generatedProposals.length === 0) {
    container.innerHTML = `<div class="card-panel" style="text-align:center;padding:40px;color:var(--text-dim);">Haz clic en "Generar Propuestas" para crear copys de alto impacto.</div>`;
    return;
  }

  generatedProposals.forEach((p, idx) => {
    const card = document.createElement("div");
    card.className = "card-panel";
    card.style.marginBottom = "18px";
    card.innerHTML = `
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
        <span class="platform-pill pill-${p.target_platform || 'instagram'}">Propuesta #${idx + 1}</span>
        <span style="font-size:0.75rem;color:var(--text-dim);font-weight:600;">Tono: ${p.tone}</span>
      </div>
      <h4 style="font-size:1rem;font-weight:700;margin-bottom:8px;color:var(--text-main);">${escapeHtml(p.title)}</h4>
      <div style="background:var(--bg-input);border:1px solid var(--border);border-radius:8px;padding:14px;white-space:pre-wrap;font-size:0.85rem;line-height:1.6;margin-bottom:12px;" id="prop-text-${idx}">${escapeHtml(p.caption)}</div>
      <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:14px;">
        ${(p.hashtags || []).map(h => `<span style="font-size:0.75rem;color:var(--primary);background:var(--primary-light);padding:2px 8px;border-radius:4px;">${escapeHtml(h)}</span>`).join('')}
      </div>
      <div style="display:flex;flex-wrap:wrap;gap:8px;">
        <button class="btn btn-primary btn-sm" onclick="useProposalInNewPost(${idx})">Crear Publicación</button>
        <button class="btn btn-secondary btn-sm" onclick="saveProposalAsDraft(${idx})">Guardar Borrador</button>
        <button class="btn btn-secondary btn-sm" style="color:#fbbf24;border-color:rgba(245,158,11,0.4);" onclick="sendProposalForApproval(${idx})">Enviar a Aprobación</button>
        <button class="btn btn-secondary btn-sm" onclick="improveProposal(${idx})">Mejorar</button>
        <button class="btn btn-secondary btn-sm" onclick="translateProposal(${idx})">Traducir</button>
        <button class="btn btn-secondary btn-sm" onclick="copyProposal(${idx})">Copiar</button>
      </div>
    `;
    container.appendChild(card);
  });
}

function useProposalInNewPost(idx) {
  const p = generatedProposals[idx];
  if (!p) return;
  openCreatePostModal({
    title: p.title,
    content: `${p.caption}\n\n${(p.hashtags || []).join(' ')}`,
    platform: p.target_platform || "instagram"
  });
}

async function improveProposal(idx) {
  const p = generatedProposals[idx];
  const directive = prompt("¿Cómo deseas mejorar este texto? (Ej: 'Hazlo más enérgico', 'Agrega emojis', 'Más corto para TikTok')", "Agrega un gancho más fuerte");
  if (!directive) return;

  try {
    const res = await apiRequest("/ai/improve", {
      method: "POST",
      body: JSON.stringify({
        original_caption: p.caption,
        instruction: directive,
        language: document.getElementById("ai-language").value || currentLang
      })
    });
    p.caption = res.improved_caption;
    if (res.hashtags && res.hashtags.length) p.hashtags = res.hashtags;
    renderAIProposals();
    showToast("Caption mejorado", "success");
  } catch (e) {
    console.error(e);
  }
}

async function translateProposal(idx) {
  const p = generatedProposals[idx];
  const target = prompt("Selecciona idioma destino: 'es' (Español), 'en' (Inglés), 'ht' (Kreyòl Ayisyen)", currentLang === 'es' ? 'en' : 'es');
  if (!target) return;

  try {
    const res = await apiRequest("/ai/translate", {
      method: "POST",
      body: JSON.stringify({
        content: p.caption,
        target_language: target
      })
    });
    p.caption = res.translated_content;
    renderAIProposals();
    showToast("Traducción completada", "success");
  } catch (e) {
    console.error(e);
  }
}

function copyProposal(idx) {
  const p = generatedProposals[idx];
  const full = `${p.title ? p.title + '\n\n' : ''}${p.caption}\n\n${(p.hashtags || []).join(' ')}`;
  navigator.clipboard.writeText(full);
  showToast("Copiado al portapapeles", "info");
}

// 4. PUBLISHING QUEUE
async function loadPublishingQueue() {
  const tbody = document.getElementById("queue-posts-body");
  tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:24px;">Cargando cola de publicación...</td></tr>`;

  try {
    const posts = await apiRequest("/posts");
    tbody.innerHTML = "";
    if (posts.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:32px;color:var(--text-dim);">No hay publicaciones registradas.</td></tr>`;
      return;
    }

    posts.forEach(p => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td style="padding:14px;font-weight:600;">${escapeHtml(p.title || p.content.slice(0, 32))}</td>
        <td style="padding:14px;">${renderPlatformPills(p.target_platforms)}</td>
        <td style="padding:14px;"><span class="status-badge status-${p.status}">${p.status.replace('_', ' ')}</span></td>
        <td style="padding:14px;color:var(--text-muted);font-size:0.8rem;">${p.scheduled_at ? formatDate(p.scheduled_at) : 'Inmediata / Borrador'}</td>
        <td style="padding:14px;font-size:0.8rem;color:var(--text-dim);">${escapeHtml(p.author_name || 'Miembro')}</td>
        <td style="padding:14px;text-align:right;">
          <div style="display:flex;gap:6px;justify-content:flex-end;">
            ${p.status === 'draft' ? `<button class="btn btn-secondary btn-sm" onclick="submitPostForApproval(${p.id})">Aprobar</button>` : ''}
            ${p.status === 'failed' ? `<button class="btn btn-danger btn-sm" onclick="retryPostNow(${p.id})">Reintentar</button>` : ''}
            ${p.status === 'approved' ? `<button class="btn btn-success btn-sm" onclick="publishPostDirect(${p.id})">Publicar Ya</button>` : ''}
            <button class="btn btn-secondary btn-sm" onclick="openPreviewPost(${p.id})">Ver</button>
          </div>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (e) {
    console.error(e);
  }
}

async function submitPostForApproval(postId) {
  try {
    await apiRequest(`/posts/${postId}/submit-approval`, { method: "POST" });
    showToast("Enviado a revisión humana", "success");
    loadPublishingQueue();
  } catch (e) {
    console.error(e);
  }
}

async function publishPostDirect(postId) {
  try {
    const res = await apiRequest(`/posts/${postId}/publish-now`, { method: "POST" });
    if (res.success) {
      showToast("¡Publicación enviada con éxito!", "success");
    } else {
      showToast("Fallo al publicar en redes", "danger");
    }
    loadPublishingQueue();
  } catch (e) {
    console.error(e);
  }
}

async function retryPostNow(postId) {
  try {
    const res = await apiRequest(`/posts/${postId}/retry`, { method: "POST" });
    if (res.success) {
      showToast("Reintento exitoso", "success");
    } else {
      showToast("El reintento volvió a fallar", "danger");
    }
    loadPublishingQueue();
  } catch (e) {
    console.error(e);
  }
}

// 5. APPROVALS WORKFLOW
async function loadApprovals() {
  const container = document.getElementById("approvals-cards-container");
  container.innerHTML = "<p>Cargando aprobaciones pendientes...</p>";

  try {
    const pending = await apiRequest("/approvals/pending");
    container.innerHTML = "";

    if (pending.length === 0) {
      container.innerHTML = `
        <div class="card-panel" style="text-align:center;padding:48px;color:var(--text-dim);">
          <div style="font-size:2rem;margin-bottom:12px;">✅</div>
          <h3>Todo está al día</h3>
          <p style="font-size:0.85rem;margin-top:4px;">No hay publicaciones pendientes de revisión en este momento.</p>
        </div>
      `;
      return;
    }

    pending.forEach(p => {
      const card = document.createElement("div");
      card.className = "card-panel";
      card.style.borderLeft = "4px solid var(--warning)";
      card.innerHTML = `
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
          <div>
            <span class="status-badge status-pending_approval">Pendiente de Aprobación</span>
            <span style="font-size:0.8rem;color:var(--text-dim);margin-left:8px;">Creado por: ${escapeHtml(p.author_name || 'Editor')}</span>
          </div>
          <div>${renderPlatformPills(p.target_platforms)}</div>
        </div>
        <h3 style="font-size:1.1rem;margin-bottom:10px;">${escapeHtml(p.title || 'Publicación sin título')}</h3>
        <div style="background:var(--bg-input);padding:14px;border-radius:8px;margin-bottom:14px;font-size:0.88rem;white-space:pre-wrap;line-height:1.6;">${escapeHtml(p.content)}</div>
        <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;">
          <div style="font-size:0.8rem;color:var(--text-muted);">
            Programado para: <strong>${p.scheduled_at ? formatDate(p.scheduled_at) : 'Publicación tras aprobación'}</strong>
          </div>
          <div style="display:flex;gap:10px;">
            <button class="btn btn-danger btn-sm" onclick="reviewPostAction(${p.id}, 'rejected')">Rechazar con Feedback</button>
            <button class="btn btn-success btn-sm" onclick="reviewPostAction(${p.id}, 'approved')">Aprobar Publicación</button>
          </div>
        </div>
      `;
      container.appendChild(card);
    });
  } catch (e) {
    console.error(e);
  }
}

async function reviewPostAction(postId, action) {
  let comments = "";
  if (action === "rejected") {
    comments = prompt("Indica el motivo del rechazo o los cambios requeridos:", "Ajustar texto y hashtags");
    if (comments === null) return;
  }

  try {
    await apiRequest(`/approvals/${postId}/review`, {
      method: "POST",
      body: JSON.stringify({ action, comments })
    });
    showToast(action === "approved" ? "Publicación aprobada" : "Publicación rechazada", "info");
    loadApprovals();
  } catch (e) {
    console.error(e);
  }
}

// 6. CONTENT CALENDAR
async function loadCalendar() {
  const grid = document.getElementById("calendar-days-grid");
  grid.innerHTML = "";

  try {
    const posts = await apiRequest("/posts");
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth();

    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();

    // Fill blank days before 1st
    for (let i = 0; i < firstDay; i++) {
      const blank = document.createElement("div");
      blank.style.minHeight = "90px";
      blank.style.background = "rgba(255,255,255,0.01)";
      blank.style.border = "1px solid var(--border)";
      blank.style.borderRadius = "8px";
      grid.appendChild(blank);
    }

    for (let day = 1; day <= daysInMonth; day++) {
      const cell = document.createElement("div");
      cell.style.minHeight = "90px";
      cell.style.background = "var(--bg-card)";
      cell.style.border = "1px solid var(--border)";
      cell.style.borderRadius = "8px";
      cell.style.padding = "8px";
      cell.style.display = "flex";
      cell.style.flexDirection = "column";

      const isToday = day === now.getDate();
      cell.innerHTML = `
        <div style="font-size:0.78rem;font-weight:${isToday ? '800' : '600'};color:${isToday ? 'var(--primary)' : 'var(--text-dim)'};margin-bottom:6px;">
          ${day} ${isToday ? '• Hoy' : ''}
        </div>
        <div class="day-events" style="display:flex;flex-direction:column;gap:4px;flex:1;"></div>
      `;

      const eventsContainer = cell.querySelector(".day-events");
      // Find posts for this day
      posts.forEach(p => {
        const dStr = p.scheduled_at || p.published_at;
        if (dStr) {
          const pDate = new Date(dStr);
          if (pDate.getDate() === day && pDate.getMonth() === month && pDate.getFullYear() === year) {
            const pill = document.createElement("div");
            pill.style.fontSize = "0.7rem";
            pill.style.padding = "3px 6px";
            pill.style.borderRadius = "4px";
            pill.style.background = p.status === 'published' ? 'rgba(16,185,129,0.2)' : 'rgba(99,102,241,0.2)';
            pill.style.color = p.status === 'published' ? '#34d399' : '#818cf8';
            pill.style.whiteSpace = "nowrap";
            pill.style.overflow = "hidden";
            pill.style.textOverflow = "ellipsis";
            pill.style.cursor = "pointer";
            pill.textContent = p.title || p.content.slice(0, 20);
            pill.onclick = () => openPreviewPost(p.id);
            eventsContainer.appendChild(pill);
          }
        }
      });

      grid.appendChild(cell);
    }
  } catch (e) {
    console.error(e);
  }
}

// 7. ANALYTICS
async function loadAnalytics() {
  try {
    const summary = await apiRequest("/analytics/summary?days=30");
    const topPosts = await apiRequest("/analytics/top-posts");

    const tbody = document.getElementById("analytics-platform-tbody");
    tbody.innerHTML = "";

    Object.values(summary.by_platform || {}).forEach(p => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td style="padding:12px;"><span class="platform-pill pill-${p.platform}">${p.platform}</span></td>
        <td style="padding:12px;font-weight:700;">${p.followers.toLocaleString()}</td>
        <td style="padding:12px;">${p.impressions.toLocaleString()}</td>
        <td style="padding:12px;">${p.reach.toLocaleString()}</td>
        <td style="padding:12px;">${p.views.toLocaleString()}</td>
        <td style="padding:12px;">${p.likes.toLocaleString()}</td>
        <td style="padding:12px;">${p.comments.toLocaleString()}</td>
        <td style="padding:12px;font-weight:700;color:var(--success);">${p.engagement_rate}%</td>
      `;
      tbody.appendChild(tr);
    });

    const topList = document.getElementById("analytics-top-posts");
    topList.innerHTML = "";
    (topPosts || []).forEach(tp => {
      const item = document.createElement("div");
      item.className = "card-panel";
      item.style.padding = "14px";
      item.style.marginBottom = "10px";
      item.innerHTML = `
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
          <h4 style="font-size:0.9rem;font-weight:700;">${escapeHtml(tp.title)}</h4>
          <span class="platform-pill pill-${tp.platform}">${tp.platform}</span>
        </div>
        <p style="font-size:0.8rem;color:var(--text-muted);margin-bottom:8px;">${escapeHtml(tp.content_snippet)}</p>
        <div style="display:flex;gap:16px;font-size:0.75rem;color:var(--text-dim);">
          <span>❤️ ${tp.likes} likes</span>
          <span>💬 ${tp.comments} comentarios</span>
          <span>📈 <strong>${tp.engagement_rate}%</strong> interacciones</span>
        </div>
      `;
      topList.appendChild(item);
    });

  } catch (e) {
    console.error(e);
  }
}

// 8. CLIENTS
async function loadClients() {
  const container = document.getElementById("clients-grid");
  container.innerHTML = "<p>Cargando clientes de agencia...</p>";

  try {
    const clients = await apiRequest("/clients");
    container.innerHTML = "";

    if (clients.length === 0) {
      container.innerHTML = `<div class="card-panel" style="text-align:center;padding:40px;color:var(--text-dim);">No hay clientes registrados aún. Agrega clientes para gestionar marcas independientes.</div>`;
      return;
    }

    clients.forEach(c => {
      const card = document.createElement("div");
      card.className = "card-panel";
      card.innerHTML = `
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px;">
          <img src="${c.logo_url || 'https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?w=100'}" style="width:48px;height:48px;border-radius:10px;object-fit:cover;border:1px solid var(--border);">
          <div>
            <h4 style="font-size:1rem;font-weight:700;">${escapeHtml(c.name)}</h4>
            <span style="font-size:0.75rem;color:var(--primary);font-weight:600;">${escapeHtml(c.industry)}</span>
          </div>
        </div>
        <p style="font-size:0.82rem;color:var(--text-muted);margin-bottom:16px;line-height:1.5;">${escapeHtml(c.notes || 'Espacio de trabajo activo para la gestión de contenidos.')}</p>
        <div style="display:flex;justify-content:space-between;align-items:center;border-top:1px solid var(--border);padding-top:12px;">
          <span style="font-size:0.75rem;color:var(--success);font-weight:700;">● ACTIVO</span>
          <button class="btn btn-secondary btn-sm" onclick="deleteClient(${c.id})">Eliminar</button>
        </div>
      `;
      container.appendChild(card);
    });
  } catch (e) {
    console.error(e);
  }
}

async function deleteClient(id) {
  if (!confirm("¿Eliminar este cliente y sus cuentas asociadas?")) return;
  try {
    await apiRequest(`/clients/${id}`, { method: "DELETE" });
    showToast("Cliente eliminado", "info");
    loadClients();
  } catch (e) {
    console.error(e);
  }
}

// 9. TEAM MEMBERS
async function loadTeam() {
  const tbody = document.getElementById("team-members-tbody");
  tbody.innerHTML = "<tr><td colspan='4'>Cargando equipo...</td></tr>";

  try {
    const members = await apiRequest("/team");
    tbody.innerHTML = "";

    members.forEach(m => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td style="padding:14px;font-weight:600;">${escapeHtml(m.full_name)}</td>
        <td style="padding:14px;color:var(--text-muted);">${escapeHtml(m.email)}</td>
        <td style="padding:14px;"><span class="status-badge status-published">${m.role}</span></td>
        <td style="padding:14px;text-align:right;">
          <button class="btn btn-danger btn-sm" onclick="removeMember(${m.id})">Remover</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (e) {
    console.error(e);
  }
}

async function removeMember(id) {
  if (!confirm("¿Remover a este miembro del equipo?")) return;
  try {
    await apiRequest(`/team/${id}`, { method: "DELETE" });
    showToast("Miembro removido", "info");
    loadTeam();
  } catch (e) {
    console.error(e);
  }
}

// 10. BILLING & PLANS
async function loadBilling() {
  try {
    const status = await apiRequest("/billing/status");
    const plans = await apiRequest("/billing/plans");

    document.getElementById("bill-current-plan").textContent = status.plan_name;
    document.getElementById("bill-sub-status").textContent = status.status.toUpperCase();

    document.getElementById("bill-acc-meter").textContent = `${status.social_accounts_used} / ${status.social_accounts_limit}`;
    document.getElementById("bill-posts-meter").textContent = `${status.posts_published_this_month} / ${status.posts_limit}`;
    document.getElementById("bill-ai-meter").textContent = `${status.ai_credits_used} / ${status.ai_credits_limit}`;

    const container = document.getElementById("billing-plans-cards");
    container.innerHTML = "";

    plans.forEach(p => {
      const isCurrent = p.code === status.plan_code;
      const card = document.createElement("div");
      card.className = "card-panel";
      card.style.border = isCurrent ? "2px solid var(--primary)" : "1px solid var(--border)";
      card.innerHTML = `
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
          <h3 style="font-size:1.15rem;font-weight:700;">${p.name}</h3>
          ${isCurrent ? '<span class="status-badge status-published">Plan Actual</span>' : ''}
        </div>
        <div style="margin-bottom:16px;">
          <span style="font-size:1.8rem;font-weight:800;">$${p.price_monthly}</span>
          <span style="font-size:0.8rem;color:var(--text-dim);"> / mes</span>
        </div>
        <ul style="list-style:none;margin-bottom:20px;display:flex;flex-direction:column;gap:8px;font-size:0.82rem;color:var(--text-muted);">
          ${(p.features || []).map(f => `<li>✓ ${escapeHtml(f)}</li>`).join('')}
        </ul>
        <button class="btn ${isCurrent ? 'btn-secondary' : 'btn-primary'}" style="width:100%;" ${isCurrent ? 'disabled' : ''} onclick="checkoutPlan('${p.code}')">
          ${isCurrent ? 'Activo' : 'Elegir Plan'}
        </button>
      `;
      container.appendChild(card);
    });
  } catch (e) {
    console.error(e);
  }
}

async function checkoutPlan(code) {
  try {
    const res = await apiRequest("/billing/checkout", {
      method: "POST",
      body: JSON.stringify({ plan_code: code, billing_cycle: "monthly" })
    });
    if (res.is_mock) {
      showToast("Plan activado en modo desarrollo.", "success");
      loadBilling();
    } else {
      window.location.href = res.checkout_url;
    }
  } catch (e) {
    console.error(e);
  }
}

// 11. SETTINGS
async function loadSettings() {
  try {
    const s = await apiRequest("/settings");
    document.getElementById("set-org-name").value = s.organization_name;
    document.getElementById("set-industry").value = s.industry;
    document.getElementById("set-language").value = s.language;
    document.getElementById("set-timezone").value = s.timezone;
    document.getElementById("set-auto-publish").checked = s.auto_publish_enabled;

    // Checks list
    const checksWrap = document.getElementById("settings-api-checks");
    checksWrap.innerHTML = `
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;font-size:0.85rem;">
        <div>Meta (Instagram/Facebook): <strong>${s.meta_configured ? 'Configurado' : 'Modo Sandbox'}</strong></div>
        <div>TikTok Content API: <strong>${s.tiktok_configured ? 'Configurado' : 'Modo Sandbox'}</strong></div>
        <div>YouTube / Google OAuth: <strong>${s.youtube_configured ? 'Configurado' : 'Modo Sandbox'}</strong></div>
        <div>OpenAI Content Studio: <strong>${s.openai_configured ? 'API Key Activa' : 'Generador Multilingüe Integrado'}</strong></div>
        <div>Stripe Billing: <strong>${s.stripe_configured ? 'Configurado' : 'Modo Sandbox'}</strong></div>
      </div>
    `;
  } catch (e) {
    console.error(e);
  }
}

async function saveSettingsForm(e) {
  if (e) e.preventDefault();
  const payload = {
    organization_name: document.getElementById("set-org-name").value,
    industry: document.getElementById("set-industry").value,
    language: document.getElementById("set-language").value,
    timezone: document.getElementById("set-timezone").value,
    auto_publish_enabled: document.getElementById("set-auto-publish").checked
  };

  try {
    await apiRequest("/settings", {
      method: "PUT",
      body: JSON.stringify(payload)
    });
    showToast("Configuración guardada", "success");
    loadSettings();
  } catch (err) {
    console.error(err);
  }
}

// MODALS & HELPERS
function openModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.add("open");
}

function closeModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove("open");
}

function openCreatePostModal(preset = {}) {
  document.getElementById("modal-post-title").value = preset.title || "";
  document.getElementById("modal-post-content").value = preset.content || "";
  document.getElementById("modal-post-datetime").value = "";
  document.getElementById("modal-post-approval").checked = true;

  // Platform selection
  const plat = preset.platform || "instagram";
  document.querySelectorAll(".post-plat-check").forEach(cb => {
    cb.checked = cb.value === plat || (preset.platforms && preset.platforms.includes(cb.value));
  });

  openModal("modal-create-post");
}

async function submitCreatePostForm(e) {
  if (e) e.preventDefault();
  const targetPlatforms = Array.from(document.querySelectorAll(".post-plat-check:checked")).map(c => c.value);
  if (targetPlatforms.length === 0) {
    showToast("Selecciona al menos una red social", "danger");
    return;
  }

  const payload = {
    title: document.getElementById("modal-post-title").value,
    content: document.getElementById("modal-post-content").value,
    target_platforms: targetPlatforms,
    scheduled_at: document.getElementById("modal-post-datetime").value || null,
    submit_for_approval: document.getElementById("modal-post-approval").checked
  };

  try {
    await apiRequest("/posts", {
      method: "POST",
      body: JSON.stringify(payload)
    });
    closeModal("modal-create-post");
    showToast("Publicación creada correctamente", "success");
    if (activeView === "queue") loadPublishingQueue();
    else if (activeView === "overview") loadOverview();
    else if (activeView === "calendar") loadCalendar();
  } catch (err) {
    console.error(err);
  }
}

function openManualConnectModal(platform) {
  document.getElementById("manual-conn-platform").value = platform;
  document.getElementById("manual-conn-user").value = "";
  document.getElementById("manual-conn-token").value = "";
  openModal("modal-manual-connect");
}

async function submitManualConnect(e) {
  if (e) e.preventDefault();
  const platform = document.getElementById("manual-conn-platform").value;
  const username = document.getElementById("manual-conn-user").value;
  const token = document.getElementById("manual-conn-token").value;

  try {
    await apiRequest("/social/connect-manual", {
      method: "POST",
      body: JSON.stringify({
        platform,
        platform_account_id: `${platform}_${Date.now()}`,
        username,
        display_name: username,
        access_token: token || `verified_token_${Date.now()}`
      })
    });
    closeModal("modal-manual-connect");
    showToast("Cuenta conectada con éxito", "success");
    loadSocialAccounts();
  } catch (err) {
    console.error(err);
  }
}

// MEDIA LIBRARY
let currentMediaFolder = "";

async function loadMediaLibrary(folder = "") {
  currentMediaFolder = folder;
  const container = document.getElementById("media-assets-grid");
  const countEl = document.getElementById("media-assets-count");
  if (!container) return;

  container.innerHTML = "<p>Cargando archivos multimedia...</p>";

  try {
    const url = folder ? `/media?folder=${encodeURIComponent(folder)}` : "/media";
    const assets = await apiRequest(url);
    container.innerHTML = "";

    if (countEl) countEl.textContent = `${assets.length} archivo(s)`;

    if (assets.length === 0) {
      container.innerHTML = `
        <div class="card-panel" style="grid-column:1/-1;text-align:center;padding:48px;color:var(--text-dim);">
          <div style="font-size:2.2rem;margin-bottom:12px;">📁</div>
          <h3>Biblioteca vacía</h3>
          <p style="font-size:0.85rem;margin-top:6px;">Sube imágenes, videos o logos para utilizarlos en tus publicaciones.</p>
        </div>
      `;
      return;
    }

    assets.forEach(a => {
      const card = document.createElement("div");
      card.className = "card-panel";
      card.style.padding = "12px";
      card.style.display = "flex";
      card.style.flexDirection = "column";
      card.style.justifyContent = "space-between";

      const isVideo = a.media_type === "video" || a.mime_type.startsWith("video/");
      const sizeMb = (a.file_size / (1024 * 1024)).toFixed(2);

      card.innerHTML = `
        <div>
          <div style="width:100%;height:140px;border-radius:8px;overflow:hidden;background:#050811;margin-bottom:10px;display:flex;align-items:center;justify-content:center;position:relative;">
            ${isVideo
              ? `<video src="${a.file_url}" style="width:100%;height:100%;object-fit:cover;"></video><span style="position:absolute;top:8px;right:8px;background:rgba(0,0,0,0.7);padding:2px 8px;border-radius:4px;font-size:0.7rem;font-weight:700;">VIDEO</span>`
              : `<img src="${a.file_url}" style="width:100%;height:100%;object-fit:cover;" onerror="this.src='https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=200'">`
            }
          </div>
          <h4 style="font-size:0.85rem;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:var(--text-main);" title="${escapeHtml(a.original_name)}">${escapeHtml(a.original_name)}</h4>
          <div style="display:flex;justify-content:space-between;font-size:0.72rem;color:var(--text-dim);margin:6px 0 12px;">
            <span>📁 ${escapeHtml(a.folder || 'General')}</span>
            <span>${sizeMb} MB</span>
          </div>
        </div>
        <div style="display:flex;gap:6px;">
          <button class="btn btn-primary btn-sm" style="flex:1;" onclick="useAssetInNewPost('${a.file_url}', ${a.id})">Usar en Post</button>
          <button class="btn btn-danger btn-sm" onclick="deleteMediaAsset(${a.id})">✕</button>
        </div>
      `;
      container.appendChild(card);
    });
  } catch (e) {
    console.error(e);
  }
}

function filterMediaFolder(folder) {
  loadMediaLibrary(folder);
}

async function submitUploadMedia(e) {
  e.preventDefault();
  const fileInput = document.getElementById("media-file-input");
  const folder = document.getElementById("media-upload-folder").value;
  const tags = document.getElementById("media-upload-tags").value;
  const submitBtn = document.getElementById("btn-submit-upload");

  if (!fileInput.files || !fileInput.files[0]) {
    showToast("Selecciona un archivo", "danger");
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);
  formData.append("folder", folder);
  formData.append("tags", tags);

  submitBtn.disabled = true;
  submitBtn.textContent = "Subiendo...";

  try {
    const res = await fetch("/api/v1/media/upload", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${authToken}`
      },
      body: formData
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Error al subir archivo");

    closeModal("modal-upload-media");
    fileInput.value = "";
    showToast("Archivo subido a la biblioteca", "success");
    loadMediaLibrary(currentMediaFolder);
  } catch (err) {
    showToast(err.message, "danger");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Subir Archivo";
  }
}

async function deleteMediaAsset(id) {
  if (!confirm("¿Eliminar este archivo de la biblioteca?")) return;
  try {
    await apiRequest(`/media/${id}`, { method: "DELETE" });
    showToast("Archivo eliminado", "info");
    loadMediaLibrary(currentMediaFolder);
  } catch (e) {
    console.error(e);
  }
}

function useAssetInNewPost(url, assetId) {
  openCreatePostModal({
    title: "",
    content: "¡Echa un vistazo a nuestra última actualización!",
    media_ids: [assetId]
  });
}

// LIVE MULTI-PLATFORM POST PREVIEWER (Metricool style)
let activePreviewPost = null;
let activeMockupPlatform = "instagram";

async function openPreviewPost(id) {
  try {
    activePreviewPost = await apiRequest(`/posts/${id}`);
    const platforms = activePreviewPost.target_platforms || ["instagram"];
    activeMockupPlatform = platforms[0] || "instagram";

    document.getElementById("preview-modal-title").textContent = activePreviewPost.title || "Vista Previa de Publicación";
    document.getElementById("preview-modal-status").innerHTML = `<span class="status-badge status-${activePreviewPost.status}">${activePreviewPost.status.replace('_', ' ')}</span>`;
    document.getElementById("preview-modal-footer-info").textContent = `Programado: ${activePreviewPost.scheduled_at ? formatDate(activePreviewPost.scheduled_at) : 'Inmediato'} • Autor: ${activePreviewPost.author_name || 'Equipo'}`;

    // Highlight active mockup tab
    document.querySelectorAll(".preview-tab-btn").forEach(btn => {
      btn.classList.toggle("active", btn.getAttribute("data-mockup") === activeMockupPlatform);
    });

    renderMockup(activePreviewPost, activeMockupPlatform);
    openModal("modal-preview-post");
  } catch (e) {
    console.error(e);
  }
}

function switchMockupPlatform(platform) {
  activeMockupPlatform = platform;
  document.querySelectorAll(".preview-tab-btn").forEach(btn => {
    btn.classList.toggle("active", btn.getAttribute("data-mockup") === platform);
  });
  if (activePreviewPost) {
    renderMockup(activePreviewPost, platform);
  }
}

function renderMockup(post, platform) {
  const container = document.getElementById("preview-mockup-container");
  if (!container) return;

  const mediaUrl = (post.media_urls && post.media_urls.length > 0)
    ? post.media_urls[0]
    : "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500";

  const safeContent = escapeHtml(post.content || "");

  if (platform === "instagram") {
    container.innerHTML = `
      <div style="background:#000;color:#fff;font-family:-apple-system,BlinkMacSystemFont,sans-serif;">
        <!-- IG Header -->
        <div style="display:flex;align-items:center;justify-content:space-between;padding:10px 14px;">
          <div style="display:flex;align-items:center;gap:10px;">
            <div style="width:34px;height:34px;border-radius:50%;background:linear-gradient(45deg,#f09433,#e6683c,#dc2743,#cc2366,#bc1888);padding:2px;">
              <img src="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=100" style="width:100%;height:100%;border-radius:50%;object-fit:cover;border:2px solid #000;">
            </div>
            <div>
              <span style="font-weight:700;font-size:0.82rem;">nuviogrowth_official</span>
              <span style="color:#0095f6;font-size:0.75rem;margin-left:4px;">● Seguir</span>
            </div>
          </div>
          <span style="color:#8e8e8e;font-size:1.1rem;">•••</span>
        </div>
        <!-- Media Box -->
        <div style="width:100%;aspect-ratio:1/1;background:#111;overflow:hidden;">
          <img src="${mediaUrl}" style="width:100%;height:100%;object-fit:cover;">
        </div>
        <!-- Actions bar -->
        <div style="padding:10px 14px;">
          <div style="display:flex;justify-content:space-between;font-size:1.2rem;margin-bottom:8px;">
            <div style="display:flex;gap:14px;">
              <span>❤️</span><span>💬</span><span>🚀</span>
            </div>
            <span>🔖</span>
          </div>
          <div style="font-weight:700;font-size:0.8rem;margin-bottom:6px;">1,420 Me gusta</div>
          <div style="font-size:0.82rem;line-height:1.5;">
            <span style="font-weight:700;">nuviogrowth_official</span> ${safeContent}
          </div>
          <div style="color:#8e8e8e;font-size:0.72rem;margin-top:6px;text-transform:uppercase;">Hace 2 horas</div>
        </div>
      </div>
    `;
  } else if (platform === "tiktok") {
    container.innerHTML = `
      <div style="position:relative;background:#000;color:#fff;aspect-ratio:9/16;max-height:480px;margin:0 auto;overflow:hidden;border-radius:8px;">
        <img src="${mediaUrl}" style="width:100%;height:100%;object-fit:cover;opacity:0.85;">
        <!-- Side action bar -->
        <div style="position:absolute;right:10px;bottom:70px;display:flex;flex-direction:column;align-items:center;gap:16px;">
          <div style="width:40px;height:40px;border-radius:50%;border:2px solid #fff;overflow:hidden;"><img src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100" style="width:100%;height:100%;object-fit:cover;"></div>
          <div style="display:flex;flex-direction:column;align-items:center;font-size:0.75rem;"><span style="font-size:1.4rem;">❤️</span>48.2K</div>
          <div style="display:flex;flex-direction:column;align-items:center;font-size:0.75rem;"><span style="font-size:1.4rem;">💬</span>1,420</div>
          <div style="display:flex;flex-direction:column;align-items:center;font-size:0.75rem;"><span style="font-size:1.4rem;">🔖</span>3,910</div>
          <div style="display:flex;flex-direction:column;align-items:center;font-size:0.75rem;"><span style="font-size:1.4rem;">↪️</span>890</div>
        </div>
        <!-- Bottom overlay -->
        <div style="position:absolute;left:12px;bottom:16px;right:60px;">
          <div style="font-weight:700;font-size:0.88rem;margin-bottom:4px;">@nuviogrowth_tips</div>
          <div style="font-size:0.78rem;line-height:1.4;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;">${safeContent}</div>
          <div style="font-size:0.7rem;color:#ddd;margin-top:6px;">🎵 Sonido original - Nuvio Growth Sound</div>
        </div>
      </div>
    `;
  } else if (platform === "facebook") {
    container.innerHTML = `
      <div style="background:#242526;color:#e4e6eb;font-family:-apple-system,sans-serif;padding:12px;border-radius:8px;">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
          <img src="https://images.unsplash.com/photo-1557804506-669a67965ba0?w=100" style="width:40px;height:40px;border-radius:50%;">
          <div>
            <div style="font-weight:700;font-size:0.85rem;color:#e4e6eb;">Nuvio Growth Platform <span style="color:#2e89ff;">✔</span></div>
            <div style="font-size:0.72rem;color:#b0b3b8;">Publicado recientemente • 🌐 Público</div>
          </div>
        </div>
        <div style="font-size:0.85rem;line-height:1.5;margin-bottom:10px;">${safeContent}</div>
        <div style="border-radius:6px;overflow:hidden;background:#000;margin-bottom:10px;">
          <img src="${mediaUrl}" style="width:100%;max-height:220px;object-fit:cover;">
        </div>
        <div style="display:flex;justify-content:space-between;font-size:0.75rem;color:#b0b3b8;border-bottom:1px solid #3e4042;padding-bottom:8px;">
          <span>👍❤️ 842</span>
          <span>114 comentarios • 58 veces compartido</span>
        </div>
        <div style="display:flex;justify-content:space-around;padding-top:8px;font-size:0.8rem;color:#b0b3b8;font-weight:600;">
          <span>👍 Me gusta</span><span>💬 Comentar</span><span>↪️ Compartir</span>
        </div>
      </div>
    `;
  } else {
    // YouTube
    container.innerHTML = `
      <div style="background:#0f0f0f;color:#f1f1f1;font-family:Roboto,sans-serif;border-radius:8px;overflow:hidden;">
        <div style="position:relative;width:100%;aspect-ratio:16/9;background:#000;">
          <img src="${mediaUrl}" style="width:100%;height:100%;object-fit:cover;">
          <span style="position:absolute;bottom:8px;right:8px;background:rgba(0,0,0,0.8);font-size:0.72rem;padding:2px 6px;border-radius:4px;font-weight:700;">12:45</span>
        </div>
        <div style="padding:12px;display:flex;gap:12px;">
          <img src="https://images.unsplash.com/photo-1570295999919-56ceb5ecca61?w=100" style="width:36px;height:36px;border-radius:50%;">
          <div>
            <h4 style="font-size:0.9rem;font-weight:600;margin-bottom:4px;line-height:1.4;">${escapeHtml(post.title || safeContent.slice(0, 50))}</h4>
            <div style="font-size:0.75rem;color:#aaa;">Nuvio AI Growth Academy • 22.4K suscriptores</div>
            <div style="font-size:0.72rem;color:#aaa;margin-top:2px;">18K vistas • hace 1 día</div>
          </div>
        </div>
      </div>
    `;
  }
}

function renderPlatformPills(platforms) {
  if (!platforms || !platforms.length) return `<span class="platform-pill pill-instagram">General</span>`;
  return platforms.map(p => `<span class="platform-pill pill-${p}">${p}</span>`).join(" ");
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/[&<>'"]/g, tag => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    "'": '&#39;',
    '"': '&quot;'
  }[tag] || tag));
}

function formatDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleString("es-ES", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

// Initial Bootstrap
window.addEventListener("DOMContentLoaded", async () => {
  // Mobile menu toggle
  const mobileBtn = document.getElementById("mobileMenuBtn");
  if (mobileBtn) {
    mobileBtn.addEventListener("click", () => {
      document.querySelector(".sidebar").classList.toggle("mobile-open");
    });
  }

  // Language selector
  if (langSelect) {
    langSelect.value = currentLang;
    langSelect.addEventListener("change", (e) => {
      currentLang = e.target.value;
      localStorage.setItem("nuvio_lang", currentLang);
      location.reload();
    });
  }

  // Nav item click listener
  document.querySelectorAll(".nav-item").forEach(item => {
    item.addEventListener("click", () => {
      const v = item.getAttribute("data-view");
      if (v) switchView(v);
    });
  });

  // Verify or auto-authenticate
  if (!authToken) {
    await autoLogin();
  } else {
    await loadCurrentUser();
  }

  // Handle URL hash router
  const hash = window.location.hash.replace("#", "") || "overview";
  switchView(hash);
});

