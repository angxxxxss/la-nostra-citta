# La Nostra Città, Il Nostro Futuro

Piattaforma web del comitato cittadino **Insieme per Milano** per raccogliere, documentare e ordinare le priorità dei quartieri. Il progetto usa Python/Flask, HTML/CSS/JavaScript vanilla e MySQL 8.

## Avvio con MySQL remoto

Requisiti: Python 3.11+ e un database MySQL 8 remoto raggiungibile dal Codespace (per esempio Aiven). L'applicazione non usa SQLite né ripiega su un MySQL locale: host, porta, database e credenziali devono essere configurati nel file .env.

Crea l'ambiente Python e installa le dipendenze:

\x60\x60\x60bash
python -m venv .venv
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
# macOS/Linux o Codespaces: source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
\x60\x60\x60

Nel .env inserisci i valori di connessione mostrati dal provider MySQL. Per Aiven, scarica il certificato CA e indica il suo percorso assoluto in DATABASE_SSL_CA; il client verifica il certificato e il nome dell'host quando il campo è compilato. Non inserire il file .env, password o certificati privati in Git.

Crea il database remoto dal pannello del provider, se non esiste. Con MySQL Workbench connettiti all'host remoto, seleziona quel database e applica, nell'ordine, database/schema/schema.sql e database/seeds/initial_data.sql. Attenzione: `database/seeds/initial_data.sql` contiene ancora record dimostrativi, inclusi account, identità, segnalazioni e interazioni; non eseguirlo sul database remoto reale. Per i quartieri esegui `database/migrations/001_quartieri_milano.sql`, anche se il database esiste già: installa/aggiorna in modo idempotente gli 88 NIL ufficiali di Milano. Non eseguire più volte lo schema su un database già popolato senza prima valutarne l'effetto.
Crea il database remoto dal pannello del provider, se non esiste. Con MySQL Workbench connettiti all'host remoto, seleziona quel database e applica, nell'ordine, `database/schema/schema.sql` e `database/migrations/001_application_schema.sql`. La migrazione applicativa crea le tabelle lowercase richieste dal codice e include i seed di servizio per ruoli, stati e categorie, ma non crea account o segnalazioni dimostrative. Per i quartieri esegui anche `database/migrations/001_quartieri_milano.sql`, che installa o aggiorna in modo idempotente gli 88 NIL ufficiali di Milano. Il file `database/seeds/initial_data.sql` contiene ancora record dimostrativi, inclusi account, identità, segnalazioni e interazioni: non eseguirlo sul database remoto reale. Non eseguire più volte lo schema su un database già popolato senza prima valutarne l'effetto.

Avvia Flask nel Codespace:

\x60\x60\x60bash
flask --app run.py run --debug
\x60\x60\x60

Apri la porta 5000 dal pannello Ports di Codespaces. Non attivare --debug in produzione. Per la produzione usa HTTPS, una SECRET_KEY casuale, SESSION_COOKIE_SECURE=true e uno storage privato persistente per gli upload.

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


------------------------------


Requisiti utente (RU)
Descrivono le esigenze dei cittadini e dei membri del comitato, indicando cosa devono poter fare attraverso la piattaforma.

RU1 – Registrazione e identificazione: il cittadino deve poter creare un profilo personale, inserendo i propri dati e verificando la propria identità tramite carta d'identità, SPID o CIE.

RU2 – Accesso alla piattaforma: il cittadino deve poter accedere al proprio account in modo sicuro, così che le proprie attività siano riconducibili alla sua identità.

RU3 – Segnalazione delle problematiche: il cittadino deve poter segnalare problemi presenti nella città, come buche stradali, illuminazione carente, aree verdi abbandonate, problemi di viabilità, criticità idrogeologiche e movida selvaggia, indicando il luogo e allegando fotografie o video.

RU4 – Consultazione delle segnalazioni: il cittadino deve poter visualizzare le segnalazioni pubblicate dagli altri utenti, comprese descrizioni, fotografie, video, autori e posizioni.

RU5 – Partecipazione e interazione: il cittadino deve poter commentare le segnalazioni degli altri utenti ed esprimere il proprio sostegno o interesse verso le problematiche pubblicate.

RU6 – Gestione dei propri contenuti: il cittadino deve poter modificare o cancellare le proprie segnalazioni e i propri commenti.

