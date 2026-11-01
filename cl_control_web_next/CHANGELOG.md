# 0.1.0-beta.14

- CL Control AI Studio: prima interfaccia per richieste in linguaggio naturale, con esempi e proposte di dashboard.
- Pianificatore locale deterministico: interpreta parole chiave, controlla entita reali di Home Assistant e produce solo layout JSON schema 1.
- Nessun provider LLM configurato o eseguito; nessuna richiesta cloud, nessun invio di dati fuori dall'impianto.
- Nessun comando a dispositivi e nessun salvataggio automatico: la proposta deve essere verificata e approvata nell'editor visuale.
- Endpoint /api/studio/draft protetto da Ingress e limitato al pannello amministratore.
- Preparazione della separazione Core AI Studio (KNX/Modbus) dal motore dashboard.
 
# 0.1.0-beta.13

- Editor visuale dashboard: modifica titolo e singoli widget, scegli entita reali, aggiungi e rimuovi widget, riordina con controlli accessibili.
- Catalogo backend solo per Ingress con tipi supportati e nomi delle entita; niente stati, credenziali o attributi privati.
- Ogni modifica invalida l'anteprima precedente. Verifica con schema server prima dell'approvazione e salvataggio esplicito.
- Anteprima non interattiva; nessun comando ai dispositivi durante la progettazione.
- Modello persistente beta 12 invariato; salvataggio con controllo di revisione e conferma.
- Futura AI Studio potra usare lo stesso catalogo e schema JSON senza eseguire codice generato.

# 0.1.0-beta.12

- Corretto il volume persistente Supervisor `/data` inizialmente root-owned: all'avvio vengono preparati permessi esclusivi per l'utente applicativo e poi il processo Python viene eseguito con uid 10001 tramite gosu.
- Nessun dato dashboard cancellato, nessuna modifica all'archivio dei layout o alle entita Home Assistant.
- Il salvataggio della dashboard deve ora risultare disponibile dall'endpoint `/api/layout`.

# 0.1.0-beta.11

- Primo motore di dashboard dinamiche: schema versionato, widget con tipi e campi autorizzati, rendering guidato dai dati dell'impianto.
- Nuovo editor Personalizza (solo pannello amministrativo) con proposta automatica deterministica, anteprima senza scrittura, approvazione esplicita e salvataggio persistente.
- Validazione di entita reali, anti-iniezione, protezione da aggiornamenti concorrenti, scrittura atomica su /data e 600 per il file.
- Nessun motore AI remoto attivato, nessuna esecuzione di codice generato, nessuna scrittura di comandi dispositivi.
- Accesso cliente rimane disabilitato; ancora da implementare i permessi per entita e l'integrazione Core dell'archivio layout.

# 0.1.0-beta.10

- Sicurezza: verifica esplicita dello stato live e delle capacita supportate prima dei comandi luci e multimedia.
- Base futura ruoli cliente/installatore: rilevamento ID utente HA esclusivamente dal proxy Ingress attendibile.
- Endpoint /api/access senza identificatori personali per verificare presenza e attendibilita dell'identita Ingress.
- Nessuna attribuzione automatica di privilegi installatore da header client; nessun accesso cliente attivato.
- La Web App rimane panel_admin=true; per i clienti e ancora necessaria una vera integrazione con i permessi HA per utente e per entita.
- Protezione contro spoofing di identita testata; SENEC, Power Control e impianti non modificati.

# 0.1.0-beta.9

- Nuova navigazione smartphone fissa in basso, cinque sezioni: Home, Aree, Luci, Energia, Altro, adattata a safe area e schermi 320 px.
- Nuova pagina Altro per i sistemi non presenti nella barra inferiore.
- Scenari e preferiti puntano alla dashboard CL Control Core gia installata, senza esportare dati privati ne creare un secondo archivio.
- Ingress continua riservato agli amministratori; niente accesso clienti prematuro, token e permessi Core non vengono aggirati.
- Test frontend sulla navigazione, sulla route Core e sulla conservazione dei dati utenti.

# 0.1.0-beta.8

- Energia: pannello realtime in sola lettura con sorgenti SENEC indipendenti prioritarie.
- Fotovoltaico, consumo casa, rete e batteria con direzione import/export e carica/scarica; SOC con provenienza dei dati.
- Fallback ai sensori CL Power Control se SENEC non disponibile e indicazione esplicita dei valori mancanti.
- Nessuna stima di bilanci energetici tra sensori non coerenti; nessun cambiamento ai carichi o alla configurazione di Power Control.
- Sensori e sicurezza continuano a essere gestiti dal backend HA tramite Ingress; test CI estesi.

# 0.1.0-beta.7

- Bridge realtime via WebSocket Home Assistant -> Ingress: riceve esclusivamente gli stati sanitizzati delle entità supportate, senza inviare SUPERVISOR_TOKEN al browser.
- Riconnessione dopo interruzioni e fallback automatico al polling; sospensione degli aggiornamenti visivi durante dialoghi, ricerche e regolazioni.
- Test GitHub Actions ampliati a tutti i test Python e frontend, attivi su push main, branch e Pull Request.
- Mantiene l'accesso solo amministratore fino alla progettazione di autorizzazioni utente verificate: nessun ampliamento dei permessi cliente.
- CL Power Control e SENEC non modificati. Collaudo di apparecchi reali e controllo autorizzazioni cliente ancora necessario.

# 0.1.0-beta.6

- Aperture: Apri, Stop, Chiudi e posizione con conferma Applica.
- Clima: temperatura ambiente, setpoint, modalità, profili e ventilazione rilevati automaticamente.
- Validazione server di disponibilità, capacità, servizi e limiti prima dei comandi.
- Nessun comando fisico inviato durante il collaudo.

# 0.1.0-beta.5

- Telecomando su ogni card media: accensione, volume/mute, riproduzione, sorgenti/app e tasti disponibili tramite rilevamento automatico.
- Associazione telecomandi Samsung/Android al dispositivo del registro; supporto pulsanti LG webOS. Controllo server dei servizi, capacità, sorgenti e codici consentiti.
- Logo unico e titoli non duplicati; navigazione, spaziatura, dimensioni dei controlli e dialoghi migliorati per smartphone.
- Verifica responsive 320–1440 px e test automatici frontend/backend; collaudo fisico non eseguito.

# 0.1.0-beta.4

- Card luci e finestra dettagli seguono colore RGB/RGBW/RGBWW o temperatura Kelvin; alone e bordo variano con il dimmer. Anteprima immediata durante il trascinamento, poi conferma dello stato Home Assistant.

- Card multimedia Midnight Glass: sfumature blu/viola, play/pausa circolare, icone audio/TV e barra volume sottile; finiture coordinate sulle altre card.

- Grafica Blue Tech Premium: icone SVG, superfici blu, banner architettonico locale e layout adattivo.
- Schede luci compatte in tutte le viste, accensione rapida separata dal tocco per i dettagli.
- Finestra accessibile con luminosità, colore, bianco RGBW e temperatura Kelvin solo se supportati.
- Cambio tonalità RGBW/RGBWW con conservazione dei canali bianchi.
- Aggiornamento periodico sospeso durante l'uso dei dettagli e dei campi di ricerca.
- Backend Ingress, autorizzazioni e servizi consentiti invariati.

Verifica: test di validazione API e test frontend; anteprima con dati simulati. Il collaudo dentro Ingress con dispositivi reali resta da eseguire. I moduli in sola lettura della precedente beta restano in sola lettura.
