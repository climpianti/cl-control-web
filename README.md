# CL Control Web

Interfaccia domotica premium di **CL Impianti**, coordinata con [climpianti.net](https://www.climpianti.net/).

## Stato del progetto
- **App installata di riferimento:** `CL Control Web 0.2.0-beta.6` su Home Assistant di test.
- **Repository:** fase di recupero e consolidamento del codice originale.
- **Design system:** bozza `design-system/cl-blue-tech-premium.css`, da integrare dopo collaudo.
- **Nessun rilascio installabile da questo repository è ancora disponibile.**

Non considerare i file pubblicati qui una copia completa dell'App. La Web App attuale utilizza Ingress e un backend con persistenza in `/data`: vanno importati anche backend, test, configurazioni degli ambienti di build e istruzioni di packaging.

## Architettura approvata
- **CL Control Web:** interfaccia unica per cliente e installatore (home, planimetrie, luci RGBW, multimedia, energia).
- [CL Control Core](https://github.com/climpianti/cl-control): integrazione HACS, API WebSocket, Discovery KNX/Modbus, scenari e servizi.
- CL Power Control e CL Irrigation: integrazioni autonome dell'ecosistema.

## Regole di sicurezza
- Nessuna credenziale o token Home Assistant in GitHub o nel frontend.
- Non pubblicare `/data`, file `.env`, backup, planimetrie reali o dati dei clienti.
- Prima di modificare l'App esistente: backup, test offline, verifica di compatibilità e piano rollback.
- Non disinstallare `local_cl_control_web`: potrebbe eliminare i dati persistenti.

## Sviluppo
La cartella `design-system/` contiene override CSS separati dal codice applicativo per favorire revisione e rollback. Non è ancora abilitata nell'App installata.

Vedi [MIGRATION.md](MIGRATION.md) per i passaggi di recupero della sorgente e convergenza verso HACS.
