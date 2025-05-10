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
import signal
from curses import wrapper
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Thread
import random

import tools
import pages
import windows
from config import updateConfig
from tools import getDictItem





# { "timestamp":"2025-05-10T05:10:56Z", "event":"CodexEntry", "EntryID":1300701, "Name":"$Codex_Ent_Standard_Rocky_Ice_No_Atmos_Name;", "Name_Localised":"Nicht terraformierbar", "SubCategory":"$Codex_SubCategory_Terrestrials;", "SubCategory_Localised":"Terrestrische Planeten", "Category":"$Codex_Category_StellarBodies;", "Category_Localised":"Himmelskörper", "Region":"$Codex_RegionName_20;", "Region_Localised":"Dryman's Point", "System":"Pyranaea KW-C c13-5", "SystemAddress":1500453806450, "BodyID":0, "IsNewEntry":true }





# Konfiguration laden
updateConfig()
config = configparser.ConfigParser()
config.read('config.ini')

# zusätzliche Dinge zur Laufzeit
gamedata = {}
gamedata["hack"] = {}                       # !! DOUH !!
gamedata["hack"]["windows"] = {}            # !! DOUH !!
gamedata["hack"]["stdscr"] = None           # !! DOUH !!
gamedata["stations"] = []                   # alle bekannten Stationen
gamedata["modnames"] = []                   # alle Module
gamedata["cargo"] = []                      # Frachtraum
gamedata["materials"] = {}                  # Materialien
gamedata["materials"]["raw"] = []
gamedata["materials"]["manufactured"] = []
gamedata["materials"]["encoded"] = []
gamedata["locker"] = {}                     # Schmuggel
gamedata["locker"]["items"] = []
gamedata["locker"]["components"] = []
gamedata["locker"]["consumables"] = []
gamedata["locker"]["data"] = []
gamedata["missions"] = []                   # angenomene Missionen
gamedata["route"] = []                      # aktuelle Sprungroute
gamedata["stored"] = {}                     # gelagerte Dinge
gamedata["stored"]["modules"] = []
gamedata["stored"]["ships"] = []
gamedata["stored"]["outfit"] = []
gamedata["saasignals"] = []                 # Scan-Daten
gamedata["asteroid"] = []                   # - ?? - und schon haben wir einen Punkt der mir nicht bekannt vorkommt
gamedata["events"] = {}                     # aktuelles
gamedata["events"]["channel"] = config["user"]["channel"]       # vom Benutzer bevorzugt
gamedata["events"]["lastch"] = "npc"                            # letzte vom System angekommene - NPC existiert auf jedenfall
gamedata["events"]["npc"] = [ "", "", "", "", "" ]              # ... daher vorbereiten
gamedata["events"]["debug"] = [ "", "", "", "", "" ]            # pauschal - ist ja auch immer da
gamedata["status"] = [ "", "", "", "", "" ] # Status-Fenster - rechts unten
gamedata["system"] = {}                     # Informationen zum aktuellem System - aus den einzelnen Events gestückelt
gamedata["system"]["name"] = config["user"]["system"]  # Namen übernehmen
gamedata["fss"] = {}                        # Scanndaten
gamedata["fss"]["planets"] = []
gamedata["fss"]["signals"] = []
gamedata["fss"]["completed"] = False
gamedata["fss"]["count"] = 0
gamedata["farming"] = {}
gamedata["farming"]["log"] = []             # Log für Farming via SRV (ggf. auch anderes)

if os.path.exists("esaos.log"): os.remove("esaos.log")
gamedata["logger"] = logging.getLogger("esaos")
hdlr = logging.FileHandler("esaos.log")
hdlr.setFormatter(logging.Formatter('%(levelname)s > %(message)s'))
gamedata["logger"].addHandler(hdlr)
gamedata["logger"].setLevel(logging.DEBUG)
gamedata["logger"].info("Startup")

