import configparser
import curses
import os
import json
import sys
import logging
import time
import multiprocessing
import platform
import subprocess
from curses import wrapper
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Thread

import tools
import pages
import windows
from config import updateConfig
from tools import getDictItem





# Konfiguration laden
updateConfig()
config = configparser.ConfigParser()
config.read('config.ini')

# zusätzliche Dinge zur Laufzeit
gamedata = {}
gamedata["stations"] = []
gamedata["modnames"] = []
gamedata["cargo"] = []
gamedata["materials"] = {}
gamedata["materials"]["raw"] = []
gamedata["materials"]["manufactured"] = []
gamedata["materials"]["encoded"] = []
gamedata["locker"] = {}
gamedata["locker"]["items"] = []
gamedata["locker"]["components"] = []
gamedata["locker"]["consumables"] = []
gamedata["locker"]["data"] = []
gamedata["missions"] = []
gamedata["route"] = []
gamedata["stored"] = {}
gamedata["stored"]["modules"] = []
gamedata["stored"]["ships"] = []
gamedata["stored"]["outfit"] = []
gamedata["saasignals"] = []
gamedata["asteroid"] = []
gamedata["events"] = {}
gamedata["events"]["channel"] = config["user"]["channel"]       # vom Benutzer bevorzugt
gamedata["events"]["lastch"] = "npc"                            # letzte vom System angekommene - NPC existiert auf jedenfall
gamedata["events"]["npc"] = [ "", "", "", "", "" ]              # ... daher vorbereiten
gamedata["events"]["debug"] = [ "", "", "", "", "" ]            # pauschal - ist ja auch immer da
gamedata["status"] = [ "", "", "", "", "" ]



if os.path.exists("esaos.log"): os.remove("esaos.log")
gamedata["logger"] = logging.getLogger("esaos")
hdlr = logging.FileHandler("esaos.log")
hdlr.setFormatter(logging.Formatter('%(levelname)s > %(message)s'))
gamedata["logger"].addHandler(hdlr)
gamedata["logger"].setLevel(logging.DEBUG)
gamedata["logger"].info("Startup")

stdscr = curses.initscr()





