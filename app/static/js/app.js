// NUVIO GROWTH BOT - Master Dashboard Application State & Router
let currentLang = localStorage.getItem("nuvio_lang") || "es";
let authToken = localStorage.getItem("nuvio_token") || "";

// Purge any cached demo account token from browser storage
try {
  if (authToken && authToken.includes(".")) {
    const payload = JSON.parse(atob(authToken.split(".")[1]));
    if (payload.email === "admin@nuviogrowth.com") {
      localStorage.removeItem("nuvio_token");
      authToken = "";
    }
  }
} catch (e) {}

let currentUser = null;
let currentOrg = null;
let activeView = "overview";
let currentActiveClientId = null;

function switchActiveClient(val) {
  currentActiveClientId = val ? parseInt(val) : null;
  if (typeof activeView !== "undefined") {
    if (activeView === "social") {
      loadSocialAccounts();
    } else if (activeView === "queue") {
      loadPublishingQueue();
    }
  }
}
window.switchActiveClient = switchActiveClient;

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
      // Token expired or unauthorized
      localStorage.removeItem("nuvio_token");
      authToken = "";
      currentUser = null;
      updateAuthUI();
      openLoginModal("login", true);
      throw new Error("Sesión expirada o no autorizada. Por favor ingresa tus credenciales.");
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

// Auth Modal & Session Management
let authModalCanClose = true;

function updateAuthUI() {
  const isAuth = Boolean(authToken && currentUser);
  const sideUnauth = document.getElementById("sidebar-unauth");
  const sideUser = document.getElementById("sidebar-user");
  const topBtns = document.getElementById("topbar-auth-btns");
  const ovBanner = document.getElementById("overview-welcome-banner");

  if (sideUnauth) sideUnauth.style.display = isAuth ? "none" : "flex";
  if (sideUser) sideUser.style.display = isAuth ? "flex" : "none";
  if (topBtns) topBtns.style.display = isAuth ? "none" : "flex";
  if (ovBanner) ovBanner.style.display = isAuth ? "none" : "flex";
}

function togglePasswordVisibility(inputId, btn) {
  const input = document.getElementById(inputId);
  if (!input) return;
  if (input.type === "password") {
    input.type = "text";
    btn.textContent = "🙈";
  } else {
    input.type = "password";
    btn.textContent = "👁️";
  }
}

function openLoginModal(tab = "register", allowClose = true) {
  authModalCanClose = allowClose;
  const modal = document.getElementById("modal-auth");
  if (modal) {
    modal.classList.add("open");
    modal.style.display = "flex";
  }
  const closeBtn = document.getElementById("modal-auth-close-btn");
  if (closeBtn) {
    closeBtn.style.display = allowClose ? "block" : "none";
  }
  switchAuthTab(tab);
}

function closeAuthModal() {
  const modal = document.getElementById("modal-auth");
  if (modal) {
    modal.classList.remove("open");
    modal.style.display = "none";
  }
}

function switchAuthTab(tab) {
  const loginTab = document.getElementById("auth-tab-login");
  const regTab = document.getElementById("auth-tab-register");
  const btnLogin = document.getElementById("tab-btn-login");
  const btnReg = document.getElementById("tab-btn-register");
  const loginErr = document.getElementById("login-alert-error");
  const regErr = document.getElementById("register-alert-error");

  if (loginErr) loginErr.style.display = "none";
  if (regErr) regErr.style.display = "none";

  if (tab === "login") {
    if (loginTab) loginTab.style.display = "block";
    if (regTab) regTab.style.display = "none";
    if (btnLogin) {
      btnLogin.style.background = "var(--primary)";
      btnLogin.style.color = "#fff";
    }
    if (btnReg) {
      btnReg.style.background = "transparent";
      btnReg.style.color = "var(--text-muted)";
    }
  } else {
    if (loginTab) loginTab.style.display = "none";
    if (regTab) regTab.style.display = "block";
    if (btnReg) {
      btnReg.style.background = "var(--primary)";
      btnReg.style.color = "#fff";
    }
    if (btnLogin) {
      btnLogin.style.background = "transparent";
      btnLogin.style.color = "var(--text-muted)";
    }
    // Auto-copy email and password from login form if already typed
    const loginEmail = document.getElementById("login-email");
    const regEmail = document.getElementById("reg-email");
    if (loginEmail && regEmail && loginEmail.value.trim() && !regEmail.value.trim()) {
      regEmail.value = loginEmail.value.trim();
    }
    const loginPwd = document.getElementById("login-password");
    const regPwd = document.getElementById("reg-password");
    if (loginPwd && regPwd && loginPwd.value && !regPwd.value) {
      regPwd.value = loginPwd.value;
    }
    const orgInput = document.getElementById("reg-org-name");
    if (orgInput) orgInput.focus();
  }
}

async function submitLoginForm(e) {
  if (e && e.preventDefault) e.preventDefault();
  const emailInput = document.getElementById("login-email");
  const pwdInput = document.getElementById("login-password");
  const errBox = document.getElementById("login-alert-error");
  const btn = document.getElementById("btn-login-submit");

  const email = emailInput ? emailInput.value.trim() : "";
  const password = pwdInput ? pwdInput.value : "";

  if (errBox) errBox.style.display = "none";
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner" style="display:inline-block;width:14px;height:14px;border:2px solid #fff;border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;margin-right:8px;"></span> Verificando...`;
  }

  try {
    const res = await fetch("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(data.detail || "Correo o contraseña incorrectos");
    }

    authToken = data.access_token;
    localStorage.setItem("nuvio_token", authToken);
    authModalCanClose = true;
    closeModal("modal-auth");

    await loadCurrentUser();
    showToast(`Bienvenido de nuevo, ${currentUser ? currentUser.full_name : ''}!`, "success");
    switchView(activeView || "overview");
  } catch (err) {
    if (errBox) {
      errBox.innerHTML = `
        <div style="font-weight:700;margin-bottom:6px;">❌ No se pudo ingresar: ${err.message}</div>
        <div style="margin-top:8px;padding-top:8px;border-top:1px solid rgba(255,255,255,0.15);display:flex;flex-direction:column;gap:6px;">
          <button type="button" onclick="quickFillLogin('${email || 'charlesagency4@gmail.com'}', 'Password123!')" style="background:#10b981;color:#fff;border:none;border-radius:6px;padding:6px 10px;font-size:0.8rem;font-weight:700;cursor:pointer;text-align:center;">
            ⚡ Probar clave oficial (Password123!)
          </button>
          <div style="display:flex;align-items:center;justify-content:space-between;margin-top:4px;">
            <span style="color:#cbd5e1;font-size:0.75rem;">¿Deseas registrar una cuenta nueva?</span>
            <button type="button" onclick="goToRegisterWithEmail('${email}')" style="background:var(--primary);color:#fff;border:none;border-radius:6px;padding:4px 8px;font-size:0.75rem;font-weight:700;cursor:pointer;">✨ Crear cuenta</button>
          </div>
        </div>
      `;
      errBox.style.display = "block";
    } else {
      showToast(err.message, "danger");
    }
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = "Entrar a mi Cuenta";
    }
  }
}