# CSV einlesen
gamedata["translations"] = {}
with open(config["localnames"]["translations"], encoding="utf-8") as csvfile:
    # { key : { lang : trans , ... } }
    header = csvfile.readline().split('\t')
    for line in csvfile:
        row = { }
        part = line.split('\t')
        for i in range(1, len(header)):
            header[i] = header[i].strip()
            row[header[i]] = part[i].strip() # unnützes Zeuchs lösch'n
        gamedata["translations"][part[0]] = row
    # noch die Sprachen sammeln für Einstellungen
    gamedata["translations"]["languages"] = []
    for i in range(1, len(header)):
        gamedata["translations"]["languages"].append(header[i])
gamedata["logger"].info("Übersetzungen geladen")

gamedata["hack"]["stdscr"] = curses.initscr()



LOG_NAME_MISSING_EVENTS = "missing-events.log"



class MyFileHandler(FileSystemEventHandler):
    def __init__(self, config):
        self.config = config
        self.oldlog = ""
        self.logfile = None
        self.init_jumptable()
        if os.path.exists(LOG_NAME_MISSING_EVENTS):
            os.remove(LOG_NAME_MISSING_EVENTS)
        if "playback.log" in config["eddir"]["lastlog"]:
            if os.path.exists(config["eddir"]["lastlog"]):
                os.remove(config["eddir"]["lastlog"])
        else:
            self.openLogfile(config["eddir"]["lastlog"])
    def init_jumptable(self):
        self.jumptable = {}
        self.jumptable["Shutdown"] = Event_Shutdown
        self.jumptable["SquadronStartup"] = Event_SquadronStartup
        self.jumptable["LoadGame"] = Event_LoadGame
        self.jumptable["Resurrect"] = Event_Resurrect
        self.jumptable["NavRoute"] = Event_NavRoute
        self.jumptable["NavRouteClear"] = Event_NavRouteClear
        self.jumptable["FSDTarget"] = Event_FSDTarget
        self.jumptable["FSDJump"] = Event_FSDJump
        self.jumptable["StartJump"] = Event_StartJump
        self.jumptable["JetConeBoost"] = Event_JetConeBoost
        self.jumptable["SupercruiseExit"] = Event_SupercruiseExit
        self.jumptable["SupercruiseEntry"] = Event_SupercruiseEntry
        self.jumptable["Docked"] = Event_Docked
        self.jumptable["DockingGranted"] = Event_DockingGranted
        self.jumptable["DockingDenied"] = Event_DockingDenied
        self.jumptable["Undocked"] = Event_Undocked
        self.jumptable["Touchdown"] = Event_Touchdown
        self.jumptable["Liftoff"] = Event_Liftoff
        self.jumptable["Cargo"] = Event_Cargo
        self.jumptable["StoredModules"] = Event_StoredModules
        self.jumptable["StoredShips"] =  Event_StoredShips
        self.jumptable["Loadout"] = Event_Loadout
        self.jumptable["Died"] = Event_GameOver
        self.jumptable["Materials"] = Event_Materials
        self.jumptable["ShipLocker"] = Event_ShipLocker
        self.jumptable["Missions"] = Event_Missions
        self.jumptable["MissionAccepted"] = Event_MissionAccepted
        self.jumptable["MissionRedirected"] = Event_MissionRedirected
        self.jumptable["MissionCompleted"] = Event_MissionCompleted
        self.jumptable["LeaveBody"] = Event_LeaveBody
        self.jumptable["ApproachBody"] = Event_ApproachBody
        self.jumptable["ApproachSettlement"] = Event_ApproachSettlement
        self.jumptable["SAASignalsFound"] = Event_SAASignalsFound
        self.jumptable["ProspectedAsteroid"] = Event_ProspectedAsteroid
        self.jumptable["AsteroidCracked"] = Event_AsteroidCracked
        self.jumptable["MiningRefined"] = Event_MiningRefined
        self.jumptable["ReceiveText"] = Event_ReceiveText
        self.jumptable["EscapeInterdiction"] = Event_EscapeInterdiction
        self.jumptable["MarketBuy"] = Event_MarketBuy
        self.jumptable["MarketSell"] = Event_MarketSell
        self.jumptable["Repair"] = Event_Repair
        self.jumptable["BuyDrones"] = Event_BuyDrones
        self.jumptable["SellDrones"] = Event_SellDrones
        self.jumptable["SellExplorationData"] = Event_SellExplorationData
        self.jumptable["ShipyardBuy"] = Event_ShipyardBuy
        self.jumptable["ShipyardSell"] = Event_ShipyardSell
        self.jumptable["ShipyardTransfer"] = Event_ShipyardTransfer
        self.jumptable["ModuleBuy"] = Event_ModuleBuy
        self.jumptable["ModuleSell"] = Event_ModuleSell
        self.jumptable["ModuleSellRemote"] = Event_ModuleSell
        self.jumptable["ModuleStore"] =  Event_ModuleStore
        self.jumptable["BuyExplorationData"] = Event_BuyExplorationData
        self.jumptable["BuyTradeData"] = Event_BuyTradeData
        self.jumptable["BuyAmmo"] =  Event_BuyAmmo
        self.jumptable["CrewHire"] = Event_CrewHire
        self.jumptable["FetchRemoteModule"] = Event_FetchRemoteModule
        self.jumptable["RefuelAll"] = Event_RefuelAll
        self.jumptable["RefuelPartial"] = Event_RefuelPartial
        self.jumptable["RepairAll"] = Event_RepairAll
        self.jumptable["RestockVehicle"] = Event_RestockVehicle
        self.jumptable["PowerplayFastTrack"] = Event_PowerplayFastTrack
        self.jumptable["NpcCrewPaidWage"] = Event_NpcCrewPaidWage
        self.jumptable["Scan"] = Event_Scan
        self.jumptable["FSSAllBodiesFound"] = Event_FSSAllBodiesFound
        self.jumptable["FSSDiscoveryScan"] = Event_FSSDiscoveryScan
        self.jumptable["FSSBodySignals"] = Event_FSSBodySignals
        self.jumptable["FSSSignalDiscovered"] = Event_SignalDiscovered
        self.jumptable["ShieldState"] = Event_ShieldState
        self.jumptable["MaterialCollected"] = Event_MaterialCollected
        self.jumptable["ScanOrganic"] = Event_ScanOrganic
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
        while self.has_another_line(self.logfile):
            try:
                gamedata["event"] = None
                self.secure_dispatch(event)
            except Exception as ex:
                #gamedata["logger"].error("{0}".format(ex), exc_info=True)
                gamedata["logger"].exception(ex)
                if gamedata["event"] is not None: gamedata["logger"].error(">>> {0}".format(json.dumps(gamedata["event"])))
    def secure_dispatch(self, event):
        global winevents, gamedata, winmenu
        entry = json.loads(self.logfile.readline())
        gamedata["event"] = entry
        name = entry["event"]
        addMessage("debug", f"EVENT: {name}")
        if name in self.jumptable:
            self.jumptable[name](entry)
        else:
            # write event to missing-events.log
            with open(LOG_NAME_MISSING_EVENTS, "a") as f:
                f.write(json.dumps(entry) + "\n")
        winmenu.update()



