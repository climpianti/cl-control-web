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