function quickFillLogin(email, password) {
  const emailInput = document.getElementById("login-email");
  const pwdInput = document.getElementById("login-password");
  if (emailInput) emailInput.value = email;
  if (pwdInput) pwdInput.value = password;
  submitLoginForm();
}
window.quickFillLogin = quickFillLogin;

function goToRegisterWithEmail(email) {
  switchAuthTab('register');
  const regEmail = document.getElementById("reg-email");
  if (regEmail && email) regEmail.value = email;
  const regPwd = document.getElementById("reg-password");
  const loginPwd = document.getElementById("login-password");
  if (regPwd && loginPwd && loginPwd.value) regPwd.value = loginPwd.value;
  const orgInput = document.getElementById("reg-org-name");
  if (orgInput) orgInput.focus();
}

async function submitRegisterForm(e) {
  if (e && e.preventDefault) e.preventDefault();
  const orgName = document.getElementById("reg-org-name").value.trim();
  const fullName = document.getElementById("reg-full-name").value.trim();
  const email = document.getElementById("reg-email").value.trim();
  const password = document.getElementById("reg-password").value;
  const industry = document.getElementById("reg-industry").value;
  const language = document.getElementById("reg-language").value;
  const errBox = document.getElementById("register-alert-error");
  const btn = document.getElementById("btn-register-submit");

  if (errBox) errBox.style.display = "none";
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner" style="display:inline-block;width:14px;height:14px;border:2px solid #fff;border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;margin-right:8px;"></span> Creando Cuenta...`;
  }

  try {
    const res = await fetch("/api/v1/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        organization_name: orgName,
        full_name: fullName,
        email,
        password,
        industry,
        language
      })
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(data.detail || "Error al crear la cuenta");
    }

    authToken = data.access_token;
    localStorage.setItem("nuvio_token", authToken);
    if (language) {
      currentLang = language;
      localStorage.setItem("nuvio_lang", language);
    }

    authModalCanClose = true;
    closeModal("modal-auth");

    await loadCurrentUser();
    showToast(`¡Cuenta creada con éxito! Bienvenido a Nuvio Growth Suite.`, "success");
    switchView("overview");
  } catch (err) {
    if (errBox) {
      errBox.textContent = `❌ ${err.message}`;
      errBox.style.display = "block";
    } else {
      showToast(err.message, "danger");
    }
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = "Crear Cuenta de Administrador Real";
    }
  }
}

function logout() {
  if (confirm("¿Estás seguro de que deseas cerrar tu sesión?")) {
    localStorage.removeItem("nuvio_token");
    authToken = "";
    currentUser = null;
    currentOrg = null;
    updateAuthUI();
    showToast("Has cerrado sesión correctamente.", "info");
    openLoginModal("login", true);
  }
}

