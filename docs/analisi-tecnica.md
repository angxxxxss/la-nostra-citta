# Analisi tecnica — La Nostra Città, Il Nostro Futuro

Data: 12 ottobre 2026. Il repository `angxxxxss/la-nostra-citta` era vuoto al momento dell'ispezione; questa base viene creata da zero seguendo i requisiti allegati e la richiesta esplicita di usare Flask/MySQL. L'analisi requisiti deriva dal testo fornito e dal PDF, dato che `analisi_requisiti_esercizio_1.md` non era presente nel repository.

## 1. Stato attuale e struttura consegnata

Il progetto iniziale era vuoto. La nuova base contiene:

```text
app/                    factory, configurazione, connessione DB e autorizzazione
app/routes/             web, auth, segnalazioni, moderazione
app/services/            spazio per servizi di dominio
app/repositories/        spazio per repository separati
app/validators/          validazione input comune
static/css, static/js/   interfaccia responsive e modulo API JavaScript
templates/              pagina HTML servita da Flask
 database/schema/        DDL MySQL 8 e trigger
 database/seeds/         ruoli, quartieri, categorie e stati iniziali
docs/                   requisiti, modello logico, architettura IA, analisi tecnica
tests/                  test Flask e test MySQL opt-in
run.py                   avvio
requirements.txt         dipendenze Python fissate
.env.example             configurazione senza segreti
.gitignore               esclusioni locali
```

La webapp è HTML/CSS/JS vanilla servita da Flask e implementa una prima versione navigabile con registrazione/login, richiesta verifica documento, consultazione/ricerca, mappa, segnalazione con allegato, commenti, sostegni, classifica, stati e moderazione. I dati sono persistiti su MySQL tramite `mysql-connector-python` con connection pool e query parametrizzate.

Non sono presenti credenziali reali o file `.env` nel progetto. Upload e sessioni sono in `instance/`, esclusa da Git. In produzione sono richiesti Redis per sessioni/rate-limit, HTTPS, secret forte, storage privato e backup.

### Funzioni operative e limiti

- Registrazione, password Argon2id, login/logout, sessioni server-side (Redis in produzione), token CSRF, rate limit e controlli ruolo sono implementati.
- La verifica con scansione carta usa upload privati e revisione del comitato. SPID/CIE reali restituiscono `501 PROVIDER_NOT_CONFIGURED`: servono identity provider accreditato, callback, credenziali e revisione di conformità.
- Foto/video vengono verificati dal contenuto, archiviati con nomi generati, associati a hash/MIME/dimensione e lettura coordinate EXIF. Le coordinate inviate dal cittadino sono facoltative; se mancano si tenta il fallback EXIF.
- Le segnalazioni e le interazioni sono limitate a utenti verificati. Il proprietario è verificato nelle query di modifica/cancellazione.
- I record IA sono predisposti come attività in attesa; non è ancora collegato un worker/modello. L'automazione RF15, RF16 e RF18 richiede la scelta e integrazione di modelli e soglie.
- I test automatici coprono pagina, validazione iniziale, autenticazione protetta, password e controlli upload. Il test DB della chiave anti-duplicato è opt-in e richiede MySQL test separato.
- Accessibilità visuale/semantica è curata in prima istanza; serve ancora un audit WCAG completo e un test browser end-to-end.

## 2. Conformità requisito per requisito