class MyFileHandler(FileSystemEventHandler):
    def __init__(self, config):
        self.config = config
        self.oldlog = ""
        self.logfile = None
        self.openLogfile(config["eddir"]["lastlog"])
    def has_another_line(self, file):
        cur_pos = file.tell()
        does_it = bool(file.readline())
        file.seek(cur_pos)
        return does_it
    def openLogfile(self, newlogpath):
        if not os.path.exists(newlogpath): return
        if self.logfile is not None: self.logfile.close()
        addMessage("debug", "Logfile: " + os.path.basename(newlogpath))
        self.oldlog = newlogpath;
        self.logfile = open(newlogpath, "rt")
        try:  # catch OSError in case of a one line file
            self.logfile.seek(0, os.SEEK_END)
        except OSError:
            self.logfile.seek(0)
        self.config["eddir"]["lastlog"] = newlogpath
        with open(r"config.ini", 'w') as configfile: self.config.write(configfile)
    def on_modified(self,  event):
        if not event.src_path.endswith(".log"): return
        if event.src_path != self.oldlog: self.openLogfile(event.src_path)
        try:
            gamedata["event"] = None
            self.secureDispatch(event)
        except Exception as ex:
            #gamedata["logger"].error("{0}".format(ex), exc_info=True)
            gamedata["logger"].exception(ex)
            if not gamedata["event"] is None: gamedata["logger"].error(">>> {0}".format(json.dumps(gamedata["event"])))
    def secureDispatch(self, event):
        while self.has_another_line(self.logfile):
            global winevents, gamedata, winmenu
            entry = json.loads(self.logfile.readline())
            gamedata["event"] = entry
            addMessage("debug", "EVENT: " + entry["event"])
            if entry["event"] == "Shutdown": Event_Shutdown(entry)
            if entry["event"] == "SquadronStartup": Event_SquadronStartup(entry)
            if entry["event"] == "LoadGame": Event_LoadGame(entry)
            if entry["event"] == "Resurrect": Event_Resurrect(entry)
            if entry["event"] == "NavRoute": Event_NavRoute(entry)
            if entry["event"] == "NavRouteClear": Event_NavRouteClear(entry)
            if entry["event"] == "FSDTarget": Event_FSDTarget(entry)
            if entry["event"] == "FSDJump": Event_FSDJump(entry)
            if entry["event"] == "JetConeBoost": Event_JetConeBoost(entry)
            if entry["event"] == "SupercruiseExit": Event_SupercruiseExit(entry)
            if entry["event"] == "SupercruiseEntry": Event_SupercruiseEntry(entry)
            if entry["event"] == "Docked": Event_Docked(entry)
            if entry["event"] == "DockingGranted": Event_DockingGranted(entry)
            if entry["event"] == "DockingDenied": Event_DockingDenied(entry)
            if entry["event"] == "Undocked": Event_Undocked(entry)
            if entry["event"] == "Touchdown": Event_Touchdown(entry)
            if entry["event"] == "Liftoff": Event_Liftoff(entry)
            if entry["event"] == "Cargo": Event_Cargo(entry)
            if entry["event"] == "StoredModules": Event_StoredModules(entry)
            if entry["event"] == "StoredShips": Event_StoredShips(entry)
            if entry["event"] == "Loadout": Event_Loadout(entry)
            if entry["event"] == "Died": Event_GameOver(entry)
            if entry["event"] == "Materials": Event_Materials(entry)
            if entry["event"] == "ShipLocker": Event_ShipLocker(entry)
            if entry["event"] == "Missions": Event_Missions(entry)
            if entry["event"] == "MissionAccepted": Event_MissionAccepted(entry)
            if entry["event"] == "MissionRedirected": Event_MissionRedirected(entry)
            if entry["event"] == "MissionCompleted": Event_MissionCompleted(entry)
            if entry["event"] == "LeaveBody": Event_LeaveBody(entry)
            if entry["event"] == "ApproachBody": Event_ApproachBody(entry)
            if entry["event"] == "ApproachSettlement": Event_ApproachSettlement(entry)
            if entry["event"] == "SAASignalsFound": Event_SAASignalsFound(entry)
            if entry["event"] == "ProspectedAsteroid": Event_ProspectedAsteroid(entry)
            if entry["event"] == "AsteroidCracked": Event_AsteroidCracked(entry)
            if entry["event"] == "MiningRefined": Event_MiningRefined(entry)
            if entry["event"] == "ReceiveText": Event_ReceiveText(entry)
            if entry["event"] == "EscapeInterdiction": Event_EscapeInterdiction(entry)
            if entry["event"] == "MarketBuy": Event_MarketBuy(entry)
            if entry["event"] == "MarketSell": Event_MarketSell(entry)
            if entry["event"] == "Repair": Event_Repair(entry)
            if entry["event"] == "BuyDrones": Event_BuyDrones(entry)
            if entry["event"] == "SellDrones": Event_SellDrones(entry)
            if entry["event"] == "SellExplorationData": Event_SellExplorationData(entry)
            if entry["event"] == "ShipyardBuy": Event_ShipyardBuy(entry)
            if entry["event"] == "ShipyardSell": Event_ShipyardSell(entry)
            if entry["event"] == "ShipyardTransfer": Event_ShipyardTransfer(entry)
            if entry["event"] == "ModuleBuy": Event_ModuleBuy(entry)
            if entry["event"] == "ModuleSell": Event_ModuleSell(entry)
            if entry["event"] == "ModuleSellRemote": Event_ModuleSell(entry)
            if entry["event"] == "ModuleStore": Event_ModuleStore(entry)
            if entry["event"] == "BuyExplorationData": Event_BuyExplorationData(entry)
            if entry["event"] == "BuyTradeData": Event_BuyTradeData(entry)
            if entry["event"] == "BuyAmmo": Event_BuyAmmo(entry)
            if entry["event"] == "CrewHire": Event_CrewHire(entry)
            if entry["event"] == "FetchRemoteModule": Event_FetchRemoteModule(entry)
            if entry["event"] == "RefuelAll": Event_RefuelAll(entry)
            if entry["event"] == "RefuelPartial": Event_RefuelPartial(entry)
            if entry["event"] == "RepairAll": Event_RepairAll(entry)
            if entry["event"] == "RestockVehicle": Event_RestockVehicle(entry)
            if entry["event"] == "PowerplayFastTrack": Event_PowerplayFastTrack(entry)
            if entry["event"] == "NpcCrewPaidWage": Event_NpcCrewPaidWage(entry)
            winmenu.update()



def Event_Shutdown(entry):
    tools.saveConfig(config, gamedata)
def Event_SquadronStartup(entry):
    config["user"]["squadname"] = entry["SquadronName"]
    config["user"]["squadrank"] = str(entry["CurrentRank"])
def Event_LoadGame(entry):
    global winheader
    config["user"]["name"] = entry["Commander"]
    config["user"]["ship"] = entry["ShipName"]
    config["user"]["ident"] = entry["ShipIdent"]
    config["user"]["credits"] = str(entry["Credits"])
    config["user"]["loan"] = str(entry["Loan"])
    with open(r"config.ini", 'w') as configfile: config.write(configfile)
    winheader.update()
def Event_Resurrect(entry):
    handleCreditsSub("Cost", entry)
def Event_NavRoute(entry):
    autoPage(2)
