# CL Control Web — nuova generazione

Versione di sviluppo: **0.1.0-beta.1**. **Nuovo progetto, non compatibile con il vecchio backend CL Control Web 0.2.0-beta.6.**

## Architettura

- Integrazione nativa Home Assistant `custom_components/cl_control_web`, installabile tramite HACS **quando il repository è accessibile a HACS**, oppure tramite copia della cartella sotto `/config/custom_components/`.
- Pannello laterale `/cl-control-next` con il design CL Impianti Blue Tech Premium.
- Autenticazione e autorizzazioni tramite sessione Home Assistant; nessun token o password nel codice frontend.
- Aree, luci e multimedia dalle API Home Assistant. Inventario KNX tramite API dell'integrazione KNX già installata, senza file XML duplicati.
- Non modifica le entità, il progetto ETS, la configurazione KNX o il vecchio CL Control Core.

## Installazione manuale controllata (beta)

1. Esportare/creare un backup Home Assistant; conservare la vecchia App finché i test non sono terminati.
2. Copiare **l'intera directory** `custom_components/cl_control_web` in `/config/custom_components/cl_control_web`.
3. Riavviare Home Assistant.
4. Da **Impostazioni → Dispositivi e servizi → Aggiungi integrazione**, cercare *CL Control Web* e aggiungerla.
5. Aprire **CL Control Next** nella barra laterale. Percorso `/cl-control-next`.
6. Verificare tutte le aree, luci, comandi multimedia e la pagina KNX.

**Non disinstallare la vecchia App `local_cl_control_web` finché la nuova non è stata provata.** La vecchia App archivia dati in un proprio volume e la disinstallazione può eliminarli.

## Limiti della prima beta

- Planimetrie avanzate, effetti RGBW, scenari fotografati, dashboard energia, personalizzazioni utente e moduli TV sono **ancora da implementare**.
- La Discovery KNX mostra un inventario di progetto in sola lettura; non genera ancora entità né esegue automaticamente abbinamenti.
- Comandi luci e multimedia dipendono dalle capacità offerte dalle entità Home Assistant.
- QA frontend nel browser e verifica runtime sono obbligatori prima della sostituzione definitiva.

## Distribuzione

Repository privato durante la fase di sviluppo. La distribuzione su HACS richiederà di accertare l'accessibilità del repository al client HACS collegato, oppure un rilascio pubblico controllato. Il ramo `next/0.1.0-beta.1` non è stato ancora rilasciato come versione stabile.

## Ecosistema

- `climpianti/cl-control`: Core HACS (Discovery, API, scenari)
- `climpianti/cl-control-web`: interfaccia cliente e installatore
- `climpianti/CL-Power-Control` e `climpianti/CL-Irrigation`: moduli indipendenti

La convergenza delle API avverrà nei prossimi incrementi, senza copiare codice del vecchio backend.
