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

function load() { try { return JSON.parse(localStorage.getItem(key)) || []; } catch { return []; } }
function save(items) { localStorage.setItem(key, JSON.stringify(items)); }
function nextDate(day) {
  const d = new Date(); d.setHours(0, 0, 0, 0);
  const delta = (day - d.getDay() + 7) % 7 || 7;
  d.setDate(d.getDate() + delta); return d;
}
function render() {
  const items = load().sort((a, b) => a.day - b.day || a.time.localeCompare(b.time));
  agenda.replaceChildren(); empty.hidden = items.length > 0;
  for (const item of items) {
    const date = nextDate(Number(item.day));
    const li = document.createElement("li");
    li.innerHTML = `<span class="date"><b>${date.getDate()}</b>${date.toLocaleDateString("es-ES", {month:"short"})}</span><div><strong>${weekdays[item.day]} · ${item.time}</strong><small>Lanzamiento: viernes · ${item.launch}</small></div><span class="state">BORRADOR</span><button class="delete" aria-label="Eliminar ${weekdays[item.day]} ${item.time}">×</button>`;
    li.querySelector(".delete").onclick = () => { save(load().filter(x => x.id !== item.id)); render(); };
    agenda.append(li);
  }
}

document.querySelector("#add-target").onclick = () => dialog.showModal();
document.querySelector("#close-dialog").onclick = document.querySelector("#cancel-dialog").onclick = () => dialog.close();
document.querySelector("#agent-info").onclick = () => document.querySelector("#agent-dialog").showModal();
document.querySelector("#close-auth").onclick = () => authDialog.close();
signInButton.onclick = () => authDialog.showModal();
form.addEventListener("submit", event => {
  event.preventDefault();
  const item = {id: crypto.randomUUID(), day: form.weekday.value, time: form["class-time"].value, launch: form["launch-time"].value};
  save([...load(), item]); dialog.close(); form.reset(); form["class-time"].value = "18:00"; form["launch-time"].value = "15:30"; render();
});

const firebaseApp = initializeApp(window.GYM_BOOKING_FIREBASE);
const auth = getAuth(firebaseApp);
function authError(error) {
  if (error.code === "auth/email-already-in-use") return "Ese correo ya tiene cuenta. Prueba a entrar.";
  if (error.code === "auth/invalid-credential") return "Correo o contraseña incorrectos.";
  if (error.code === "auth/weak-password") return "La contraseña necesita al menos 8 caracteres.";
  return "No se pudo completar el acceso. Prueba de nuevo.";
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
authForm.addEventListener("submit", event => { event.preventDefault(); authenticate("login"); });
document.querySelector("#register").onclick = () => authenticate("register");
onAuthStateChanged(auth, user => {
  if (!user) return;
  connectionTitle.textContent = "Sesión iniciada";
  connectionDetail.textContent = "WodBuster queda pendiente de conexión segura.";
  signInButton.textContent = user.email || "Mi cuenta";
  verifyRemoteSession(user);
});

render();
if ("serviceWorker" in navigator) navigator.serviceWorker.register("./sw.js");