def Event_Shutdown(entry):
    tools.saveConfig(config, gamedata)
    os.kill(os.getpid(), signal.SIGINT)
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
def Event_FSDTarget(entry): # das ist das aktuelle System !?
    global gamedata
    # { "timestamp":"2022-10-08T12:59:46Z", "event":"FSDTarget", "Name":"Sharru Sector YO-A b0", "SystemAddress":671760000393, "StarClass":"M", "RemainingJumpsInRoute":8 }
    gamedata["system"]["starclass"] = entry["StarClass"] # falscher Stern - versteckt aber einen Bug
    pass
def Event_StartJump(entry):
    autoPage(2) #   pauschal die Route aufrufen
def Event_FSDJump(entry):
    global winheader, winstatus, gamedata
    def lineSystem(entry):
        starname = entry["StarSystem"]
        goverment = getDictItem(entry, "SystemGovernment", "SystemGovernment_Localised")
        if goverment == "n/v":
            goverment = "" # hier nichts weiter anzeigen
        else:
            goverment = " - " + goverment
        if "Powers" in entry:
            playname = entry["Powers"][0]
            playstate = getDictItem(entry, "PowerplayState", "PowerplayState_Localised")
            output = "{0} - {1} ({2})".format(starname, playname, playstate)
        else:
            output = "{0} {1}".format(starname, goverment)
        return output
    def lineEconomy(entry):
        security = getDictItem(entry, "SystemSecurity", "SystemSecurity_Localised")
        economy1 = getDictItem(entry, "SystemEconomy", "SystemEconomy_Localised")
        economy2 = getDictItem(entry, "SystemSecondEconomy", "SystemSecondEconomy_Localised")
        if economy1 != "n/v":
            return "{0} | {1} - {2}".format(economy1, economy2, security)
        return "Sternenklasse: " + gamedata["system"]["starclass"]
    def lineFaction(entry):
        if not "SystemFaction" in entry:
            return "Position: {0:.1f} / {1:.1f} / {2:.1f} ".format(entry["StarPos"][0], entry["StarPos"][1], entry["StarPos"][2])
        sysfaction = getDictItem(entry["SystemFaction"], "Name")
        sysstate = getDictItem(entry["SystemFaction"], "FactionState")
        if sysfaction is None: return ""
        if sysstate is None:
            return sysfaction
        else:
            return "{0} ({1})".format(sysfaction, sysstate)
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
    gamedata["fss"]["planets"] = []         # letzten Scan löschen
    gamedata["fss"]["signals"] = []         # letzten Scan löschen
    gamedata["fss"]["completed"] = False
    gamedata["fss"]["count"] = 0
    if "StarClass" in entry:
        gamedata["system"]["starclass"] = entry["StarClass"]
    else:
        gamedata["system"]["starclass"] = "Primär"
    gamedata["system"]["name"] = config["user"]["system"]
    winheader.update()
    winstatus.update()
    if len(gamedata["route"]) > 0:
        autoPage(2)
    else:
        autoPage(getPrioPage())
