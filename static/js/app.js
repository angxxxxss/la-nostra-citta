import { api, initializeCsrf } from "./api.js";

const $ = (selector) => document.querySelector(selector);
let authMode = "login";
let map;
let markers;
const esc = (value = "") => String(value).replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);

async function loadLookups() {
  const [neighborhoods, categories] = await Promise.all([api("/api/quartieri"), api("/api/categorie")]);
  for (const item of neighborhoods.items) {
    const option = new Option(item.nome, item.id_quartiere);
    $("#neighborhoods").add(option.cloneNode(true));
    $("#filter-neighborhood").add(option);
    $("#register-neighborhood").add(option.cloneNode(true));
  }
  for (const item of categories.items) $("#filter-category").add(new Option(item.nome_categoria, item.id_categoria));
  $("#categories").innerHTML = categories.items.map((item) => `<label class="check-pill"><input type="checkbox" name="categorie" value="${item.id_categoria}"><span>${esc(item.nome_categoria)}</span></label>`).join("");
}

function initMap() {
  if (!window.L) return;
  map = L.map("city-map").setView([45.4642, 9.19], 11);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19, attribution: "&copy; OpenStreetMap" }).addTo(map);
  markers = L.layerGroup().addTo(map);
}

async function loadReports() {
  const params = new URLSearchParams();
  if ($("#filter-neighborhood").value) params.set("quartiere", $("#filter-neighborhood").value);
  if ($("#filter-category").value) params.set("categoria", $("#filter-category").value);
  if ($("#search-reports").value.trim()) params.set("q", $("#search-reports").value.trim());
  try {
    const { items } = await api(`/api/segnalazioni?${params}`);
    const list = $("#report-list");
    list.innerHTML = items.length ? items.map((item) => `<article class="report-card"><div class="card-top"><span class="tag">${esc(item.quartiere)}</span><span class="state">${esc(item.stato)}</span></div><h3>${esc(item.titolo)}</h3>${item.allegati.map((a) => a.tipo === "Foto" ? `<img class="report-media" loading="lazy" src="/api/segnalazioni/${item.id_segnalazione}/allegati/${a.id_file}" alt="Foto allegata alla segnalazione ${esc(item.titolo)}">` : `<video class="report-media" controls preload="none"><source src="/api/segnalazioni/${item.id_segnalazione}/allegati/${a.id_file}" type="${esc(a.mime_type)}">Il browser non supporta il video.</video>`).join("")}<p>${esc(item.descrizione)}</p><p class="location">⌖ ${esc(item.indirizzo)}</p><div class="tags">${item.categorie.map((c) => `<span>${esc(c.nome_categoria)}</span>`).join("")}</div><div class="card-bottom"><span>di ${esc(item.nome)} ${esc(item.cognome)}</span><div><button class="text-button support" data-id="${item.id_segnalazione}" data-kind="Sostegno">♡ ${item.sostegni.Sostegno || 0}</button><button class="text-button support" data-id="${item.id_segnalazione}" data-kind="Interesse">◎ ${item.sostegni.Interesse || 0}</button></div></div><details><summary>Commenti e aggiornamenti</summary><div class="status-history" data-history="${item.id_segnalazione}"><p>Caricamento aggiornamenti…</p></div><div class="comments" data-report="${item.id_segnalazione}"><p>Caricamento commenti…</p></div><form class="comment-form" data-report="${item.id_segnalazione}"><label class="sr-only">Scrivi un commento<input name="testo" maxlength="2000" required placeholder="Aggiungi un commento"></label><button class="text-button">Invia</button></form></details></article>`).join("") : `<div class="empty-state"><h3>Ancora nessuna segnalazione</h3><p>Quando la comunità condividerà le prime proposte, appariranno qui.</p></div>`;
    if (markers) {
      markers.clearLayers();
      items.filter((i) => i.latitudine !== null && i.longitudine !== null).forEach((i) => L.marker([i.latitudine, i.longitudine]).bindPopup(`<strong>${esc(i.titolo)}</strong><br>${esc(i.indirizzo)}`).addTo(markers));
    }
    for (const item of items) { loadComments(item.id_segnalazione); loadHistory(item.id_segnalazione); }
    list.querySelectorAll(".support").forEach((button) => button.addEventListener("click", async () => {
      try { await api(`/api/segnalazioni/${button.dataset.id}/sostegni`, { method: "POST", body: JSON.stringify({ tipo: button.dataset.kind }) }); await loadReports(); await loadPriorities(); }
      catch (error) { alert(error.message); }
    }));
    list.querySelectorAll(".comment-form").forEach((form) => form.addEventListener("submit", async (event) => {
      event.preventDefault();
      try { await api(`/api/segnalazioni/${form.dataset.report}/commenti`, { method: "POST", body: JSON.stringify({ testo: new FormData(form).get("testo") }) }); form.reset(); await loadComments(form.dataset.report); }
      catch (error) { alert(error.message); }
    }));
  } catch (error) { $("#report-list").innerHTML = `<p class="error-message">${esc(error.message)}. Controlla la configurazione MySQL.</p>`; }
}

