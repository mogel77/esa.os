import configparser
import os




def checkEntry(section, key, value):
    global config, configchanges
    if not config.has_section(section):
        config.add_section(section)
        print("keine Section '" + section + "' gefunden")
        configchanges = True
    if not config.has_option(section, key):
        config.set(section, key, value)
        print("Option '" + key + "' mit '" + value + "' angelegt")
        configchanges = True

def updateConfig():
    global config, configchanges
    # pauschal alles einlesen

    # alles nach Daten ..
    if not os.path.exists('daten'): os.makedirs('daten')
    # ... und Resourcen ...
    if not os.path.exists('resources'): os.makedirs('resources')
    # .. außer die Config
    config = configparser.ConfigParser()
    config.read('config.ini')

    # Konfiguration erstellen
    checkEntry('eddir', 'path', 'unset')
    checkEntry('eddir', 'lastlog', 'unsed')
    checkEntry('eddir', 'edmc', '../EDMarketConnector')

    # Download URLS
    # checkEntry('urls', 'commodities', 'https://edgalaxydata.space/EDDB/dumps/commodities.json')
    checkEntry('urls', 'galaxy_gz', 'https://downloads.spansh.co.uk/galaxy_1day.json.gz')

    # Dateinamen nach dem Download bzw. zum Speichern der Daten
    checkEntry('localnames', 'modnames', 'resources/modnames.json')
    checkEntry('localnames', 'stations', 'daten/stations.json')
    # checkEntry('localnames', 'commodities', 'daten/commodities.json')
    checkEntry('localnames', 'galaxy_gz', 'daten/galaxy.gz')
    checkEntry('localnames', 'galaxy_json', 'daten/galaxy.json')
    checkEntry('localnames', 'galaxy_jsonl', 'daten/galaxy.jsonl')
    checkEntry('localnames', 'materials', 'daten/materials.json')
    checkEntry('localnames', 'shiplocker', 'daten/shiplocker.json')
    checkEntry('localnames', 'missions', 'daten/missions.json')
    checkEntry('localnames', 'modules', 'daten/modules.json')
    checkEntry('localnames', 'saasignals', 'daten/saasignals.json')
    checkEntry('localnames', 'hangar', 'daten/hangar.json')
    checkEntry('localnames', 'outfit', 'daten/outfit.json')
    checkEntry('localnames', 'asteroid', 'daten/asteroid.json')

    # Zeitstempel der Downloads
    checkEntry('downloads', 'commodities', '20220101-000000')
    checkEntry('downloads', 'galaxy_gz', '20220101-000000')

    # Zeitrahmen der Updates -> Timeout
    checkEntry('updates', 'commodities', '168')     # 1x pro Woche
    checkEntry('updates', 'galaxy_gz', '24')           # 1x am Tag

    # Filter für die einzelnen Systeme und Stationen
    checkEntry('filter', 'distance', '1000')        # was weiter vom Heimatsystem weg ist, wird entfernt

    # Entfernungen der Stationen
    checkEntry('distances', 'stations', '5000')     # Ls
    checkEntry('distances', 'systems', '200')       # Ly

    # Details zum Benutzer
    checkEntry('user', 'license', 'no')             # yes fürs Akzeptieren (Verweis auf EDMC & Co)
    checkEntry('user', 'system', 'Sol')             # aktuelles System
    checkEntry('user', 'locx', '0.0')               # aktuelle Koordinaten
    checkEntry('user', 'locy', '0.0')
    checkEntry('user', 'locz', '0.0')
    checkEntry('user', 'homesys', 'Sol')               # Heimat System
    checkEntry('user', 'homex', '0.0')
    checkEntry('user', 'homey', '0.0')
    checkEntry('user', 'homez', '0.0')
    checkEntry('user', 'name', 'CMDR Jameson')
    checkEntry('user', 'ship', 'Sidewinder')
    checkEntry('user', 'ident', 'sf-one')           # Kennung des Schiffs
    checkEntry('user', 'credits', '1000')
    checkEntry('user', 'loan', '1000')              # Schulden, die Guten
    checkEntry('user', 'squadname', 'Einzelkämpfer')
    checkEntry('user', 'squadrank', '0')
    checkEntry('user', 'channel', 'auto')

    # Seitenmanagement
    checkEntry('pages', 'activepage','1')           # aktive Seite
    checkEntry('pages', 'priopage', 'mining')       # Seite nach einem NavRouteClear (Mining oder Cargo)
    checkEntry('pages', 'autopage','yes')           # later - automatisches Wechseln der Seiten bei passendem Event
    checkEntry('pages', 'events', 'no')             # debug-Ausgabe - oder auch knallen der Exception (also nicht verstecken)
    checkEntry('pages', 'edmc', 'no')          # Autostart von EDMC

    # und dann schreiben
    with open(r"config.ini", 'w') as configfile:
        config.write(configfile)



if __name__ == "__main__":
    updateConfig()

