# Predisposizione all'integrazione IA

```mermaid
flowchart TD
    A[Browser: form HTML e JavaScript] --> B[Flask API: autenticazione, CSRF, validazione]
    B --> C[Servizio segnalazioni e transazione MySQL]
    C --> D[(MySQL: segnalazione, allegati, analisi_ia)]
    C --> E[Storage privato dei media]
    D --> F[Coda: moderazione testo]
    D --> G[Coda: classificazione categorie]
    E --> H[Coda: EXIF e coerenza visiva]
    F --> I[Worker IA da integrare]
    G --> I
    H --> I
    I --> D
    D --> J[Revisione umana del comitato]
```

La webapp crea record `analisi_ia` in stato `In attesa` per moderazione testo, classificazione e verifica multimediale. È quindi rappresentato il flusso dati e la persistenza dell'esito; non sono inclusi modelli, provider esterni o worker. Prima dell'attivazione occorre definire soglie, gestione dei falsi positivi, modello e versione, tempi di conservazione, minimizzazione dei dati e procedura di contestazione. L'estrazione EXIF di immagini è invece implementata durante il caricamento; se le coordinate EXIF sono presenti vengono usate come posizione iniziale, modificabile dall'utente nel form.
