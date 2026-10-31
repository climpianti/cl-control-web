# CL Control Web Next

Nuova **App Home Assistant con Ingress** e interfaccia CL Impianti Blue Tech Premium, sviluppata da zero.

## Stato

- `cl_control_web_next` **0.1.0-beta.1**: codice sorgente sul ramo `app/0.1.0-beta.1`.
- Vecchia App `local_cl_control_web` 0.2.0-beta.6: non modificata.
- Integrazione Core `cl_control`: resta indipendente.
- Questa è una **prima beta funzionale**: Home, Luci, RGBW, Multimedia. KNX in sola descrizione; niente planimetrie/energia.
- NON ancora collaudata dentro Home Assistant. Verificare CI e QA prima dell'uso su impianti reali.

## Installazione Home Assistant OS

Per un repository privato non accessibile allo Store Apps, il percorso più prevedibile è l'App locale.

1. Recuperare **la cartella `cl_control_web_next` completa**, senza rinominarne lo slug.
2. Inserirla in `/addons/cl_control_web_next` (o nella cartella locale App che il proprio sistema usa).
3. Aprire Impostazioni → App → Store e aggiornare i repository locali.
4. Installare **CL Control Web Next**, avviarla e aprirla tramite **Apri interfaccia utente Web**.
5. Testare dispositivi e navigazione. Non esporre la porta 8099 alla LAN: il frontend è pensato per Ingress autenticato.
6. Solo dopo verifica e backup si valuterà la rimozione della vecchia App.

Una normale integrazione HACS **non** installa questa App.

## Sicurezza

- Il token `SUPERVISOR_TOKEN` viene usato dal backend, mai inviato al browser.
- Nessuna porta host pubblicata. Solo Ingress autenticato.
- Comandi HA ammessi: accensione/spegnimento `light`, luminosità e colore; play/pause, precedente/successivo e volume `media_player`.
- Non sono implementati comandi sicurezza, serrature, allarmi o servizi generici.
- L'App usa la sessione Ingress; non richiede una password dedicata.

## Prossimi moduli

Aree e piani, planimetrie, energia, Discovery KNX del Core, scene e AI Studio. Le funzioni vengono introdotte per beta successive con test e rollback.
