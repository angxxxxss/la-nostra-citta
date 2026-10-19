-- =====================================
-- INSERT: RUOLI
-- =====================================

INSERT INTO Ruolo (nome_ruolo, descrizione) VALUES
('Cittadino', 'Utente che inserisce e consulta segnalazioni'),
('Comitato', 'Membro del comitato con poteri di supervisione');

-- =====================================
-- INSERT: UTENTI
-- Password di esempio: usare hash reali in produzione
-- =====================================

INSERT INTO Utente
(nome, cognome, codice_fiscale, email, password,
 indirizzo, quartiere, stato_verifica, stato_account, id_ruolo)
VALUES
('Mario', 'Rossi', 'RSSMRA90A01F205X',
 'mario.rossi@email.it', 'HASH_PASSWORD_1',
 'Via Roma 10', 'Centro', 'Verificato', 'Attivo', 1),

('Laura', 'Bianchi', 'BNCLRA85B41F205Y',
 'laura.bianchi@email.it', 'HASH_PASSWORD_2',
 'Via Verdi 25', 'Navigli', 'Verificato', 'Attivo', 1),

('Giulia', 'Verdi', 'VRDGLI80C50F205Z',
 'giulia.verdi@email.it', 'HASH_PASSWORD_3',
 'Piazza Duomo 1', 'Centro', 'Verificato', 'Attivo', 2);

-- =====================================
-- INSERT: IDENTITA
-- =====================================

INSERT INTO Identita
(id_utente, tipo_verifica, numero_documento,
 fronte, retro, data_verifica)
VALUES
(1, 'Carta identita', 'AA123456',
 'documenti/mario_fronte.jpg',
 'documenti/mario_retro.jpg',
 '2026-09-20 10:00:00'),

(2, 'SPID', NULL, NULL, NULL,
 '2026-09-21 11:30:00'),

(3, 'CIE', NULL, NULL, NULL,
 '2026-09-22 09:15:00');

-- =====================================
-- INSERT: LUOGHI
-- =====================================

INSERT INTO Luogo
(indirizzo, quartiere, latitudine, longitudine)
VALUES
('Via Roma 15', 'Centro', 45.4642000, 9.1900000),
('Via Verdi 30', 'Navigli', 45.4500000, 9.1700000),
('Viale Monza 100', 'NoLo', 45.5000000, 9.2200000);

-- =====================================
-- INSERT: STATI
-- =====================================

INSERT INTO Stato (nome_stato, descrizione) VALUES
('Ricevuta', 'Segnalazione appena pubblicata'),
('In valutazione', 'Segnalazione in fase di analisi'),
('Presa in carico', 'Problematica presa in carico'),
('Inviata ai candidati', 'Proposta inviata ai candidati Sindaco'),
('Conclusa', 'Segnalazione conclusa');

-- =====================================
-- INSERT: SEGNALAZIONI
-- =====================================

INSERT INTO Segnalazione
(titolo, descrizione, id_utente, id_luogo, id_stato)
VALUES
('Buche stradali in Via Roma',
 'La strada presenta diverse buche che rendono
 difficoltoso il passaggio dei veicoli.',
 1, 1, 2),

('Illuminazione insufficiente',
 'In Via Verdi alcuni lampioni non funzionano
 e la strada risulta poco illuminata.',
 2, 2, 1),

('Area verde abbandonata',
 'Il parco necessita di manutenzione e pulizia.',
 1, 3, 1);

-- =====================================
-- INSERT: FILE MULTIMEDIALI
-- =====================================

INSERT INTO File_Multimediale
(id_segnalazione, tipo, percorso, metadati_exif)
VALUES
(1, 'Foto', 'uploads/buche_roma.jpg',
 'Coordinate non disponibili'),

(1, 'Video', 'uploads/buche_roma.mp4',
 NULL),

(2, 'Foto', 'uploads/lampioni_verdi.jpg',
 'Coordinate non disponibili'),

(3, 'Foto', 'uploads/parco_abbandonato.jpg',
 'Coordinate non disponibili');

-- =====================================
-- INSERT: COMMENTI
-- =====================================

INSERT INTO Commento
(testo, id_utente, id_segnalazione)
VALUES
('Anche io ho notato questo problema.',
 2, 1),

('Sarebbe importante intervenire al più presto.',
 3, 1),

('Concordo, la zona è davvero poco illuminata.',
 1, 2);

-- =====================================
-- INSERT: SOSTEGNI
-- =====================================

INSERT INTO Sostegno
(id_utente, id_segnalazione, tipo)
VALUES
(2, 1, 'Sostegno'),
(3, 1, 'Interesse'),
(1, 2, 'Sostegno'),
(3, 2, 'Sostegno'),
(2, 3, 'Interesse');

-- =====================================
-- INSERT: CATEGORIE
-- =====================================

INSERT INTO Categoria (nome_categoria) VALUES
('Ambiente'),
('Mobilità Urbana'),
('Politiche Giovanili'),
('Decoro Urbano'),
('Illuminazione');

-- =====================================
-- INSERT: ASSOCIAZIONE CATEGORIE
-- =====================================

INSERT INTO Segnalazione_Categoria
(id_segnalazione, id_categoria)
VALUES
(1, 2),
(2, 5),
(3, 1),
(3, 4);

-- =====================================
-- INSERT: MODERAZIONE
-- =====================================

INSERT INTO Moderazione
(id_moderatore, id_utente, tipo_intervento, motivazione)
VALUES
(3, 2, 'Controllo',
 'Verifica di una segnalazione');

-- =====================================
-- CLASSIFICA DELLE SEGNALAZIONI
-- =====================================

SELECT
    s.id_segnalazione,
    s.titolo,
    COUNT(DISTINCT so.id_utente) AS numero_sostenitori
FROM Segnalazione s
LEFT JOIN Sostegno so
    ON s.id_segnalazione = so.id_segnalazione
GROUP BY s.id_segnalazione, s.titolo
ORDER BY numero_sostenitori DESC;
