INSERT IGNORE INTO ruolo (nome_ruolo,descrizione) VALUES
('Cittadino','Può consultare e, se verificato, partecipare'),
('Comitato','Può supervisionare e aggiornare gli stati'),
('Moderatore','Può moderare contenuti e account');
INSERT IGNORE INTO quartiere (nome) VALUES
('Centro Storico'),('Brera'),('Navigli'),('Isola'),('NoLo'),('Affori'),('Bicocca'),('Città Studi'),('San Siro'),('Porta Romana');
INSERT IGNORE INTO stato_segnalazione (nome,descrizione,ordine) VALUES
('Ricevuta','Segnalazione inviata dalla comunità',1),
('In valutazione','Il comitato sta valutando la proposta',2),
('Presa in carico','La necessità è stata presa in carico',3),
('Inviata ai candidati','Proposta inserita nel documento condiviso',4),
('Conclusa','Intervento concluso o obiettivo raggiunto',5),
('Rifiutata','Proposta non accolta con motivazione',6);
INSERT IGNORE INTO categoria (nome_categoria) VALUES
('Ambiente'),('Mobilità Urbana'),('Politiche Giovanili'),('Decoro Urbano'),('Illuminazione'),('Viabilità'),('Criticità Idrogeologica'),('Movida');