def Event_NavRouteClear(entry):
    # ACHTUNG - Event kommt vor FSDTarget
    # { "timestamp":"2022-10-08T12:59:46Z", "event":"NavRoute" }
    gamedata["route"] = [] # löschen -damit FSDJump nicht wieder die leere Route aufruft
    autoPage(getPrioPage())
def Event_FSDTarget(entry): # das ist das nächste Ziel zum Sprung
    # { "timestamp":"2022-10-08T12:59:46Z", "event":"FSDTarget", "Name":"Sharru Sector YO-A b0", "SystemAddress":671760000393, "StarClass":"M", "RemainingJumpsInRoute":8 }
    pass
def Event_FSDJump(entry):
    def lineSystem(entry):
        starname = entry["StarSystem"]
        goverment = getDictItem(entry, "SystemGovernment", "SystemGovernment_Localised")
        if "Powers" in entry:
            playname = entry["Powers"][0]
            playstate = getDictItem(entry, "PowerplayState", "PowerplayState_Localised")
            output = "{0} - {1} ({2})".format(starname, playname, playstate)
        else:
            output = "{0} - {1}".format(starname, goverment)
        return output
    def lineEconomy(entry):
        security = getDictItem(entry, "SystemSecurity", "SystemSecurity_Localised")
        economy1 = getDictItem(entry, "SystemEconomy", "SystemEconomy_Localised")
        economy2 = getDictItem(entry, "SystemSecondEconomy", "SystemSecondEconomy_Localised")
        output = "{0} | {1} - {2}".format(economy1, economy2, security)
        return output
    def lineFaction(entry):
        if not "SystemFaction" in entry: return ""
        sysfaction = getDictItem(entry["SystemFaction"], "Name")
        sysstate = getDictItem(entry["SystemFaction"], "FactionState")
        if sysfaction is None: return ""
        if sysstate is None:
            return sysfaction
        else:
            return "{0} ({1})".format(sysfaction, sysstate)
    global winheader, winstatus
    if "JumpDist" in entry:
        travel = int(config["user"]["travel"])
        travel += int(entry["JumpDist"])
        config["user"]["travel"] = str(travel)
    # 'StarSystem': 'Sol'
    # 'StarPos': [0.0, 0.0, 0.0]
    config["user"]["system"] = entry["StarSystem"]
    config["user"]["locx"] = str(entry["StarPos"][0])
    config["user"]["locy"] = str(entry["StarPos"][1])
    config["user"]["locz"] = str(entry["StarPos"][2])
    tools.saveConfig(config, gamedata)
    gamedata["status"][0] = ""
    gamedata["status"][1] = lineSystem(entry)
    gamedata["status"][2] = lineEconomy(entry)
    gamedata["status"][3] = lineFaction(entry)
    gamedata["status"][4] = ""
    winheader.update()
    winstatus.update()
    if len(gamedata["route"]) > 0:
        autoPage(2)
    else:
        autoPage(getPrioPage())
def Event_JetConeBoost(entry):
    gamedata["status"][0] = "   __  ____  ____     ____   __    __   ____  ____ "
    gamedata["status"][1] = " _(  )(  __)(_  _)___(  _ \ /  \  /  \ / ___)(_  _)"
    gamedata["status"][2] = "/ \) \ ) _)   )( (___)) _ ((  O )(  O )\___ \  )(  "
    gamedata["status"][3] = "\____/(____) (__)    (____/ \__/  \__/ (____/ (__) "
    winstatus.update()

def Event_SupercruiseExit(entry):
    gamedata["status"][0] = ""
    gamedata["status"][1] = "Supercruise verlassen bei " + entry["Body"]
    gamedata["status"][2] = "System: " + entry["StarSystem"]
    gamedata["status"][3] = ""
    gamedata["status"][4] = ""
    winstatus.update()
def Event_SupercruiseEntry(entry):
    gamedata["status"][0] = ""
    gamedata["status"][1] = "Eintritt in Supercruise im System " + entry["StarSystem"]
    gamedata["status"][2] = ""
    gamedata["status"][3] = ""
    gamedata["status"][4] = ""
    winstatus.update()

def Event_Docked(entry):
    gamedata["status"][0] = ""
    gamedata["status"][1] = "{0} ({1}) - {2}".format(entry["StationName"], entry["StationType"], entry["StationGovernment_Localised"])
    gamedata["status"][2] = ""
    if "StationFaction" in entry:
        name = entry["StationFaction"]["Name"]
        state = ""
        if "FactionState" in entry["StationFaction"]: state = entry["StationFaction"]["FactionState"]
        gamedata["status"][2] = name + " (" + state + ")"
    gamedata["status"][3] = ""
    if "StationEconomy_Localised" in entry: gamedata["status"][3] = entry["StationEconomy_Localised"]
    gamedata["status"][4] = ""
    winstatus.update()
