import requests
import gzip
import shutil
import os
import curses
import math
import json
import time
import random
import sys
from os.path import exists
from datetime import datetime
from enum import Enum

from tools import getDictItem
from config import updateConfig





class PageBasepage:
    def __init__(self, config, gamedata):
        self.screen = curses.newwin(22, 110, 7, 20)
        self.config = config
        self.gamedata = gamedata
        curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    def t(self, key): # !! douh !! die Erste
        lang = self.config["user"]["language"]
        if not key in self.gamedata["translations"]:
            self.gamedata["logger"].error(f"Key '{key}' nicht gefunden")
            return key
        if not lang in self.gamedata["translations"][key]:
            self.gamedata["logger"].error(f"Sprache '{lang}' für '{key}' nicht gefunden")
            return lang
        return self.gamedata["translations"][key][lang]
    def handleInput(self, key):
        #self.gamedata["logger"].warn("keine Überschreibung der Tasten für die aktuelle Page")
        pass
    def update(self):
        #self.gamedata["logger"].warn("keine Überschreibung der aktuellen Page für Ausgabe")
        pass
    def print(self, posy, posx, content):
        color_escape = False
        color_color = 0         #   -_-
        try:
            if len(content) > 0:
                for i in range(0, len(content)):
                    char = content[i]
                    if color_escape:
                        if char == "w": color_color = 0
                        if char == "b": color_color = 1
                        if char == "r": color_color = 2
                        if char == "g": color_color = 3
                        if char == "y": color_color = 4
                        color_escape = False
                        continue
                    if char == "~":
                        color_escape = True
                        continue
                    if self.config["pages"]["coloring"] == "no": color_color = 0
                    if posx < curses.COLS - 1: self.screen.addstr(posy, posx, char, curses.color_pair(color_color))
                    color_escape = False
                    posx += 1
            else:
                self.screen.addstr(posy, posx, "", curses.color_pair(0))
        except curses.error:
            pass # ! douh ! - schlucken ist immer doof
    def countDrones(self):
        # zählt die drohnen im Cargo
        if len(self.gamedata["cargo"]) == 0: return 0
        for fracht in self.gamedata["cargo"]:
            if fracht["Name"] == "drones": return fracht["Count"]
        return 0
    def hasCargo(self):
        # prüft den Cargo - abzüglich Drohnen
        if len(self.gamedata["cargo"]) == 0: return False
        # wenigsten eine Fracht anders als Drohnen
        if len(self.gamedata["cargo"]) > 1: return True
        drones = False
        for fracht in self.gamedata["cargo"]:
            if fracht["Name"] == "drones": drones = True
        return not drones
    def getPrice(self, market, commodities):
        # der Preis am Markt
        for c in market["commodities"]:
            if c["symbol"] == commodities: return int(c["sellPrice"])
        return 0
    def getHighestPriceMarket(self, itemname):
        # der Markt mit dem besten Preis
        market = None       # der kaufende Markt
        price = 0           # der Preis des Marktes
        playerpos = [ float(self.config["user"]["locx"]), float(self.config["user"]["locy"]), float(self.config["user"]["locz"]) ]
        for station in self.gamedata["stations"]:
            systempos = [ float(station["coords"][0]), float(station["coords"][1]), float(station["coords"][2]) ]
            distance = math.dist(playerpos, systempos)
            if distance > float(self.config["distances"]["systems"]): continue
            if station["ls"] > float(self.config["distances"]["stations"]): continue
            for commodities in station["commodities"]:
                if commodities["demand"] <= 0: continue;
                if commodities["symbol"] != itemname: continue
                if commodities["sellPrice"] < 1.0: continue
                if market is None:
                    market = station
                    price = self.getPrice(station, itemname)
                else:
                    neu = self.getPrice(station, itemname)
                    if neu > price:
                        market = station
                        price = neu
        return market
    def getCheapestPriceMarket(self, itemname):
        # Markt mit dem billigsten Preis
        market = None       # der verkaufende Markt
        price = 10000000    # der Preis des Marktes - dürfte aktuelle nie höher sein
        playerpos = [ float(self.config["user"]["locx"]), float(self.config["user"]["locy"]), float(self.config["user"]["locz"]) ]
        for station in self.gamedata["stations"]:
            systempos = [ float(station["coords"][0]), float(station["coords"][1]), float(station["coords"][2]) ]
            distance = math.dist(playerpos, systempos)
            if distance > float(self.config["distances"]["systems"]): continue
            if station["ls"] > float(self.config["distances"]["stations"]): continue
            for commodities in station["commodities"]:
                if commodities["supply"] <= 0: continue;
                if commodities["symbol"] != itemname: continue
                if commodities["buyPrice"] < 1.0: continue
                if market is None:
                    market = station
                    price = self.getPrice(station, itemname)
                else:
                    neu = self.getPrice(station, itemname)
                    if neu < price:
                        market = station
                        price = neu
        return market
    def getNearestPrice(self, itemname, supply=0):
        # der am nächsten liegende Markt
        # self.gamedata["logger"].info("suche Item: " + itemname)
        market = None                                           # der verkaufende Markt
        mindistance = float(self.config["distances"]["systems"])   # der Preis des Marktes - dürfte aktuelle nie höher sein
        playerpos = [ float(self.config["user"]["locx"]), float(self.config["user"]["locy"]), float(self.config["user"]["locz"]) ]
        for station in self.gamedata["stations"]:
            systempos = [ float(station["coords"][0]), float(station["coords"][1]), float(station["coords"][2]) ]
            distance = math.dist(playerpos, systempos)
            if distance > float(self.config["distances"]["systems"]): continue
            if station["ls"] > float(self.config["distances"]["stations"]): continue
            for commodities in station["commodities"]:
                if commodities["supply"] <= supply: continue;
                if commodities["symbol"] != itemname: continue
                if commodities["buyPrice"] < 1.0: continue
                if market is None:
                    market = station
                    self.result_distance = mindistance
                else:
                    if distance < mindistance:
                        market = station
                        mindistance = distance
                        self.result_distance = mindistance
        return market
    def getStationWithService(self, servicename):
        station = None                                          # die anbietende Station
        distance = 120000                                       # müsste reichen
        # wird IMMER global gesucht
        playerpos = [ float(self.config["user"]["locx"]), float(self.config["user"]["locy"]), float(self.config["user"]["locz"]) ]
        for s in self.gamedata["stations"]:
            systempos = [ float(s["coords"][0]), float(s["coords"][1]), float(s["coords"][2]) ]
            if distance < math.dist(playerpos, systempos): continue
            if not "services" in s: continue
            found = False
            for service in s["services"]: 
                if service.casefold() == servicename.casefold(): found = True
            if not found: continue
            distance = math.dist(playerpos, systempos)
            station = s
        return station
    def getMission4ID(self, missionid):
        if len(self.gamedata["missions"]) == 0: return None
        for m in self.gamedata["missions"]:
            if m == missionid: return m
        return None
    def getMission4Item(self, itemname_localised):
        if len(self.gamedata["missions"]) == 0: return None
        for m in self.gamedata["missions"]:
            if getDictItem(m, "Commoditiy", "Commodity_Localised").casefold() == itemname_localised.casefold(): return m
        return None
    def getItemFromCargo(self, itemname):
        if len(self.gamedata["cargo"]) == 0: return None
        for item in self.gamedata["cargo"]:
            cargoname = getDictItem(item, "Name", "Name_Localised")
            if cargoname.casefold() == itemname.casefold(): return item
        return None





class PageLoading(PageBasepage):        # ohne Kennung
    esa = [
            "Elite Ship Assistant . Operating System . V2.beta.apfel-666",
            "",
            " ____  __    __  ____  ____                        ",
            "(  __)(  )  (  )(_  _)(  __)                       ",
            " ) _) / (_/\ )(   )(   ) _)                        ",
            "(____)\____/(__) (__) (____)                       ",
            " ____  _  _  __  ____                              ",
            "/ ___)/ )( \(  )(  _ \                             ",
            "\___ \) __ ( )(  ) __/                             ",
            "(____/\_)(_/(__)(__)                               ",
            "  __   ____  ____  __  ____  ____  __   __ _  ____ ",
            " / _\ / ___)/ ___)(  )/ ___)(_  _)/ _\ (  ( \(_  _)",
            "/    \\\\___ \\\\___ \ )( \___ \  )( /    \/    /  )(  ",
            "\_/\_/(____/(____/(__)(____/ (__)\_/\_/\_)__) (__) ",
            "",
            "Willkommen zurück {0}",
            " - lade Sternensysteme",
            ""
        ]

    def __init__(self, config, gamedata):
        super().__init__(config, gamedata)

    def update(self):
        self.screen.clear()
        for i in range(0, len(self.esa)):
            self.print(i, 0, self.esa[i].format(self.config["user"]["name"]))
            self.screen.refresh()
            time.sleep(random.random() / 3)
