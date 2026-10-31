# Piano di recupero e migrazione

## Fonte verificata
- App Home Assistant `local_cl_control_web`, versione `0.2.0-beta.6`, in esecuzione.
- Asset HTTP `/assets/app.css` leggibile.
- `/assets/app.js` viene restituito con un limite di risposta di 51.200 caratteri: **non è una sorgente completa verificata**.
- Il solo frontend HTTP non contiene il codice Python/backend, i Dockerfile o i test.

## Prossimi passi
1. Recuperare i sorgenti originali dell'App dalla cartella locale `local_apps/cl_control_web` (su precedenti sistemi `addons/cl_control_web`) tramite accesso autorizzato ai file di Home Assistant o archivio sorgente.
2. Importarli in un ramo di sviluppo con audit per credenziali, dati cliente e percorsi locali.
3. Eseguire test backend/frontend e creare un checkpoint sulla beta funzionante.
4. Applicare e testare la palette di `design-system/cl-blue-tech-premium.css` e poi integrare i componenti nel CSS principale.
5. Eliminare la duplicazione di logica tra Web App e Core HACS usando API documentate.
6. Distribuire sul solo impianto beta, verificare migrazione di impostazioni, immagini e marker e mantenere rollback.

## Nota
L'aggiornamento della Web App installata **non è stato eseguito** tramite questo repository. Non sostituire i file dell'App con soltanto gli asset recuperati dall'HTTP.
