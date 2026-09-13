const key = "gym-booking-hub.targets.v1";
const weekdays = ["Domingo", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"];
const agenda = document.querySelector("#agenda");
const empty = document.querySelector("#empty-state");
const dialog = document.querySelector("#target-dialog");
const form = document.querySelector("#target-form");

function load() { try { return JSON.parse(localStorage.getItem(key)) || []; } catch { return []; } }
function save(items) { localStorage.setItem(key, JSON.stringify(items)); }
function nextDate(day) {
  const d = new Date(); d.setHours(0, 0, 0, 0);
  const delta = (day - d.getDay() + 7) % 7 || 7;
  d.setDate(d.getDate() + delta); return d;
}
function render() {
  const items = load().sort((a,b) => a.day - b.day || a.time.localeCompare(b.time));
  agenda.replaceChildren(); empty.hidden = items.length > 0;
  for (const item of items) {
    const date = nextDate(Number(item.day));
    const li = document.createElement("li");
    li.innerHTML = `<span class="date"><b>${date.getDate()}</b>${date.toLocaleDateString("es-ES", {month:"short"})}</span><div><strong>${weekdays[item.day]} · ${item.time}</strong><small>Lanzamiento: viernes · ${item.launch}</small></div><span class="state">PLANIFICADA</span><button class="delete" aria-label="Eliminar ${weekdays[item.day]} ${item.time}">×</button>`;
    li.querySelector(".delete").onclick = () => { save(load().filter(x => x.id !== item.id)); render(); };
    agenda.append(li);
  }
}
document.querySelector("#add-target").onclick = () => dialog.showModal();
document.querySelector("#close-dialog").onclick = document.querySelector("#cancel-dialog").onclick = () => dialog.close();
document.querySelector("#agent-info").onclick = () => document.querySelector("#agent-dialog").showModal();
form.addEventListener("submit", event => { event.preventDefault(); const item = {id: crypto.randomUUID(), day: form.weekday.value, time: form["class-time"].value, launch: form["launch-time"].value}; save([...load(), item]); dialog.close(); form.reset(); form["class-time"].value="18:00"; form["launch-time"].value="15:30"; render(); });
render();