async function loadComments(reportId) {
  const container = document.querySelector(`[data-report="${reportId}"].comments`);
  if (!container) return;
  try {
    const { items } = await api(`/api/segnalazioni/${reportId}/commenti`);
    container.innerHTML = items.length ? items.map((item) => `<p><strong>${esc(item.nome)} ${esc(item.cognome)}</strong> ${esc(item.testo)}</p>`).join("") : "<p>Nessun commento.</p>";
  } catch { container.innerHTML = "<p>Commenti non disponibili.</p>"; }
}

async function loadHistory(reportId) {
  const container = document.querySelector(`[data-history="${reportId}"]`);
  if (!container) return;
  try {
    const { items } = await api(`/api/segnalazioni/${reportId}/storico`);
    container.innerHTML = items.length ? `<strong>Aggiornamenti</strong>${items.map((item) => `<p>${esc(item.stato)} · ${esc(item.nota || "")} <small>${esc(item.nome)} ${esc(item.cognome)}</small></p>`).join("")}` : "";
  } catch { container.textContent = "Aggiornamenti non disponibili."; }
}

async function loadPriorities() {
  try {
    const { items } = await api("/api/segnalazioni/priorita");
    $("#priority-list").innerHTML = items.length ? items.map((item) => `<li><span>${esc(item.titolo)}</span><strong>${item.sostenitori} sostegni</strong></li>`).join("") : "<li>La classifica si popolerà con le prime segnalazioni.</li>";
  } catch { $("#priority-list").innerHTML = "<li>Classifica non disponibile.</li>"; }
}

async function refreshUser() {
  try {
    const { user } = await api("/api/auth/me");
    $("#user-status").textContent = user.verified ? `${user.email} · verificato` : `${user.email} · da verificare`;
    $("#open-auth").classList.add("hidden"); $("#logout").classList.remove("hidden");
    $("#verifica-identita").classList.toggle("hidden", user.verified);
  } catch {
    $("#user-status").textContent = "Visitatore";
    $("#open-auth").classList.remove("hidden"); $("#logout").classList.add("hidden");
    $("#verifica-identita").classList.add("hidden");
  }
}

$("#open-auth").addEventListener("click", () => $("#auth-dialog").showModal());
$("#close-auth").addEventListener("click", () => $("#auth-dialog").close());
document.querySelectorAll(".tab").forEach((tab) => tab.addEventListener("click", () => {
  authMode = tab.dataset.mode;
  document.querySelectorAll(".tab").forEach((item) => item.classList.toggle("active", item === tab));
  $("#register-fields").classList.toggle("hidden", authMode !== "register");
  $("#auth-submit").textContent = authMode === "login" ? "Accedi" : "Crea account";
  $("#auth-title").textContent = authMode === "login" ? "Accedi alla piattaforma" : "Crea il tuo account";
}));

$("#auth-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(event.currentTarget));
  try {
    const result = await api(`/api/auth/${authMode === "login" ? "login" : "register"}`, { method: "POST", body: JSON.stringify(data) });
    $("#auth-message").textContent = authMode === "login" ? "Accesso effettuato." : result.message;
    if (authMode === "login") { await initializeCsrf(); $("#auth-dialog").close(); await refreshUser(); }
  } catch (error) { $("#auth-message").textContent = error.message; }
});

$("#logout").addEventListener("click", async () => { try { await api("/api/auth/logout", { method: "POST" }); await initializeCsrf(); await refreshUser(); } catch (error) { alert(error.message); } });

$("#report-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const data = new FormData(form);
  data.delete("categorie");
  form.querySelectorAll("input[name='categorie']:checked").forEach((input) => data.append("categorie", input.value));
  try { await api("/api/segnalazioni", { method: "POST", body: data }); $("#report-message").textContent = "Segnalazione pubblicata."; form.reset(); await loadReports(); await loadPriorities(); }
  catch (error) { $("#report-message").textContent = error.message; }
});

$("#identity-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try { const data = new FormData(event.currentTarget); await api("/api/auth/verify-document", { method: "POST", body: data }); $("#identity-message").textContent = "Documenti inviati per la verifica."; }
  catch (error) { $("#identity-message").textContent = error.message; }
});

$("#filter-neighborhood").addEventListener("change", loadReports);
$("#filter-category").addEventListener("change", loadReports);
let searchTimer;
$("#search-reports").addEventListener("input", () => { clearTimeout(searchTimer); searchTimer = setTimeout(loadReports, 250); });

await initializeCsrf();
initMap();
await Promise.allSettled([loadLookups(), refreshUser()]);
await Promise.all([loadReports(), loadPriorities()]);
