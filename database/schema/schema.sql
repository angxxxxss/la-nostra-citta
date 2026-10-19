-- NIL ufficiali usati nei menu quartiere e nei luoghi delle segnalazioni.
CREATE TABLE IF NOT EXISTS Quartiere (
    id_quartiere INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(150) NOT NULL UNIQUE,
    attivo BOOLEAN NOT NULL DEFAULT TRUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================
-- 1. RUOLO
-- =====================================

CREATE TABLE Ruolo (
    id_ruolo INT AUTO_INCREMENT PRIMARY KEY,
    nome_ruolo VARCHAR(50) NOT NULL UNIQUE,
    descrizione VARCHAR(255)
);

-- =====================================
-- 2. UTENTE
-- =====================================

CREATE TABLE Utente (
    id_utente INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(50) NOT NULL,
    cognome VARCHAR(50) NOT NULL,
    codice_fiscale CHAR(16) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    indirizzo VARCHAR(150) NOT NULL,
    quartiere VARCHAR(100),
    data_registrazione DATETIME DEFAULT CURRENT_TIMESTAMP,
    stato_verifica ENUM('In attesa', 'Verificato', 'Rifiutato')
        DEFAULT 'In attesa',
    stato_account ENUM('Attivo', 'Bannato')
        DEFAULT 'Attivo',
    id_ruolo INT NOT NULL,
    FOREIGN KEY (id_ruolo) REFERENCES Ruolo(id_ruolo)
);

-- =====================================
-- 3. IDENTITA
-- =====================================

CREATE TABLE Identita (
    id_identita INT AUTO_INCREMENT PRIMARY KEY,
    id_utente INT NOT NULL UNIQUE,
    tipo_verifica ENUM('Carta identita', 'SPID', 'CIE') NOT NULL,
    numero_documento VARCHAR(50),
    fronte VARCHAR(255),
    retro VARCHAR(255),
    data_verifica DATETIME,
    FOREIGN KEY (id_utente) REFERENCES Utente(id_utente)
);

-- =====================================
-- 4. LUOGO
-- =====================================

CREATE TABLE Luogo (
    id_luogo INT AUTO_INCREMENT PRIMARY KEY,
    indirizzo VARCHAR(150) NOT NULL,
    quartiere VARCHAR(100),
    latitudine DECIMAL(10,7),
    longitudine DECIMAL(10,7)
);

-- =====================================
-- 5. STATO
-- =====================================

CREATE TABLE Stato (
    id_stato INT AUTO_INCREMENT PRIMARY KEY,
    nome_stato VARCHAR(50) NOT NULL UNIQUE,
    descrizione VARCHAR(255)
);

-- =====================================
-- 6. SEGNALAZIONE
-- =====================================

CREATE TABLE Segnalazione (
    id_segnalazione INT AUTO_INCREMENT PRIMARY KEY,
    titolo VARCHAR(150) NOT NULL,
    descrizione TEXT NOT NULL,
    data_creazione DATETIME DEFAULT CURRENT_TIMESTAMP,
    id_utente INT NOT NULL,
    id_luogo INT NOT NULL,
    id_stato INT NOT NULL,
    FOREIGN KEY (id_utente) REFERENCES Utente(id_utente),
    FOREIGN KEY (id_luogo) REFERENCES Luogo(id_luogo),
    FOREIGN KEY (id_stato) REFERENCES Stato(id_stato)
);

-- =====================================
-- 7. FILE MULTIMEDIALE
-- =====================================

CREATE TABLE File_Multimediale (
    id_file INT AUTO_INCREMENT PRIMARY KEY,
    id_segnalazione INT NOT NULL,
    tipo ENUM('Foto', 'Video') NOT NULL,
    percorso VARCHAR(255) NOT NULL,
    metadati_exif TEXT,
    data_caricamento DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_segnalazione)
        REFERENCES Segnalazione(id_segnalazione)
        ON DELETE CASCADE
);

-- =====================================
-- 8. COMMENTO
-- =====================================

CREATE TABLE Commento (
    id_commento INT AUTO_INCREMENT PRIMARY KEY,
    testo TEXT NOT NULL,
    data DATETIME DEFAULT CURRENT_TIMESTAMP,
    modificato_il DATETIME NULL,
    cancellato BOOLEAN DEFAULT FALSE,
    id_utente INT NOT NULL,
    id_segnalazione INT NOT NULL,
    FOREIGN KEY (id_utente) REFERENCES Utente(id_utente),
    FOREIGN KEY (id_segnalazione)
        REFERENCES Segnalazione(id_segnalazione)
        ON DELETE CASCADE
);

-- =====================================
-- 9. SOSTEGNO
-- =====================================

CREATE TABLE Sostegno (
    id_sostegno INT AUTO_INCREMENT PRIMARY KEY,
    id_utente INT NOT NULL,
    id_segnalazione INT NOT NULL,
    data DATETIME DEFAULT CURRENT_TIMESTAMP,
    tipo ENUM('Sostegno', 'Interesse') NOT NULL,
    UNIQUE (id_utente, id_segnalazione, tipo),
    FOREIGN KEY (id_utente) REFERENCES Utente(id_utente),
    FOREIGN KEY (id_segnalazione)
        REFERENCES Segnalazione(id_segnalazione)
        ON DELETE CASCADE
);

-- =====================================
-- 10. CATEGORIA
-- =====================================

CREATE TABLE Categoria (
    id_categoria INT AUTO_INCREMENT PRIMARY KEY,
    nome_categoria VARCHAR(100) NOT NULL UNIQUE
);

-- =====================================
-- 11. SEGNALAZIONE - CATEGORIA
-- =====================================

CREATE TABLE Segnalazione_Categoria (
    id_segnalazione INT NOT NULL,
    id_categoria INT NOT NULL,
    PRIMARY KEY (id_segnalazione, id_categoria),
    FOREIGN KEY (id_segnalazione)
        REFERENCES Segnalazione(id_segnalazione)
        ON DELETE CASCADE,
    FOREIGN KEY (id_categoria)
        REFERENCES Categoria(id_categoria)
);

-- =====================================
-- 12. MODERAZIONE / BAN
-- =====================================

CREATE TABLE Moderazione (
    id_moderazione INT AUTO_INCREMENT PRIMARY KEY,
    id_moderatore INT NOT NULL,
    id_utente INT NOT NULL,
    data DATETIME DEFAULT CURRENT_TIMESTAMP,
    tipo_intervento ENUM('Ban', 'Sblocco', 'Controllo')
        NOT NULL,
    motivazione VARCHAR(255),
    FOREIGN KEY (id_moderatore) REFERENCES Utente(id_utente),
    FOREIGN KEY (id_utente) REFERENCES Utente(id_utente)
);