def Event_DockingGranted(entry):
    # { "timestamp":"2022-10-10T04:14:21Z", "event":"DockingGranted", "LandingPad":5, "MarketID":3227670528, "StationName":"Griggs Station", "StationType":"Outpost" }
    gamedata["status"][0] = ""
    gamedata["status"][1] = "Landeerlaubnis von " + entry["StationName"]
    gamedata["status"][2] = "Landeplatz " + str(entry["LandingPad"])
    gamedata["status"][3] = ""
    gamedata["status"][4] = ""
    winstatus.update()
def Event_DockingDenied(entry):
    gamedata["status"][0] = ""
    gamedata["status"][1] = entry["StationName"] + " verweigert Landeerlaubnis"
    gamedata["status"][2] = "Grund: " + entry["Reason"]
    gamedata["status"][3] = ""
    gamedata["status"][4] = ""
    winstatus.update()
def Event_Undocked(entry):
    for i in range(0, 5): gamedata["status"][i] = ""
    winstatus.update()
def Event_Touchdown(entry):
    gamedata["status"][0] = ""
    gamedata["status"][1] = "gelandet auf Planet " + entry["Body"]
    gamedata["status"][2] = "Lat/Lng: {0:.4f}°/{1:.4f}°".format(entry["Latitude"], entry["Longitude"])
    gamedata["status"][3] = "System: " + entry["StarSystem"]
    gamedata["status"][4] = ""
    winstatus.update()
def Event_Liftoff(entry):
    gamedata["status"][0] = ""
    gamedata["status"][1] = "von " + entry["Body"] + " gestartet"
    gamedata["status"][2] = ""
    gamedata["status"][3] = ""
    gamedata["status"][4] = ""
    winstatus.update()

def Event_Cargo(entry):
    global gamedata, config
    #{ "timestamp":"2022-10-08T12:44:51Z", "event":"Cargo", "Vessel":"Ship", "Count":172, "Inventory":[ { "Name":"monazite", "Name_Localised":"Monazit", "Count":32, "Stolen":0 }, { "Name":"musgravite", "Name_Localised":"Musgravit", "Count":35, "Stolen":0 }, { "Name":"alexandrite", "Name_Localised":"Alexandrit", "Count":100, "Stolen":0 }, { "Name":"drones", "Name_Localised":"Drohne", "Count":5, "Stolen":0 } ] }
    if "Inventory" in entry:
        gamedata["cargo"] = entry["Inventory"]
    else:
        with open(config["eddir"]["path"] + "/Cargo.json", "r") as f:
            gamedata["cargo"] = json.load(f)["Inventory"]
    if len(gamedata["cargo"]) > 0:
        autoPage(1)
    else:
        if len(gamedata["missions"]) > 0:
            autoPage(3)
        else:
            autoPage(1)
def Event_StoredModules(entry):
    global gamedata, config
    gamedata["stored"]["modules"] = entry["Items"]
    with open(config["localnames"]["modules"], "w") as out:
        out.write(json.dumps(gamedata["stored"]["modules"]) + '\n')
    autoPage(4)
def Event_StoredShips(entry):
    global gamedata, config
    gamedata["stored"]["ships"] = [] # alles löschen
    # dann alle Schiffe zusammen in einer Liste - macht die Verwaltung einfacher
    for ship in entry["ShipsHere"]:
        ship["StarSystem"] = entry["StarSystem"]
        ship["ShipMarketID"] = entry["MarketID"]
        ship["TransferPrice"] = 0
        ship["TransferTime"] = 0
        gamedata["stored"]["ships"].append(ship)
    for ship in entry["ShipsRemote"]:
        gamedata["stored"]["ships"].append(ship)
    with open(config["localnames"]["hangar"], "w") as out:
        out.write(json.dumps(gamedata["stored"]["ships"]) + '\n')
    autoPage(5)
def Event_Loadout(entry):
    config["user"]["ship"] = entry["ShipName"]
    config["user"]["ident"] = entry["ShipIdent"]
    gamedata["stored"]["outfit"] = entry
    with open(config["localnames"]["outfit"], "w") as out:
        out.write(json.dumps(gamedata["stored"]["outfit"]) + '\n')
    tools.saveConfig(config, gamedata)
    for i in range(0, 4): gamedata["status"][i] = ""
    winheader.update()
    winstatus.update()
    autoPage(6)
def Event_GameOver(entry):
    gamedata["status"][0] = "  ___   __   _  _  ____     __   _  _  ____  ____ "
    gamedata["status"][1] = " / __) / _\ ( \/ )(  __)   /  \ / )( \(  __)(  _ \\"
    gamedata["status"][2] = "( (_ \/    \/ \/ \ ) _)   (  O )\ \/ / ) _)  )   /"
    gamedata["status"][3] = " \___/\_/\_/\_)(_/(____)   \__/  \__/ (____)(__\_)"
    gamedata["status"][4] = ""
    winstatus.update()

