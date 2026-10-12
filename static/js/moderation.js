import { api, initializeCsrf } from "./api.js";
const $ = (s) => document.querySelector(s);
const esc = (v = "") => String(v).replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[c]);
const message = (error) => { $("#access-message").textContent = error.message; };

async function load() {
  await initializeCsrf();
  try {
    const dashboard = await api("/api/moderation/dashboard");
    $("#dashboard").classList.remove("hidden");
    $("#access-message").textContent = "Accesso autorizzato.";
    $("#stats").innerHTML = `<div><strong>${dashboard.segnalazioni.reduce((n,x)=>n+x.totale,0)}</strong><span>segnalazioni</span></div><div><strong>${dashboard.verifiche.find(x=>x.stato_verifica==='In attesa')?.totale || 0}</strong><span>verifiche da valutare</span></div><div><strong>${dashboard.analisi_ia_in_attesa}</strong><span>analisi IA in attesa</span></div>`;
    await Promise.all([loadVerifications(), loadReports(), loadAI(), loadUsers()]);
  } catch (error) { message(error); }
}

async function loadVerifications() {
  const { items } = await api("/api/moderation/verifiche");
  $("#verification-list").innerHTML = items.length ? items.map((item) => `<article><div><strong>${esc(item.nome)} ${esc(item.cognome)}</strong><span>${esc(item.email)} · ${esc(item.tipo_verifica)}</span></div><div class="moderation-actions"><a href="/api/moderation/verifiche/${item.id_identita}/documenti/fronte" target="_blank" rel="noopener">Fronte</a><a href="/api/moderation/verifiche/${item.id_identita}/documenti/retro" target="_blank" rel="noopener">Retro</a><button data-id="${item.id_identita}" data-outcome="Verificato">Approva</button><button data-id="${item.id_identita}" data-outcome="Rifiutato">Rifiuta</button></div></article>`).join("") : "<p>Nessuna verifica in attesa.</p>";
  $("#verification-list").querySelectorAll("button").forEach((button) => button.addEventListener("click", async () => { await api(`/api/moderation/verifiche/${button.dataset.id}`, {method:"PATCH",body:JSON.stringify({esito:button.dataset.outcome})}); await loadVerifications(); }));
}

async function loadReports() {
  const { items } = await api("/api/moderation/segnalazioni");
  $("#moderation-reports").innerHTML = items.length ? items.map((item) => `<article><div><strong>${esc(item.titolo)}</strong><span>${esc(item.nome)} ${esc(item.cognome)} · ${esc(item.stato)} · ${esc(item.stato_pubblicazione)}</span></div><div class="moderation-actions"><select data-state-id="${item.id_segnalazione}" aria-label="Nuovo stato per ${esc(item.titolo)}"><option>In valutazione</option><option>Presa in carico</option><option>Inviata ai candidati</option><option>Conclusa</option><option>Rifiutata</option></select><button data-state="${item.id_segnalazione}">Aggiorna stato</button>${item.stato_pubblicazione === "Pubblicata" ? `<button data-id="${item.id_segnalazione}" data-visibility="Nascosta">Nascondi</button>` : `<button data-id="${item.id_segnalazione}" data-visibility="Pubblicata">Ripubblica</button>`}</div></article>`).join("") : "<p>Nessuna segnalazione.</p>";
  $("#moderation-reports").querySelectorAll("button[data-visibility]").forEach((button) => button.addEventListener("click", async () => { await api(`/api/moderation/segnalazioni/${button.dataset.id}/visibilita`, {method:"PATCH",body:JSON.stringify({visibilita:button.dataset.visibility})}); await loadReports(); }));
  $("#moderation-reports").querySelectorAll("button[data-state]").forEach((button) => button.addEventListener("click", async () => { const select = document.querySelector(`[data-state-id="${button.dataset.state}"]`); await api(`/api/segnalazioni/${button.dataset.state}/stato`, {method:"PATCH",body:JSON.stringify({stato:select.value})}); await loadReports(); }));
}

async function loadAI() {
  const { items } = await api("/api/moderation/analisi-ia");
  $("#ai-list").innerHTML = items.length ? items.map((item) => `<article><div><strong>${esc(item.titolo)} · ${esc(item.tipo_analisi)}</strong><span>${esc(item.stato)} · ${esc(item.descrizione)}</span></div><div class="moderation-actions"><button data-id="${item.id_analisi}" data-decision="Confermata">Conferma</button><button data-id="${item.id_analisi}" data-decision="Respinta">Respingi</button><button data-id="${item.id_analisi}" data-decision="Da rivedere">Rivedi</button></div></article>`).join("") : "<p>Nessun risultato IA in revisione.</p>";
  $("#ai-list").querySelectorAll("button").forEach((button) => button.addEventListener("click", async () => { await api(`/api/moderation/analisi-ia/${button.dataset.id}`, {method:"PATCH",body:JSON.stringify({decisione:button.dataset.decision})}); await loadAI(); }));
}

async function loadUsers() {
  const { items } = await api("/api/moderation/utenti");
  $("#user-list").innerHTML = items.length ? items.map((item) => `<article><div><strong>${esc(item.nome)} ${esc(item.cognome)}</strong><span>${esc(item.email)} · ${esc(item.stato_account)} · ${esc(item.stato_verifica)}</span></div>${item.stato_account === "Attivo" ? `<button data-id="${item.id_utente}">Banna</button>` : ""}</article>`).join("") : "<p>Nessun utente.</p>";
  $("#user-list").querySelectorAll("button").forEach((button) => button.addEventListener("click", async () => { const motivo = prompt("Motivo del ban:"); if (motivo?.trim()) { await api(`/api/moderation/utenti/${button.dataset.id}/ban`, {method:"POST",body:JSON.stringify({motivo})}); await loadUsers(); } }));
}

load().catch(message);