| ID | Requisito | Presente | Parziale | Assente | File coinvolti | Problema/nota | Soluzione o completamento | Priorità |
|---|---|:---:|:---:|:---:|---|---|---|---|
| RU1 | Profilo e verifica identità |  | ✓ |  | `auth.py`, `routes/auth.py`, `routes/moderation.py`, schema | Documento carta supportato; provider SPID/CIE non configurato | Collegare identity provider accreditato | Critica |
| RU2 | Accesso sicuro | ✓ |  |  | `auth.py`, `routes/auth.py`, `config.py` | Sessione/CSRF e rate limit presenti | Configurare HTTPS e storage sessioni persistente in produzione | Alta |
| RU3 | Segnalare problemi, luogo e media | ✓ |  |  | `routes/reports.py`, `uploads.py`, `templates/index.html` | Upload foto/video; localizzazione tramite indirizzo/coordinate | Validazioni e requisito allegato già applicati | Alta |
| RU4 | Consultare segnalazioni/autore/posizione/media | ✓ |  |  | `routes/reports.py`, `app.js` | Elenco e mappa, dettaglio JSON e file | Aggiungere paginazione UI e controlli qualità mappa | Media |
| RU5 | Commentare e sostenere/interessarsi | ✓ |  |  | `routes/reports.py`, `app.js` | Solo profili verificati scrivono | Migliorare interfaccia di gestione commenti | Media |
| RU6 | Modificare/cancellare contenuti propri | ✓ |  |  | `routes/reports.py` | API ownership-check presenti | Aggiungere controlli UI per azioni proprietario | Media |
| RU7 | Classifica priorità | ✓ |  |  | `routes/reports.py`, `app.js` | Ordinamento per sostegni e interessi | Rendere configurabile il punteggio se il comitato vuole pesi diversi | Media |
| RU8 | Evoluzione e invio ai candidati | ✓ |  |  | `routes/reports.py`, schema | Stati e storico; nessun invio automatico di documento programmatico | Definire processo approvativo e formato export | Alta |
| RU9 | Supervisione comitato | ✓ |  |  | `routes/moderation.py` | Dashboard e verifiche disponibili | Aggiungere filtri e audit di tutte le operazioni | Alta |
| RU10 | Ban moderatori | ✓ |  |  | `routes/moderation.py`, schema | Ban motivato e moderatore tracciato | Aggiungere procedura di sblocco/ricorso | Alta |
| RF1 | Registrazione campi profilo e password | ✓ |  |  | `routes/auth.py`, schema | Password hash Argon2id | Aggiungere e-mail di conferma/reset password | Alta |
| RF2 | Verifica carta/SPID/CIE |  | ✓ |  | `routes/auth.py`, `routes/moderation.py` | Flusso carta disponibile; SPID/CIE non connessi | Adapter/provider e callback sicure | Critica |
| RF3 | Login associato al profilo verificato | ✓ |  |  | `routes/auth.py`, `auth.py` | Login e sessione; le operazioni di scrittura richiedono verifica | Mantenere sessioni e controlli aggiornati | Alta |
| RF4 | Ruoli cittadino/comitato | ✓ |  |  | `auth.py`, schema | Cittadino, Comitato, Moderatore | Creare account privilegiati tramite bootstrap amministrativo sicuro | Alta |
| RF5 | Segnalazione con media obbligatorio | ✓ |  |  | `routes/reports.py`, `uploads.py`, DDL | Bozza→media→pubblicazione, trigger di integrità | Già coperto lato app e DB | Critica |
| RF6 | Tipologie/categorie problema | ✓ |  |  | `database/seeds/initial_data.sql`, `routes/reports.py` | Categorie iniziali disponibili | Il comitato può amministrarle in una fase successiva | Media |
| RF7 | Visualizzazione dettagli | ✓ |  |  | `routes/reports.py`, `app.js` | Elenco e media via endpoint protetto da path | Completare paginazione e preview video | Media |
| RF8 | Commenti e sostegno/interesse | ✓ |  |  | `routes/reports.py` | Autenticazione e verifica richieste | Aggiungere test DB di integrazione | Alta |
| RF9 | Modifica/eliminazione solo propri commenti | ✓ |  |  | `routes/reports.py` | Vincolo autore nella query | UI per modifica/eliminazione | Alta |
| RF10 | Modifica/eliminazione solo proprie segnalazioni | ✓ |  |  | `routes/reports.py` | Vincolo autore nella query | UI per modifica/eliminazione | Alta |
| RF11 | Classifica | ✓ |  |  | `routes/reports.py` | Conteggi distinti e ordinamento | Formalizzare eventuali pesi prima del rilascio | Media |
| RF12 | Stato e storico | ✓ |  |  | `routes/reports.py`, DDL | Transizioni del comitato e audit iniziale | Aggiungere validazione delle transizioni consentite | Alta |
| RF13 | Area comitato | ✓ |  |  | `routes/moderation.py` | Endpoint dashboard/verifiche protetti da ruolo | Frontend dedicato di amministrazione | Media |
| RF14 | Ban moderatore | ✓ |  |  | `routes/moderation.py`, `moderazione` | Operazione tracciata con motivazione | Aggiungere sblocco e gestione ricorsi | Alta |
| RF15 | Moderazione IA testi |  | ✓ |  | `analisi_ia`, `routes/moderation.py` | Coda e revisione pronte, nessun modello/worker | Integrare classificatore NLP e policy soglia | Alta |
| RF16 | Classificazione IA |  | ✓ |  | `analisi_ia`, `segnalazione_categoria` | Coda e relazioni presenti, inferenza assente | Worker multi-label versionato | Media |
| RF17 | Estrazione coordinate EXIF | ✓ |  |  | `uploads.py`, `routes/reports.py` | Estrazione e fallback coordinate applicati | Aggiungere test con immagini EXIF note | Media |
| RF18 | Verifica coerenza immagine/testo |  | ✓ |  | `analisi_ia`, `routes/moderation.py` | Predisposizione e revisione, modello non collegato | Integrare modello vision e gestione falsi positivi | Media |

## 3. Database MySQL