def Event_Materials(entry):
    gamedata["materials"]["raw"] = entry["Raw"]
    gamedata["materials"]["manufactured"] = entry["Manufactured"]
    gamedata["materials"]["encoded"] = entry["Encoded"]
    with open(config["localnames"]["materials"], "w") as out:
        out.write(json.dumps(gamedata["materials"]["raw"]) + '\n')
        out.write(json.dumps(gamedata["materials"]["manufactured"]) + '\n')
        out.write(json.dumps(gamedata["materials"]["encoded"]) + '\n')
def Event_ShipLocker(entry):
    if not "items" in entry: return # mnachmal ist einfach nichts da
    gamedata["locker"]["items"] = entry["Items"]
    gamedata["locker"]["components"] = entry["Components"]
    gamedata["locker"]["consumables"] = entry["Consumables"]
    gamedata["locker"]["data"] = entry["Data"]
    with open(config["localnames"]["shiplocker"], "w") as out:
        out.write(json.dumps(gamedata["locker"]["items"]) + '\n')
        out.write(json.dumps(gamedata["locker"]["components"]) + '\n')
        out.write(json.dumps(gamedata["locker"]["consumables"]) + '\n')
        out.write(json.dumps(gamedata["locker"]["data"]) + '\n')

def Event_Missions(entry):
    found = []
    # aktive Mission suchen und in found[] packen
    for mission in gamedata["missions"]:
        for active in entry["Active"]:
            if active["MissionID"] == mission["MissionID"]: found.append(mission)
    gamedata["missions"] = found
    with open(config["localnames"]["missions"], "w") as out:
        for m in gamedata["missions"]: out.write(json.dumps(m) + '\n')
def Event_MissionAccepted(entry):
    # unwichtiges löschen
    temp = json.dumps(entry)
    entry = json.loads(temp)
    del entry["timestamp"]
    del entry["event"]
    gamedata["missions"].append(entry)
    with open(config["localnames"]["missions"], "w") as out:
        for m in gamedata["missions"]:
            out.write(json.dumps(m) + '\n')
    autoPage(3)
def Event_MissionRedirected(entry):
    # { "timestamp":"2022-10-15T13:18:04Z", "event":"MissionRedirected", "MissionID":894845762, "Name":"Mission_Salvage", "NewDestinationStation":"Li Qing Jao", "NewDestinationSystem":"Sol", "OldDestinationStation":"", "OldDestinationSystem":"Avik" }
    id = entry["MissionID"]
    for m in gamedata["missions"]:
        if m["MissionID"] == id:
            m["DestinationSystem"] = entry["NewDestinationSystem"]
            m["DestinationStation"] = entry["NewDestinationStation"]
            with open(config["localnames"]["missions"], "w") as out:
                for m in gamedata["missions"]: out.write(json.dumps(m) + '\n')
            break
    pageManager()
def Event_MissionCompleted(event):
    id = event["MissionID"]
    for m in gamedata["missions"]:
        if m["MissionID"] == id:
            gamedata["missions"].remove(m)
            with open(config["localnames"]["missions"], "w") as out:
                for m in gamedata["missions"]: out.write(json.dumps(m) + '\n')
            handleCreditsAdd("Reward", event)
            pageManager()
            break
    autoPage(getPrioPage())

def Event_LeaveBody(entry):
    gamedata["status"][0] = ""
    gamedata["status"][1] = "Planet " + entry["Body"] + " verlassen"
    gamedata["status"][2] = "betrete das Universum bei " + entry["StarSystem"]
    gamedata["status"][3] = ""
    gamedata["status"][4] = ""
    winstatus.update()
def Event_ApproachBody(entry):
    gamedata["status"][0] = ""
    gamedata["status"][1] = "Orbital-Cruise bei " + entry["Body"]
    gamedata["status"][2] = ""
    gamedata["status"][3] = ""
    gamedata["status"][4] = ""
    winstatus.update()
def Event_ApproachSettlement(entry):
    gamedata["status"][0] = ""
    gamedata["status"][1] = "Landeanflug bei " + entry["Name"]
    gamedata["status"][2] = "Planet " + entry["BodyName"]
    gamedata["status"][3] = ""
    gamedata["status"][4] = ""
    winstatus.update()

def Event_SAASignalsFound(entry):
    if not "Signals" in entry: return # nix gefunden
    gamedata["saasignals"] = entry
    with open(config["localnames"]["saasignals"], "w") as out:
        out.write(json.dumps(entry) + '\n')
    autoPage(7)
