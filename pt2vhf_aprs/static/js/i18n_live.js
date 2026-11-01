/* Keyed independently of the positional legacy catalogs (issue #157). */
(() => {
  'use strict';
  const entries = {
    'Desconectado': ['Disconnected', 'Desconectado', 'Déconnecté', 'Getrennt', 'Disconnesso'],
    'Conectando…': ['Connecting…', 'Conectando…', 'Connexion…', 'Verbindung wird hergestellt…', 'Connessione…'],
    'Reconectando…': ['Reconnecting…', 'Reconectando…', 'Reconnexion…', 'Verbindung wird wiederhergestellt…', 'Riconnessione…'],
    'Desconectando...': ['Disconnecting...', 'Desconectando...', 'Déconnexion...', 'Verbindung wird getrennt...', 'Disconnessione...'],
    'Conectado; autenticando...': ['Connected; authenticating...', 'Conectado; autenticando...', 'Connecté ; authentification...', 'Verbunden; Authentifizierung...', 'Connesso; autenticazione...'],
    'Conectado e verificado': ['Connected and verified', 'Conectado y verificado', 'Connecté et vérifié', 'Verbunden und verifiziert', 'Connesso e verificato'],
    'Conectado sem verificação': ['Connected without verification', 'Conectado sin verificar', 'Connecté sans vérification', 'Verbunden ohne Verifizierung', 'Connesso senza verifica'],
    'Conexão perdida': ['Connection lost', 'Conexión perdida', 'Connexion perdue', 'Verbindung verloren', 'Connessione persa'],
    'Configuração incompleta': ['Incomplete configuration', 'Configuración incompleta', 'Configuration incomplète', 'Unvollständige Konfiguration', 'Configurazione incompleta'],
    'Reconectando com a nova configuração...': ['Reconnecting with new settings...', 'Reconectando con la nueva configuración...', 'Reconnexion avec les nouveaux paramètres...', 'Verbindung mit neuen Einstellungen wird hergestellt...', 'Riconnessione con le nuove impostazioni...'],
    'Aguardando': ['Waiting', 'Esperando', 'En attente', 'Warten', 'In attesa'],
    'Aguardando próxima verificação.': ['Waiting for the next check.', 'Esperando la próxima comprobación.', 'En attente de la prochaine vérification.', 'Warten auf die nächste Prüfung.', 'In attesa della prossima verifica.'],
    'Aguarde enquanto a operação é concluída.': ['Please wait for the operation to finish.', 'Espere a que finalice la operación.', 'Veuillez patienter jusqu’à la fin de l’opération.', 'Bitte warten Sie, bis der Vorgang abgeschlossen ist.', 'Attendere il completamento dell’operazione.'],
    'A atualização está em andamento. Aguarde a conclusão.': ['The update is in progress. Wait for it to finish.', 'La actualización está en curso. Espere a que finalice.', 'La mise à jour est en cours. Attendez la fin.', 'Das Update läuft. Bitte warten Sie, bis es abgeschlossen ist.', 'L’aggiornamento è in corso. Attendere il completamento.'],
    'Agendamento atualizado.': ['Schedule updated.', 'Programación actualizada.', 'Programmation mise à jour.', 'Zeitplan aktualisiert.', 'Pianificazione aggiornata.'],
    'Agendamento criado.': ['Schedule created.', 'Programación creada.', 'Programmation créée.', 'Zeitplan erstellt.', 'Pianificazione creata.'],
    'A mensagem já está sendo colocada na fila.': ['The message is already being queued.', 'El mensaje ya se está poniendo en cola.', 'Le message est déjà en cours de mise en file.', 'Die Nachricht wird bereits eingereiht.', 'Il messaggio è già in fase di accodamento.'],
    'Abrir esta estação no mapa': ['Open this station on the map', 'Abrir esta estación en el mapa', 'Ouvrir cette station sur la carte', 'Diese Station auf der Karte öffnen', 'Apri questa stazione sulla mappa'],
    'Atualizando radar…': ['Updating radar…', 'Actualizando radar…', 'Mise à jour du radar…', 'Radar wird aktualisiert…', 'Aggiornamento radar…'],
    'Analisando rotas RF…': ['Analyzing RF routes…', 'Analizando rutas RF…', 'Analyse des routes RF…', 'RF-Routen werden analysiert…', 'Analisi dei percorsi RF…'],
    'Calculando Recordes RF…': ['Calculating RF records…', 'Calculando récords RF…', 'Calcul des records RF…', 'RF-Rekorde werden berechnet…', 'Calcolo dei record RF…'],
    'Banco em ordem': ['Database OK', 'Base de datos correcta', 'Base de données en bon état', 'Datenbank in Ordnung', 'Database integro'],
    'Banco utilizável, com avisos': ['Database usable, with warnings', 'Base de datos utilizable, con advertencias', 'Base de données utilisable, avec avertissements', 'Datenbank verwendbar, mit Warnungen', 'Database utilizzabile, con avvisi'],
    'Ainda não há instalador publicado no site PT2VHF.': ['No installer has been published on the PT2VHF website yet.', 'Todavía no hay un instalador publicado en el sitio PT2VHF.', 'Aucun programme d’installation n’est encore publié sur le site PT2VHF.', 'Auf der PT2VHF-Website wurde noch kein Installationsprogramm veröffentlicht.', 'Non è ancora stato pubblicato un programma di installazione sul sito PT2VHF.'],
    'Filtrar (origem, destino ou texto)': ['Filter (sender, recipient or text)', 'Filtrar (origen, destino o texto)', 'Filtrer (origine, destination ou texte)', 'Filtern (Absender, Empfänger oder Text)', 'Filtra (mittente, destinatario o testo)'],
    'Fechar': ['Close', 'Cerrar', 'Fermer', 'Schließen', 'Chiudi']
  };
  window.PT2VHF_I18N = window.PT2VHF_I18N || {};
  ['en', 'es', 'fr', 'de-DE', 'it-IT'].forEach((locale, index) => {
    const catalog = window.PT2VHF_I18N[locale] ||= {};
    for (const [key, values] of Object.entries(entries)) catalog[key] = values[index];
  });
})();