def Event_JetConeBoost(entry):
    gamedata["status"][0] = "   __  ____  ____     ____   __    __   ____  ____ "
    gamedata["status"][1] = " _(  )(  __)(_  _)___(  _ \\ /  \\  /  \\ / ___)(_  _)"
    gamedata["status"][2] = "/ \\) \\ ) _)   )( (___)) _ ((  O )(  O )\\___ \\  )(  "
    gamedata["status"][3] = "\\____/(____) (__)    (____/ \\__/  \\__/ (____/ (__) "
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
    autoPage(9)
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
    gamedata["status"][1] = " / __) / _\\ ( \\/ )(  __)   /  \\ / )( \\(  __)(  _ \\"
    gamedata["status"][2] = "( (_ \\/    \\/ \\/ \\ ) _)   (  O )\\ \\/ / ) _)  )   /"
    gamedata["status"][3] = " \\___/\\_/\\_/\\_)(_/(____)   \\__/  \\__/ (____)(__\\_)"
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
    gamedata["status"][1] = " (  )(  ( \\(_  _)(  __)(  _ \\(    \\(  )/ __)(_  _)  / \\/ \\  "
    gamedata["status"][2] = "  )( /    /  )(   ) _)  )   / ) D ( )(( (__   )(    \\_/\\_/  "
    gamedata["status"][3] = " (__)\\_)__) (__) (____)(__\\_)(____/(__)\\___) (__)   (_)(_)  "
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
    gamedata["status"][1] = "    / \\   _(  ) / _\\  / __)(  / )(  _ \\ /  \\(_  _)  / \\  "
    gamedata["status"][2] = "    \\_/  / \\) \\/    \\( (__  )  (  ) __/(  O ) )(    \\_/  "
    gamedata["status"][3] = "    (_)  \\____/\\_/\\_/ \\___)(__\\_)(__)   \\__/ (__)   (_)  "
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
def Event_MaterialCollected(entry):
    gamedata["farming"]["log"].insert(0, entry)
    gamedata["farming"]["log"] = gamedata["farming"]["log"][:22]
    autoPage(100) # Farming-Page
