-- Esempi di segnalazioni pubblicate dal membro del comitato.
-- Eseguire dopo 001_application_schema.sql e 001_quartieri_milano.sql.

INSERT INTO luogo (indirizzo, id_quartiere)
SELECT 'Via Padova 120', q.id_quartiere
FROM quartiere q
WHERE q.nome = 'Padova - Turro - Crescenzago'
  AND NOT EXISTS (
      SELECT 1 FROM luogo l WHERE l.indirizzo = 'Via Padova 120' AND l.id_quartiere = q.id_quartiere
  );

INSERT INTO luogo (indirizzo, id_quartiere)
SELECT 'Via Ripamonti 120', q.id_quartiere
FROM quartiere q
WHERE q.nome = 'Vigentino - Quartiere Fatima'
  AND NOT EXISTS (
      SELECT 1 FROM luogo l WHERE l.indirizzo = 'Via Ripamonti 120' AND l.id_quartiere = q.id_quartiere
  );

INSERT INTO luogo (indirizzo, id_quartiere)
SELECT 'Parco Sempione, ingresso Arena', q.id_quartiere
FROM quartiere q
WHERE q.nome = 'Parco Sempione'
  AND NOT EXISTS (
      SELECT 1 FROM luogo l WHERE l.indirizzo = 'Parco Sempione, ingresso Arena' AND l.id_quartiere = q.id_quartiere
  );

INSERT INTO segnalazione (
    titolo,
    descrizione,
    id_utente,
    id_luogo,
    id_stato,
    stato_pubblicazione,
    latitudine,
    longitudine
)
SELECT
    esempi.titolo,
    esempi.descrizione,
    u.id_utente,
    l.id_luogo,
    st.id_stato,
    'Pubblicata',
    esempi.latitudine,
    esempi.longitudine
FROM (
    SELECT
        'Illuminazione insufficiente in Via Padova' AS titolo,
        'Diversi lampioni non funzionano e il tratto risulta poco illuminato nelle ore serali.' AS descrizione,
        'Via Padova 120' AS indirizzo,
        45.4978000 AS latitudine,
        9.2323000 AS longitudine,
        'Ricevuta' AS stato,
        'Illuminazione' AS categoria
    UNION ALL
    SELECT
        'Buche in Via Ripamonti',
        'La carreggiata presenta buche profonde che rendono rischioso il passaggio di biciclette e motocicli.',
        'Via Ripamonti 120',
        45.4379000,
        9.2045000,
        'In valutazione',
        'Mobilità Urbana'
    UNION ALL
    SELECT
        'Manutenzione del verde al Parco Sempione',
        'Alcune aiuole sono deteriorate e l''area necessita di pulizia e manutenzione ordinaria.',
        'Parco Sempione, ingresso Arena',
        45.4721000,
        9.1779000,
        'Presa in carico',
        'Ambiente'
) AS esempi
JOIN utente u ON u.email = 'comitato@example.com'
JOIN luogo l ON l.indirizzo = esempi.indirizzo
JOIN stato_segnalazione st ON st.nome = esempi.stato
WHERE NOT EXISTS (
    SELECT 1
    FROM segnalazione s_esistente
    WHERE s_esistente.titolo = esempi.titolo
      AND s_esistente.id_utente = u.id_utente
);

INSERT INTO segnalazione_categoria (id_segnalazione, id_categoria, origine)
SELECT s.id_segnalazione, c.id_categoria, 'comitato'
FROM segnalazione s
JOIN categoria c ON c.nome_categoria = CASE s.titolo
    WHEN 'Illuminazione insufficiente in Via Padova' THEN 'Illuminazione'
    WHEN 'Buche in Via Ripamonti' THEN 'Mobilità Urbana'
    WHEN 'Manutenzione del verde al Parco Sempione' THEN 'Ambiente'
END
JOIN utente u ON u.id_utente = s.id_utente
WHERE u.email = 'comitato@example.com'
  AND s.titolo IN (
      'Illuminazione insufficiente in Via Padova',
      'Buche in Via Ripamonti',
      'Manutenzione del verde al Parco Sempione'
  )
ON DUPLICATE KEY UPDATE origine = 'comitato';
