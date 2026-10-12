# La Nostra Città, Il Nostro Futuro

Piattaforma web del comitato cittadino **Insieme per Milano** per raccogliere, documentare e ordinare le priorità dei quartieri. Il progetto usa Python/Flask, HTML/CSS/JavaScript vanilla e MySQL 8.

## Avvio locale

Requisiti: Python 3.11+ e MySQL 8.0.16+.

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
# Windows PowerShell: Copy-Item .env.example .env
# macOS/Linux: cp .env.example .env
```

Imposta in `.env` credenziali MySQL locali, `SECRET_KEY` casuale di almeno 32 caratteri e `DATABASE_NAME=la_nostra_citta`. In produzione configura anche Redis e `SESSION_COOKIE_SECURE=true`. Crea il database applicando gli script nell'ordine seguente:

```bash
mysql -u root -p -e "CREATE DATABASE la_nostra_citta CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci"
mysql -u root -p la_nostra_citta < database/schema/schema.sql
mysql -u root -p la_nostra_citta < database/seeds/initial_data.sql
```

Avvia il server di sviluppo:

```bash
flask --app run.py run --debug
```

Apri <http://127.0.0.1:5000>. Non attivare `--debug` in produzione. In produzione usa HTTPS, `FLASK_ENV=production`, `SESSION_COOKIE_SECURE=true`, una `SECRET_KEY` casuale dedicata, `REDIS_URL` per sessioni/rate-limit e uno storage privato persistente per gli upload.

## Funzioni presenti

- registrazione con nome, cognome, codice fiscale, e-mail, residenza e password Argon2id;
- login/logout con sessione server-side e cookie `HttpOnly`, `SameSite=Lax`, token CSRF e limiti alle richieste;
- invio dei documenti di identità in area privata e approvazione/rifiuto da parte del comitato;
- creazione e consultazione di segnalazioni con posizione, categorie e foto/video controllati lato server;
- lettura EXIF delle coordinate, mappa, commenti, sostegni/interesse, classifica e avanzamento degli stati;
- dashboard, gestione di verifiche, revisione IA e ban per il comitato/moderatori.

## Funzioni che richiedono configurazione o integrazione

- Il flusso reale SPID/CIE deve essere collegato a un identity provider accreditato e alle sue credenziali. L'endpoint documenta e segnala tale mancanza invece di simulare un'identità verificata.
- I record `analisi_ia` sono creati come coda/predisposizione. Moderazione automatica, classificazione e verifica visiva necessitano ancora di un worker e di modelli/servizi selezionati. Le proposte restano soggette a revisione umana.
- Gli upload sono salvati in `instance/uploads` per sviluppo. In produzione spostali in object storage privato, aggiungi scansione antimalware, backup e policy di conservazione. I documenti identità non sono esposti come file statici.
- Le verifiche di accessibilità e privacy formali e i test end-to-end su MySQL vanno completati prima di un rilascio pubblico.

## API principali

Le richieste mutative inviate da JavaScript includono `X-CSRFToken`, recuperato da `GET /api/csrf`. Il browser usa cookie di sessione same-origin; CORS non è abilitato.

| Metodo e percorso | Uso |
|---|---|
| `GET /api/health`, `GET /api/csrf`, `GET /api/auth/me` | stato, token CSRF, utente corrente |
| `POST /api/auth/register`, `/login`, `/logout`, `/verify-document` | account e identificazione |
| `GET /api/quartieri`, `/api/categorie` | dati per filtri e form |
| `GET /api/segnalazioni`, `/api/segnalazioni/<id>`, `/api/segnalazioni/priorita` | elenco, dettaglio e classifica |
| `POST /api/segnalazioni`, `PATCH/DELETE /api/segnalazioni/<id>` | crea e gestisci le proprie segnalazioni |
| `GET/POST /api/segnalazioni/<id>/commenti`, `PATCH/DELETE /api/commenti/<id>` | commenti |
| `POST/DELETE /api/segnalazioni/<id>/sostegni` | sostegno e interesse |
| `PATCH /api/segnalazioni/<id>/stato` | avanzamento, solo comitato/moderatori |
| `/api/moderation/*` | dashboard e operazioni riservate |

Risposte d'errore JSON usano `error.code` e `error.message`. La specifica estesa dei requisiti e del modello si trova in `docs/`.

## Account moderatore iniziale

Registra l'account che userà il comitato, poi assegna il ruolo da terminale: `flask --app run.py promote-moderator`. Il comando è disponibile solo sul server e chiede l'e-mail dell'account esistente. Non creare utenti privilegiati attraverso il form pubblico.

## Test

```bash
pytest
```

I test MySQL sono opt-in e accettano solo un database il cui nome contiene `test`. In un `.env` separato imposta `DATABASE_NAME=la_nostra_citta_test` e `RUN_MYSQL_INTEGRATION=1`; applica al database di test gli stessi schema e seed prima di eseguire i test. Non puntare mai i test a un database di produzione.

## Sicurezza e dati personali

Non aggiungere `.env`, documenti, file caricati, dump contenenti dati personali o segreti a Git. Raccogli solo i dati necessari, proteggi il database e limita l'accesso ai documenti d'identità ai moderatori autorizzati. La verifica tramite scansioni carta è revisionata dal comitato; l'integrazione SPID/CIE è un requisito esterno da completare prima dell'uso pubblico.