def Event_ScanOrganic(entry):
    gamedata["farming"]["log"].insert(0, entry)
    gamedata["farming"]["log"] = gamedata["farming"]["log"][:22]
    autoPage(100) # Farming-Page

def Event_Scan(entry):
    global gamedata
    planet = {}
    planet["name"] = entry["BodyName"]
    planet["id"] = entry["BodyID"]
    if "PlanetClass" in entry:
        planet["type"] = entry["PlanetClass"]
    else:
        if "StarType" in entry:
            planet["type"] = entry["StarType"] + " Star"
        else:
            planet["type"] = "Belt Cluster"
    if "SurfaceGravity" in entry:
        planet["gravity"] = entry["SurfaceGravity"]
    else:
        planet["gravity"] = 0.0
    if "SurfaceTemperature" in entry:
        planet["temp"] = entry["SurfaceTemperature"]
    else:
        planet["temp"] = 0
    if "Composition" in entry:
        planet["composition"] = entry["Composition"]      # dict
    else:
        planet["composition"] = { }
    if "Materials" in entry:
        planet["materials"] = entry["Materials"]
    else:
        planet["materials"] = { }
    if "Landable" in entry:
        planet["landable"] = entry["Landable"]
    else:
        planet["landable"] = False
    found = False
    for p in gamedata["fss"]["planets"]:
        if p["id"] == planet["id"]: 
            found = True
    if config["pages"]["fss_block_cluster"] == "yes" and "Belt" in planet["type"]:
        return
    if config["pages"]["fss_only_landable"] == "yes" and planet["landable"] == False:
        return
    if found == False:
        gamedata["fss"]["planets"].append(planet)
        with open(config["localnames"]["fss"], "w") as out:
            out.write(json.dumps(gamedata["fss"]["planets"]) + '\n')
        gamedata["logger"].info(f"FSS-Scan: {planet}")
    if config["pages"]["onlydetailed"] == "no":
        autoPage(9)
    else:
        if entry["ScanType"] == "Detailed":
            autoPage(9)
def Event_FSSAllBodiesFound(entry):
    global gamedata
    gamedata["fss"]["completed"] = True
    autoPage(9)
def Event_FSSDiscoveryScan(entry):
    global gamedata
    if "BodyCount" in entry:
        gamedata["fss"]["count"] = entry["BodyCount"]
    else:
        gamedata["fss"]["count"] = -1
    autoPage(9)
def Event_FSSBodySignals(entry):
    global gamedata
    signals = {}
    signals["id"] = entry["BodyID"]
    signals["Signals"] = entry["Signals"]
    found = False
    for s in gamedata["fss"]["signals"]:
        if s["id"] == entry["BodyID"]:
            found = True
    if found == False:
        gamedata["fss"]["signals"].append(signals)
    with open(config["localnames"]["fsssignals"], "w") as out:
        out.write(json.dumps(gamedata["fss"]["signals"]) + '\n')
    # -- nicht nötig -- autoPage(9)
