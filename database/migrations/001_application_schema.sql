-- Schema applicativo atteso dal codice Flask.
-- Migrazione additiva: non modifica né elimina le tabelle legacy con nomi maiuscoli.

CREATE TABLE IF NOT EXISTS ruolo (
    id_ruolo SMALLINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nome_ruolo VARCHAR(40) NOT NULL UNIQUE,
    descrizione VARCHAR(255) NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS quartiere (
    id_quartiere SMALLINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL UNIQUE,
    attivo BOOLEAN NOT NULL DEFAULT TRUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS utente (
    id_utente BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(50) NOT NULL,
    cognome VARCHAR(50) NOT NULL,
    codice_fiscale CHAR(16) NOT NULL UNIQUE,
    email VARCHAR(254) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    indirizzo VARCHAR(180) NOT NULL,
    id_quartiere SMALLINT UNSIGNED NULL,
    data_registrazione TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    stato_verifica ENUM('In attesa','Verificato','Rifiutato') NOT NULL DEFAULT 'In attesa',
    stato_account ENUM('Attivo','Sospeso','Bannato') NOT NULL DEFAULT 'Attivo',
    id_ruolo SMALLINT UNSIGNED NOT NULL,
    CONSTRAINT fk_app_utente_quartiere FOREIGN KEY (id_quartiere) REFERENCES quartiere(id_quartiere) ON DELETE SET NULL,
    CONSTRAINT fk_app_utente_ruolo FOREIGN KEY (id_ruolo) REFERENCES ruolo(id_ruolo),
    INDEX ix_utente_ruolo_stato (id_ruolo, stato_account)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS identita (
    id_identita BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    id_utente BIGINT UNSIGNED NOT NULL UNIQUE,
    tipo_verifica ENUM('Carta identita','SPID','CIE') NOT NULL,
    fronte VARCHAR(500) NULL,
    retro VARCHAR(500) NULL,
    stato_verifica ENUM('In attesa','Verificato','Rifiutato') NOT NULL DEFAULT 'In attesa',
    data_richiesta TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_verifica TIMESTAMP NULL,
    id_revisore BIGINT UNSIGNED NULL,
    CONSTRAINT fk_app_identita_utente FOREIGN KEY (id_utente) REFERENCES utente(id_utente) ON DELETE CASCADE,
    CONSTRAINT fk_app_identita_revisore FOREIGN KEY (id_revisore) REFERENCES utente(id_utente) ON DELETE SET NULL,
    INDEX ix_identita_stato_data (stato_verifica, data_richiesta)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS stato_segnalazione (
    id_stato SMALLINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(50) NOT NULL UNIQUE,
    descrizione VARCHAR(255) NULL,
    ordine SMALLINT UNSIGNED NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS categoria (
    id_categoria SMALLINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nome_categoria VARCHAR(100) NOT NULL UNIQUE,
    descrizione VARCHAR(255) NULL,
    attiva BOOLEAN NOT NULL DEFAULT TRUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS luogo (
    id_luogo BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    indirizzo VARCHAR(180) NOT NULL,
    id_quartiere SMALLINT UNSIGNED NOT NULL,
    CONSTRAINT fk_app_luogo_quartiere FOREIGN KEY (id_quartiere) REFERENCES quartiere(id_quartiere),
    INDEX ix_luogo_quartiere (id_quartiere)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS segnalazione (
    id_segnalazione BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    titolo VARCHAR(150) NOT NULL,
    descrizione TEXT NOT NULL,
    data_creazione TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    id_utente BIGINT UNSIGNED NOT NULL,
    id_luogo BIGINT UNSIGNED NOT NULL,
    id_stato SMALLINT UNSIGNED NOT NULL,
    stato_pubblicazione ENUM('Bozza','Pubblicata','Nascosta') NOT NULL DEFAULT 'Bozza',
    latitudine DECIMAL(10,7) NULL,
    longitudine DECIMAL(10,7) NULL,
    CONSTRAINT fk_app_segnalazione_utente FOREIGN KEY (id_utente) REFERENCES utente(id_utente),
    CONSTRAINT fk_app_segnalazione_luogo FOREIGN KEY (id_luogo) REFERENCES luogo(id_luogo),
    CONSTRAINT fk_app_segnalazione_stato FOREIGN KEY (id_stato) REFERENCES stato_segnalazione(id_stato),
    CHECK (latitudine IS NULL OR latitudine BETWEEN -90 AND 90),
    CHECK (longitudine IS NULL OR longitudine BETWEEN -180 AND 180),
    CHECK ((latitudine IS NULL) = (longitudine IS NULL)),
    INDEX ix_segnalazione_pubblicazione_data (stato_pubblicazione, data_creazione),
    INDEX ix_segnalazione_autore_data (id_utente, data_creazione),
    INDEX ix_segnalazione_stato (id_stato)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS file_multimediale (
    id_file BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    id_segnalazione BIGINT UNSIGNED NOT NULL,
    tipo ENUM('Foto','Video') NOT NULL,
    percorso VARCHAR(500) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    dimensione BIGINT UNSIGNED NOT NULL,
    sha256 CHAR(64) NOT NULL,
    coordinate_exif JSON NULL,
    data_caricamento TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_app_file_segnalazione FOREIGN KEY (id_segnalazione) REFERENCES segnalazione(id_segnalazione) ON DELETE CASCADE,
    INDEX ix_file_segnalazione (id_segnalazione)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS segnalazione_categoria (
    id_segnalazione BIGINT UNSIGNED NOT NULL,
    id_categoria SMALLINT UNSIGNED NOT NULL,
    origine ENUM('utente','IA','comitato') NOT NULL DEFAULT 'utente',
    PRIMARY KEY (id_segnalazione, id_categoria),
    CONSTRAINT fk_app_sc_segnalazione FOREIGN KEY (id_segnalazione) REFERENCES segnalazione(id_segnalazione) ON DELETE CASCADE,
    CONSTRAINT fk_app_sc_categoria FOREIGN KEY (id_categoria) REFERENCES categoria(id_categoria),
    INDEX ix_sc_categoria (id_categoria, id_segnalazione)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS commento (
    id_commento BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    testo TEXT NOT NULL,
    data TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modificato_il TIMESTAMP NULL,
    cancellato BOOLEAN NOT NULL DEFAULT FALSE,
    id_utente BIGINT UNSIGNED NOT NULL,
    id_segnalazione BIGINT UNSIGNED NOT NULL,
    CONSTRAINT fk_app_commento_utente FOREIGN KEY (id_utente) REFERENCES utente(id_utente),
    CONSTRAINT fk_app_commento_segnalazione FOREIGN KEY (id_segnalazione) REFERENCES segnalazione(id_segnalazione) ON DELETE CASCADE,
    INDEX ix_commento_segnalazione_data (id_segnalazione, data)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS sostegno (
    id_sostegno BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    data TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tipo ENUM('Sostegno','Interesse') NOT NULL,
    id_utente BIGINT UNSIGNED NOT NULL,
    id_segnalazione BIGINT UNSIGNED NOT NULL,
    UNIQUE KEY uq_sostegno_utente_segnalazione_tipo (id_utente, id_segnalazione, tipo),
    CONSTRAINT fk_app_sostegno_utente FOREIGN KEY (id_utente) REFERENCES utente(id_utente),
    CONSTRAINT fk_app_sostegno_segnalazione FOREIGN KEY (id_segnalazione) REFERENCES segnalazione(id_segnalazione) ON DELETE CASCADE,
    INDEX ix_sostegno_segnalazione_tipo (id_segnalazione, tipo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS storico_stato (
    id_storico BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    id_segnalazione BIGINT UNSIGNED NOT NULL,
    id_stato_precedente SMALLINT UNSIGNED NULL,
    id_stato_nuovo SMALLINT UNSIGNED NOT NULL,
    id_utente BIGINT UNSIGNED NOT NULL,
    data_modifica TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    nota VARCHAR(500) NULL,
    CONSTRAINT fk_app_storico_segnalazione FOREIGN KEY (id_segnalazione) REFERENCES segnalazione(id_segnalazione) ON DELETE CASCADE,
    CONSTRAINT fk_app_storico_precedente FOREIGN KEY (id_stato_precedente) REFERENCES stato_segnalazione(id_stato),
    CONSTRAINT fk_app_storico_nuovo FOREIGN KEY (id_stato_nuovo) REFERENCES stato_segnalazione(id_stato),
    CONSTRAINT fk_app_storico_utente FOREIGN KEY (id_utente) REFERENCES utente(id_utente),
    INDEX ix_storico_segnalazione_data (id_segnalazione, data_modifica)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS analisi_ia (
    id_analisi BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    id_segnalazione BIGINT UNSIGNED NOT NULL,
    id_file BIGINT UNSIGNED NULL,
    tipo_analisi ENUM('moderazione_testo','classificazione','estrazione_exif','verifica_multimediale') NOT NULL,
    stato ENUM('In attesa','In elaborazione','Completata','Errore','Revisione richiesta') NOT NULL DEFAULT 'In attesa',
    modello VARCHAR(120) NULL,
    versione_modello VARCHAR(60) NULL,
    risultato JSON NULL,
    punteggio DECIMAL(6,5) NULL,
    decisione_revisore VARCHAR(50) NULL,
    id_revisore BIGINT UNSIGNED NULL,
    data_creazione TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_completamento TIMESTAMP NULL,
    CONSTRAINT fk_app_analisi_segnalazione FOREIGN KEY (id_segnalazione) REFERENCES segnalazione(id_segnalazione) ON DELETE CASCADE,
    CONSTRAINT fk_app_analisi_file FOREIGN KEY (id_file) REFERENCES file_multimediale(id_file) ON DELETE SET NULL,
    CONSTRAINT fk_app_analisi_revisore FOREIGN KEY (id_revisore) REFERENCES utente(id_utente) ON DELETE SET NULL,
    CHECK (punteggio IS NULL OR punteggio BETWEEN 0 AND 1),
    INDEX ix_analisi_stato_data (stato, data_creazione)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS moderazione (
    id_moderazione BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    id_moderatore BIGINT UNSIGNED NOT NULL,
    id_utente BIGINT UNSIGNED NOT NULL,
    data TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tipo_intervento ENUM('Ban','Sblocco','Controllo') NOT NULL,
    motivazione VARCHAR(500) NOT NULL,
    CONSTRAINT fk_app_moderazione_moderatore FOREIGN KEY (id_moderatore) REFERENCES utente(id_utente),
    CONSTRAINT fk_app_moderazione_utente FOREIGN KEY (id_utente) REFERENCES utente(id_utente),
    INDEX ix_moderazione_utente_data (id_utente, data)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

INSERT INTO ruolo (nome_ruolo, descrizione) VALUES
    ('Cittadino', 'Utente che inserisce e consulta segnalazioni'),
    ('Comitato', 'Membro del comitato con poteri di supervisione'),
    ('Moderatore', 'Membro del comitato con poteri di moderazione')
ON DUPLICATE KEY UPDATE descrizione = VALUES(descrizione);

INSERT INTO stato_segnalazione (nome, descrizione, ordine) VALUES
    ('Ricevuta', 'Segnalazione appena pubblicata', 1),
    ('In valutazione', 'Segnalazione in fase di analisi', 2),
    ('Presa in carico', 'Problematica presa in carico', 3),
    ('Inviata ai candidati', 'Proposta inviata ai candidati Sindaco', 4),
    ('Conclusa', 'Segnalazione conclusa', 5)
ON DUPLICATE KEY UPDATE descrizione = VALUES(descrizione), ordine = VALUES(ordine);

INSERT INTO categoria (nome_categoria, descrizione) VALUES
    ('Ambiente', 'Aree verdi e ambiente'),
    ('Mobilità Urbana', 'Viabilità e trasporti'),
    ('Politiche Giovanili', 'Servizi e iniziative per giovani'),
    ('Decoro Urbano', 'Pulizia e manutenzione'),
    ('Illuminazione', 'Illuminazione pubblica')
ON DUPLICATE KEY UPDATE descrizione = VALUES(descrizione), attiva = TRUE;