def Event_ReceiveText(entry):
    message = entry["Message"]
    if "Pirat" in message:
        Event_ReceiveText_Pirat(entry)
        return
    channel = entry["Channel"]
    if "Message_Localised" in entry: message = entry["Message_Localised"]
    addMessage(channel, message)
def Event_ReceiveText_Pirat(entry):
    gamedata["status"][0] = "  __  __ _  ____  ____  ____  ____  __  ___  ____    _  _   "
    gamedata["status"][1] = " (  )(  ( \(_  _)(  __)(  _ \(    \(  )/ __)(_  _)  / \/ \  "
    gamedata["status"][2] = "  )( /    /  )(   ) _)  )   / ) D ( )(( (__   )(    \_/\_/  "
    gamedata["status"][3] = " (__)\_)__) (__) (____)(__\_)(____/(__)\___) (__)   (_)(_)  "
    gamedata["status"][4] = ""
    winstatus.update()
def Event_EscapeInterdiction(entry):
    for i in range(0, 4): gamedata["status"][i] = ""
    winstatus.update()

def Event_ProspectedAsteroid(entry):
    gamedata["asteroid"] = entry
    with open(config["localnames"]["asteroid"], "w") as out:
        out.write(json.dumps(entry) + '\n')
    autoPage(8)
def Event_AsteroidCracked(entry):
    gamedata["status"][0] = "     _      __   __    ___  __ _  ____   __  ____    _   "
    gamedata["status"][1] = "    / \   _(  ) / _\  / __)(  / )(  _ \ /  \(_  _)  / \  "
    gamedata["status"][2] = "    \_/  / \) \/    \( (__  )  (  ) __/(  O ) )(    \_/  "
    gamedata["status"][3] = "    (_)  \____/\_/\_/ \___)(__\_)(__)   \__/ (__)   (_)  "
    gamedata["status"][4] = ""
    winstatus.update()
def Event_MiningRefined(entry):
    for i in range(0, 4): gamedata["status"][i] = ""
    winstatus.update()

def handleCreditsAdd(key, transaction):
    if key in transaction:
        value = int(config["user"]["credits"]) + transaction[key]
        config["user"]["credits"] = str(value)
    else:
        j = json.dumps(transaction)
        gamedata["logger"].info("MoneyAdd: Key '{0}' nicht gefunden -> {1}".format(key, j))
    winheader.update()
def handleCreditsSub(key, transaction):
    if key in transaction:
        value = int(config["user"]["credits"]) - transaction[key]
        config["user"]["credits"] = str(value)
    else:
        j = json.dumps(transaction)
        gamedata["logger"].info("MoneySub: Key '{0}' nicht gefunden -> {1}".format(key, j))
    winheader.update()
def Event_MarketBuy(entry):
    handleCreditsSub("TotalCost", entry)
def Event_MarketSell(entry):
    handleCreditsAdd("TotalSale", entry)
def Event_Repair(entry):
    handleCreditsSub("Cost", entry)
def Event_BuyDrones(entry):
    handleCreditsSub("TotalCost", entry)
def Event_SellDrones(entry):
    handleCreditsSub("TotalSale", entry)
def Event_SellExplorationData(entry):
    handleCreditsAdd("TotalEarnings", entry)
def Event_ShipyardBuy(entry):
    handleCreditsSub("ShipPrice", entry)
    handleCreditsAdd("SellPrice", entry)   # falls das aktuelle Schiff gleich verkauft wurde
def Event_ShipyardSell(entry):
    handleCreditsAdd("ShipPrice", entry)
def Event_ShipyardTransfer(entry):
    handleCreditsSub("TransferPrice", entry)
def Event_ModuleBuy(entry):
    handleCreditsSub("BuyPrice", entry)
    # bei einem Kauf & Verkauf, dann landet alles in einem Event
    handleCreditsSub("SellPrice", entry)
def Event_ModuleSell(entry):
    # auch ModuleSellRemote
    handleCreditsAdd("SellPrice", entry)
def Event_ModuleStore(entry):
    handleCreditsSub("Cost", entry)
def Event_BuyExplorationData(entry):
    handleCreditsSub("Cost", entry)
def Event_BuyTradeData(entry):
    handleCreditsSub("Cost", entry)
def Event_BuyAmmo(entry):
    handleCreditsSub("Cost", entry)
def Event_CrewHire(entry):
    handleCreditsSub("Cost", entry)
def Event_FetchRemoteModule(entry):
    handleCreditsSub("TransferCost", entry)
def Event_RefuelAll(entry):
    handleCreditsSub("Cost", entry)
def Event_RefuelPartial(entry):
    handleCreditsSub("Cost", entry)
def Event_RepairAll(entry):
    handleCreditsSub("Cost", entry)
