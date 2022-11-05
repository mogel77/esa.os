english - hmmmm, later

# Wer, Wie, Was

ESA.OS ist ein zusätzliches Hilfsmittel für das Spiel [Elite Dangerous](https://www.elitedangerous.com/).

Prinzipell sollte es auf jedem Betriebsystem mit Python 3.10 laufen. Das Design ist aber komplett für die Konsole konzipiert und sieht nur richtig gut mit [Cool-Retro-Term](https://github.com/Swordfish90/cool-retro-term) aus. Im Vollbild auf einem zweiten Monitor. Für mich persönlich gehört das zu einem Weltraumspiel dazu (Kerbel Space Programm).

## Seiten

Wie in der Console üblich wird auf Tastendruck reagiert, die Maus ist also unnütz. Und damit nicht ständig zwischen den Fenstern bzw. Monitoren gewechselt wrden muss, schalten ESA.OS automatisch die passenden Seiten auf. Wenn also etwas Gekauft/Verkauft wurde wird der Cargo angezeigt. Nimmt man eine Mission an, wird automatisch die Missionsübersicht gezeigt. Wird eine Route geplant, dann die Routen-Seiten.

Um auf verschiedenen Seiten zusätzlich die Preise noch zu sehen, muss über die Einstellungsseite die nötige Datenbank herunter geladen werden. Die Empfehlung für den Kaffee ist wichtig, da der Download durchaus eine Weile dauern kann (+5min).

# Installation

## erste Verwendung

### kurze Konfiguration

Am einfachten ist es erstmal `config.py` zu starten. Dadurch wird die `config.ini` erzeugt. Der Pfad für das Elite Dangerous Journal muss gesetzt werden. Dazu in der Section 'eddir' den Wert 'path' mit dem richtigen Verzeichnis füttern. Alle anderen Werte sind erstmal unwichtig

### Lizenz

Ja, der muss zugestimmt werden. Wenn der Pfad für das Journal in der Konfiguration bereits angepasst wurde, dann ist das der kleine Schritt.

## Python Packages

* Python 3.10.6 (zumindest lief es damit auf meinem Rechner)
* vermutlich `curses` bzw. `ncurses`
* tweepy

# TODO + Bugs und ~~Probleme~~ Herausforderungen

* Credits komplett abfangen - leider kommt für jede Transaktion ein eigenes Event und alle habe ich an dere Stelle noch nicht "gefunden"
* Outfitter Seite übersetzten - aktuell sind das noch die reinen Keys von ED



# externe Seiten - die geholfen haben

* Audio - https://www.soundjay.com/dial-up-modem-sound-effect.html
* ANSI-Art - https://patorjk.com/software/taag/#p=display&f=Graceful&t=esa.os