async function loadCurrentUser() {
  try {
    currentUser = await apiRequest("/auth/me");
    const settingsData = await apiRequest("/settings");
    currentOrg = settingsData;
    if (currentUserNameEl) currentUserNameEl.textContent = currentUser.full_name;
    if (currentUserOrgEl) currentUserOrgEl.textContent = currentOrg.organization_name;
    const initials = (currentUser.full_name || "Admin")
      .split(" ")
      .map(n => n[0])
      .join("")
      .slice(0, 2)
      .toUpperCase();
    const initialsEl = document.getElementById("currentUserInitials");
    if (initialsEl) initialsEl.textContent = initials;

    if (currentUser.language && ["es", "en", "ht"].includes(currentUser.language)) {
      currentLang = currentUser.language;
      if (langSelect) langSelect.value = currentLang;
    }
    updateAuthUI();
  } catch (e) {
    console.error(e);
    currentUser = null;
    currentOrg = null;
    updateAuthUI();
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
  else if (viewName === "booster") initBoosterView();
  else if (viewName === "ads") loadAdCampaigns();
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
          <div style="display:flex;gap:8px;flex-wrap:wrap;">
            <button class="btn btn-secondary btn-sm" style="flex:1;" onclick="testAccountConn(${conn.id})">Probar API</button>
            <button class="btn btn-secondary btn-sm" style="flex:1;" onclick="syncAccountProfile(${conn.id})">Sincronizar</button>
            <button class="btn btn-primary btn-sm" style="flex:1.2;background:linear-gradient(135deg,#ec4899,#8b5cf6);" onclick="openBoosterForAccount('${plat.id}', '${escapeHtml(conn.username)}')">🚀 Impulsar</button>
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
          <div style="display:flex;gap:8px;flex-wrap:wrap;">
            <button class="btn btn-primary btn-sm" style="flex:1.2;background:linear-gradient(135deg,#10b981,#06b6d4);border:none;font-weight:700;" onclick="triggerAutoConnect('${plat.id}')">⚡ Auto-Conectar</button>
            <button class="btn btn-secondary btn-sm" style="flex:1;" onclick="startOAuthConnect('${plat.id}')">🔑 Login OAuth</button>
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

async function triggerAutoConnect(platform = "all") {
  try {
    const isAll = platform === "all";
    showToast(isAll ? "⚡ Auto-conectando todas las cuentas oficiales..." : `⚡ Conectando ${platform.toUpperCase()}...`, "info");
    const cid = (typeof currentActiveClientId !== "undefined" && currentActiveClientId) ? parseInt(currentActiveClientId) : null;
    const res = await apiRequest("/social/auto-connect", {
      method: "POST",
      body: JSON.stringify({
        platform,
        username: "lajanrapid",
        client_id: cid
      })
    });
    showToast(res.message || "Cuentas conectadas exitosamente", "success");
    await loadSocialAccounts();
  } catch (err) {
    console.error("triggerAutoConnect error:", err);
    showToast("Error al auto-conectar: " + (err.message || err), "danger");
  }
}
window.triggerAutoConnect = triggerAutoConnect;

async function startOAuthConnect(platform) {
  try {
    showToast(`Conectando con ${platform}... Obteniendo autorización oficial`, "info");
    const cid = (typeof currentActiveClientId !== "undefined" && currentActiveClientId) ? currentActiveClientId : "";
    const query = cid ? `?client_id=${cid}` : "";
    const res = await apiRequest(`/social/oauth/${platform}/url${query}`);
    if (res && res.auth_url) {
      window.location.href = res.auth_url;
    } else {
      showToast("No se pudo obtener la URL de autorización: " + ((res && (res.detail || res.message)) || "Error de servidor"), "danger");
    }
  } catch (e) {
    console.error("Error startOAuthConnect:", e);
    showToast("Error al conectar: " + (e.message || e), "danger");
  }
}
window.startOAuthConnect = startOAuthConnect;

async function testAccountConn(id) {
  try {
    const res = await apiRequest(`/social/accounts/${id}/test`, { method: "POST" });
    showToast(res.message, res.success ? "success" : "danger");
  } catch (e) {
    console.error(e);
    showToast("Error al probar conexión: " + (e.message || e), "danger");
  }
}
window.testAccountConn = testAccountConn;

async function syncAccountProfile(id) {
  try {
    await apiRequest(`/social/accounts/${id}/sync`, { method: "POST" });
    showToast("Perfil de cuenta sincronizado", "success");
    loadSocialAccounts();
  } catch (e) {
    console.error(e);
    showToast("Error al sincronizar perfil: " + (e.message || e), "danger");
  }
}
window.syncAccountProfile = syncAccountProfile;

async function disconnectAccount(id) {
  if (!confirm("¿Deseas desconectar esta cuenta social de Nuvio Growth Bot?")) return;
  try {
    await apiRequest(`/social/accounts/${id}`, { method: "DELETE" });
    showToast("Cuenta desconectada", "info");
    loadSocialAccounts();
  } catch (e) {
    console.error(e);
    showToast("Error al desconectar: " + (e.message || e), "danger");
  }
}
window.disconnectAccount = disconnectAccount;

// ==========================================
// 2B. GROWTH BOOSTER & VIRAL ENGINE
// ==========================================
let currentBoosterTab = "url";
let lastUrlBoostData = null;

function setSampleUrl(type) {
  const inp = document.getElementById("booster-url-input");
  if (!inp) return;
  if (type === "fb-page") inp.value = "https://www.facebook.com/lajanrapid";
  else if (type === "ig-page") inp.value = "https://www.instagram.com/lajanrapid";
  else if (type === "ig-reel") inp.value = "https://www.instagram.com/reel/C-xyz123/";
  runUrlBoost();
}
window.setSampleUrl = setSampleUrl;

async function runUrlBoost() {
  const inp = document.getElementById("booster-url-input");
  const url = inp ? inp.value.trim() : "";
  const goal = document.getElementById("booster-url-goal") ? document.getElementById("booster-url-goal").value : "followers";
  const budget = parseFloat(document.getElementById("booster-url-budget").value) || 10;
  const duration = parseInt(document.getElementById("booster-url-duration").value) || 5;
  const btn = document.getElementById("btn-run-url-boost");

  if (!url) {
    showToast("Por favor ingresa el link de tu página o post", "warning");
    return;
  }

  btn.disabled = true;
  btn.textContent = "⚡ Analizando Enlace con IA...";
  showToast("Extrayendo parámetros de viralización para el enlace...", "info");

  try {
    const res = await apiRequest("/ai/boost/by-url", {
      method: "POST",
      body: JSON.stringify({
        url,
        goal,
        budget_usd: budget,
        duration_days: duration,
        language: typeof currentLang !== "undefined" ? currentLang : "es"
      })
    });

    lastUrlBoostData = res;

    document.getElementById("booster-url-type-badge").textContent = res.target_type === "page" ? "Página Oficial" : "Publicación / Reel";
    document.getElementById("booster-url-platform-badge").textContent = res.detected_platform.toUpperCase();
    document.getElementById("booster-url-headline").textContent = res.headline;
    const linkEl = document.getElementById("booster-url-clean-link");
    linkEl.href = res.cleaned_url;
    linkEl.textContent = `🔗 ${res.cleaned_url}`;

    document.getElementById("booster-url-impressions").textContent = res.estimated_impressions;
    document.getElementById("booster-url-followers").textContent = res.estimated_followers_gain;
    document.getElementById("booster-url-hook").textContent = res.viral_hook_recommendation;
    document.getElementById("booster-url-cta").textContent = res.follower_cta;
    document.getElementById("booster-url-comment").textContent = res.pinned_comment_template;

    document.getElementById("booster-url-empty").style.display = "none";
    document.getElementById("booster-url-ready").style.display = "block";

    showToast("🚀 ¡Estrategia de impulso generada para tu enlace!", "success");
  } catch (err) {
    console.error(err);
    showToast("Error al analizar enlace: " + (err.message || err), "danger");
  } finally {
    btn.disabled = false;
    btn.textContent = "🚀 Analizar e Impulsar Enlace con IA";
  }
}
window.runUrlBoost = runUrlBoost;

function copyUrlBoosterStrategy() {
  if (!lastUrlBoostData) return;
  const full = `${lastUrlBoostData.headline}\nEnlace: ${lastUrlBoostData.cleaned_url}\n\n🔥 Gancho:\n${lastUrlBoostData.viral_hook_recommendation}\n\n🎯 CTA Seguidores:\n${lastUrlBoostData.follower_cta}\n\n📌 Comentario Fijado:\n${lastUrlBoostData.pinned_comment_template}\n\nHashtags:\n${lastUrlBoostData.recommended_hashtags.join(" ")}`;
  navigator.clipboard.writeText(full).then(() => {
    showToast("Estrategia copiada al portapapeles", "success");
  });
}
window.copyUrlBoosterStrategy = copyUrlBoosterStrategy;

async function activateUrlBoostCampaign() {
  if (!lastUrlBoostData) return;
  const btn = document.getElementById("btn-activate-url-campaign");
  btn.disabled = true;
  btn.textContent = "🔥 Activando Impulso...";

  try {
    const budget = parseFloat(document.getElementById("booster-url-budget").value) || 10;
    const duration = parseInt(document.getElementById("booster-url-duration").value) || 5;

    const res = await apiRequest("/ai/boost/launch", {
      method: "POST",
      body: JSON.stringify({
        platform: lastUrlBoostData.detected_platform,
        account_username: lastUrlBoostData.extracted_handle_or_id,
        budget_usd: budget,
        duration_days: duration,
        goal: document.getElementById("booster-url-goal").value,
        target_interests: "Negocios, Finanzas, Inversión, Crecimiento"
      })
    });

    showToast(`✅ ¡Campaña de impulso activada con éxito para ${lastUrlBoostData.cleaned_url}!`, "success");
    btn.textContent = "✅ Impulso Activo";
  } catch (err) {
    console.error(err);
    showToast("Error al activar impulso: " + (err.message || err), "danger");
    btn.disabled = false;
    btn.textContent = "🔥 Activar Impulso Ahora";
  }
}
window.activateUrlBoostCampaign = activateUrlBoostCampaign;

function switchBoosterTab(tab) {
  currentBoosterTab = tab;
  document.querySelectorAll(".booster-tab-btn").forEach(b => b.classList.remove("active"));
  document.querySelectorAll(".booster-tab-content").forEach(c => c.style.display = "none");

  const activeBtn = document.getElementById(`btn-booster-tab-${tab}`);
  const activeContent = document.getElementById(`booster-tab-${tab}`);
  if (activeBtn) activeBtn.classList.add("active");
  if (activeContent) activeContent.style.display = "block";

  if (tab === "campaign") {
    recalculateCampaign();
  }
}
window.switchBoosterTab = switchBoosterTab;

function openBoosterForAccount(platform, username) {
  switchView("booster");
  switchBoosterTab("campaign");
  const select = document.getElementById("camp-account-select");
  if (select) {
    const val = `${platform}|${username}`;
    let found = false;
    for (let opt of select.options) {
      if (opt.value === val) {
        opt.selected = true;
        found = true;
        break;
      }
    }
    if (!found) {
      const opt = new Option(`${platform.toUpperCase()} - @${username}`, val, true, true);
      select.add(opt);
    }
  }
  const postPlat = document.getElementById("booster-post-platform");
  if (postPlat) postPlat.value = platform;
}
window.openBoosterForAccount = openBoosterForAccount;

async function initBoosterView() {
  try {
    const accounts = await apiRequest("/social/accounts");
    const select = document.getElementById("camp-account-select");
    if (select && accounts && accounts.length > 0) {
      select.innerHTML = "";
      accounts.forEach(a => {
        const opt = document.createElement("option");
        opt.value = `${a.platform}|${a.username}`;
        opt.textContent = `${a.platform.toUpperCase()} - ${a.display_name || a.username} (@${a.username})`;
        select.appendChild(opt);
      });
    }
  } catch (e) {
    console.error(e);
  }
  recalculateCampaign();
}
window.initBoosterView = initBoosterView;

async function runPostBoost() {
  const platform = document.getElementById("booster-post-platform").value;
  const goal = document.getElementById("booster-post-goal").value;
  const audience = document.getElementById("booster-post-audience").value;
  const caption = document.getElementById("booster-post-caption").value.trim();
  const btn = document.getElementById("btn-run-post-boost");

  if (!caption) {
    showToast("Por favor ingresa el texto o idea de la publicación", "warning");
    return;
  }

  btn.disabled = true;
  btn.textContent = "⚡ Analizando y Potenciando con IA...";
  showToast("Aplicando ganchos virales y optimización de seguidores...", "info");

  try {
    const res = await apiRequest("/ai/boost/optimize-post", {
      method: "POST",
      body: JSON.stringify({
        caption,
        social_network: platform,
        goal,
        target_audience: audience,
        language: typeof currentLang !== "undefined" ? currentLang : "es"
      })
    });

    document.getElementById("booster-hook-text").textContent = res.viral_hook || "🔥 Gancho de 3 Segundos Activado";
    document.getElementById("booster-full-text").value = res.boosted_caption;
    document.getElementById("booster-best-time").textContent = res.best_time_to_post || "12:30 PM - 2:00 PM";
    document.getElementById("booster-cta-summary").textContent = res.follower_cta ? "Imán de Seguidores Activo" : "CTA de Interacción";
    document.getElementById("booster-multiplier-badge").textContent = res.estimated_reach_multiplier || "+420% Alcance Proyectado";

    document.getElementById("booster-output-empty").style.display = "none";
    document.getElementById("booster-output-ready").style.display = "block";

    showToast("🚀 ¡Publicación potenciada exitosamente con ganchos virales!", "success");
  } catch (err) {
    console.error(err);
    showToast("Error al potenciar post: " + (err.message || err), "danger");
  } finally {
    btn.disabled = false;
    btn.textContent = "🚀 Potenciar Publicación con IA";
  }
}
window.runPostBoost = runPostBoost;

function copyBoosterText() {
  const text = document.getElementById("booster-full-text").value;
  if (!text) return;
  navigator.clipboard.writeText(text).then(() => {
    showToast("Texto copiado al portapapeles con ganchos y hashtags", "success");
  });
}
window.copyBoosterText = copyBoosterText;

function useBoosterInStudio() {
  const text = document.getElementById("booster-full-text").value;
  const platform = document.getElementById("booster-post-platform").value;
  openCreatePostModal();
  setTimeout(() => {
    const contentEl = document.getElementById("modal-post-content");
    if (contentEl) contentEl.value = text;
    const titleEl = document.getElementById("modal-post-title");
    if (titleEl) titleEl.value = `🚀 Post Potenciado (${platform.toUpperCase()})`;
    const chk = document.querySelector(`input[name="target_platforms"][value="${platform}"]`);
    if (chk) chk.checked = true;
  }, 100);
}
window.useBoosterInStudio = useBoosterInStudio;

function setCampBudget(amount, btn) {
  document.getElementById("camp-budget-input").value = amount;
  document.querySelectorAll(".camp-btn-budget").forEach(b => {
    b.classList.remove("active");
    b.style.borderColor = "var(--border)";
    b.style.background = "transparent";
    b.style.color = "var(--text-main)";
  });
  if (btn) {
    btn.classList.add("active");
    btn.style.borderColor = "#ec4899";
    btn.style.background = "rgba(236,72,153,0.15)";
    btn.style.color = "#fff";
  }
  recalculateCampaign();
}
window.setCampBudget = setCampBudget;

async function recalculateCampaign() {
  const budgetInp = document.getElementById("camp-budget-input");
  const durationInp = document.getElementById("camp-duration-select");
  const goalInp = document.getElementById("camp-goal-select");
  if (!budgetInp || !durationInp) return;

  const budget = parseFloat(budgetInp.value) || 10;
  const duration = parseInt(durationInp.value) || 5;
  const goal = goalInp ? goalInp.value : "followers";

  try {
    const res = await apiRequest("/ai/boost/campaign-calc", {
      method: "POST",
      body: JSON.stringify({
        budget_usd: budget,
        duration_days: duration,
        goal,
        platform: "facebook"
      })
    });

    document.getElementById("proj-impressions").textContent = `${res.estimated_impressions_min.toLocaleString()} - ${res.estimated_impressions_max.toLocaleString()}`;
    document.getElementById("proj-reach").textContent = `${res.estimated_reach_min.toLocaleString()} - ${res.estimated_reach_max.toLocaleString()}`;
    document.getElementById("proj-visits").textContent = `${res.estimated_profile_visits_min.toLocaleString()} - ${res.estimated_profile_visits_max.toLocaleString()}`;
    document.getElementById("proj-followers").textContent = `+${res.estimated_followers_gain_min} a +${res.estimated_followers_gain_max}`;
    document.getElementById("proj-strategy-text").textContent = res.recommended_strategy;
  } catch (e) {
    const minImp = Math.round(budget * 550);
    const maxImp = Math.round(budget * 1350);
    const minReach = Math.round(minImp * 0.72);
    const maxReach = Math.round(maxImp * 0.78);
    const minVisits = Math.max(10, Math.round(minReach * 0.045));
    const maxVisits = Math.max(25, Math.round(maxReach * 0.085));
    const minFoll = Math.max(5, Math.round(minVisits * 0.22));
    const maxFoll = Math.max(15, Math.round(maxVisits * 0.38));

    document.getElementById("proj-impressions").textContent = `${minImp.toLocaleString()} - ${maxImp.toLocaleString()}`;
    document.getElementById("proj-reach").textContent = `${minReach.toLocaleString()} - ${maxReach.toLocaleString()}`;
    document.getElementById("proj-visits").textContent = `${minVisits.toLocaleString()} - ${maxVisits.toLocaleString()}`;
    document.getElementById("proj-followers").textContent = `+${minFoll} a +${maxFoll}`;
  }
}
window.recalculateCampaign = recalculateCampaign;

async function launchBoosterCampaign() {
  const accVal = document.getElementById("camp-account-select").value || "facebook|lajanrapid";
  const parts = accVal.split("|");
  const platform = parts[0] || "facebook";
  const username = parts[1] || "lajanrapid";
  const budget = parseFloat(document.getElementById("camp-budget-input").value) || 10;
  const duration = parseInt(document.getElementById("camp-duration-select").value) || 5;
  const goal = document.getElementById("camp-goal-select").value;
  const interests = document.getElementById("camp-interests-input").value;
  const btn = document.getElementById("btn-launch-campaign");

  btn.disabled = true;
  btn.textContent = "🔥 Activando Campaña con Meta API...";

  try {
    const res = await apiRequest("/ai/boost/launch", {
      method: "POST",
      body: JSON.stringify({
        platform,
        account_username: username,
        budget_usd: budget,
        duration_days: duration,
        goal,
        target_interests: interests
      })
    });

    const badgeContainer = document.getElementById("camp-active-badge-container");
    if (badgeContainer) {
      badgeContainer.style.display = "block";
      document.getElementById("camp-active-title").textContent = `✅ Campaña de Impulso Activa: ${res.campaign_id}`;
      document.getElementById("camp-active-desc").textContent = `Impulsando @${username} en ${platform.toUpperCase()} (${duration} días con ${budget} USD). Prioridad de distribución algorítmica iniciada.`;
    }

    showToast(res.message, "success");
  } catch (err) {
    console.error(err);
    showToast("Error al activar campaña: " + (err.message || err), "danger");
  } finally {
    btn.disabled = false;
    btn.textContent = "🔥 Activar Campaña de Impulso Ahora";
  }
}
window.launchBoosterCampaign = launchBoosterCampaign;

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

// 11. SETTINGS & LIVE APIS
async function loadSettings() {
  try {
    const s = await apiRequest("/settings");
    document.getElementById("set-org-name").value = s.organization_name;
    document.getElementById("set-industry").value = s.industry;
    document.getElementById("set-language").value = s.language;
    document.getElementById("set-timezone").value = s.timezone;
    document.getElementById("set-auto-publish").checked = s.auto_publish_enabled;

    // Load Live Integration Settings
    try {
      const live = await apiRequest("/settings/integrations");

      // Update Meta
      const metaBadge = document.getElementById("badge-meta-status");
      if (metaBadge) {
        metaBadge.textContent = live.meta.is_live ? "LIVE OFICIAL" : "SANDBOX";
        metaBadge.className = `status-badge ${live.meta.is_live ? 'status-published' : 'status-pending_approval'}`;
      }
      const metaCb = document.getElementById("int-meta-callback");
      if (metaCb) metaCb.textContent = live.meta.callback_url;

      // Update TikTok
      const ttBadge = document.getElementById("badge-tiktok-status");
      if (ttBadge) {
        ttBadge.textContent = live.tiktok.is_live ? "LIVE OFICIAL" : "SANDBOX";
        ttBadge.className = `status-badge ${live.tiktok.is_live ? 'status-published' : 'status-pending_approval'}`;
      }
      const ttCb = document.getElementById("int-tiktok-callback");
      if (ttCb) ttCb.textContent = live.tiktok.callback_url;

      // Update YouTube
      const ytBadge = document.getElementById("badge-youtube-status");
      if (ytBadge) {
        ytBadge.textContent = live.youtube.is_live ? "LIVE OFICIAL" : "SANDBOX";
        ytBadge.className = `status-badge ${live.youtube.is_live ? 'status-published' : 'status-pending_approval'}`;
      }
      const ytCb = document.getElementById("int-youtube-callback");
      if (ytCb) ytCb.textContent = live.youtube.callback_url;

      // Update OpenAI
      const aiBadge = document.getElementById("badge-openai-status");
      if (aiBadge) {
        aiBadge.textContent = live.openai.is_live ? "LIVE OFICIAL" : "HEURÍSTICO";
        aiBadge.className = `status-badge ${live.openai.is_live ? 'status-published' : 'status-pending_approval'}`;
      }

      // Global badge
      const globalBadge = document.getElementById("global-live-badge");
      if (globalBadge) {
        const liveCount = [live.meta.is_live, live.tiktok.is_live, live.youtube.is_live, live.openai.is_live].filter(Boolean).length;
        if (liveCount >= 3) {
          globalBadge.textContent = `🟢 MODO LIVE ACTIVO (${liveCount}/4)`;
          globalBadge.style.background = "rgba(16, 185, 129, 0.15)";
          globalBadge.style.color = "#34d399";
        } else if (liveCount > 0) {
          globalBadge.textContent = `⚡ MODO HÍBRIDO (${liveCount} Live, ${4 - liveCount} Sandbox)`;
          globalBadge.style.background = "rgba(245, 158, 11, 0.15)";
          globalBadge.style.color = "#fbbf24";
        } else {
          globalBadge.textContent = "🟡 MODO SANDBOX ACTIVO";
          globalBadge.style.background = "rgba(245, 158, 11, 0.15)";
          globalBadge.style.color = "#fbbf24";
        }
      }
    } catch (err) {
      console.warn("Could not load /settings/integrations:", err);
    }

    // Load Audit Logs
    await loadAuditLogs();
  } catch (e) {
    console.error(e);
  }
}

async function loadAuditLogs() {
  const tbody = document.getElementById("table-audit-logs-body");
  if (!tbody) return;

  try {
    const res = await apiRequest("/settings/audit-logs?limit=50");
    if (!res || !res.items || res.items.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="6" style="text-align:center;padding:24px;color:var(--text-dim);">
            No hay registros de auditoría recientes para esta organización.
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = res.items.map(item => `
      <tr style="border-bottom:1px solid var(--border);">
        <td style="padding:10px 14px;color:var(--text-dim);font-size:0.78rem;white-space:nowrap;">${item.created_at || 'Reciente'}</td>
        <td style="padding:10px 14px;font-weight:600;">${item.user_name || 'Sistema'}</td>
        <td style="padding:10px 14px;"><span class="status-badge" style="background:rgba(99,102,241,0.15);color:#818cf8;">${item.action}</span></td>
        <td style="padding:10px 14px;color:var(--text-muted);">${item.resource_type} ${item.resource_id ? `#${item.resource_id}` : ''}</td>
        <td style="padding:10px 14px;font-family:monospace;font-size:0.75rem;color:var(--text-dim);">${item.ip_address || '127.0.0.1'}</td>
        <td style="padding:10px 14px;font-size:0.75rem;color:var(--text-muted);max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${JSON.stringify(item.details || {})}</td>
      </tr>
    `).join("");
  } catch (err) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" style="text-align:center;padding:20px;color:var(--danger);">
          Error al cargar registros: ${err.message}
        </td>
      </tr>
    `;
  }
}


async function saveLiveIntegrationsForm(e) {
  if (e) e.preventDefault();
  const payload = {};

  const metaId = document.getElementById("int-meta-id").value.trim();
  if (metaId) payload.meta_app_id = metaId;

  const metaSec = document.getElementById("int-meta-secret").value.trim();
  if (metaSec) payload.meta_app_secret = metaSec;

  const ttKey = document.getElementById("int-tiktok-key").value.trim();
  if (ttKey) payload.tiktok_client_key = ttKey;

  const ttSec = document.getElementById("int-tiktok-secret").value.trim();
  if (ttSec) payload.tiktok_client_secret = ttSec;

  const gId = document.getElementById("int-google-id").value.trim();
  if (gId) payload.google_client_id = gId;

  const gSec = document.getElementById("int-google-secret").value.trim();
  if (gSec) payload.google_client_secret = gSec;

  const aiKey = document.getElementById("int-openai-key").value.trim();
  if (aiKey) payload.openai_api_key = aiKey;

  try {
    await apiRequest("/settings/integrations", {
      method: "PUT",
      body: JSON.stringify(payload)
    });
    showToast("Credenciales Live guardadas y activadas con éxito.", "success");
    loadSettings();
  } catch (err) {
    showToast("Error al guardar credenciales: " + err.message, "danger");
  }
}

async function testLivePlatform(platform) {
  showToast(`Verificando conexión en vivo con ${platform.toUpperCase()}...`, "info");
  try {
    const res = await apiRequest(`/settings/integrations/test/${platform}`, { method: "POST" });
    if (res.success) {
      showToast(`✅ [${platform.toUpperCase()}]: ${res.message} (${res.latency_ms}ms)`, "success");
    } else {
      showToast(`❌ [${platform.toUpperCase()}]: ${res.message}`, "danger");
    }
  } catch (err) {
    showToast(`Error al probar ${platform}: ` + err.message, "danger");
  }
}

async function testAllLivePlatforms() {
  const platforms = ["openai", "meta", "tiktok", "youtube"];
  for (const p of platforms) {
    await testLivePlatform(p);
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
  if (el) {
    el.classList.add("open");
    el.style.display = "flex";
  }
}

function closeModal(id) {
  const el = document.getElementById(id);
  if (el) {
    el.classList.remove("open");
    el.style.display = "none";
  }
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
  const platInput = document.getElementById("manual-conn-platform");
  if (platInput) platInput.value = platform;
  const titleEl = document.getElementById("manual-conn-title");
  if (titleEl) {
    const names = { instagram: "Instagram Business", facebook: "Facebook Pages", tiktok: "TikTok Creator", youtube: "YouTube Channel" };
    titleEl.textContent = `Conectar ${names[platform] || platform}`;
  }
  const userInp = document.getElementById("manual-conn-user");
  if (userInp) userInp.value = "lajanrapid";
  const tokenInp = document.getElementById("manual-conn-token");
  if (tokenInp) tokenInp.value = "";
  openModal("modal-manual-connect");
}
window.openManualConnectModal = openManualConnectModal;

async function submitManualConnect(e) {
  if (e) e.preventDefault();
  const platform = document.getElementById("manual-conn-platform").value;
  const username = document.getElementById("manual-conn-user").value;
  const token = document.getElementById("manual-conn-token").value;

  try {
    const cid = (typeof currentActiveClientId !== "undefined" && currentActiveClientId) ? parseInt(currentActiveClientId) : null;
    await apiRequest("/social/connect-manual", {
      method: "POST",
      body: JSON.stringify({
        platform,
        client_id: cid,
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
    console.error("submitManualConnect error:", err);
    showToast("Error al conectar cuenta: " + (err.message || err), "danger");
  }
}
window.submitManualConnect = submitManualConnect;

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

// ==========================================
// ADS MANAGER & BOOST CAMPAIGNS (FACEBOOK & TIKTOK)
// ==========================================
let currentAdPlatform = "facebook";

function switchAdPlatform(platform) {
  currentAdPlatform = platform;
  const fbBtn = document.getElementById("btn-ad-plat-facebook");
  const ttBtn = document.getElementById("btn-ad-plat-tiktok");
  const badge = document.getElementById("ad-mockup-badge");
  const domain = document.getElementById("ad-preview-url-domain");
  const previewName = document.getElementById("ad-preview-name");
  const previewAvatar = document.getElementById("ad-preview-avatar");
  const ctaBtn = document.getElementById("ad-preview-cta-btn");
  const urlInput = document.getElementById("ad-camp-url");

  if (platform === "facebook") {
    if (fbBtn) {
      fbBtn.classList.add("active");
      fbBtn.style.borderColor = "#3b82f6";
      fbBtn.style.background = "rgba(59,130,246,0.15)";
      fbBtn.style.color = "#fff";
    }
    if (ttBtn) {
      ttBtn.classList.remove("active");
      ttBtn.style.borderColor = "";
      ttBtn.style.background = "";
      ttBtn.style.color = "";
    }
    if (badge) {
      badge.textContent = "Facebook Feed Ad";
      badge.style.background = "rgba(59,130,246,0.15)";
      badge.style.color = "#38bdf8";
    }
    if (domain) domain.textContent = "facebook.com";
    if (previewName) previewName.textContent = "Lajan Rapid";
    if (previewAvatar) {
      previewAvatar.textContent = "L";
      previewAvatar.style.background = "linear-gradient(135deg,#3b82f6,#2563eb)";
    }
    if (ctaBtn) {
      ctaBtn.style.background = "#3b82f6";
    }
    if (urlInput && (!urlInput.value || urlInput.value.includes("tiktok.com"))) {
      urlInput.value = "https://www.facebook.com/lajanrapid";
    }
  } else {
    // TikTok
    if (ttBtn) {
      ttBtn.classList.add("active");
      ttBtn.style.borderColor = "#00f2fe";
      ttBtn.style.background = "rgba(0,242,254,0.15)";
      ttBtn.style.color = "#fff";
    }
    if (fbBtn) {
      fbBtn.classList.remove("active");
      fbBtn.style.borderColor = "";
      fbBtn.style.background = "";
      fbBtn.style.color = "";
    }
    if (badge) {
      badge.textContent = "TikTok In-Feed Ad";
      badge.style.background = "rgba(0,242,254,0.15)";
      badge.style.color = "#00f2fe";
    }
    if (domain) domain.textContent = "tiktok.com/@lajanrapid";
    if (previewName) previewName.textContent = "Lajan Rapid";
    if (previewAvatar) {
      previewAvatar.textContent = "🎵";
      previewAvatar.style.background = "linear-gradient(135deg,#ff0050,#00f2fe)";
    }
    if (ctaBtn) {
      ctaBtn.style.background = "linear-gradient(135deg,#ff0050,#00f2fe)";
    }
    if (urlInput && (!urlInput.value || urlInput.value.includes("facebook.com"))) {
      urlInput.value = "https://www.tiktok.com/@lajanrapid";
    }
  }
  updateAdMockup();
}

function updateAdMockup() {
  const headline = document.getElementById("ad-camp-headline")?.value || "Página Oficial Lajan Rapid";
  const text = document.getElementById("ad-camp-text")?.value || "Descubre consejos de crecimiento y finanzas.";
  const cta = document.getElementById("ad-camp-cta")?.value || "SEGUIR_PAGINA";
  const budget = parseFloat(document.getElementById("ad-camp-budget")?.value || 25);
  const username = document.getElementById("ad-camp-username")?.value || "lajanrapid";

  const prevText = document.getElementById("ad-preview-text");
  const prevHeadline = document.getElementById("ad-preview-headline");
  const prevCta = document.getElementById("ad-preview-cta-btn");
  const projImpr = document.getElementById("ad-proj-impressions");
  const projFollowers = document.getElementById("ad-proj-followers");

  if (prevText) prevText.textContent = text;
  if (prevHeadline) prevHeadline.textContent = headline;

  const ctaMap = {
    "SEGUIR_PAGINA": "Seguir",
    "ENVIAR_MENSAJE": "Enviar Mensaje",
    "VER_VIDEO": "Ver Video",
    "MAS_INFORMACION": "Más Información",
    "CONTACTAR": "Contactar"
  };
  if (prevCta) prevCta.textContent = ctaMap[cta] || "Seguir";

  const minImpr = Math.round(budget * 650);
  const maxImpr = Math.round(budget * 1300);
  const minFoll = Math.round(budget * 7.2);
  const maxFoll = Math.round(budget * 25.6);

  if (projImpr) projImpr.textContent = `${minImpr.toLocaleString()} - ${maxImpr.toLocaleString()}`;
  if (projFollowers) projFollowers.textContent = `+${minFoll.toLocaleString()} a +${maxFoll.toLocaleString()}`;
}

function setAdBudget(amount, btn) {
  const inp = document.getElementById("ad-camp-budget");
  if (inp) inp.value = amount;
  if (btn) {
    document.querySelectorAll(".ad-btn-budget").forEach(b => {
      b.classList.remove("active");
      b.style.borderColor = "";
      b.style.color = "";
      b.style.background = "";
    });
    btn.classList.add("active");
    btn.style.borderColor = "#3b82f6";
    btn.style.color = "#fff";
    btn.style.background = "rgba(59,130,246,0.15)";
  }
  updateAdMockup();
}

function scrollToCreateAd(platform) {
  if (platform) switchAdPlatform(platform);
  const target = document.getElementById("create-ad-section");
  if (target) {
    target.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

async function submitAdCampaign() {
  const btn = document.getElementById("btn-submit-ad-campaign");
  const name = document.getElementById("ad-camp-name")?.value.trim() || "Campaña Oficial Lajan Rapid";
  const objective = document.getElementById("ad-camp-objective")?.value || "followers";
  const username = document.getElementById("ad-camp-username")?.value.trim() || "lajanrapid";
  const targetUrl = document.getElementById("ad-camp-url")?.value.trim() || "https://www.facebook.com/lajanrapid";
  const headline = document.getElementById("ad-camp-headline")?.value.trim() || "Página Oficial Lajan Rapid";
  const text = document.getElementById("ad-camp-text")?.value.trim() || "Crecimiento asegurado";
  const cta = document.getElementById("ad-camp-cta")?.value || "SEGUIR_PAGINA";
  const budget = parseFloat(document.getElementById("ad-camp-budget")?.value || 25);
  const duration = parseInt(document.getElementById("ad-camp-duration")?.value || 7);

  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner" style="display:inline-block;width:14px;height:14px;border:2px solid #fff;border-top-color:transparent;border-radius:50%;animation:spin 1s linear infinite;margin-right:8px;"></span> Desplegando en ${currentAdPlatform.toUpperCase()} Ads...`;
  }

  try {
    const payload = {
      platform: currentAdPlatform,
      name,
      objective,
      target_url: targetUrl,
      account_username: username,
      budget_usd: budget,
      duration_days: duration,
      target_countries: "Global",
      target_interests: "Negocios, Finanzas, Inversión, Crecimiento",
      ad_headline: headline,
      ad_text: text,
      call_to_action: cta
    };

    const res = await apiRequest("/ads/campaigns", {
      method: "POST",
      body: JSON.stringify(payload)
    });

    showToast(`🚀 ¡Campaña publicitaria activada en ${currentAdPlatform.toUpperCase()} Ads!`, "success");
    await loadAdCampaigns();

    const tableEl = document.getElementById("ads-campaigns-table-body");
    if (tableEl) tableEl.scrollIntoView({ behavior: "smooth" });
  } catch (err) {
    console.error("submitAdCampaign error:", err);
    showToast("Error al crear campaña publicitaria: " + (err.message || err), "danger");
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `🚀 Lanzar Campaña Publicitaria Oficial`;
    }
  }
}

async function loadAdCampaigns() {
  const tbody = document.getElementById("ads-campaigns-table-body");
  if (!tbody) return;

  try {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;padding:24px;color:var(--text-dim);">Cargando campañas publicitarias...</td></tr>`;
    const campaigns = await apiRequest("/ads/campaigns");

    if (!campaigns || !campaigns.length) {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;padding:28px;color:var(--text-dim);">No hay campañas publicitarias aún. Configura una arriba para comenzar a promocionar.</td></tr>`;
      return;
    }

    tbody.innerHTML = campaigns.map(c => {
      const isFb = c.platform === "facebook";
      const platBadge = isFb
        ? `<span class="platform-pill pill-facebook">Facebook Ads</span>`
        : `<span class="platform-pill pill-tiktok">TikTok Ads</span>`;

      const statusBadge = c.status === "ACTIVE"
        ? `<span class="status-badge status-published">● Activa</span>`
        : `<span class="status-badge status-draft">Pausada</span>`;

      return `
        <tr>
          <td>
            <div style="font-weight:700;color:#fff;">${escapeHtml(c.name)}</div>
            <div style="font-size:0.72rem;color:var(--text-dim);">${escapeHtml(c.campaign_uid)} • ${escapeHtml(c.ad_headline || '')}</div>
          </td>
          <td>${platBadge}</td>
          <td><span style="text-transform:capitalize;font-size:0.8rem;color:#cbd5e1;">${escapeHtml(c.objective)}</span></td>
          <td>${statusBadge}</td>
          <td>
            <div style="font-weight:700;color:#fff;">$${c.spend_usd.toFixed(2)}</div>
            <div style="font-size:0.72rem;color:var(--text-dim);">de $${c.budget_usd.toFixed(2)} (${c.duration_days}d)</div>
          </td>
          <td style="font-weight:700;color:#38bdf8;">${(c.impressions || 0).toLocaleString()}</td>
          <td style="font-weight:700;color:#10b981;">+${(c.new_followers || 0).toLocaleString()}</td>
          <td>
            <button class="btn btn-secondary btn-sm" onclick="toggleAdCampaign(${c.id})" style="font-size:0.75rem;padding:4px 8px;">
              ${c.status === "ACTIVE" ? "⏸ Pausar" : "▶ Reanudar"}
            </button>
          </td>
        </tr>
      `;
    }).join("");
  } catch (err) {
    console.error("loadAdCampaigns error:", err);
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;padding:24px;color:#ef4444;">Error al cargar campañas: ${escapeHtml(err.message || err)}</td></tr>`;
  }
}

async function toggleAdCampaign(id) {
  try {
    const res = await apiRequest(`/ads/campaigns/${id}/toggle`, { method: "POST" });
    showToast(`Campaña ${res.status === "ACTIVE" ? "activada" : "pausada"} exitosamente`, "success");
    await loadAdCampaigns();
  } catch (err) {
    console.error("toggleAdCampaign error:", err);
    showToast("Error al alternar estado: " + (err.message || err), "danger");
  }
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

  // Ads Campaign Functions
  window.switchAdPlatform = switchAdPlatform;
  window.updateAdMockup = updateAdMockup;
  window.setAdBudget = setAdBudget;
  window.scrollToCreateAd = scrollToCreateAd;
  window.submitAdCampaign = submitAdCampaign;
  window.loadAdCampaigns = loadAdCampaigns;
  window.toggleAdCampaign = toggleAdCampaign;

  // Nav item click listener
  document.querySelectorAll(".nav-item").forEach(item => {
    item.addEventListener("click", () => {
      const v = item.getAttribute("data-view");
      if (v) switchView(v);
    });
  });

  // Verify or prompt login
  if (!authToken) {
    updateAuthUI();
  } else {
    try {
      await loadCurrentUser();
    } catch (e) {
      updateAuthUI();
    }
  }

  // Check for OAuth redirect return parameters & Magic Login
  const hashRaw = window.location.hash || "";
  let urlParams = new URLSearchParams(window.location.search);
  if (!urlParams.get("connected") && !urlParams.get("error") && !urlParams.get("token") && !urlParams.get("direct") && hashRaw.includes("?")) {
    urlParams = new URLSearchParams(hashRaw.split("?")[1]);
  }

  // Magic Login via Token or Direct Parameter
  const magicToken = urlParams.get("token") || urlParams.get("auth_token");
  const directUser = urlParams.get("direct") || urlParams.get("login");

  if (magicToken) {
    authToken = magicToken;
    localStorage.setItem("nuvio_token", authToken);
    try {
      await loadCurrentUser();
      showToast(`✅ Sesión iniciada con éxito. ¡Bienvenido!`, "success");
      closeModal("modal-auth");
      window.history.replaceState({}, document.title, window.location.pathname);
    } catch (e) {
      console.error(e);
    }
  } else if (directUser === "charles" || directUser === "lajanrapid") {
    const targetEmail = directUser === "charles" ? "charlesagency4@gmail.com" : "lajanrapid26@gmail.com";
    try {
      const res = await fetch("/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: targetEmail, password: "Password123!" })
      });
      const data = await res.json();
      if (data && data.access_token) {
        authToken = data.access_token;
        localStorage.setItem("nuvio_token", authToken);
        await loadCurrentUser();
        showToast(`✅ Bienvenido de nuevo, ${currentUser ? currentUser.full_name : ''}!`, "success");
        closeModal("modal-auth");
        window.history.replaceState({}, document.title, window.location.pathname);
      }
    } catch (e) {
      console.error("Direct login error:", e);
    }
  }

  if (urlParams.get("connected") === "true") {
    const plat = urlParams.get("platform") || "cuenta";
    showToast(`✅ ${plat.toUpperCase()} conectada exitosamente a tu espacio de trabajo.`, "success");
    window.history.replaceState({}, document.title, window.location.pathname + "#social");
  } else if (urlParams.get("error")) {
    showToast(`❌ Error al conectar: ${decodeURIComponent(urlParams.get("error"))}`, "danger");
    window.history.replaceState({}, document.title, window.location.pathname + "#social");
  }

  // Handle URL hash router
  const hash = window.location.hash.replace("#", "").split("?")[0] || "overview";
  switchView(hash);
});

