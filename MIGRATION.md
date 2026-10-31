# Sostituzione della vecchia App (procedura, non ancora eseguita)

1. Verificare il repository e i controlli CI.
2. Installare l'integrazione `cl_control_web` sul beta test **in parallelo**, lasciando `local_cl_control_web` avviata.
3. Controllare il rendering mobile e desktop, i comandi principali, i log e la Discovery ETS.
4. Confermare che non esistono dipendenze e salvare un backup separato di configurazione e dati dell'App precedente.
5. Fermare la vecchia App; non disinstallarla prima della verifica di rollback.
6. Solo dopo il collaudo, rimuovere la vecchia App con conferma esplicita degli effetti sui dati.

Rollback: disabilitare/rimuovere solo la nuova integrazione `cl_control_web` e tornare alla vecchia App; evitare restore globale HA per un problema soltanto UI.
