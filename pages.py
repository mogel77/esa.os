import requests
import gzip
import shutil
import os
import curses
import math
import json
import time
import random
from os.path import exists
from datetime import datetime

from tools import getDictItem
from config import updateConfig




class PageBasepage:
    def __init__(self, config, gamedata):
        self.screen = curses.newwin(22, 110, 7, 20)
        self.config = config
        self.gamedata = gamedata
    def print(self, posy, posx, content):
        try:
            if len(content) > 0:
                for i in range(0, len(content)):
                    if posx + i < curses.COLS - 1: self.screen.addstr(posy, posx + i, content[i])
            else:
                self.screen.addstr(posy, posx, "")
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
        r = requests.get(url, allow_redirects=True)
        open(name, 'wb').write(r.content)

    def printline(self, y, x, text):
        self.print(y, x, text)
        self.print(y + 1, x, "> ")
        self.screen.refresh()

    def update(self):
        self.gamedata["stations"] = []
        self.screen.clear()
        for i in range(0, len(self.uds)): self.print(i + 2, 5, self.uds[i])
        self.screen.refresh()
        self.printline(13, 5, "> download galaxy.gz \"https://files.egn/galaxy.gz\"")
        self.download("galaxy_gz")
        self.printline(14, 5, "> gzip -u galaxy.gz")
        with gzip.open(self.config["localnames"]["galaxy_gz"], 'rb') as f_in:
            with open(self.config["localnames"]["galaxy_json"], 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        self.printline(15, 5, "> get stations from galaxy.json -max {0}ly".format(self.config["filter"]["distance"]))
        j_stations = []     # Array
        j_bodies = []
        with open(self.config["localnames"]["galaxy_json"], "r") as f:
            galaxy = json.load(f)
            with open(self.config["localnames"]["bodies"], "w") as bodies:
                with open(self.config["localnames"]["stations"], "w") as stations:
                    hx = float(self.config["user"]["homex"])
                    hy = float(self.config["user"]["homey"])
                    hz = float(self.config["user"]["homez"])
                    userhome = [ hx, hy, hz ]
                    for g in galaxy:
                        dist = math.dist([ g["coords"]["x"], g["coords"]["y"], g["coords"]["z"] ], userhome)
                        if dist > float(self.config["filter"]["distance"]): continue
                        for station in g["stations"]:
                            if not "market" in station: continue
                            if "Carrier" in station["type"]: continue   # erstmal keine Carrier
                            j_market = {}
                            # -- for key, value in station.items(): print(key)
                            # System: name - coords
                            j_market["system"] = g["name"]
                            j_market["coords"] = [ g["coords"]["x"], g["coords"]["y"], g["coords"]["z"] ]
                            # Market: name - id
                            j_market["id"] = station["id"]
                            j_market["name"] = station["name"]
                            j_market["ls"] = station["distanceToArrival"]
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
                                body["type"] = b["type"]
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
class PageSettings(PageBasepage):       # 0
    def __init__(self, config, gamedata):
        super().__init__(config, gamedata)

    def formatSetting(self, key, option, text):
        return "({0}) {1:>7} {2}".format(key, option, text)

    def scrollSetting(self, current, options):
        index = 0
        # aktuelle option suchen bzw. den Index dazu
        for o in options:
            if str(o) == current: break
            index += 1
        index += 1 # aktuellen Index erhöhen - wollen ja nächste Option
        if index >= len(options): index = 0
        return str(options[index])

    def update(self):
        if len(self.gamedata["stations"]) == 0:
            avail = "keine Stationen vorhanden"
        else:
            avail = str(len(self.gamedata["stations"])) + " Stationen"
        self.screen.clear()
        self.print(2, 5, self.formatSetting("U", "", "Update der Sternensysteme starten - {0}".format(avail)))
        self.print(4, 5, self.formatSetting("H", self.config["user"]["homesys"], "Heimatsystem"))
        self.print(5, 5, self.formatSetting("J", self.config["distances"]["systems"], "max. Entfernung der Systeme für Verkauf (Ly)"))
        self.print(6, 5, self.formatSetting("L", self.config["distances"]["stations"], "max. Entfernung der Stationen für Verkauf (Ls)"))
        self.print(7, 5, self.formatSetting("A", self.config["pages"]["autopage"], "automatisch die Seiten umschalten"))
        self.print(8, 5, self.formatSetting("P", self.config["pages"]["priopage"], "Seite nach dem Ende der Route"))
        self.print(14, 5, self.formatSetting("M", self.config["pages"]["edmc"], "Autostart von EDMarketConnector (experimentell)"))
        self.print(15, 5, self.formatSetting("F", self.config["filter"]["distance"], "Systeme weiter vom Heimatsystem, werden gelöscht/ignoriert (Ly)"))
        self.print(16, 5, self.formatSetting("E", self.config["pages"]["events"], "Events anzeigen (Debug-Funktion)"))
        self.screen.refresh()

    def handleInput(self, key):
        distances = [ 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000 ]
        if key == "u" or key == "U": self.config["pages"]["activepage"] = "U"
        if key == "e" or key == "E": self.config["pages"]["events"] = self.scrollSetting(self.config["pages"]["events"], [ "yes", "no" ])
        if key == "a" or key == "A": self.config["pages"]["autopage"] = self.scrollSetting(self.config["pages"]["autopage"], [ "yes", "no" ])
        if key == "p" or key == "P": self.config["pages"]["priopage"] = self.scrollSetting(self.config["pages"]["priopage"], [ "mission", "cargo" ])
        if key == "j" or key == "J": self.config["distances"]["systems"] = self.scrollSetting(self.config["distances"]["systems"], distances)
        if key == "l" or key == "L": self.config["distances"]["stations"] = self.scrollSetting(self.config["distances"]["stations"], distances)
        if key == "m" or key == "M": self.config["pages"]["edmc"] = self.scrollSetting(self.config["pages"]["edmc"], [ "yes", "no" ])
        if key == "f" or key == "F": self.config["filter"]["distance"] = self.scrollSetting(self.config["filter"]["distance"], distances)
        if key == "h" or key == "H":
            home = self.scrollSetting(self.config["user"]["homesys"], [ "Sol", "Achenar", "Alioth", self.config["user"]["system"] ])
            # Pauschal das aktuelle System setzen
            self.config["user"]["homesys"] = self.config["user"]["system"]
            self.config["user"]["homex"] = self.config["user"]["locx"]
            self.config["user"]["homey"] = self.config["user"]["locy"]
            self.config["user"]["homez"] = self.config["user"]["locz"]
            # jetzt die "richtigen" Werte
            if home == "Sol":
                self.config["user"]["homesys"] = "Sol"
                self.config["user"]["homex"] = "0.0"
                self.config["user"]["homey"] = "0.0"
                self.config["user"]["homez"] = "0.0"
            if home == "Achenar":
                self.config["user"]["homesys"] = "Achenar"
                self.config["user"]["homex"] = "67.5"
                self.config["user"]["homey"] = "-119.46875"
                self.config["user"]["homez"] = "24.84375"
            if home == "Alioth":
                self.config["user"]["homesys"] = "Alioth"
                self.config["user"]["homex"] = "-33.65625"
                self.config["user"]["homey"] = "72.46875"
                self.config["user"]["homez"] = "-20.65625"
        self.update()





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
        else:
            self.update_clear()
        self.screen.refresh()

    def update_clear(self):
        self.print(5, 10, "es ist im Moment keine Reise geplant")

    def update_route(self):
        route = self.gamedata["route"]
        fuelstar = "OBAFGKM" # Sterne zum Tanken
        oldpos = [ float(self.config["user"]["locx"]), float(self.config["user"]["locy"]), float(self.config["user"]["locz"]) ]
        position = 0
        jumps = 0
        found = False
        lastsystem = None
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
                self.print(18, 5, "{0:8} {1}   insgesamt {2} Sprünge".format(" ", "...", len(route)))
            oldpos = system["StarPos"]
            self.disttotal += distance
            position += 1           # Position für die Ausgabe
            jumps += 1              # Anzahl der noch vorhandenen Sprünge
            lastsystem = system
        if position > 16: position = 16
        self.screen.refresh()
    def showProgress(self):
        routemax = len(self.gamedata["route"])
        if routemax <= 1: return # Sec-Check
        percent = (self.routestep / routemax) * 100.0
        filler = ""
        for i in range(0, 100): filler += "-"     # vorfüllen
        temp = list(filler)
        if percent < 100: temp[int(percent)] = "|"     # auffüllen
        filler = "".join(temp)
        self.print(21, 2, "[{0}]".format(filler))
        self.print(20, 2, "{0}".format(self.gamedata["route"][0]["StarSystem"]))
        self.print(20, 74, "{0:>30}".format(self.gamedata["route"][routemax - 1]["StarSystem"]))
        self.print(20, 35, "{0:^20}".format("{0:.1f}ly".format(self.disttotal)))
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





class PageCargo_alt(PageBasepage):          # 1
    def __init__(self, config, gamedata):
        super().__init__(config, gamedata)
        self.loadCargo()

    def loadCargo(self):
        if not exists(self.config["eddir"]["path"] + "/Cargo.json"): return
        with open(self.config["eddir"]["path"] + "/Cargo.json", "r") as f:
            self.gamedata["cargo"] = json.load(f)["Inventory"]

    def getMission(self, id):
        for m in self.gamedata["missions"]:
            if m["MissionID"] == id: return m
        return None

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
        stations = self.gamedata["stations"]
        itemnumber = 0
        for item in cargo:
            maxmarket = None
            maxdistance = 0.0
            price = 0
            if not "MissionID" in item:
                for station in stations:
                    systempos = [ float(station["coords"][0]), float(station["coords"][1]), float(station["coords"][2]) ]
                    distance = math.dist(playerpos, systempos)
                    if distance > float(self.config["distances"]["systems"]): continue
                    if station["ls"] > float(self.config["distances"]["stations"]): continue
                    for commodities in station["commodities"]:
                        if commodities["demand"] <= 0: continue;
                        if commodities["symbol"] != item["Name"]: continue
                        if commodities["sellPrice"] < 1.0: continue
                        if maxmarket is None:
                            maxmarket = station
                        else:
                            neu = self.getPrice(station, item["Name"])
                            if neu > price:
                                maxdistance = distance
                                maxmarket = station
                                price = neu
            # maxmarket hat jetzt den besten Preis für das Item
            cargo_item = item["Name"]
            if "Name_Localised" in item: cargo_item = item["Name_Localised"]
            cargo_count = item['Count']
            self.cargouse += cargo_count
            cargo_price = "{:,}".format(price)
            fullmarge = price * cargo_count
            cargo_marge = "{:,}".format(price * cargo_count)
            line1 = "{0:>14}\u00A2   {1:3}  {2:30}".format(cargo_marge, cargo_count, cargo_item)
            line2 = ""
            if not maxmarket is None:
                missionitem = False
                for mission in self.gamedata["missions"]:
                    if "Commodity_Localised" in mission:
                        if mission["Commodity_Localised"] == cargo_item: missionitem = True
                if missionitem:
                    line2 = "{0:14}    {1:3}  >> mögliche Fracht für eine Liefer-Mission".format(" ", " ") # , maxdistance, cargo_system, cargo_market)
                else:
                    cargo_system = maxmarket["system"]
                    cargo_distance = "{:6.1f}".format(maxdistance) + "ly"
                    cargo_market = maxmarket["name"]
                    line2 = "{0:14}    {1:3}  {2:4.1f}ly {3} ({4})".format(" ", " ", maxdistance, cargo_system, cargo_market)
                self.marge_total += fullmarge
            else:
                if not "MissionID" in item:
                    missionitem = False
                    for mission in self.gamedata["missions"]:
                        if "Commodity_Localised" in mission:
                            if mission["Commodity_Localised"].lower() == cargo_item.lower(): missionitem = True
                    if missionitem:
                        line2 = "{0:14}    {1:3}  >> mögliche Fracht für eine Liefer-Mission".format(" ", " ") # , maxdistance, cargo_system, cargo_market)
                    else:
                        line2 = "{0:14}    {1:3}  innerhalb von {2:4.1f}ly nicht verkaufbar".format(" ", " ", float(self.config["distances"]["systems"]))
                    self.marge_total += fullmarge
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
        percent = (self.cargouse / self.cargomax) * 100.0
        filler = ""
        for i in range(0, 100): filler += " "     # vorfüllen
        temp = list(filler)
        for i in range(0, int(percent)): temp[i] = "="     # auffüllen
        filler = "".join(temp)
        #output = "{0:>3} Drohnen [{1}] {2:>3}/{3:>3}".format(self.limpetcount, filler, self.cargouse, self.cargomax)
        self.print(21, 2, "[{0}]".format(filler))
        self.print(20, 2, "{0} Drohnen".format(self.limpetcount))
        self.print(20, 95, "{0:>3} / {1:>3}".format(self.cargomax - self.cargouse, self.cargomax))
        self.print(20, 35, "{0:^20}".format("{0:,}\u00A2 ".format(self.marge_total)))
class PageMissions_alt(PageBasepage):       # 3
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

    def update_missions(self):
        line = 0
        for m in self.gamedata["missions"]:
            # "Expiry": "2022-10-10T16:33:06Z"
            expired = "zeitlos"
            if "Expiry" in m:
                now = datetime.utcnow()
                exp = datetime.fromisoformat(m["Expiry"].replace("T", " ").replace("Z", ""))
                s = (exp - now).seconds
                hours = s // 3600
                s = s - (hours * 3600)
                minutes = s // 60
                seconds = s - (minutes * 60)
                expired = "{:02}h{:02}m".format(int(hours), int(minutes))
                if "DestinationSystem" in m:
                    if "DestinationStation" in m:
                        self.print(line * 2 + 1, 2, "{0:>10}   {1} ({2})".format(" ", m["DestinationSystem"], m["DestinationStation"]))
                    else:
                        self.print(line * 2 + 1, 2, "{0:>10}   {1} ({2})".format(" ", m["DestinationSystem"], m["DestinationSettlement"]))
                    if m["DestinationSystem"] == self.config["user"]["system"]: self.print(line * 2 + 1, 13, ">")
                else:
                    self.print(line * 2 + 1, 2, "{0:>10}   Bodenmission".format(" "))
            else:
                self.print(line * 2 + 1, 2, "{0:>10}   {1}".format("", m["Faction"]))
            self.print(line * 2 + 0, 2, "{0:>10}   {1}".format(expired, m["LocalisedName"]))
            line += 1







