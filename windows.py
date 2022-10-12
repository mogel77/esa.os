import curses
import math





class WinBaseWindow:
    def __init__(self, config, gamedata, height, width, posy, posx):
        self.screen = curses.newwin(height, width, posy, posx)
        self.config = config
        self.gamedata = gamedata

    def print(self, posy, posx, content):
        try:
            self.screen.addstr(posy, posx, content)
        except curses.error:
            pass # ! douh ! - schlucken ist immer doof

    def hLine(self, sy, sx, length):
        for i in range(0, length):
            self.print(sy, sx, "-")
            sx += 1;

    def vLine(self, sy, sx, length):
        for i in range(0, length):
            self.print(sy, sx, "|")
            sy += 1;

    def dot(self, sy, sx, dot):
        self.print(sy, sx, dot)




# zur Zeit eher wegen Debug-Ausgaben
class WinEvents(WinBaseWindow):
    def __init__(self, config, gamedata):
        super().__init__(config, gamedata, 6, 65, 30, 0)

    def update(self):
        self.screen.clear()
        self.hLine(0, 0, 65)
        self.vLine(1, 64, 5)
        self.dot(0, 64, "+")
        self.dot(0, 19, "+")
        self.screen.refresh()

        channel = self.gamedata["events"]["channel"]
        lastch = self.gamedata["events"]["lastch"]
        # self.gamedata["logger"].info("Channel: {0} - LastCh: {1}".format(channel, lastch))

        # prüfen ob etwas angezeigt werden soll
        if not channel == "auto":
            lastch = channel
            # self.gamedata["logger"].info("Channel ist NICHT auto sondern " + lastch)
        else:
            if lastch == "debug" and self.config["pages"]["events"] == "no": return

        # prüfen ob der gewählte Kanal schon vorhanden ist
        if not lastch in self.gamedata["events"]:
            # self.gamedata["logger"].error("Channel: " + lastch + " nicht in events")
            return

        # content anzeigen
        # self.gamedata["logger"].info("Ausgabe für Channel "+ lastch)
        events = self.gamedata["events"][lastch]
        for i in range(0, 5): self.print(5 - i, 0, events[i])
        self.screen.refresh()



class WinMenu(WinBaseWindow):
    def __init__(self, config, gamedata):
        super().__init__(config, gamedata, 24, 20, 6, 0)

    def update(self):
        self.screen.clear()
        self.update_chatter()
        self.update_menu()
        self.print(17, 0, "         Menü > ")
        self.screen.refresh()

    def update_menu(self):
        if not self.config["user"]["license"] == "yes": return
        modules = [ "Settings", "Cargo", "Route", "Mission", "Module", "Hangar", "Ausstattung", "SAA Scan", "Asteroid Scan" ]
        for i in range(0, len(modules)):
            self.print(i + 1, 0, "{0:>14} - {1}".format(modules[i][-14:], i))

    def update_chatter(self):
        self.vLine(0, 19, 24)
        self.hLine(19, 0, 19)
        self.dot(19, 19, "+")
        self.print(21, 5, "(C)hannel")
        self.print(22, 2, "[{0:^13}]".format(self.gamedata["events"]["channel"]))

    def scrollSetting(self, current, options):
        index = 0
        # aktuelle option suchen bzw. den Index dazu
        for o in options:
            if str(o) == current: break
            index += 1
        index += 1 # aktuellen Index erhöhen - wollen ja nächste Option
        if index >= len(options): index = 0
        return str(options[index])

    def handleKey(self, key):
        if not (key == "c" or key == "C"): return # sec-check
        options = [ "auto" ]
        for channel in self.gamedata["events"]:
            if not isinstance(self.gamedata["events"][channel], str): options.append(channel)
        self.gamedata["events"]["channel"] = self.scrollSetting(self.gamedata["events"]["channel"], options)
        self.config["user"]["channel"] = self.gamedata["events"]["channel"]



esaos = [ " ____  ____   __      __   ____ ", "(  __)/ ___) / _\    /  \ / ___)", " ) _) \___ \/    \ _(  O )\___ \\", "(____)(____/\_/\_/(_)\__/ (____/" ]

class WinHeader(WinBaseWindow):
    def __init__(self, config, gamedata):
        super().__init__(config, gamedata, 6, 130, 0, 0)

    def update(self):
        self.screen.clear()
        for i in range (0,4):
            self.print(i, 5, esaos[i])

        self.hLine(5, 0, 130)
        self.vLine(0, 42, 5)
        self.dot(5, 42, "+")
        self.dot(5, 19, "+")

        if self.config['user']['squadrank'] == '0':
            self.print(1, 45, self.config["user"]["name"])
        else:
            self.print(1, 45, "{0} - {1} (Rank {2})".format(self.config["user"]["name"], self.config["user"]["squadname"], self.config["user"]["squadrank"]))
        self.print(2, 45, "{0:,d}cr - [{1}] {2}".format(int(self.config["user"]["credits"]), self.config["user"]["ident"], self.config["user"]["ship"]))

        pos = [ float(self.config["user"]["locx"]), float(self.config["user"]["locy"]), float(self.config["user"]["locz"]) ]
        home = [ float(self.config["user"]["homex"]), float(self.config["user"]["homey"]), float(self.config["user"]["homez"]) ]
        distance = math.dist(pos, home)
        self.print(3, 45, "{0} - {1:.1f}ly from {2}".format(self.config["user"]["system"], distance, self.config["user"]["homesys"]))
        self.screen.refresh()




# zur Zeit eher wegen Debug-Ausgaben
class WinStatus(WinBaseWindow):
    def __init__(self, config, gamedata):
        super().__init__(config, gamedata, 6, 65, 30, 65)

    def update(self):
        self.screen.clear()
        self.hLine(0, 0, 65)
        for i in range(0, 5):
            self.print(i + 1, 3, self.gamedata["status"][i]);
        self.screen.refresh()
