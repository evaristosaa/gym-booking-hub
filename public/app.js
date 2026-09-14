import { initializeApp } from "https://www.gstatic.com/firebasejs/12.8.0/firebase-app.js";
import { createUserWithEmailAndPassword, getAuth, onAuthStateChanged, signInWithEmailAndPassword } from "https://www.gstatic.com/firebasejs/12.8.0/firebase-auth.js";

const key = "gym-booking-hub.targets.v1";
const weekdays = ["Domingo", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"];
const agenda = document.querySelector("#agenda");
const empty = document.querySelector("#empty-state");
const dialog = document.querySelector("#target-dialog");
const form = document.querySelector("#target-form");
const authDialog = document.querySelector("#auth-dialog");
const authForm = document.querySelector("#auth-form");
const authMessage = document.querySelector("#auth-message");
const signInButton = document.querySelector("#sign-in");
const connectionTitle = document.querySelector("#connection-title");
const connectionDetail = document.querySelector("#connection-detail");
const connectionDot = document.querySelector("#connection-dot");
const connectionButton = document.querySelector("#agent-info");
const wodbusterDialog = document.querySelector("#agent-dialog");
const wodbusterForm = document.querySelector("#wodbuster-form");
const wodbusterMessage = document.querySelector("#wodbuster-message");
const liveReservations = document.querySelector("#live-reservations");
const liveEmpty = document.querySelector("#live-empty");
const watchDialog = document.querySelector("#watch-dialog");
const watchForm = document.querySelector("#watch-form");
const watchesList = document.querySelector("#watches");
const watchesEmpty = document.querySelector("#watches-empty");
const notificationMessage = document.querySelector("#notification-message");
let wodbusterStatus = { configured: false, verified: false };
let remoteSchedules = null;
let remoteWatches = [];

function load() { try { return JSON.parse(localStorage.getItem(key)) || []; } catch { return []; } }
function save(items) { localStorage.setItem(key, JSON.stringify(items)); }
function nextDate(day) {
  // The weekly plan always targets the calendar week after the current one.
  // On a Sunday, for example, Monday means eight days away, never tomorrow.
  const d = new Date(); d.setHours(0, 0, 0, 0);
  d.setDate(d.getDate() + 8 - d.getDay()); // next week's Monday
  d.setDate(d.getDate() + (Number(day) === 0 ? 6 : Number(day) - 1));
  return d;
}
function render() {
  const source = remoteSchedules ?? load();
  const items = source.map(item => ({
    id: item.id,
    day: item.weekday ?? item.day,
    time: item.class_time ?? item.time,
    launch: item.launch_time ?? item.launch,
  })).sort((a, b) => a.day - b.day || a.time.localeCompare(b.time));
  agenda.replaceChildren(); empty.hidden = items.length > 0;
  for (const item of items) {
    const date = nextDate(Number(item.day));
    const li = document.createElement("li");
    const state = remoteSchedules ? "ACTIVA" : "BORRADOR";
    li.innerHTML = `<span class="date"><b>${date.getDate()}</b>${date.toLocaleDateString("es-ES", {month:"short"})}</span><div><strong>${weekdays[item.day]} · ${item.time}</strong><small>Intento: viernes · ${item.launch}</small></div><span class="state">${state}</span><button class="delete" aria-label="Eliminar ${weekdays[item.day]} ${item.time}">×</button>`;
    li.querySelector(".delete").onclick = async () => {
      if (remoteSchedules) {
        await apiRequest(`/v1/schedules/${item.id}`, { method: "DELETE" });
        remoteSchedules = remoteSchedules.filter(schedule => schedule.id !== item.id);
      } else save(load().filter(x => x.id !== item.id));
      render();
    };
    agenda.append(li);
  }
}

document.querySelector("#add-target").onclick = () => dialog.showModal();
document.querySelector("#add-watch").onclick = () => {
  const today = new Date();
  const localDate = new Date(today.getTime() - today.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
  document.querySelector("#watch-date").min = localDate;
  document.querySelector("#watch-date").value ||= localDate;
  watchDialog.showModal();
};
document.querySelector("#close-dialog").onclick = document.querySelector("#cancel-dialog").onclick = () => dialog.close();
document.querySelector("#close-watch").onclick = document.querySelector("#cancel-watch").onclick = () => watchDialog.close();
connectionButton.onclick = () => wodbusterStatus.configured ? testWodBuster() : wodbusterDialog.showModal();
document.querySelector("#close-wodbuster").onclick = document.querySelector("#cancel-wodbuster").onclick = () => wodbusterDialog.close();
document.querySelector("#close-auth").onclick = () => authDialog.close();
signInButton.onclick = () => authDialog.showModal();
form.addEventListener("submit", event => {
  event.preventDefault();
  const item = {id: crypto.randomUUID(), day: form.weekday.value, time: form["class-time"].value, launch: form["launch-time"].value};
  const complete = () => { dialog.close(); form.reset(); form["class-time"].value = "18:00"; form["launch-time"].value = "15:30"; render(); };
  if (!auth.currentUser) { save([...load(), item]); complete(); return; }
  apiRequest("/v1/schedules", { method: "POST", body: JSON.stringify({ weekday: Number(item.day), class_time: item.time, launch_time: item.launch }) })
    .then(response => response.json())
    .then(schedule => { remoteSchedules = [...(remoteSchedules || []), schedule]; complete(); })
    .catch(() => { save([...load(), item]); complete(); });
});

const firebaseApp = initializeApp(window.GYM_BOOKING_FIREBASE);
const auth = getAuth(firebaseApp);
function authError(error) {
  if (error.code === "auth/email-already-in-use") return "Ese correo ya tiene cuenta. Prueba a entrar.";
  if (error.code === "auth/invalid-credential") return "Correo o contraseña incorrectos.";
  if (error.code === "auth/weak-password") return "La contraseña necesita al menos 8 caracteres.";
  if (error.code === "auth/network-request-failed") return "No se pudo contactar con el acceso. Revisa la conexión o la VPN y prueba de nuevo.";
  if (error.code === "auth/unauthorized-domain") return "Esta dirección aún no está autorizada. Recarga la app y prueba de nuevo.";
  if (error.code === "auth/too-many-requests") return "Demasiados intentos seguidos. Espera unos minutos antes de volver a probar.";
  return `No se pudo completar el acceso (${error.code || "error desconocido"}).`;
}
async function authenticate(action) {
  const email = document.querySelector("#auth-email").value.trim();
  const password = document.querySelector("#auth-password").value;
  authMessage.textContent = "Comprobando…";
  try {
    if (action === "register") await createUserWithEmailAndPassword(auth, email, password);
    else await signInWithEmailAndPassword(auth, email, password);
    authForm.reset(); authDialog.close();
  } catch (error) { authMessage.textContent = authError(error); }
}
async function verifyRemoteSession(user) {
  try {
    const token = await user.getIdToken();
    const response = await fetch(`${window.GYM_BOOKING_FIREBASE.apiBaseUrl}/v1/session`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) throw new Error("session verification failed");
    connectionTitle.textContent = "Sesión protegida";
    connectionDetail.textContent = "Conecta WodBuster para sincronizar tus reservas reales.";
  } catch {
    connectionTitle.textContent = "Sesión local; servicio no disponible";
    connectionDetail.textContent = "Tu cuenta está creada, pero la sincronización se reintentará.";
  }
}
async function apiRequest(path, options = {}) {
  const user = auth.currentUser;
  if (!user) throw new Error("sign-in-required");
  const token = await user.getIdToken();
  return fetch(`${window.GYM_BOOKING_FIREBASE.apiBaseUrl}${path}`, {
    ...options,
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json", ...(options.headers || {}) },
  });
}
async function refreshWodBusterStatus() {
  try {
    const response = await apiRequest("/v1/connections/wodbuster");
    if (!response.ok) return;
    const connection = await response.json();
    wodbusterStatus = connection;
    if (!connection.configured) return;
    if (connection.verified) {
      connectionTitle.textContent = "WodBuster verificado";
      connectionDetail.textContent = `Cuenta ${connection.usernameHint} validada correctamente.`;
      connectionDot.classList.add("healthy");
      connectionButton.textContent = "Probar de nuevo";
      refreshLiveReservations();
    } else {
      connectionTitle.textContent = "WodBuster sin validar";
      connectionDetail.textContent = `Cuenta ${connection.usernameHint} guardada cifrada. Falta probarla.`;
      connectionDot.classList.remove("healthy");
      connectionButton.textContent = "Probar conexión";
    }
  } catch { /* Session status already communicates a transient backend problem. */ }
}
async function testWodBuster() {
  connectionButton.disabled = true; connectionButton.textContent = "Probando…";
  try {
    const response = await apiRequest("/v1/connections/wodbuster/test", { method: "POST" });
    if (!response.ok) throw new Error("test-failed");
    await refreshWodBusterStatus();
  } catch {
    connectionTitle.textContent = "WodBuster no validado";
    connectionDetail.textContent = "Revisa usuario y contraseña e inténtalo otra vez.";
    connectionDot.classList.remove("healthy");
  } finally { connectionButton.disabled = false; if (!wodbusterStatus.verified) connectionButton.textContent = "Probar conexión"; }
}
function renderLiveReservations(items) {
  liveReservations.replaceChildren(); liveEmpty.hidden = items.length > 0;
  for (const item of items) {
    const date = new Date(`${item.date}T12:00:00`);
    const li = document.createElement("li");
    li.innerHTML = `<span class="date"><b>${date.getDate()}</b>${date.toLocaleDateString("es-ES", {month:"short"})}</span><div><strong>${item.time}</strong><small>${item.name}</small></div><span class="state">CONFIRMADA</span>`;
    liveReservations.append(li);
  }
}
function renderWatches() {
  watchesList.replaceChildren();
  watchesEmpty.hidden = remoteWatches.length > 0;
  for (const watch of remoteWatches) {
    const date = new Date(`${watch.class_date}T12:00:00`);
    const li = document.createElement("li");
    li.innerHTML = `<span class="date"><b>${date.getDate()}</b>${date.toLocaleDateString("es-ES", {month:"short"})}</span><div><strong>${watch.class_time}</strong><small>${watch.last_result || "Vigilando plazas libres cada 10 minutos"}</small></div><span class="state">VIGILANDO</span><button class="delete" aria-label="Dejar de vigilar">×</button>`;
    li.querySelector(".delete").onclick = async () => {
      await apiRequest(`/v1/availability-watches/${watch.id}`, { method: "DELETE" });
      remoteWatches = remoteWatches.filter(item => item.id !== watch.id);
      renderWatches();
    };
    watchesList.append(li);
  }
}
async function refreshWatches() {
  try {
    const response = await apiRequest("/v1/availability-watches");
    if (!response.ok) throw new Error("watches-failed");
    remoteWatches = (await response.json()).watches || [];
    renderWatches();
  } catch { /* The user can still use the Friday plan if the worker is unavailable. */ }
}
watchForm.addEventListener("submit", async event => {
  event.preventDefault();
  try {
    const response = await apiRequest("/v1/availability-watches", {
      method: "POST",
      body: JSON.stringify({ class_date: document.querySelector("#watch-date").value, class_time: document.querySelector("#watch-time").value }),
    });
    if (!response.ok) throw new Error("watch-failed");
    watchForm.reset(); watchDialog.close(); await refreshWatches();
  } catch { notificationMessage.textContent = "No se pudo activar la vigilancia. Prueba de nuevo."; }
});
function urlBase64ToUint8Array(value) {
  const padding = "=".repeat((4 - value.length % 4) % 4);
  const bytes = atob((value + padding).replace(/-/g, "+").replace(/_/g, "/"));
  return Uint8Array.from(bytes, char => char.charCodeAt(0));
}
document.querySelector("#enable-notifications").onclick = async () => {
  const key = window.GYM_BOOKING_FIREBASE.webPushPublicKey;
  if (!auth.currentUser) { notificationMessage.textContent = "Entra primero con tu cuenta de Gym Booking Hub."; return; }
  if (!key || !("Notification" in window) || !("PushManager" in window)) { notificationMessage.textContent = "Los avisos aún se están preparando."; return; }
  try {
    const permission = await Notification.requestPermission();
    if (permission !== "granted") throw new Error("denied");
    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: urlBase64ToUint8Array(key) });
    const response = await apiRequest("/v1/push-subscriptions", { method: "PUT", body: JSON.stringify(subscription) });
    if (!response.ok) throw new Error("save-failed");
    notificationMessage.textContent = "Avisos activados en este móvil.";
  } catch { notificationMessage.textContent = "No se pudieron activar los avisos. Revisa los permisos del navegador."; }
};
async function refreshLiveReservations() {
  if (!wodbusterStatus.verified) return;
  liveEmpty.hidden = false; liveEmpty.textContent = "Leyendo reservas confirmadas…";
  try {
    const response = await apiRequest("/v1/reservations");
    if (!response.ok) throw new Error("reservations-failed");
    const payload = await response.json();
    renderLiveReservations(payload.reservations || []);
    if (!payload.reservations?.length) liveEmpty.textContent = "No hay reservas confirmadas en las próximas tres semanas.";
  } catch { liveEmpty.textContent = "No se pudieron actualizar las reservas. Prueba otra vez."; }
}
async function syncSchedules() {
  try {
    const response = await apiRequest("/v1/schedules");
    if (!response.ok) throw new Error("schedules-failed");
    remoteSchedules = (await response.json()).schedules || [];
    const drafts = load();
    for (const draft of drafts) {
      const create = await apiRequest("/v1/schedules", {
        method: "POST",
        body: JSON.stringify({ weekday: Number(draft.day), class_time: draft.time, launch_time: draft.launch }),
      });
      if (create.ok) {
        const schedule = await create.json();
        if (!remoteSchedules.some(item => item.id === schedule.id)) remoteSchedules.push(schedule);
      }
    }
    if (drafts.length) localStorage.removeItem(key);
    render();
  } catch { remoteSchedules = null; render(); }
}
document.querySelector("#refresh-reservations").onclick = refreshLiveReservations;
wodbusterForm.addEventListener("submit", async event => {
  event.preventDefault();
  wodbusterMessage.textContent = "Guardando conexión cifrada…";
  try {
    const response = await apiRequest("/v1/connections/wodbuster", {
      method: "PUT",
      body: JSON.stringify({ username: document.querySelector("#wodbuster-username").value.trim(), password: document.querySelector("#wodbuster-password").value }),
    });
    if (!response.ok) throw new Error("save-failed");
    wodbusterForm.reset(); wodbusterDialog.close(); await refreshWodBusterStatus();
  } catch (error) {
    wodbusterMessage.textContent = error.message === "sign-in-required" ? "Primero entra con tu cuenta de Gym Booking Hub." : "No se pudo guardar. Prueba de nuevo.";
  }
});
authForm.addEventListener("submit", event => { event.preventDefault(); authenticate("login"); });
document.querySelector("#register").onclick = () => authenticate("register");
onAuthStateChanged(auth, user => {
  if (!user) return;
  connectionTitle.textContent = "Sesión iniciada";
  connectionDetail.textContent = "WodBuster queda pendiente de conexión segura.";
  signInButton.textContent = user.email || "Mi cuenta";
  verifyRemoteSession(user);
  refreshWodBusterStatus();
  syncSchedules();
  refreshWatches();
});

render();
if ("serviceWorker" in navigator) navigator.serviceWorker.register("./sw.js");