Lo schema è in `database/schema/schema.sql`, con seed separati. Le tabelle principali sono RUOLO, QUARTIERE, UTENTE, IDENTITA, STATO_SEGNALAZIONE, CATEGORIA, LUOGO, SEGNALAZIONE, FILE_MULTIMEDIALE, SEGNALAZIONE_CATEGORIA, COMMENTO, SOSTEGNO, STORICO_STATO, ANALISI_IA e MODERAZIONE. PK, FK, unique, check e indici sono specificati nel DDL; tutte le tabelle usano InnoDB e utf8mb4. I risultati IA/EXIF sono JSON, le coordinate DECIMAL.

La struttura è in 3NF per le entità principali: ruolo, quartiere, stato e categoria sono riferimenti; gli N:M usano tabelle ponte; il quartiere di una segnalazione si deriva da luogo invece di duplicarlo. Non si conservano numeri di carta; i documenti vengono archiviati in area privata e referenziati tramite percorso non pubblico.

Vincoli da attenzionare: MySQL applica `CHECK` solo da 8.0.16; l'allegato minimo non è esprimibile con una semplice FK, perciò service e trigger agiscono al passaggio a Pubblicata. La chiave sostegno rende univoco ciascun tipo per persona/segnalazione. Il trigger deve essere caricato con il DDL MySQL che contiene `DELIMITER`.

## 4. Stack e scelte tecniche

- **Flask application factory** (`create_app`) e Blueprint separati per web, auth, segnalazioni e moderazione.
- **Driver:** `mysql-connector-python` con pool; query sempre parametrizzate. La query di aggiornamento permette solo colonne predefinite.
- **Autenticazione:** `Flask-Session` server-side, sessione rigenerata al login, cookie HttpOnly/SameSite, Secure configurabile per HTTPS; decoratori login/ruolo.
- **CSRF:** `Flask-WTF CSRFProtect` con token JSON consegnato a JavaScript e header `X-CSRFToken`.
- **Password:** `argon2-cffi` Argon2id; rate limit su login e registrazione.
- **Validazione:** controlli espliciti server-side; client solo per assistenza. Errori JSON coerenti.
- **Upload:** limite Flask, firma MIME reale, Pillow per verifica immagini/EXIF, UUID, directory privata, hash; file rimossi se fallisce il commit.
- **Configurazione:** `python-dotenv`, `.env.example`, segreti esclusi da Git; nessuna CORS perché frontend e API sono same-origin.
- **Test:** pytest e database MySQL separato; unit test locali e test integrazione opt-in.
- **Client futuro:** API REST versionate/logica fuori dai template; nessun framework mobile inserito ora.

## 5. Architettura applicativa e IA

```text
Browser HTML/CSS/JS → fetch JSON o multipart → Flask Blueprint /api
→ sessione, CSRF, ruoli e validazione → route → service/repository
→ pool MySQL → dati e metadati
```

Le route includono al momento parte della logica applicativa direttamente: il progetto ha i package `services` e `repositories`, ma il refactoring completo dei domini in questi livelli resta un miglioramento necessario prima che le API crescano. Le query restano parametrizzate.

```text
Segnalazione → transazione DB + media privati → record analisi_ia in attesa
→ worker futuro (moderazione/classificazione/vision) → risultato JSON versionato
→ revisione umana e aggiornamento motivato
```

La lettura EXIF è sincrona e locale. Gli altri moduli IA sono predisposti tramite record/endpoint di revisione ma non eseguono inferenza.

## 6. Struttura consegnata

```text
app/{routes,services,repositories,validators}/
app/{__init__.py,auth.py,config.py,db.py,uploads.py}
static/{css/styles.css,js/{api.js,app.js}}
templates/index.html
database/{schema/schema.sql,seeds/initial_data.sql}
docs/{requisiti.md,modello-logico.md,architettura-ia.md,analisi-tecnica.md}
tests/{conftest.py,test_app.py,test_mysql_integration.py}
run.py requirements.txt .env.example .gitignore README.md
```

## 7. Piano di completamento

1. Verificare installazione dipendenze, schema e pool con un MySQL locale/test.
2. Eseguire test, correggere eventuali incompatibilità tra MySQL connector e ambiente.
3. Estrarre service/repository per auth, report, interazioni e moderazione.
4. Completare UI dashboard/modifica/eliminazione, stati e anteprime video.
5. Eseguire test E2E, accessibilità WCAG e revisione sicurezza/privacy.
6. Integrare provider SPID/CIE accreditato.
7. Integrare worker IA asincroni e valutare modelli/soglie.
8. Preparare deploy con HTTPS, session store durevole, object storage privato, backup e monitoraggio.

Le prime basi funzionali e i documenti di progettazione sono inclusi; l'elenco sopra separa le integrazioni che dipendono da servizi e credenziali esterni dal lavoro implementato nel repository.