def Event_RestockVehicle(entry):
    handleCreditsSub("Cost", entry)
def Event_PowerplayFastTrack(entry):
    handleCreditsSub("Cost", entry)
def Event_NpcCrewPaidWage(entry):
    handleCreditsSub("Amount", entry)


# { "timestamp":"2022-10-16T19:06:26Z", "event":"MissionAbandoned", "Name":"Mission_Collect_name", "MissionID":895117670 }



def addMessage(channel, message):
    global gamedata, winevents, winmenu
    gamedata["logger"].info("Channel: {0} - Message: {1}".format(channel, message))
    # existienz prüfen
    if not channel in gamedata["events"]:
        gamedata["logger"].info("Channel '" + channel + "' ist noch nicht vorhanden")
        gamedata["events"][channel] = [ "", "", "", "", ""]
    # eintragen
    for i in range(0, 4): gamedata["events"][channel][i] = gamedata["events"][channel][i + 1]
    gamedata["events"][channel][4] = message[-63:]
    # letzten Channel setzen & Aktualisieren
    gamedata["events"]["lastch"] = channel
    winevents.update()
    winmenu.update()       # force cursor pos





def getPrioPage():
    def prioMission():
        #  Priorität hat die Mission-Seite
        if len(gamedata["missions"]) > 0:
            return "3"
        else:
            if len(gamedata["cargo"]) > 0:
                only = False
                for fracht in gamedata["cargo"]:
                    if fracht["Name"].casefold() == "drones": only = True
                if len(gamedata["cargo"]) > 1: only = False # noch was anderes als Drohnen
                if only == True:
                    # nur dronen im Frachtraum
                    return "3"
                else:
                    return "1"
            else:
                # keine Fracht, also doch die Missionen
                return "3"
    def prioCargo():
        # Priorität hat die Cargo-Seite
        if len(gamedata["cargo"]) > 0:
            only = False
            for fracht in gamedata["cargo"]:
                if fracht["Name"].casefold() == "drones": only = True
            if len(gamedata["cargo"]) > 1: only = False # noch was anderes als Drohnen
            if only == True:
                # nur dronen im Frachtraum
                if len(gamedata["missions"]) > 0:
                    return "3"
                else:
                    return "1"
            else:
                return "1"
        else:
            if len(gamedata["missions"]) == 0:
                return "1"
            else:
                return "3"
    if config["pages"]["priopage"] == "cargo": return prioCargo()
    return prioMission()
def autoPage(page):
    pageManager.lastPage = "?"
    if config["pages"]["autopage"] == "yes": config["pages"]["activepage"] = str(page)
    pageManager()
def pageManager():
    if config["pages"]["events"] == "yes":
        pageManager_raw()       # debug-meldungen und Fehler des Programms
    else:
        pageManager_catch()     # alles schön verstecken - hoffentlich
def pageManager_catch():
    try:
        pageManager_raw()
    except Exception as ex:
        # gamedata["logger"].error("{0}".format(ex))
        gamedata["logger"].exception(ex)
        if "event" in gamedata: gamedata["logger"].error("!!! " + json.dumps(gamedata["event"])) # das wurde "gesendet"
def pageManager_raw():
    global config
    global pagesettings, pagetwitter
    global pagecargo, pageroute, pagemissions, pagestoredmodules, pagesaasignals, pagelicense, pageshiphangar, pageshipoutfit, pageasteroid, pagedownloads
    page = config["pages"]["activepage"]
    if config["user"]["license"] == "yes":
        if page == pageManager.lastPage: return
        # ! douh !
        if page == "1": pagecargo.update()
        if page == "2": pageroute.update()
        if page == "3": pagemissions.update()
        if page == "4": pagestoredmodules.update()
        if page == "5": pageshiphangar.update()
        if page == "6": pageshipoutfit.update()
        if page == "7": pagesaasignals.update()
        if page == "8": pageasteroid.update()
        if page == "S": pagesettings.update()
        if page == "U": pagedownloads.update()
        if page == "T": 
            if not config["twitter"]["api_key"] == "unset":  pagetwitter.update()
        pageManager.lastPage = page
    else:
        pagelicense.update()

def inputManager(key):
    global config
    global pagesettings, pagelicense
    page = config["pages"]["activepage"]
    if config["user"]["license"] == "no":
        pagelicense.handleInput(key)
    else:
        if key == "c" or key == "C": winmenu.handleKey(key)
        if page == "S": pagesettings.handleInput(key)
        if page == "T": pagetwitter.handleInput(key)
        if page == "2": pageroute.handleInput(key)