def Event_SignalDiscovered(entry):
    global gamedata
    planet = {}
    # planet["name"] = entry["SignalName_Localised"]
    planet["name"] = "Star Phenomenon"
    planet["id"] = random.randint(1000000, 9999999)
    planet["type"] = "Unknown"
    planet["gravity"] = 0
    planet["temp"] = 0
    planet["composition"] = { }
    planet["materials"] = { }
    planet["landable"] = False
    found = False
    for p in gamedata["fss"]["planets"]:
        if p["id"] == planet["id"]: 
            found = True
    if found == False:
        gamedata["fss"]["planets"].append(planet)
        with open(config["localnames"]["fss"], "w") as out:
            out.write(json.dumps(gamedata["fss"]["planets"]) + '\n')
        gamedata["logger"].info(f"FSS-Scan: {planet}")
    if config["pages"]["onlydetailed"] == "no":
        autoPage(9)
    else:
        if entry["ScanType"] == "Detailed":
            autoPage(9)

def Event_ShieldState(entry):
    if not "ShieldsUp" in entry: return
    if entry["ShieldsUp"] == True:
        for i in range(0, 5):
            gamedata["status"][i] = ""
    else:
        gamedata["status"][0] = " ____  _  _  __  ____  __    ____    ____   __   _  _  __ _ "
        gamedata["status"][1] = "/ ___)/ )( \\(  )(  __)(  )  (    \\  (    \\ /  \\ / )( \\(  ( \\"
        gamedata["status"][2] = "\\___ \\) __ ( )(  ) _) / (_/\\ ) D (   ) D ((  O )\\ /\\ //    /"
        gamedata["status"][3] = "(____/\\_)(_/(__)(____)\\____/(____/  (____/ \\__/ (_/\\_)\\_)__)"
        gamedata["status"][4] = ""
    winstatus.update()





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
    # page - die aufzurufende Page (wenn Auto aktiviert ist)
    pageManager.lastNumber = "?"
    if config["pages"]["autopage"] == "yes": config["pages"]["activepage"] = str(page)
    pageManager()
def pageManager():
    # kompletten Screen neu aufbauen
    winmenu.update()
    winheader.update()
    winevents.update()
    winstatus.update()
    # Page anzeigen
    if config["pages"]["events"] == "yes":
        pageManager_raw()       # debug-meldungen und Fehler des Programms
    else:
        pageManager_catch()     # alles schön verstecken
def pageManager_catch():
    try:
        pageManager_raw()
    except Exception as ex:
        gamedata["logger"].exception(ex)
        if "event" in gamedata: gamedata["logger"].error("!!! " + json.dumps(gamedata["event"])) # das wurde "gesendet"
def pageManager_raw():
    global config
    global pagesettings
    global pagecargo, pageroute, pagemissions, pagestoredmodules, pagesaasignals, pagelicense, pageshiphangar, pageshipoutfit, pageasteroid, pagedownloads, pagefss
    global pagefarming
    pageNumber = config["pages"]["activepage"]
    if config["user"]["license"] == "yes":
        if pageNumber == pageManager.lastNumber : return
        # ! douh !
        if pageNumber == "1": pageManager.currentPage = pagecargo
        if pageNumber == "2": pageManager.currentPage = pageroute
        if pageNumber == "3": pageManager.currentPage = pagemissions
        if pageNumber == "4": pageManager.currentPage = pagestoredmodules
        if pageNumber == "5": pageManager.currentPage = pageshiphangar
        if pageNumber == "6": pageManager.currentPage = pageshipoutfit
        if pageNumber == "7": pageManager.currentPage = pagesaasignals
        if pageNumber == "8": pageManager.currentPage = pageasteroid
        if pageNumber == "9": pageManager.currentPage = pagefss
        if pageNumber == "S": pageManager.currentPage = pagesettings
        if pageNumber == "U": pageManager.currentPage = pagedownloads
        if pageNumber == "100": pageManager.currentPage = pagefarming
        pageManager.lastNumber  = pageNumber
        pageManager.currentPage.update()
    else:
        pagelicense.update()