class PageLicense(PageBasepage):        # ohne Kennung
    lic = [
            "Lizenbestimmungen für ESA.OS",
            "",
            "[X] ich gelobe EDMarketConnector oder ein vergleichbares",
            "    Programm zu verwenden, um die Marktdaten auf",
            "    aktuellen Stand - für alle Spieler - zu halten",
            "",
            "[{0}] Pfad in der 'config.ini' ist auf das ED-Verzeichnis gesetzt",
            "",
            "Drücke {1} zum Akzeptieren"
        ]
    def __init__(self, config, gamedata):
        super().__init__(config, gamedata)

    def update(self):
        self.screen.clear()
        checkpath = " "
        key = "---"
        if exists(self.config["eddir"]["path"]):
            checkpath = "X"
            key = "(T)"
        for i in range(0, len(self.lic)):
            self.print(i, 0, self.lic[i].format(checkpath, key))
        self.screen.refresh()

    def handleInput(self, key):
        if not key == "t" or key == "T": return
        if not exists(self.config["eddir"]["path"]): return
        self.config["user"]["license"] = "yes"
        with open(r"config.ini", 'w') as configfile: self.config.write(configfile)
class PageDownloads(PageBasepage):      # U
    uds = [
                " _  _  ____  ____   __  ____  ____    ____  ____  ____                              ",
                "/ )( \(  _ \(    \ / _\(_  _)(  __)  (    \(  __)(  _ \                             ",
                ") \/ ( ) __/ ) D (/    \ )(   ) _)    ) D ( ) _)  )   /                             ",
                "\____/(__)  (____/\_/\_/(__) (____)  (____/(____)(__\_)                             ",
                " ____  ____  ____  ____  __ _  ____  __ _  ____  _  _  ____  ____  ____  _  _  ____ ",
                "/ ___)(_  _)(  __)(  _ \(  ( \(  __)(  ( \/ ___)( \/ )/ ___)(_  _)(  __)( \/ )(  __)",
                "\___ \  )(   ) _)  )   //    / ) _) /    /\___ \ )  / \___ \  )(   ) _) / \/ \ ) _) ",
                "(____/ (__) (____)(__\_)\_)__)(____)\_)__)(____/(__/  (____/ (__) (____)\_)(_/(____)",
                "",
                "(BTW: es ist Zeit für einen Kaffee)"
            ]
    def __init__(self, config, gamedata):
        super().__init__(config, gamedata)

    def download(self, key):
        url = self.config["urls"][key]
        name = self.config["localnames"][key]
        headers = { "User-Agent" : "Github / ESA.OS (Elite Ship Assistant)" }
        r = requests.get(url, allow_redirects=True, headers=headers)
        open(name, 'wb').write(r.content)

    def printline(self, y, x, text):
        self.print(y, x, text)
        self.print(y + 1, x, "> ")
        self.screen.refresh()

    def downloadAndClip(self):
        # download
        self.download("galaxy_gz")
        # auspacken
        self.printline(14, 5, "> gzip -u galaxy.gz")
        with gzip.open(self.config["localnames"]["galaxy_gz"], 'rb') as f_in:
            with open(self.config["localnames"]["galaxy_json"], 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        # manuell wandeln von JSON nach JSONL
        self.printline(15, 5, "> split galaxy.json -format jsonl")
        with open(self.config["localnames"]["galaxy_json"], 'rb+') as file:
            file.seek(0, 0)
            # Klammer '[' am Anfang löschen - davon ausgehend das kein BOM
            # vorhanden ist und es gleich damit losgeht
            file.write(b' ')
            # Klammer ']' am Ende suchen und löschen
            for i in range(0, 10):
                file.seek(0 - i, 2)
                character = file.read(1)
                # print(character)
                if character == b']':
                    # durch das lesen sind wir einmal weiter gerutscht
                    file.seek(0 - i, 2)
                    # Klammer löschen
                    file.write(b' ')
                    break # komplett abbrechen - sonst werden
                # weitere Klammern gefunden, welche den letzten Datensatz zerstören
            filesize = os.stat(self.config["localnames"]["galaxy_json"]).st_size
            position = 0
            clipcounter = 0
            #print("Filesize: {0} bytes".format(filesize))
            while position < (filesize - 2):
                file.seek(position, 0)
                character = file.read(1)

                # Klammern zählen und ggf.
                # das Komma ersetzen
                if character == b'{':
                    clipcounter += 1
                if character == b'}':
                    clipcounter -= 1
                if character == b',':
                    if clipcounter == 0:
                        file.seek(position, 0)  # gleiche Pos
                        file.write(b'\n')       # Zeilenumbruch erzwingen
                        # print(f'Zeilenumbruch bei {position}')
                position += 1
                
                # Sicherheitscheck
                if clipcounter < 0:
                    #print(f'tja, schief gelaufen bei Position {position}')
                    break

    def update(self):
        self.gamedata["stations"] = []
        self.screen.clear()
        for i in range(0, len(self.uds)): self.print(i + 2, 5, self.uds[i])
        self.screen.refresh()
        self.printline(13, 5, "> download galaxy.gz \"https://files.egn/galaxy.gz\"")
        self.downloadAndClip()
        usecarrier = "-nocarrier"
        if self.config["distances"]["carrier"] == "yes": usecarrier = "-usecarrier"
        self.printline(16, 5, "> get stations from galaxy.json -max {0}ly {1}".format(self.config["filter"]["distance"], usecarrier))
        j_stations = []     # Array
        j_bodies = []
        firsthundret = 0
        with open(self.config["localnames"]["galaxy_json"], "r") as f:
#            galaxy = json.load(f)
            with open(self.config["localnames"]["bodies"], "w") as bodies:
                with open(self.config["localnames"]["stations"], "w") as stations:
                    hx = float(self.config["user"]["homex"])
                    hy = float(self.config["user"]["homey"])
                    hz = float(self.config["user"]["homez"])
                    userhome = [ hx, hy, hz ]
                    for line in f:
                        l = line.strip()  # einkürzen
                        if len(l) == 0:   # keine gültige Galaxy
                            continue
                        g = json.loads(l) # Galaxy zerlegen
                        dist = math.dist([ g["coords"]["x"], g["coords"]["y"], g["coords"]["z"] ], userhome)
                        if dist > float(self.config["filter"]["distance"]): continue
                        for station in g["stations"]:
                            if not "market" in station: continue
                            if self.config["distances"]["carrier"] == "no":
                                if "Carrier" in station["type"]:
                                    continue   # erstmal keine Carrier
                            j_market = {}
                            # -- for key, value in station.items(): print(key)
                            # System: name - coords
                            j_market["system"] = g["name"]
                            j_market["coords"] = [ g["coords"]["x"], g["coords"]["y"], g["coords"]["z"] ]
                            # Market: name - id
                            j_market["id"] = station["id"]
                            j_market["name"] = station["name"]
                            j_market["ls"] = station["distanceToArrival"]
                            j_market["services"] = []
                            if "services" in station: 
                                j_market["services"] = station["services"]
                                for service in j_market["services"]:
                                    if not service in self.config["pages"]["services_known"]:
                                        if len(self.config["pages"]["services_known"]) > 0: self.config["pages"]["services_known"] += ", "
                                        self.config["pages"]["services_known"] += service
                            # Prices
                            j_market["commodities"] = []
                            # -- for key, value in market.items(): print(key)
                            commodities = station["market"]["commodities"]
                            for c in commodities:
                                c["symbol"] = c["symbol"].lower()
                                j_market["commodities"].append(c)
                            j_stations.append(j_market)
                            stations.write(json.dumps(j_market) + '\n')
                        if "bodies" in g:
                            j_body = { }
                            j_body["system"] = g["name"]
                            j_body["coords"] = [ g["coords"]["x"], g["coords"]["y"], g["coords"]["z"] ]
                            j_body["bodies"] = [ ]
                            for b in g["bodies"]:
                                body = { }
                                body["name"] = b["name"]
                                if "typ" in b:
                                    body["type"] = b["type"]
                                else:
                                    body["type"] = "unknown"
                                body["id"] = b["bodyId"]
                                # belts -> []
                                # materials -> {}
                                # signals -> {}{}
                                if "subType" in b: body["subtype"] = b["subType"]
                                if "parents" in b: body["parents"] = b["parents"]
                                j_body["bodies"].append(body)
                            bodies.write(json.dumps(j_body) + '\n')

        # und gleich merken fürs spielen
        self.gamedata["stations"] = j_stations
        self.printline(16, 5, "{0} Stationen gefunden".format(len(j_stations)))
        os.remove(self.config["localnames"]["galaxy_gz"])
        os.remove(self.config["localnames"]["galaxy_json"])
        self.screen.clear()
        self.screen.refresh()
        self.config["pages"]["activepage"] = "0"





class PageCargo(PageBasepage):          # 1
    def __init__(self, config, gamedata):
        super().__init__(config, gamedata)
        self.loadCargo()

    def loadCargo(self):
        if not exists(self.config["eddir"]["path"] + "/Cargo.json"): return
        with open(self.config["eddir"]["path"] + "/Cargo.json", "r") as f:
            self.gamedata["cargo"] = json.load(f)["Inventory"]

    def update(self):
        self.cargouse = 0
        self.marge_total = 0
        if len(self.gamedata["stored"]["outfit"]) > 0:
            self.cargomax = self.gamedata["stored"]["outfit"]["CargoCapacity"]
        else:
            self.cargomax = 999 # maximaler Speicherraum - da das Outfit noch nicht geladen wurde
        self.limpetcount = 0
        self.screen.clear()
        if self.hasCargo(): # mehr als genug Fracht
            self.update_cargo()
        else:
            # entweder 1x Fracht oder nur Drohnen
            self.limpetcount = self.countDrones()
            if self.limpetcount == 0:
                # es ist Fracht
                self.update_cargo()
            else: # es sind nur Drohnen
                self.cargouse = self.limpetcount
                self.update_clear()
        self.showCapacity()
        self.screen.refresh()
    def update_clear(self):
        self.print(5, 10, "der Frachtraum ist zur Zeit leer")
    def update_cargo(self):
        cargo = self.gamedata["cargo"]
        self.print(10, 20, "... berechne Daten für aktuellen Cargo ...")
        self.screen.refresh()
        self.screen.clear()
        playerpos = [ float(self.config["user"]["locx"]), float(self.config["user"]["locy"]), float(self.config["user"]["locz"]) ]
        itemnumber = 0
        price = 0
        self.cargouse = self.countDrones()
        for item in cargo:
            cargo_item = item["Name"] # NICHT den Name_Localised
            if cargo_item == "drones": continue # Drohnen werden nicht direkt gezählt
            station = self.getHighestPriceMarket(cargo_item)
            cargo_count = item['Count']
            self.cargouse += cargo_count
            mission = self.getMission4Item(getDictItem(item, "Name", "Name_Localised"))
            if mission is None:
                if "MissionID" in item: mission = self.getMission4ID(item["MissionID"])
            line2 = ""
            if not station is None:
                price = self.getPrice(station, cargo_item)
                systempos = [ float(station["coords"][0]), float(station["coords"][1]), float(station["coords"][2]) ]
                distance = math.dist(playerpos, systempos)
                cargo_marge = "{:,}".format(price * cargo_count)
                line1 = "{0:>14}\u00A2   {1:3}  {2:30}".format(cargo_marge, cargo_count, getDictItem(item, "Name", "Name_Localised"))
                if not mission is None:
                    missionname = getDictItem(mission, "Name", "LocalisedName")
                    missionsystem = mission["DestinationSystem"]
                    line2 = "{0:14}    {1:3}  >> Fracht für: {2} ({3})".format(" ", " ", missionname, missionsystem) # , maxdistance, cargo_system, cargo_market)
                else:
                    cargo_system = station["system"]
                    cargo_market = station["name"]
                    line2 = "{0:14}    {1:3}  {2:4.1f}ly {3} ({4})".format(" ", " ", distance, cargo_system, cargo_market)
                self.marge_total += price * cargo_count
            else:
                line1 = "{0:>14}\u00A2   {1:3}  {2:30}".format(0, cargo_count, cargo_item)
                if not "MissionID" in item:
                    missionitem = False
                    for mission in self.gamedata["missions"]:
                        if "Commodity_Localised" in mission:
                            if mission["Commodity_Localised"].lower() == cargo_item.lower(): missionitem = True
                    if missionitem:
                        line2 = "{0:14}    {1:3}  >> mögliche Fracht für eine Liefer-Mission".format(" ", " ") # , maxdistance, cargo_system, cargo_market)
                    else:
                        line2 = "{0:14}    {1:3}  innerhalb von {2:4.1f}ly nicht verkaufbar".format(" ", " ", float(self.config["distances"]["systems"]))
                else:
                    mission = self.getMission(item["MissionID"])
                    if mission is None:
                        line2 = "{0:14}    {1:3}  >> Fracht für eine unbekannte Mission".format(" ", " ")
                    else:
                        line2 = "{0:14}    {1:3}  >> {2}".format(" ", " ", mission["LocalisedName"])
            if item["Name"] == "drones":
                self.limpetcount = cargo_count
                continue # Drohnen müssen ausgeblendet werden
            self.print(itemnumber * 2 + 0, 5, line1)
            self.print(itemnumber * 2 + 1, 5, line2)
            itemnumber += 1
            self.screen.refresh()
    def showCapacity(self):
        percent = 0
        if self.cargomax != 0: percent = (self.cargouse / self.cargomax) * 100.0
        filler = ""
        for i in range(0, 100): filler += " "     # vorfüllen
        temp = list(filler)
        for i in range(0, int(percent)): temp[i] = "="     # auffüllen
        filler = "".join(temp)
        #output = "{0:>3} Drohnen [{1}] {2:>3}/{3:>3}".format(self.limpetcount, filler, self.cargouse, self.cargomax)
        self.print(21, 2, "[{0}]".format(filler))
        self.print(20, 2, "{0} Drohnen".format(self.countDrones()))
        self.print(20, 95, "{0:>3} / {1:>3}".format(self.cargomax - self.cargouse, self.cargomax))
        self.print(20, 35, "{0:^20}".format("{0:,}\u00A2 ".format(self.marge_total)))
class PageRoute(PageBasepage):          # 2
    def __init__(self, config, gamedata):
        super().__init__(config, gamedata)
        self.loadRoute()
    def loadRoute(self):
        if not exists(self.config["eddir"]["path"] + "/NavRoute.json"): return
        with open(self.config["eddir"]["path"] + "/NavRoute.json", "r") as f:
            self.gamedata["route"] = json.load(f)["Route"]
    def update(self):
        self.loadRoute()
        self.screen.clear()
        self.disttotal = 0
        if len(self.gamedata["route"]) > 0:
            self.update_route()
            self.showProgress()
            self.showTravel()
        else:
            self.update_clear()
        self.showServices()
        self.screen.refresh()
    def update_clear(self):
        self.print(5, 5, "es ist im Moment keine Reise geplant")
    def update_route(self):
        route = self.gamedata["route"]
        fuelstar = "KGBMOFA" # Sterne zum Tanken
        oldpos = [ float(self.config["user"]["locx"]), float(self.config["user"]["locy"]), float(self.config["user"]["locz"]) ]
        position = 0
        jumps = 0
        found = False
        self.routestep = 0
        for system in route:
            if system["StarSystem"] == self.config["user"]["system"]:
                found = True
                continue
            if not found:
                # geflogenen Punkte zählen
                self.routestep += 1
                continue
            distance = math.dist(oldpos, system["StarPos"])
            name = system["StarSystem"]
            startype = system["StarClass"]
            if (position < 18):
                if not startype in fuelstar: startype = "!"
                if system["StarClass"][0] == "D": startype = "*"
                self.print(position, 5, "{2}   {0:6.1f}ly   {1}".format(distance, name, startype))
            else:
                self.print(18, 5, "{0:8} {1}   noch {2} Sprünge".format(" ", "...", len(route) - self.routestep - 1))
            oldpos = system["StarPos"]
            self.disttotal += distance
            position += 1           # Position für die Ausgabe
            jumps += 1              # Anzahl der noch vorhandenen Sprünge
        if position > 16: position = 16
        self.screen.refresh()
    def showProgress(self):
        fuelstar = "KGBMOFA" # Sterne zum Tanken
        routemax = len(self.gamedata["route"])
        if routemax <= 1: return # Sec-Check
        filler = ""
        for i in range(0, 100): filler += "-"     # vorfüllen
        temp = list(filler)
        # Problemsterne anzeigen
        star = 0
        for system in self.gamedata["route"]:
            star += 1
            startype = system["StarClass"]
            if startype in fuelstar:
                continue
            startype = "!"
            pos = star / len(self.gamedata["route"]) * 100
            if system["StarClass"][0] == "D": startype = "*"
            if pos < 100: temp[int(pos)] = startype
        # aktuelle Position
        percent = (self.routestep / routemax) * 100.0
        if percent < 100: temp[int(percent)] = "X"     # Position anzeigen
        filler = "".join(temp)
        self.print(21, 2, "[{0}]".format(filler))
        self.print(20, 2, "{0}".format(self.gamedata["route"][0]["StarSystem"]))
        self.print(20, 74, "{0:>30}".format(self.gamedata["route"][routemax - 1]["StarSystem"]))
        self.print(20, 35, "{0:^20}".format("{0:.1f}ly".format(self.disttotal)))
    def showServices(self):
        services = []
        for s in self.config["pages"]["services"].split(","): services.append(s.strip())
        playerpos = [ float(self.config["user"]["locx"]), float(self.config["user"]["locy"]), float(self.config["user"]["locz"]) ]
        line = 0
        for service in services:
            station = self.getStationWithService(service)
            if station is None: continue
            systempos = [ float(station["coords"][0]), float(station["coords"][1]), float(station["coords"][2]) ]
            distance = math.dist(playerpos, systempos)
            self.print(2 * line + 0, 50, "~g{0}~w in ~g{1}~w".format(service, station["system"]))
            self.print(2 * line + 1, 50, "   {0:.1f}ly bei {1}".format(distance, station["name"]))
            line = line + 1
            if line > 11: break
    def showTravel(self):
        travel = "(~yR~w) Reiseroute: {0}ly total".format(self.config["user"]["travel"])
        self.print(18, 68, "{0:>40}".format(travel))
    def handleInput(self, key):
        if key == "r" or key == "R":
            self.config["user"]["travel"] = "0"
            self.update()
class PageMissions(PageBasepage):       # 3
    def __init__(self, config, gamedata):
        super().__init__(config, gamedata)
        self.loadMissions()
    def loadMissions(self):
        if exists(self.config["localnames"]["missions"]):
            with open(self.config["localnames"]["missions"], "r") as file:
                for line in file.readlines():
                    mission = json.loads(line)
                    self.gamedata["missions"].append(mission)
    def update(self):
        self.screen.clear()
        if len(self.gamedata["missions"]) > 0:
            self.update_missions()
        else:
            self.update_clear()
        self.screen.refresh()
    def update_clear(self):
        self.print(5, 10, "keine Aufträge vorhanden")
    def getExpiry(self, mission):
        if "Expiry" in mission:
            now = datetime.utcnow()
            exp = datetime.fromisoformat(mission["Expiry"].replace("T", " ").replace("Z", ""))
            s = (exp - now).seconds
            hours = s // 3600
            s = s - (hours * 3600)
            minutes = s // 60
            return "{:02}h{:02}m".format(int(hours), int(minutes))
        return "zeitlos"
    def update_missions(self):
        line = 0
        for mission in self.gamedata["missions"]:
            self.isCorrectSystem = False
            mission_type = mission["Name"].casefold()
            expired = self.getExpiry(mission)
            self.gamedata["logger"].info(mission_type + ": " + mission["LocalisedName"]);
            self.print(line * 2 + 0, 2, "{0:>10}   {1}".format(expired, mission["LocalisedName"]))
            if "mission_collect" in mission_type: self.showMissionDefault(mission, line)
            if "mission_mining" in mission_type: self.showMining(mission, line)
            if "mission_delivery_cooperative" in mission_type: self.showDeliveryCoop(mission, line)
            if "mission_onfoot_collect" in mission_type: self.showFootCollect(mission, line)
            if "mission_salvage" in mission_type: self.showMissionDefault(mission, line)
            if "mission_courier" in mission_type: self.showMissionDefault(mission, line)
            if "mission_courier_service" in mission_type: self.showMissionDefault(mission, line)
            if "mission_delivery_democracy" in mission_type: self.showMissionDefault(mission, line)
            if "mission_courier_engineer" in mission_type: self.showMissionDefault(mission, line)
            if "mission_onfoot_salvage" in mission_type: self.showFootCollect(mission, line)
            if "mission_onfoot_assassination" in mission_type: self.showMissionAssasinate(mission, line)
            if "mission_onfoot_onslaught" in mission_type: 
                if not "illegal" in mission_type:
                    self.showMissionOnslaughtLegal(mission, line)
                else:
                    self.showMissionOnslaughtIllegal(mission, line)
            if self.isCorrectSystem: self.print(line * 2 + 1, 13, ">")
            self.screen.refresh()
            line += 1
    def showMissionDefault(self, mission, line):
        if "DestinationStation" in mission:
            self.print(line * 2 + 1, 2, "{0:>10}   {1} ({2})".format(" ", mission["DestinationSystem"], mission["DestinationStation"]))
        else:
            self.print(line * 2 + 1, 2, "{0:>10}   {1} ({2})".format(" ", mission["DestinationSystem"], mission["DestinationSettlement"]))
        if mission["DestinationSystem"] == self.config["user"]["system"]: self.isCorrectSystem = True
    def showMissionAssasinate(self, mission, line):
        if "DestinationStation" in mission:
            self.print(line * 2 + 1, 2, "{0:>10}   zurück nach {1} ({2})".format(" ", mission["DestinationSystem"], mission["DestinationStation"], mission["Target"]))
        else:
            self.print(line * 2 + 1, 2, "{0:>10}   töte {3} in {1} ({2})".format(" ", mission["DestinationSystem"], mission["DestinationSettlement"], mission["Target"]))
        if mission["DestinationSystem"] == self.config["user"]["system"]: self.isCorrectSystem = True
    def showFootCollect(self, mission, line):
        if "DestinationSystem" in mission:
            self.showMissionDefault(mission, line)
        else:
            self.print(line * 2 + 1, 2, "{0:>10}   Bodenmission".format(" "))
        # -- keine Prüfung möglich - fehlt ja DestinationSystem (oder ein anderes) -- if mission["DestinationSystem"] == self.config["user"]["system"]: self.isCorrectSystem = True        
    def showDeliveryCoop(self, mission, line):
        mission_item = getDictItem(mission, "Commodity", "Commodity_Localised")
        # self.gamedata["logger"].info("MissionItem: " + mission_item)
        incargo = self.getItemFromCargo(mission_item)
#        if incargo is None:
#            self.print(line * 2 + 1, 2, "{0:>10}   >> abholen {1} ({2})".format(" ", market["system"], market["name"]))
#        else:
        if "DestinationStation" in mission:
            self.print(line * 2 + 1, 2, "{0:>10}   zurück nach {1} ({2})".format(" ", mission["DestinationSystem"], mission["DestinationStation"]))
        else:
            self.print(line * 2 + 1, 2, "{0:>10}   {1} ({2})".format(" ", mission["DestinationSystem"], mission["DestinationSettlement"]))
        if mission["DestinationSystem"] == self.config["user"]["system"]: self.isCorrectSystem = True        
    def showMining(self, mission, line):
        mission_item = getDictItem(mission, "Commodity", "Commodity_Localised")
        # self.gamedata["logger"].info("MissionItem: " + mission_item)
        incargo = self.getItemFromCargo(mission_item)
        if incargo is None:
            # market = self.getNearestPrice(mission_item)
            market = self.getNearestPrice((mission["Commodity"][1:]).replace("_Name;", "").casefold(), mission["Count"] * 2) # mind. doppelte benötigt
            if not market is None:
                self.print(line * 2 + 1, 2, "{0:>10}   kaufbar bei {1} ({2})".format(" ", market["system"], market["name"]))
            else:
                self.print(line * 2 + 1, 2, "{0:>10}   kein passenden Markt gefunden".format(" "))
        else:
            if "DestinationStation" in mission:
                self.print(line * 2 + 1, 2, "{0:>10}   abliefern bei {1} ({2})".format(" ", mission["DestinationSystem"], mission["DestinationStation"]))
            else:
                self.print(line * 2 + 1, 2, "{0:>10}   abliefern bei {1} ({2})".format(" ", mission["DestinationSystem"], mission["DestinationSettlement"]))
        if mission["DestinationSystem"] == self.config["user"]["system"]: self.isCorrectSystem = True
    def showMissionOnslaughtLegal(self, mission, line):
        if "DestinationStation" in mission:
            self.print(line * 2 + 1, 2, "{0:>10}   beichten in {1} ({2})".format(" ", mission["DestinationSystem"], mission["DestinationStation"]))
        else:
            self.print(line * 2 + 1, 2, "{0:>10}   lizensierter Amoklauf in {1} ({2})".format(" ", mission["DestinationSystem"], mission["DestinationSettlement"]))
        if mission["DestinationSystem"] == self.config["user"]["system"]: self.isCorrectSystem = True
    def showMissionOnslaughtIllegal(self, mission, line):
        if "DestinationStation" in mission:
            self.print(line * 2 + 1, 2, "{0:>10}   zurück nach {1} ({2})".format(" ", mission["DestinationSystem"], mission["DestinationStation"]))
        else:
            self.print(line * 2 + 1, 2, "{0:>10}   Illegale Aktion in {1} ({2})".format(" ", mission["DestinationSystem"], mission["DestinationSettlement"]))
        if mission["DestinationSystem"] == self.config["user"]["system"]: self.isCorrectSystem = True
class PageStoredModules(PageBasepage):  # 4
    def __init__(self, config, gamedata):
        super().__init__(config, gamedata)
        self.loadStoredModules()

    def loadStoredModules(self):
        if exists(self.config["localnames"]["modules"]):
            with open(self.config["localnames"]["modules"], "r") as f:
                self.gamedata["stored"]["modules"] = json.load(f)

    def update(self):
        self.screen.clear()
        if len(self.gamedata["stored"]["modules"]) > 0:
            self.update_modules()
        else:
            self.update_clear()
        self.screen.refresh()

    def update_clear(self):
        self.print(5, 10, "es gibt keine gelagerten Schiffmodule")

    def update_modules(self):
        line = 0
        for module in self.gamedata["stored"]["modules"]:
            name = module["Name_Localised"]
            output = name
            if "InTransit" in module:
                output = "{0:>10}   {1:<40} {2}".format("---", name, "- In Transit -")
            else:
                time = module["TransferTime"]
                place = module["StarSystem"]
                cost = module["TransferCost"]
                hours = time // 3600
                time = time - (hours * 3600)
                minutes = time // 60
                seconds = time - (minutes * 60)
                expired = "{:02}:{:02}:{:02}".format(int(hours), int(minutes), int(seconds))
                output = "{0:>10,}\u00A2  {1:<40} {2:9} {3}".format(cost, name, expired, place)
            self.print(line, 2, output)
            line += 1
class PageShipHangar(PageBasepage):     # 5
    def __init__(self, config, gamedata):
        super().__init__(config, gamedata)
        self.loadStoredShips()

    def loadStoredShips(self):
        if exists(self.config["localnames"]["hangar"]):
            with open(self.config["localnames"]["hangar"], "r") as f:
                self.gamedata["stored"]["ships"] = json.load(f)

    def update(self):
        self.screen.clear()
        if len(self.gamedata["stored"]["ships"]) > 0:
            self.update_modules()
        else:
            self.update_clear()
        self.screen.refresh()

    def update_clear(self):
        self.print(5, 10, "es gibt keine gelagerten Schiff")

    def update_modules(self):
        line = 0
        self.print(0, 2, "{0:>14}     {1:<40} {2}".format("Wert", "Name / Transfer" , "Typ"))
        for ship in self.gamedata["stored"]["ships"]:
            type = getDictItem(ship, "ShipType", "ShipType_Localised")
            name = type # pauschal
            if "Name" in ship: name = ship["Name"]
            value = getDictItem(ship, "Value")
            hot = getDictItem(ship, "Hot")
            output1 = "{0:>14,}\u00A2    {1:<40} {2}".format(value, name, type)
            output2 = ""
            if "InTransit" in ship:
                output2 = "{0:>14}     {1:<40}".format("", "- In Transit -")
            else:
                place = ship["StarSystem"]
                if "TransferTime" in ship:
                    time = ship["TransferTime"]
                    cost = ship["TransferPrice"]
                    hours = time // 3600
                    time = time - (hours * 3600)
                    minutes = time // 60
                    seconds = time - (minutes * 60)
                    expired = "{:02}:{:02}:{:02}".format(int(hours), int(minutes), int(seconds))
                    output2 = "{0:>14}     Transfer: {2:8} von {3} für {1:,}\u00A2 ".format("", cost, expired, place)
                    if time == 0: output2 = "{0:>14}     im lokalem Hanger ({1}) gelagert".format("", place)
                else:
                    output2 = ""
            self.print(line * 2 + 2, 2, output1)
            self.print(line * 2 + 3, 2, output2)
            line += 1
class PageShipOutfit(PageBasepage):     # 6
    def __init__(self, config, gamedata):
        super().__init__(config, gamedata)
        self.loadShipOutfit()

    def loadShipOutfit(self):
        if exists(self.config["localnames"]["outfit"]):
            with open(self.config["localnames"]["outfit"], "r") as f:
                self.gamedata["stored"]["outfit"] = json.load(f)

    def update(self):
        self.screen.clear()
        if len(self.gamedata["stored"]["outfit"]) > 0:
            self.update_outfit()
        else:
            self.update_clear()
        self.screen.refresh()

    def update_clear(self):
        self.print(5, 10, "es gibt keine bekannte Ausstattung")

    # Slots
    #  - Hardpoint -> Tiny (Werkzeug) | Large & Medium (Waffen)
    #  - Armour, PowerPlant, MainEngines, LifeSupport, PowerDistributor, Radar, FuelTank
    #  - SlotXX_SizeY
    #  - ?? CargoHatch, PlanetaryApproachSuite, VesselVoice, ShipCockpit
    def update_outfit(self):
        def getSlotKey(slotname):
            internals = [ "Armour", "Powerplant", "MainEngines", "FrameShiftDrive", "LifeSupport", "PowerDistributor", "Radar", "Fueltank" ]
            key = None
            if "hardpoint" in slotname.casefold():
                if "tiny" in slotname.casefold():
                    key = "tools"
                else:
                    key = "weapons"
            if "slot" in slotname.casefold(): key = "options"   # Size ist uninteressant
            for i in internals:
                if slotname.casefold() in i.casefold(): key = "internals"
            return key
        def sortSlots():
            for outfit in self.gamedata["stored"]["outfit"]["Modules"]:
                key = getSlotKey(outfit["Slot"])
                if key is None: continue
                slots[key].append(outfit["Item"])
        def getModule4Item(item):
            for m in self.gamedata["modnames"]:
                if item.casefold() == m["ed_symbol"].casefold(): return m
            return None
        def printSlot(y, x, title, items):
            self.print(y, x, title)
            line = 0
            for item in items:
                module = getModule4Item(item)
                if module == None:
                    self.print(y + line + 2, x, item)
                else:
                    clazz = str(module["class"])
                    rating = str(module["rating"])
                    name = module["group"]["name"]
                    self.print(y + line + 2, x, "{0}{1} {2}".format(clazz, rating, name))
                line += 1
        slots = {}
        slots["weapons"] = []
        slots["tools"] = []
        slots["internals"] = []
        slots["options"] = []
        sortSlots()
        printSlot(0, 2, "Internals", slots["internals"])
        printSlot(12, 2, "Waffen", slots["weapons"])
        printSlot(0, 35, "Zusätzliches", slots["options"])
        printSlot(0, 70, "Werkzeuge", slots["tools"])
class PageSAASignals(PageBasepage):     # 7
    def __init__(self, config, gamedata):
        super().__init__(config, gamedata)
        self.loadSignals()

    def loadSignals(self):
        if exists(self.config["localnames"]["saasignals"]):
            with open(self.config["localnames"]["saasignals"], "r") as f:
                self.gamedata["saasignals"] = json.load(f)


    def getPrice(self, market, commodities):
        for c in market["commodities"]:
            if c["name"] == commodities: return int(c["sellPrice"])
        return 0

    def update(self):
        self.screen.clear()
        if not "Signals" in self.gamedata["saasignals"]:
            self.update_clear()
        else:
            if len(self.gamedata["saasignals"]["Signals"]) > 0:
                self.update_signals()
            else:
                self.update_clear()
        self.screen.refresh()

    def update_clear(self):
        self.print(5, 10, "keine Signale gefunden")

    def update_signals(self):
        self.print(2, 4, "letzter Scan von Planet " + self.gamedata["saasignals"]["BodyName"])
        self.screen.refresh()
        playerpos = [ float(self.config["user"]["locx"]), float(self.config["user"]["locy"]), float(self.config["user"]["locz"]) ]
        line = 0
        for signal in self.gamedata["saasignals"]["Signals"]:
            name = getDictItem(signal, "Type", "Type_Localised")
            count = signal["Count"]
            market = None
            maxdistance = 0
            price = 0
            for station in self.gamedata["stations"]:
                systempos = [ float(station["coords"][0]), float(station["coords"][1]), float(station["coords"][2]) ]
                distance = math.dist(playerpos, systempos)
                if distance > float(self.config["distances"]["systems"]): continue
                if station["ls"] > float(self.config["distances"]["stations"]): continue
                for commodities in station["commodities"]:
                    if getDictItem(commodities, "demand") <= 0: continue;
                    if getDictItem(commodities, "name") != signal["Type"]: continue
                    if getDictItem(commodities, "sellPrice") < 1.0: continue
                    if market is None:
                        market = station
                    else:
                        neu = self.getPrice(station, signal["Type"])
                        if neu > price:
                            maxdistance = distance
                            market = station
                            price = neu
            output = ""
            if market is None:
                output = "{1:>20} {0:>2}x - kein Markt gefunden".format(count, name)
            else:
                output = "{1:>20} {0:>2}x - {2:>10,}\u00A2  ({3:4.1f}ly {4}|{5})".format(count, name, price, maxdistance, market["system"], market["name"])
            self.print(4 + line, 5, output)
            line += 1
            self.screen.refresh() # nach jeder Zeile - das suchen der preise dauert immer etwas
class PageAsteroid(PageBasepage):       # 8
    def __init__(self, config, gamedata):
        super().__init__(config, gamedata)
        self.loadAsteroid()

    def loadAsteroid(self):
        if exists(self.config["localnames"]["asteroid"]):
            with open(self.config["localnames"]["asteroid"], "r") as f:
                self.gamedata["asteroid"] = json.load(f)


    def getPrice(self, market, commodities):
        for c in market["commodities"]:
            if c["name"] == commodities: return int(c["sellPrice"])
        return 0

    def update(self):
        self.screen.clear()
        self.screen.refresh()
        if "Materials" in self.gamedata["asteroid"]:
            if len(self.gamedata["asteroid"]["Materials"]) == 0:
                self.update_clear()
            else:
                self.update_asteroid()
        else:
            self.update_clear()
        self.screen.refresh()

    def update_clear(self):
        self.print(5, 10, "kein Asteroid gescannt")

    def update_asteroid(self):
        # Kern
        if "MotherlodeMaterial" in self.gamedata["asteroid"]:
            name = getDictItem(self.gamedata["asteroid"], "MotherlodeMaterial", "MotherlodeMaterial_Localised")
            self.print(2, 5, "          Kern: {0}".format(name))
        else:
            self.print(2, 5, "kein Kern gefunden")

        # Menge
        content = getDictItem(self.gamedata["asteroid"], "Content", "Content_Localised")
        remain = getDictItem(self.gamedata["asteroid"], "Remaining")
        self.print(4, 5, "{0}".format(content, remain))
        self.print(5, 15, "Rest: {0:.1f}%".format(remain))

        # Rest
        line = 0
        playerpos = [ float(self.config["user"]["locx"]), float(self.config["user"]["locy"]), float(self.config["user"]["locz"]) ]
        for material in self.gamedata["asteroid"]["Materials"]:
            name = getDictItem(material, "Name", "Name_Localised")
            percent = material["Proportion"]

            market = None
            maxdistance = 0
            price = 0
            for station in self.gamedata["stations"]:
                systempos = [ float(station["coords"][0]), float(station["coords"][1]), float(station["coords"][2]) ]
                distance = math.dist(playerpos, systempos)
                if distance > float(self.config["distances"]["systems"]): continue
                if station["ls"] > float(self.config["distances"]["stations"]): continue
                for commodities in station["commodities"]:
                    if getDictItem(commodities, "demand") <= 0: continue;
                    if getDictItem(commodities, "name") != name: continue
                    if getDictItem(commodities, "sellPrice") < 1.0: continue
                    if market is None:
                        market = station
                    else:
                        neu = self.getPrice(station, commodities["Type"])
                        if neu > price:
                            maxdistance = distance
                            market = station
                            price = neu
            output = ""
            if market is None:
                output = "{0:>5.1f}% {1:25} - kein Markt gefunden".format(percent, name)
            else:
                output = "{0:>5.1f}% {1:25} - {2:>10,}\u00A2  ({3:4.1f}ly {4}|{5})".format(percent, name, price, maxdistance, market["system"], market["name"])
            self.print(8 + line, 5, output)
            line += 1
            self.screen.refresh() # nach jeder Zeile - das suchen der preise dauert immer etwas
class PageFSS(PageBasepage):
    SortMode = Enum("SortMode", ["Name", "Gravitation", "Temperatur", "Typ", "Eis", "Fels", "Metall", "MAX_SORTMODE"])
    def __init__(self, config, gamedata):
        super().__init__(config, gamedata)
        self.starting = 0
        self.sortmode = PageFSS.SortMode.Name
        self.sortup = True
        self.gamedata["logger"].info("FSS initialisiert")
        self.details = False    # True -> Materialien sonst die Zusammensetzung
        if exists(self.config["localnames"]["fss"]):
            with open(self.config["localnames"]["fss"], "r") as f:
                self.gamedata["fss"]["planets"] = json.load(f)
    def generateFssScanData(self):
        # für Debug-Optionen
        for i in range(0, 25):
            planet = {}
            planet["name"] = "Planet" + str(i)
            planet["type"] = "Test"
            planet["gravity"] = i
            planet["temp"] = 260 - 10 * i
            planet["composition"] = {}
            planet["materials"] = {}
            planet["landable"] = True # um die Gravitation anzuzeigen
            self.gamedata["fss"]["planets"].append(planet)
    def update(self):
        self.screen.clear()
        additional = ""
        if self.gamedata["fss"]["completed"] == True or self.gamedata["fss"]["count"] > 0:
            if self.gamedata["fss"]["completed"] == True:
                additional = " - vollständig"
            else:
                total = self.gamedata["fss"]["count"]
                found = len(self.gamedata["fss"]["planets"])
                additional = " - gescannt {0} von {1} Planeten".format(found, total)
        self.print(0, 2, "Voll Spektrum Scanner für ~g{0}~w{1}".format(self.gamedata["system"]["name"], additional))
        self.sortPlanets()
        self.showPlanets()
        sortierung = ""
        if self.sortup:
            sortierung = "Up"
        else:
            sortierung = "Down"
        sortierung = "(~g" + sortierung + "~w[~yR~w])"
        self.print(21, 2, "Cursor ~yUp/Down~w zum Scrollen~w - ~yLeft/Right~w für Sortierung: ~g" + self.sortmode.name + "~w " + sortierung + " - [~yM~w] Materialien")
        self.screen.refresh()
    def handleInput(self, key):
        if key == curses.KEY_UP and self.starting > 0:
            self.starting -= 1
        if key == curses.KEY_DOWN and self.starting < len(self.gamedata["fss"]["planets"]) - 18:
            self.starting += 1
        if key == curses.KEY_LEFT and self.sortmode.value > 1:
            self.sortmode = PageFSS.SortMode(self.sortmode.value - 1)
        if key == curses.KEY_RIGHT and self.sortmode.value < (PageFSS.SortMode.MAX_SORTMODE.value - 1):
            self.sortmode = PageFSS.SortMode(self.sortmode.value + 1)
        if chr(key) == "g":
            self.generateFssScanData()
        if chr(key) == "m":
            self.details = not self.details
        if chr(key) == "r":
            self.sortup = not self.sortup
        self.update()
    def sortPlanets(self):
        # erstmal ganz dumm Bubble-Sort
        if self.sortup:
            self.sortPlanetsUp()
        else:
            self.sortPlanetsDown()
    def sortPlanetsUp(self):
        # self.gamedata["logger"].info("sortiere Planeten AUFsteigend")
        planets = self.gamedata["fss"]["planets"]
        changed = False
        for i in range(len(planets) - 1):
            p1 = planets[i]
            p2 = planets[i + 1]
            match self.sortmode:    # ! DOUH ! irgendwie direkt mit den Key arbeiten
                case PageFSS.SortMode.Name:
                    changed = p1["name"] > p2["name"]
                case PageFSS.SortMode.Gravitation:
                    # die Gravitation wird bei nicht landbaren Planeten ausgeblendet
                    # das muss sich auch auf die Sportierung auswirken - müssen runter fallen
                    if p1["landable"] and p2["landable"]:
                        changed = p1["gravity"] > p2["gravity"]
                    else:
                        changed = p2["landable"]
                case PageFSS.SortMode.Temperatur:
                    changed = p1["temp"] > p2["temp"]
                case PageFSS.SortMode.Typ:
                    changed = p1["type"] > p2["type"]
                case PageFSS.SortMode.Eis:
                    if "Ice" in p1["composition"] and "Ice" in p2["composition"]:
                        changed = p1["composition"]["Ice"] > p2["composition"]["Ice"]
                    else:
                        # in p1 oder p2 existiert eis - wenn Eis in p2 existiert
                        # dann wird getauscht - somit sollten alle leeren Planeten runter fallen
                        changed = "Ice" in p2["composition"]
                case PageFSS.SortMode.Fels:
                    if "Rock" in p1["composition"] and "Ice" in p2["composition"]:
                        changed = p1["composition"]["Rock"] > p2["composition"]["Rock"]
                    else:
                        changed = "Rock" in p2["composition"]
                case PageFSS.SortMode.Metall:
                    if "Ice" in p1["composition"] and "Ice" in p2["composition"]:
                        changed = p1["composition"]["Metal"] > p2["composition"]["Metal"]
                    else:
                        changed = "Metal" in p2["composition"]
            # es muss getauscht werden
            if changed == True:
                planets[i] = p2
                planets[i + 1] = p1
                self.sortPlanetsUp()
    def sortPlanetsDown(self):
        # self.gamedata["logger"].info("sortiere Planeten ABsteigend")
        planets = self.gamedata["fss"]["planets"]
        changed = False
        for i in range(len(planets) - 1):
            p1 = planets[i]
            p2 = planets[i + 1]
            match self.sortmode:    # ! DOUH ! irgendwie direkt mit den Key arbeiten
                case PageFSS.SortMode.Name:
                    changed = p1["name"] < p2["name"]
                case PageFSS.SortMode.Gravitation:
                    # die Gravitation wird bei nicht landbaren Planeten ausgeblendet
                    # das muss sich auch auf die Sportierung auswirken - müssen runter fallen
                    if p1["landable"] and p2["landable"]:
                        changed = p1["gravity"] < p2["gravity"]
                    else:
                        changed = p2["landable"]
                case PageFSS.SortMode.Temperatur:
                    changed = p1["temp"] < p2["temp"]
                case PageFSS.SortMode.Typ:
                    changed = p1["type"] < p2["type"]
                case PageFSS.SortMode.Eis:
                    if "Ice" in p1["composition"] and "Ice" in p2["composition"]:
                        changed = p1["composition"]["Ice"] < p2["composition"]["Ice"]
                    else:
                        # in p1 oder p2 existiert eis - wenn Eis in p1 existiert
                        # dann wird getauscht - somit sollten alle leeren Planeten aufsteigen fallen
                        changed = "Ice" in p2["composition"]
                case PageFSS.SortMode.Fels:
                    if "Rock" in p1["composition"] and "Ice" in p2["composition"]:
                        changed = p1["composition"]["Rock"] < p2["composition"]["Rock"]
                    else:
                        changed = "Rock" in p2["composition"]
                case PageFSS.SortMode.Metall:
                    if "Ice" in p1["composition"] and "Ice" in p2["composition"]:
                        changed = p1["composition"]["Metal"] < p2["composition"]["Metal"]
                    else:
                        changed = "Metal" in p2["composition"]
            # es muss getauscht werden
            if changed == True:
                planets[i] = p2
                planets[i + 1] = p1
                self.sortPlanetsDown()
    def showPlanets(self):
        if len(self.gamedata["fss"]["planets"]) < 18:
            self.starting = 0
        maximum = len(self.gamedata["fss"]["planets"])
        if maximum  > 18:
            maximum = 18
        for i in range(0, maximum):
            planet = self.gamedata["fss"]["planets"][i + self.starting]
            name = self.formatPlanetName(planet)
            type = self.formatBodyType(planet)
            details = self.formatDetails(planet)
            color = self.getGravityColor(planet["gravity"] / 10)
            if planet["landable"]:
                gravity = "{0}{1:>4.1f}~wG {2:>5.0F}K".format(color, planet["gravity"] / 10 , planet["temp"])
            else:
                gravity = "{0:^4}~w  {1:>5.0F}K".format("--" , planet["temp"])
            self.print(2 + i, 2, "{0:<25} {1:<12} {2:>15}   {3}".format(name, gravity, type, details))
    def formatPlanetName(self, planet):
        name = planet["name"]
        if name == self.config["user"]["system"]:
            return name
        if "Belt Cluster" in name:
            # Belt Cluster selber erstmal löschen, steht sonst
            # doppelt im Namen - Leerzeichen beachten !
            name = name.replace("Belt Cluster ", "")
            name = name.replace(self.config["user"]["system"], "Belt Cluster")
        return name.replace(self.config["user"]["system"], "Planet")
    def formatBodyType(self, planet):
        count = planet["type"].count(" ")
        if count > 2: # max. 2 Leerzeichen erlauben
            parts = planet["type"].split()
            return parts[0] + " " + parts[1]
        return planet["type"]
    def formatDetails(self, planet):
        if self.details:
            return self.formatMaterials(planet["materials"])
        return self.formatComposition(planet["composition"])
    def formatComposition(self, composition):
        if len(composition) == 0:
            return ""
        output = ""
        for name in composition:
            if len(output) > 0:
                output += " - "
            percent = composition[name] * 100
            output += "{0}:{1:4.1f}%".format(name, percent)
        return output
    def formatMaterials(self, materials):
        output = ""
        pse = {
                "arsenic":"As", "iron":"Fe", "sulphur":"S", "carbon":"C", "phosphorus":"P", "nickel":"Ni",
                "germanium":"Ge", "zinc":"Zn", "zirconium":"Zr", "cadmium":"Cd", "tellurium":"Te", "mercury":"Hg",
                "chromium":"Cr", "mangan":"Mn", "selenium":"Se", "vanadium":"V", "niobium":"Nb", "tungsten":"W", 
                "molybdenum":"Mo", "ruthenium":"Ru", "antimony":"Sb", "tin":"Sn", "polonium":"Po", "technetium":"Tc",
                "manganese":"Mn", "yttrium":"Y"
        }
        count = 0
        for mat in materials:
            count += 1
            if count > 6:
                break
            if len(output) > 0:
                output += " "
            if mat["Name"] in pse:
                name = pse[mat["Name"]]
            else:
                name = mat["Name"] # für unbekanntes
            output += "{0}:{1:.1f}%".format(name, mat["Percent"])
        return output
    def getGravityColor(self, gravity):
        if gravity < 1.0: return "~g"
        if gravity >= 5.0: return "~r"
        if gravity >= 2.0: return "~y"
        return "~w"





class PageSettings(PageBasepage):
    def __init__(self, config, gamedata):
        super().__init__(config, gamedata)
        self.index = 0
        self.pages = [ PageSettingsMain(config, gamedata, self), PageSettingsServices(config, gamedata, self) ]
        self.subpage = self.pages[0]
        self.selectedLine = 0
        self.arrowLeft = u"\u25C0"
        self.arrowRight = u"\u25B6"
    def handleInput(self, key):
        lastIndex = self.index
        # - self.gamedata["logger"].warn("key -> " + str(key))
        if key == curses.KEY_HOME and self.index > 0:
            self.index -= 1
        if key == curses.KEY_END and self.index < (len(self.pages) - 1):
            self.index += 1
        if lastIndex != self.index: # neue Seite wurde aufgerufen - Reset
            self.selectedLine = 0
            self.subpage = self.pages[self.index]
        if key == curses.KEY_UP and self.selectedLine > 0:
            self.selectedLine -= 1
        if key == curses.KEY_DOWN and self.selectedLine < self.subpage.getOptionCount() - 1:
            self.selectedLine += 1
        if key == curses.KEY_LEFT:
            self.subpage.chooseOptionLeft(self.selectedLine)
        if key == curses.KEY_RIGHT:
            self.subpage.chooseOptionRight(self.selectedLine)
        if key == 0x0a:
            self.subpage.chooseSpecialFunction(self.selectedLine)
        self.subpage.handleInput(key)
        self.update()
        self.screen.refresh()
    def update(self):
        self.screen.clear()
        self.print(0, 2, self.arrowLeft + " ~yHOME~w/~yEND~w " + self.arrowRight + "  |")
        self.print(21, 2, self.t("PAGE_SETTING_UNDERLINE"))
        pos = 17
        for i in range(0, len(self.pages)):
            page = self.pages[i]
            if i == self.index: 
                self.print(0, pos + 2, "~g" + page.getSubPageName() + "~w")
            else:
                self.print(0, pos + 2, page.getSubPageName())
            pos += len(page.getSubPageName()) + 4 # je zwei Leerzeichen weiter (davor und danach)
            if i != len(self.pages): self.print(0, pos, "|")
            pos += 1 # und noch den Pipe dazu
        self.subpage.update()
        self.screen.refresh()
class PageSettingsSubpage:
    def __init__(self, config, gamedata, basepage):
        self.config = config
        self.gamedata = gamedata
        self.basepage = basepage
        self.arrowLeft = u"\u25C0"  # shortcut
        self.arrowRight = u"\u25B6"
        self.line = 0
    def t(self, key): # !! douh !! die Zweite
        lang = self.config["user"]["language"]
        if not key in self.gamedata["translations"]:
            self.gamedata["logger"].error(f"Key '{key}' nicht gefunden")
            return key
        if not lang in self.gamedata["translations"][key]:
            self.gamedata["logger"].error(f"Sprache '{lang}' für '{key}' nicht gefunden")
            return lang
        return self.gamedata["translations"][key][lang]
    def handleInput(self, key):
        pass
    def update(self):
        pass
    def getOptionCount(self):
        return 0
    def getOptionValueSelected(self, line):
        pass
    def getOptionValuePossible(self, line):
        pass
    def getOptionValueIndex(self, line):
        value = self.getOptionValueSelected(line)
        options = self.getOptionValuePossible(line)
        for i in range(0, len(options)):
            if str(value) == str(options[i]):
                return i
        return 0
    def chooseSpecialFunction(self, line):
        pass
    def chooseOptionLeft(self, line):
        index = self.getOptionValueIndex(line) - 1
        options = self.getOptionValuePossible(line)
        if index < 0:
            index = len(options) - 1
        self.setOptionValueSelected(line, options[index])
    def chooseOptionRight(self, line):
        index = self.getOptionValueIndex(line) + 1
        options = self.getOptionValuePossible(line)
        if index >= len(options):
            index = 0
        self.setOptionValueSelected(line, options[index])
    def updateOptionLine(self, line, current, comment):
        # line - aktuelle Zeile zur Ausgabe
        # selected - aktuell ausgewählt
        # comment - Information zur option
        # options - eine Liste mit allen Informationen
        self.print(line + 5, 7, "~g{0:>15}~w".format(current))
        self.print(line + 5, 25, comment)
        if line == self.basepage.selectedLine:
            self.print(line + 5, 5, "~y" + self.arrowRight + "~w")
            self.print(line + 5, 23, "~y" + self.arrowLeft + "~w")
    def print(self, posy, posx, content):
        self.basepage.print(posy, posx, content)
class PageSettingsMain(PageSettingsSubpage):
    def __init__(self, config, gamedata, basepage):
        super().__init__(config, gamedata, basepage)
    def getSubPageName(self):
        return self.t("PAGE_SETTINGS_MAIN_TABNAME")
    def getOptionCount(self):
        return 12
    def update(self):
        self.print(2, 5, self.t("PAGE_SETTINGS_MAIN_HEADLINE"))
        self.updateOptionLine(0, self.getOptionValueSelected(0), self.t("PAGE_SETTINGS_MAIN_UPDATE"))
        self.updateOptionLine(1, self.getOptionValueSelected(1), self.t("PAGE_SETTINGS_MAIN_SALE_SYSTEM"))
        self.updateOptionLine(2, self.getOptionValueSelected(2), self.t("PAGE_SETTINGS_MAIN_SALE_STATIONS"))
        self.updateOptionLine(3, self.getOptionValueSelected(3), self.t("PAGE_SETTINGS_MAIN_CARRIER"))
        self.updateOptionLine(4, self.getOptionValueSelected(4), self.t("PAGE_SETTINGS_MAIN_AUTOPAGE"))
        self.updateOptionLine(5, self.getOptionValueSelected(5), self.t("PAGE_SETTINGS_MAIN_PRIOPAGE"))
        self.updateOptionLine(6, self.getOptionValueSelected(6), self.t("PAGE_SETTINGS_MAIN_COLORS"))
        self.updateOptionLine(7, self.getOptionValueSelected(7), self.t("PAGE_SETTINGS_MAIN_EDMC"))
        self.updateOptionLine(8, self.getOptionValueSelected(8), self.t("PAGE_SETTINGS_MAIN_BUBBLE"))
        self.updateOptionLine(9, self.getOptionValueSelected(9), self.t("PAGE_SETTINGS_MAIN_EVENTS"))
        self.updateOptionLine(10, self.getOptionValueSelected(10), self.t("PAGE_SETTINGS_MAIN_FSS"))
        self.updateOptionLine(11, self.getOptionValueSelected(11), self.t("PAGE_SETTINGS_MAIN_LANG"))
    def getOptionValueSelected(self, line):
        if line == 0: return "update"
        if line == 1: return self.config["distances"]["systems"]
        if line == 2: return self.config["distances"]["stations"]
        if line == 3: return self.config["distances"]["carrier"]
        if line == 4: return self.config["pages"]["autopage"]
        if line == 5: return self.config["pages"]["priopage"]
        if line == 6: return self.config["pages"]["coloring"]
        if line == 7: return self.config["pages"]["edmc"]
        if line == 8: return self.config["filter"]["distance"]
        if line == 9: return self.config["pages"]["events"]
        if line == 10: return self.config["pages"]["onlydetailed"]
        if line == 11: return self.config["user"]["language"]
    def setOptionValueSelected(self, line, option):
        # Zeile 0 ist uninteressant
        if line == 1: self.config["distances"]["systems"] = str(option)
        if line == 2: self.config["distances"]["stations"] = str(option)
        if line == 3: self.config["distances"]["carrier"] = str(option)
        if line == 4: self.config["pages"]["autopage"] = str(option)
        if line == 5: self.config["pages"]["priopage"] = str(option)
        if line == 6: self.config["pages"]["coloring"] = str(option)
        if line == 7: self.config["pages"]["edmc"] = str(option)
        if line == 8: self.config["filter"]["distance"] = str(option)
        if line == 9: self.config["pages"]["events"] = str(option)
        if line == 10: self.config["pages"]["onlydetailed"] = str(option)
        if line == 11: self.config["user"]["language"] = str(option)
    def getOptionValuePossible(self, line):
        distances = [ 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000, 200000 ]
        if line == 0: return "update"
        if line == 1: return distances
        if line == 2: return distances
        if line == 3: return [ "yes", "no" ]
        if line == 4: return [ "yes", "no" ]
        if line == 5: return [ "mission", "cargo" ]
        if line == 6: return [ "yes", "no" ]
        if line == 7: return [ "yes", "no" ]
        if line == 8: return distances
        if line == 9: return [ "yes", "no" ]
        if line == 10: return [ "yes", "no" ]
        if line == 11: return self.gamedata["translations"]["languages"]
    def chooseSpecialFunction(self, line):
        if line == 0: 
            self.config["pages"]["activepage"] = "U"
            self.gamedata["logger"].warn("Update für Sternensysteme ausgelöst")
class PageSettingsServices(PageSettingsSubpage):
    def __init__(self, config, gamedata, basepage):
        super().__init__(config, gamedata, basepage)
    def getSubPageName(self):
        return self.t("PAGE_SETTINGS_SERVICE_TABNAME")
    def getOptionCount(self):
        return 8
    def update(self):
        self.print(2, 5, self.t("PAGE_SETTINGS_SERVICE_HEADER"))
        for i in range(0, self.getOptionCount()):
            output = self.t("PAGE_SETTINGS_SERVICE_OUTPUTLINE")
            self.updateOptionLine(i, self.getOptionValueSelected(i), output.format(line = i + 1))
    def splitOptionsUsed(self):
        options = self.config["pages"]["services"].split(", ")
        # self.gamedata["logger"].info(str(len(options)) + " Anzahl an Optionen")
        for i in range(len(options) - 1):
            if options[i] == "":
                options[i] = "Dock"
        while len(options) < self.getOptionCount():
            options.append("Dock")
        return options
    def splitOptionsKnown(self):
        options = self.config["pages"]["services_known"].split(", ")
        return options
    def getOptionValueSelected(self, line):
        alloptions = self.getOptionValuePossible(line)
        options = self.splitOptionsUsed()
        if (line < 0):
            return alloptions[0]
        if line >= len(options):
            return alloptions[0]
        return options[line]
    def setOptionValueSelected(self, line, option):
        result = ""
        alloptions = self.splitOptionsUsed()
        for i in range(0, len(alloptions)):
            if alloptions[i] == "":
                continue
            if i != 0:
                result += ", "
            if i == line:
                result += option
            else:
                result += alloptions[i]
        self.config["pages"]["services"] = result
    def getOptionValuePossible(self, line):
        return self.config["pages"]["services_known"].split(", ")