def startEDMC():
    if config["pages"]["edmc"] == "yes":
        gamedata["logger"].info("Autostart für EDMC aktiviert -> " + platform.system())
        if os.path.exists(config["eddir"]["edmc"] + "/EDMarketConnector.py"):
            parameter = [   
                            sys.executable, 
                            config["eddir"]["edmc"] + "/EDMarketConnector.py"
                        ]
            proc = subprocess.Popen(parameter, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out = proc.communicate()[0]
            err = proc.communicate()[1]
            gamedata["logger"].info("EDMC wurde wieder beendet")
        else:
            gamedata["logger"].info("EDMC nicht gefunden bzw. Pfad falsch gesetzt")
    else:
        gamedata["logger"].info("kein Autostart für EDMC")



def prepareVersion():
    global config, gamedata
    VERSION_NEED = "3"
    if not config["esaos"]["version"] == VERSION_NEED:
        gamedata["logger"].info("Version stimmt nicht - lösche alte Files")
        if os.path.exists(config["localnames"]["stations"]): os.remove(config["localnames"]["stations"])
        config["esaos"]["version"] = VERSION_NEED
        tools.saveConfig(config, gamedata)
def main(stdsrc):
    global winheader, winmenu, winevents, winstatus
    global pagesettings, pagetwitter
    global pagecargo, pageroute, pagemissions, pagestoredmodules, pagesaasignals, pagelicense, pageshiphangar, pageshipoutfit, pageasteroid, pagedownloads

    if config["pages"]["activepage"] == "U": config["pages"]["activepage"] = "1"
    prepareVersion()

    winheader = windows.WinHeader(config, gamedata)
    winmenu = windows.WinMenu(config, gamedata)
    winevents = windows.WinEvents(config, gamedata)
    winstatus = windows.WinStatus(config, gamedata)
    pagecargo = pages.PageCargo(config, gamedata)
    pageroute = pages.PageRoute(config, gamedata)
    pagesettings = pages.PageSettings(config, gamedata)
    pagemissions = pages.PageMissions(config, gamedata)
    pageloading = pages.PageLoading(config, gamedata)
    pagestoredmodules = pages.PageStoredModules(config, gamedata)
    pagesaasignals = pages.PageSAASignals(config, gamedata)
    pagelicense = pages.PageLicense(config, gamedata)
    pageshiphangar = pages.PageShipHangar(config, gamedata)
    pageshipoutfit = pages.PageShipOutfit(config, gamedata)
    pageasteroid = pages.PageAsteroid(config, gamedata)
    pagedownloads = pages.PageDownloads(config, gamedata)
    pagetwitter = pages.PageTwitter(config, gamedata)
    pageManager.lastPage = "?"

    pageloading.update()
    if os.path.exists(config["localnames"]["stations"]):
        gamedata["logger"].info("Stationen werden geladen")
        with open(config["localnames"]["stations"], "r") as f:
            for line in f:
                gamedata["stations"].append(json.loads(line))
    else:
        gamedata["logger"].info("keine Stationen vorhanden")

    if os.path.exists(config["localnames"]["modnames"]):
        gamedata["logger"].info("Namen der Module werden geladen")
        with open(config["localnames"]["modnames"], "r") as f:
            gamedata["modnames"] = json.load(f)
    else:
        gamedata["logger"].info("keine Modulnamen vorhanden")

    winmenu.update()
    winheader.update()
    winevents.update()
    winstatus.update()

    observer = None
    path = config["eddir"]["path"]
    if os.path.exists(path):
        event_handler = MyFileHandler(config)
        observer = Observer()
        observer.schedule(event_handler, path, recursive=True)
        observer.start()
    try:
        while True:
            pageManager()
            winevents.update()
            winheader.update()
            winmenu.update()
            input = stdscr.getkey()
            # ! douh !
            if input == "1": config["pages"]["activepage"] = "1"
            if input == "2": config["pages"]["activepage"] = "2"
            if input == "3": config["pages"]["activepage"] = "3"
            if input == "4": config["pages"]["activepage"] = "4"
            if input == "5": config["pages"]["activepage"] = "5"
            if input == "6": config["pages"]["activepage"] = "6"
            if input == "7": config["pages"]["activepage"] = "7"
            if input == "8": config["pages"]["activepage"] = "8"
            if input == "s" or input == "S": config["pages"]["activepage"] = "S"
            if input == "t" or input == "T": config["pages"]["activepage"] = "T"
            # ! douh !
            inputManager(input)
    except KeyboardInterrupt:
        if not observer is None: observer.stop()
    if not observer is None: observer.join()


edmc = Thread(target=startEDMC)
edmc = multiprocessing.Process(target=startEDMC)
edmc.start()
time.sleep(1)

wrapper(main)
edmc.kill()
# Config sichern, nach dem beenden
print("speichere Konfiguration")
tools.saveConfig(config, gamedata)
print("bye, bye")