RU7 – Individuazione delle priorità: il cittadino deve poter consultare una classifica delle problematiche più sentite dalla comunità, per conoscere le necessità di intervento maggiormente condivise.

RU8 – Monitoraggio delle problematiche: il cittadino deve poter seguire l'evoluzione delle segnalazioni, dalla pubblicazione all'eventuale presa in carico o all'invio delle proposte ai candidati Sindaco.

RU9 – Supervisione del comitato: i membri del comitato devono poter controllare l'attività della piattaforma, le segnalazioni e le interazioni degli utenti.

RU10 – Moderazione: i membri del comitato con ruolo di moderatore devono poter bannare gli utenti che non rispettano le regole della piattaforma.

2. Requisiti funzionali (RF)
Descrivono le operazioni specifiche che il sistema deve eseguire per soddisfare le esigenze degli utenti.

RF1 – Registrazione: il sistema deve consentire la creazione di un account personale, richiedendo nome, cognome, codice fiscale, e-mail, indirizzo di residenza e password.

RF2 – Verifica dell'identità: il sistema deve permettere la verifica dell'identità tramite caricamento della carta d'identità fronte-retro oppure autenticazione tramite SPID o CIE.

RF3 – Login: il sistema deve autenticare gli utenti registrati e verificati tramite le credenziali inserite e associare ogni attività al relativo profilo.

RF4 – Gestione dei ruoli: il sistema deve distinguere i cittadini dai membri del comitato, assegnando a questi ultimi i privilegi di supervisione e moderazione.

RF5 – Inserimento delle segnalazioni: il sistema deve permettere agli utenti registrati di pubblicare segnalazioni contenenti titolo, descrizione dettagliata, posizione o luogo del problema e almeno una fotografia o un breve video obbligatorio.

RF6 – Gestione delle tipologie: il sistema deve consentire l'inserimento di segnalazioni relative a buche stradali, illuminazione carente, aree verdi abbandonate, problemi di viabilità, criticità idrogeologiche e fenomeni di movida selvaggia.

RF7 – Visualizzazione delle segnalazioni: il sistema deve mostrare le segnalazioni pubblicate con descrizione, contenuti multimediali, autore e posizione.

RF8 – Interazione tra utenti: il sistema deve consentire agli utenti registrati di pubblicare commenti e manifestazioni di sostegno o interesse sulle segnalazioni.

RF9 – Gestione dei commenti: il sistema deve consentire agli utenti di modificare o cancellare i propri commenti, impedendo loro di modificare o cancellare quelli degli altri.

RF10 – Gestione delle segnalazioni: il sistema deve consentire agli utenti di modificare o cancellare esclusivamente le segnalazioni di cui sono autori.

RF11 – Classifica delle priorità: il sistema deve calcolare e visualizzare una classifica delle problematiche cittadine sulla base del sostegno e dell'interesse espressi dagli utenti.

RF12 – Gestione dello stato: il sistema deve registrare e rendere consultabile lo stato di avanzamento di ogni segnalazione, dalla pubblicazione all'eventuale presa in carico o all'invio ai candidati Sindaco.

RF13 – Area riservata al comitato: il sistema deve fornire un'area dedicata ai membri del comitato per controllare le attività della piattaforma, le segnalazioni e le interazioni.

RF14 – Ban degli utenti: il sistema deve consentire ai moderatori appartenenti al comitato di bannare gli utenti che non rispettano le regole della piattaforma.

RF15 – Moderazione automatica: il sistema deve poter integrare un modulo di intelligenza artificiale che analizzi i testi delle segnalazioni, individui contenuti volgari, offensivi o d'odio e li blocchi oppure li sottoponga alla revisione del comitato.

RF16 – Classificazione tematica automatica: il sistema deve poter integrare un modulo di intelligenza artificiale che analizzi le descrizioni e associ automaticamente una o più categorie alle segnalazioni, come Ambiente, Mobilità Urbana, Politiche Giovanili e Decoro Urbano.

RF17 – Localizzazione automatica: il sistema deve poter estrarre dai metadati EXIF delle fotografie le coordinate geografiche disponibili, per facilitare la localizzazione delle segnalazioni su una mappa interattiva.

RF18 – Verifica dei contenuti multimediali: il sistema deve poter integrare un modulo di visione artificiale che verifichi la coerenza tra le immagini caricate e le descrizioni delle problematiche segnalate.