# CL Control Web Next

Nuova **App Home Assistant con Ingress** e interfaccia CL Impianti Blue Tech Premium, sviluppata da zero.

## Stato

- `cl_control_web_next` **0.1.0-beta.7**: Blue Tech Premium con luci compatte e dettagli al tocco; distribuzione dallo Store dal ramo `main` dopo integrazione della proposta.
- Vecchia App `local_cl_control_web` 0.2.0-beta.6: non modificata.
- Integrazione Core `cl_control`: resta indipendente.
- Beta funzionale: Home, Aree, Luci, RGBW, Multimedia, Aperture e Clima; riepiloghi energia e sicurezza in sola lettura. Non introduce i comandi avanzati dell'integrazione Core.
- Le luci mantengono una scheda compatta: tocco su nome/icona per i dettagli, interruttore separato per accendere e spegnere. Luminosità, colore, bianco RGBW e Kelvin compaiono solo se supportati dall'entità.
- Beta 7: bridge WebSocket bidirezionale a livello di trasporto ma con soli eventi di stato in uscita verso il browser, filtro attributi e fallback polling in caso di perdita della connessione. Le azioni sono sempre autorizzate dal backend e la pagina rimane amministrativa.
- Collaudo reale di luci, aperture, TV e clima ancora richiesto prima della distribuzione ai clienti.

## Installazione Home Assistant OS

### Installazione diretta da repository pubblico

Il progetto deve essere pubblicato sul ramo `main` e il repository GitHub deve avere visibilità **Public**.

1. In Home Assistant OS aprire **Impostazioni → App → Installa App** (Store).
2. Menu **⋮ → Repository**, aggiungere `https://github.com/climpianti/cl-control-web` e confermare.
3. Cercare **CL Control Web Next** nello Store, quindi selezionare **Installa**.
4. Avviare l'App e aprirla da **Apri interfaccia utente Web** (Ingress). Non usare il vecchio indirizzo `/cl-control-next`: apparteneva alla precedente integrazione di prova ed è un percorso diverso dall'App.
5. Verificare che il percorso Ingress abbia **una sola barra finale**. In questa beta `ingress_entry` non è impostato, perché la pagina iniziale viene servita da `/`.
6. Verificare dati e comandi, poi decidere se interrompere la vecchia App. Non disinstallarla senza backup.

Se il repository non compare, aggiornare Store e pagina, poi controllare **Impostazioni → Sistema → Registri → Supervisor**. Non usare HACS: questa distribuzione è un'**App**, non una custom integration.

### Alternativa: App locale

Se il repository resta privato: copiare la sola cartella `cl_control_web_next` in `/addons/cl_control_web_next`, aggiornare lo Store delle App locali e installare da lì. Non esporre la porta 8099 alla LAN: il frontend è pensato per Ingress autenticato.

## Sicurezza

- Il token `SUPERVISOR_TOKEN` viene usato dal backend, mai inviato al browser.
- Nessuna porta host pubblicata. Solo Ingress autenticato.
- Comandi HA ammessi: accensione/spegnimento `light`, luminosità e colore; controlli media supportati, sorgenti disponibili e telecomando con tasti consentiti.
- Non sono implementati comandi sicurezza, serrature, allarmi o servizi generici.
- L'App usa la sessione Ingress; non richiede una password dedicata.

## Telecomando e rilevamento automatico

Ogni card media apre un telecomando. Funzioni, volume, sorgenti e app vengono ricavati da `supported_features`, `source_list` e dai servizi registrati in Home Assistant. Non servono nomi di entità preimpostati.

Navigazione, Home, Indietro, canali e numeri: LG webOS usa `webostv.button`; Samsung TV e Android TV Remote usano un'entità `remote` abilitata e associata allo stesso dispositivo nel registro. In caso di associazioni multiple non si sceglie arbitrariamente un telecomando. Altre integrazioni mantengono i controlli multimediali che espongono, senza tasti direzionali inventati. L'accensione dipende dal supporto dell'integrazione e dalla configurazione del TV (ad esempio Wake-on-LAN).

Ogni comando del pannello viene validato nuovamente dal backend contro lo stato e le capacità attuali. Non sono ammessi codici telecomando, servizi generici o destinazioni arbitrari. Il token resta sul server. Il registro si legge via WebSocket del Core: se non accessibile, restano solo i controlli base. I servizi sono quelli documentati per [LG webOS](https://www.home-assistant.io/actions/webostv.button/), [Samsung TV](https://www.home-assistant.io/integrations/samsungtv/) e [Android TV Remote](https://www.home-assistant.io/integrations/androidtv_remote/).

Il codice storico completo del telecomando citato in un'altra chat non è stato recuperato: questa implementazione usa i contratti correnti di Home Assistant, non dichiara parità con funzioni storiche non verificabili.

## Verifica smartphone

Layout controllato a 320, 390, 430, 768 e 1440 px: nessun overflow orizzontale della pagina media, logo singolo, finestra telecomando scrollabile. Comandi e rilevamento verificati con un Core simulato dietro il gateway reale; resta il collaudo Ingress e TV fisici. La navigazione principale su smartphone scorre orizzontalmente.

## Prossimi moduli

Aree e piani, planimetrie, energia, Discovery KNX del Core, scene e AI Studio. Le funzioni vengono introdotte per beta successive con test e rollback.


## Realtime e accesso (beta 7)

L'app si collega tramite WebSocket al Core HA usando SUPERVISOR_TOKEN, ma lo mantiene nel container. A ogni browser Ingress viene inviato solo un sottoinsieme sanitizzato dell'evento `state_changed`. Il browser non può inviare comandi sul socket. Il numero di collegamenti simultanei è limitato. Se la connessione cade, resta il controllo periodico ogni 9 secondi, e viene ristabilita quando la pagina torna visibile. `panel_admin: true` resta attivo: accesso multiutente/cliente rimandato a un'autorizzazione per utente verificata lato server.

La configurazione di SENEC è esclusa dalla beta 7.
