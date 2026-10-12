# Analisi dei requisiti

## Visione e obiettivi

La piattaforma **La Nostra Città, Il Nostro Futuro**, promossa dal comitato **Insieme per Milano**, raccoglie bisogni urbani direttamente dagli abitanti, li rende documentabili e consultabili, fa emergere le priorità condivise e prepara proposte da presentare ai candidati Sindaco. Il progetto parte come webapp accessibile e visuale; le API JSON mantengono possibile un client futuro.

## Attori e permessi

| Attore | Permessi |
|---|---|
| Visitatore | Consultare segnalazioni pubblicate, mappa e classifica; non creare interazioni |
| Cittadino registrato non verificato | Gestire la richiesta di verifica identità e consultare i contenuti |
| Cittadino verificato | Pubblicare segnalazioni con media, commentare, sostenere/interessarsi e gestire i propri contenuti |
| Comitato | Consultare dashboard e verifiche, aggiornare stato e visibilità delle segnalazioni |
| Moderatore | Permessi del comitato, revisione delle analisi e ban motivato degli account |
| Servizi IA futuri | Analizzare testi e media in asincrono; salvare risultati auditabili senza sostituire la revisione umana |

## Requisiti utente

- **RU1 Registrazione e identificazione:** creare un profilo con dati personali e verificare identità tramite carta d'identità, SPID o CIE.
- **RU2 Accesso:** entrare in modo sicuro e rendere le azioni riconducibili a un profilo.
- **RU3 Segnalazioni:** descrivere problematiche urbane, indicare il luogo e allegare foto o video.
- **RU4 Consultazione:** vedere contenuti, autori, media e posizioni delle segnalazioni pubblicate.
- **RU5 Partecipazione:** commentare ed esprimere sostegno o interesse.
- **RU6 Contenuti propri:** modificare o cancellare le proprie segnalazioni e i propri commenti.
- **RU7 Priorità:** consultare la classifica dei problemi più condivisi.
- **RU8 Monitoraggio:** seguire il ciclo di vita della segnalazione, dalla ricezione all'eventuale presa in carico o invio ai candidati.
- **RU9 Supervisione:** permettere al comitato di controllare attività, segnalazioni e interazioni.
- **RU10 Moderazione:** permettere ai moderatori di bannare gli account che violano le regole.

## Requisiti funzionali

| ID | Requisito |
|---|---|
| RF1 | Registrare nome, cognome, codice fiscale, e-mail, indirizzo e password. |
| RF2 | Verificare l'identità tramite documenti fronte/retro o provider SPID/CIE. |
| RF3 | Autenticare account e associare le operazioni all'utente corrente. |
| RF4 | Distinguere cittadini, comitato e moderatori con autorizzazioni server-side. |
| RF5 | Creare segnalazioni con titolo, descrizione, luogo e almeno un media obbligatorio. |
| RF6 | Gestire le tipologie urbane previste: buche, illuminazione, verde, viabilità, rischi idrogeologici e movida. |
| RF7 | Mostrare descrizione, media, autore, luogo e stato. |
| RF8 | Consentire commenti, sostegno e interesse solo a utenti verificati. |
| RF9 | Consentire la modifica/cancellazione dei soli commenti propri. |
| RF10 | Consentire la modifica/cancellazione delle sole segnalazioni proprie. |
| RF11 | Ordinare le priorità in base a sostegno e interesse. |
| RF12 | Conservare e rendere consultabili stato corrente e storico. |
| RF13 | Fornire un'area di supervisione riservata al comitato. |
| RF14 | Registrare ban con motivazione e moderatore responsabile. |
| RF15 | Predisporre moderazione automatica dei testi con blocco o revisione umana. |
| RF16 | Predisporre classificazione automatica multi-categoria. |
| RF17 | Estrarre coordinate EXIF e mostrare segnalazioni geolocalizzate su mappa. |
| RF18 | Predisporre verifica di coerenza tra media e descrizione. |

## Requisiti non funzionali e regole

- **Stack:** Python 3.11+, Flask, HTML5/CSS3/JavaScript vanilla, MySQL 8+ con InnoDB e `utf8mb4`.
- **Sicurezza:** query parametrizzate; password Argon2id; cookie sessione HttpOnly/SameSite e Secure su HTTPS; CSRF su operazioni mutative; rate limit; ruoli verificati dal server; errori senza stack trace.
- **Upload:** limite dimensione, verifica del contenuto reale, nome generato dal server, storage privato, eliminazione del file se il commit DB fallisce.
- **Integrità:** email/codice fiscale univoci; coordinate in intervallo; almeno un media alla pubblicazione; associazioni non duplicate; transizioni di stato tracciate.
- **Privacy:** minimizzare dati; accesso limitato ai documenti; segreti fuori dal repository; conservazione e cancellazione da definire con il comitato.
- **Accessibilità:** HTML semantico, etichette e messaggi accessibili, navigazione da tastiera e layout responsive; audit WCAG formale da svolgere.
- **Affidabilità e prestazioni:** transazioni per operazioni multi-tabella, pool connessioni, indici per filtri/ordinamento, test automatici e database test separato.
- **IA:** elaborazione asincrona, risultati con modello/versione, esito e revisore; la decisione finale resta auditabile.

## Tracciabilità sintetica

RF1–4 → `utente`, `ruolo`, `identita`; RF5–7 → `segnalazione`, `luogo`, `file_multimediale`; RF8–11 → `commento`, `sostegno`, `categoria`, `segnalazione_categoria`; RF12 → `stato_segnalazione`, `storico_stato`; RF13–14 → ruoli e `moderazione`; RF15–18 → `analisi_ia` e coordinate/allegati.
