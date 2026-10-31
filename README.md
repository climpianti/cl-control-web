# CL Control Web Next

Nuova **App Home Assistant con Ingress** e interfaccia CL Impianti Blue Tech Premium, sviluppata da zero.

## Stato

- `cl_control_web_next` **0.1.0-beta.3**: sviluppo sul ramo `app/0.1.0-beta.3`; distribuzione dallo Store prevista dal ramo `main`.
- Vecchia App `local_cl_control_web` 0.2.0-beta.6: non modificata.
- Integrazione Core `cl_control`: resta indipendente.
- Questa è una **prima beta funzionale**: Home, Luci, RGBW, Multimedia. KNX in sola descrizione; niente planimetrie/energia.
- NON ancora collaudata dentro Home Assistant. Verificare CI e QA prima dell'uso su impianti reali.

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
- Comandi HA ammessi: accensione/spegnimento `light`, luminosità e colore; play/pause, precedente/successivo e volume `media_player`.
- Non sono implementati comandi sicurezza, serrature, allarmi o servizi generici.
- L'App usa la sessione Ingress; non richiede una password dedicata.

## Prossimi moduli

Aree e piani, planimetrie, energia, Discovery KNX del Core, scene e AI Studio. Le funzioni vengono introdotte per beta successive con test e rollback.
