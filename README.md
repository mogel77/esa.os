english - hmmmm, later

# Wer, Wie, Was

## Was ist es?
ESA.OS ist ein Schiff-Assistent für das Spiel [Elite Dangerous](https://www.elitedangerous.com/).

Prinzipell sollte es auf jedem Betriebsystem mit Python 3.10 laufen. Das Design ist aber komplett für die Konsole konzipiert und sieht nur richtig gut mit [Cool-Retro-Term](https://github.com/Swordfish90/cool-retro-term) (Hilfe für [Windows 10](https://gist.github.com/h3r/2d5dcb2f64cf34b6f7fdad85c57c1a45) [dezent veraltet]) aus. Im Vollbild auf einem zweiten Monitor. Für mich persönlich gehört das zu einem Weltraumspiel dazu (vgl. Kerbel Space Programm).

## Bedienung

Wie in der Console üblich wird auf Tastendruck reagiert, die Maus ist also unnütz. Und damit nicht ständig zwischen den Fenstern bzw. Monitoren gewechselt wrden muss, schalten ESA.OS automatisch die passenden Seiten auf. Wenn also etwas Gekauft/Verkauft wurde wird der Cargo angezeigt. Nimmt man eine Mission an, wird automatisch die Missionsübersicht gezeigt. Wird eine Route geplant, dann die Routen-Seiten.

Um auf verschiedenen Seiten zusätzlich die Preise noch zu sehen, muss über die Einstellungsseite die nötige Datenbank herunter geladen werden. Die Empfehlung für den Kaffee ist wichtig, da der Download durchaus eine Weile dauern kann (+15min).

# Installation

## erste Verwendung

### Vorweg: Update der Sternensysteme

Da die Datenmenge inzwischen gigantisch ist, habe ich zwei Varianten implementiert.  Beide Varianten benötigen (viel) Zeit ...

Der eigentliche Datensatzt wird zwar als GZip bereit gestellt, aber nach dem Auspacken ist es immer noch ein gigantischer "Block". Um damit auch auf Rechner mit wenig Speicher spielen zu können, muss dieser "Block" in einzelne Zeilen zerlegt werden. Und dieses Zerlegen frisst Speicher und Zeit.

Beide Varianten lauf aber im Hintergrund ab. Nebei Spielen ist also nicht das Problem.

#### Der "Fast-Mode"

Auch wenn ich es Fast-Mode nenne, es dauert ca. 15 Minuten. Hierbei war bei mir der Speicherverbrauch etwa 40GB. Dafür wird die gesamte Arbeit im Arbeitsspeicher ausgeführt und belasstet nicht die Festplatte.

#### Low-Memory Mode

Wärend beim "Fast-Mode" Python das Zerlegen der Daten automatisch erledigt, muss ich im Low-Memory Mode alles selber machen. Dazu verbleibt aber die Datei auf der Festplatte und entsprechend werden viele I/O Operationen auf der Festplatte ausgeführt. Bei mir waren es ca. 60 Minuten -.-

### kurze Konfiguration

Am einfachten ist es erstmal `config.py` zu starten. Dadurch wird die `config.ini` erzeugt. Der Pfad für das Elite Dangerous Journal muss gesetzt werden. Dazu in der Section 'eddir' den Wert 'path' mit dem richtigen Verzeichnis füttern.

Entgegen den meisten anderen Spielen erzeugt Elite eine Datei mit allem was im Spiel so passiert. Und der Ort ist für ESA.OS nötigt. (falls Elite an andere Stelle gespeichert ist, dann ggf. anpassen) Es reicht das Verzeichnis, da pro Sitzung eine neue Datei erzeugt wird.

#### Journal unter Windows

    Saved Games\Frontier Developments\Elite Dangerous

bzw.

    shell:SavedGames\Frontier Developments\Elite Dangerous\

#### Journal unter Linux

    ~/.steam/steam/steamapps/compatdata/359320/pfx/drive_c/users/steamuser/Saved Games/Frontier Developments/Elite Dangerous

### Lizenz

Ja, der muss zugestimmt werden. Wenn der Pfad für das Journal in der Konfiguration bereits angepasst wurde, dann ist das der kleine Schritt.

### Windows

Im folgenden einige Tipps für Windows-Nutzer. Ich selber nutze Windows nur in einer virtuellen Maschine (KVM/qemu). Habe python daher auch nur "roh" getestet, da mir die VM das Spiel nicht startet.

#### Installation von Python 3.10

https://www.python.org/downloads/windows/

Haken bei "Add Python to PATH" setzen und dann "Customize installation". Auch hier alle Haken setzen, anschließend "Next". Haken bei "Add Python to environment variables" setzen.

#### Starten

Einfach `esaos.bat` mit dem Üblichen doppeltem Klick starten. Nötige Pakete werden automatisch nachinstalliert. Die Konsole legt die benötigte Größe automatisch fest.

#### Cool-Retro-Term

Ich habe es nicht geschafft nach [der Anleitung](https://gist.github.com/h3r/2d5dcb2f64cf34b6f7fdad85c57c1a45) das Terminal zum Laufen zu bringen. Bis zum compilieren des Programms funktioniert es. Kleinere Fallstricke, die zwischendurch auftreten, lassen sich mit Google lösen.

Evt. lag es bei mir daran, das ich Windows nur in einer VM nutze und WSL (vermutlich) selbiges macht. Dadurch entsteht eine VM in einer VM.

Es fehlt dadurch natürlich das von mir gewollte "Flair".

## Python Packages

* Python 3.10.6 (zumindest lief es damit auf meinem Rechner)
* vermutlich `curses` bzw. `ncurses`

# TODO + Bugs und ~~Probleme~~ Herausforderungen

* mal schauen das die Installation unter Windows einfacher wird
* Credits komplett abfangen - leider kommt für jede Transaktion ein eigenes Event und alle habe ich an dere Stelle noch nicht "gefunden"



# externe Seiten - die geholfen haben

* Audio - https://www.soundjay.com/dial-up-modem-sound-effect.html
* ANSI-Art - https://patorjk.com/software/taag/#p=display&f=Graceful&t=esa.os