def inputManager(key):
    # key - die gedrückte taste
    global config
    global pagesettings, pagelicense
    page = config["pages"]["activepage"]
    if config["user"]["license"] == "no":
        pagelicense.handleInput(key)
    else:
        if chr(key) == "c" or chr(key) == "C": winmenu.handleKey(key) # einzige Taste ohne Page
        pageManager.currentPage.handleInput(key)



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
    VERSION_REQUIRED = "5"
    VERSION_CURRENT = config["esaos"]["version"]
    if not VERSION_CURRENT == VERSION_REQUIRED:
        gamedata["logger"].info("Version stimmt nicht - lösche alte Files")
        if VERSION_CURRENT == "2":
            gamedata["logger"].info(" - lösche alte Stations Daten")
            if os.path.exists(config["localnames"]["stations"]): os.remove(config["localnames"]["stations"])
        if VERSION_CURRENT == "3":
            gamedata["logger"].info(" - lösche alte URL für Stations Daten")
            config["urls"]["galaxy_gz"] = "https://downloads.spansh.co.uk/galaxy_stations.json.gz"
        if VERSION_CURRENT == "4":
            gamedata["logger"].info(" - lösche alte URL für Stations Daten")
            config["urls"]["galaxy_gz"] = "https://downloads.spansh.co.uk/galaxy_1day.json.gz"
        config["esaos"]["version"] = VERSION_REQUIRED
        tools.saveConfig(config, gamedata)
def main(stdsrc):
    global winheader, winmenu, winevents, winstatus
    global pagesettings, pagedownloads, pagelicense
    global pagefarming
    global pagecargo, pageroute, pagemissions, pagestoredmodules, pagesaasignals, pageshiphangar, pageshipoutfit, pageasteroid, pagefss

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
    pagefss = pages.PageFSS(config, gamedata)
    pagefarming = pages.PageFarming(config, gamedata)
    pageManager.lastNumber  = "?"
    pageManager.currentPage = pagecargo # pauschal

    gamedata["hack"]["windows"]["status"] = winstatus
    gamedata["hack"]["windows"]["menu"] = winmenu

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

    pageManager()

    observer = None
    path = config["eddir"]["path"]
    if os.path.exists(path):
        event_handler = MyFileHandler(config)
        observer = Observer()
        observer.schedule(event_handler, path, recursive=True)
        observer.start()
    try:
        while True:
            winevents.update()
            winheader.update()
            winmenu.update()
            input = gamedata["hack"]["stdscr"].getch()
            # ! douh !
            if chr(input) == "1": config["pages"]["activepage"] = "1"
            if chr(input) == "2": config["pages"]["activepage"] = "2"
            if chr(input) == "3": config["pages"]["activepage"] = "3"
            if chr(input) == "4": config["pages"]["activepage"] = "4"
            if chr(input) == "5": config["pages"]["activepage"] = "5"
            if chr(input) == "6": config["pages"]["activepage"] = "6"
            if chr(input) == "7": config["pages"]["activepage"] = "7"
            if chr(input) == "8": config["pages"]["activepage"] = "8"
            if chr(input) == "9": config["pages"]["activepage"] = "9"
            if chr(input) == "s" or chr(input) == "S": config["pages"]["activepage"] = "S"
            if chr(input) == "x" or chr(input) == "X": break
            # ! douh !
            pageManager()
            inputManager(input) # alle anderen Tasten werden hier pro Page behandelt
            pageManager()
            # ! douh !
    except KeyboardInterrupt:
        gamedata["logger"].warn("Keyboard-Interrupt ausgelöst");
    if not observer is None: observer.stop()
    gamedata["hack"]["stdscr"].refresh()

edmc = Thread(target=startEDMC)
edmc = multiprocessing.Process(target=startEDMC)
edmc.start()
time.sleep(1)

wrapper(main)
edmc.kill()
# Config sichern, nach dem beenden
print("speichere Konfiguration")
tools.saveConfig(config, gamedata)
print("\n\n\tdanke für das Nutzen von ESA.OS - have a nice day\n\n")
