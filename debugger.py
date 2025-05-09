import curses
from curses import wrapper
import configparser
import os
import tempfile
import logging

import pages



PLAYBACK_LOG = "playback.log"



class Playback:
	def __init__(self, stdscr):
		self.logfiles = []			# alle Logfiles im Verzeichnis
		self.logentry = []			# alle Einträge des aktuellen Logfiles
		self.current_logfile = 0	# das aktuell gewählte Logfile
		self.current_entry = 0		# der aktuell gewählte Eintrag
		self.rows = curses.LINES
		self.cols = curses.COLS
		self.screen = stdscr
		self.scan_old_logs()
	def print(self, posy, posx, content):
		if (posx + len(content)) > self.cols:
			content = content[:(self.cols - posx)]
		try:
			self.screen.addstr(posy, posx, content)
		except curses.error:
			# Handle the case where the position is out of bounds
			print(f"Error: Position ({posy}, {posx}) is out of bounds for the screen size ({self.rows}, {self.cols})")
	def update(self):
		self.screen.clear()
		self.print(0, 0, "Log: " + self.logfile_current())
		if len(self.logentry) > 0:
			self.print(4, 0, "S> " + self.logentry[self.current_entry].strip())
			self.print(5, 0, f"   Zeile {self.current_entry}")
			if self.current_entry > 0:
				self.print(6, 0, "P> " + self.logentry[self.current_entry - 1].strip())
			if self.current_entry > 1:
				self.print(7, 0, "P> " + self.logentry[self.current_entry - 2].strip())
			if self.current_entry > 2:
				self.print(8, 0, "P> " + self.logentry[self.current_entry - 3].strip())
			if self.current_entry > 3:
				self.print(9, 0, "P> " + self.logentry[self.current_entry - 4].strip())
		else:
			self.print(4, 3, "kein aktives Logfile")
		self.print(2, 5, "[P] Previous - [N] Next - [C] Open/Reset - [S] Step Events - [J] JSON anzeigen - [Q] Quit : ")
		self.screen.refresh()
	def scan_old_logs(self):
		# scan directory for all files with suffix .log
		self.logfiles = []
		for root, dirs, files in os.walk(config['eddir']['path']):
			for file in files:
				if file.endswith(".01.log"):
					self.logfiles.append(os.path.join(root, file))
		self.logfiles.sort(reverse = True)
	def logfile_current(self):
		return self.logfiles[self.current_logfile]
	def logfile_next(self):
		if self.current_logfile < len(self.logfiles) - 1:
			self.current_logfile += 1
			self.logentry = []  # Clear the log entry list when switching log files
			self.current_entry = 0  # Reset the current entry to the beginning
	def logfile_previous(self):
		if self.current_logfile > 0:
			self.current_logfile -= 1
			self.logentry = []  # Clear the log entry list when switching log files
			self.current_entry = 0  # Reset the current entry to the beginning
	def logfile_openfile(self):
		# remove old logfile
		file = os.path.join(config['eddir']['path'], PLAYBACK_LOG)
		if os.path.exists(file):
			os.remove(file)
		# open logfile_entry and store it in an array
		with open(self.logfile_current(), 'r') as logfile:
			self.logentry = logfile.readlines()
		self.current_entry = 0  # Reset the current line to the beginning
		file = os.path.join(config['eddir']['path'], PLAYBACK_LOG)
		if os.path.exists(file):
			os.remove(file)
	def logentry_step(self):
		if (len(self.logentry) == 0) or (self.current_entry > len(self.logentry) - 1):
			return
		entry = self.logentry[self.current_entry].strip()
		file = os.path.join(config['eddir']['path'], PLAYBACK_LOG)
		with open(file, 'a') as logfile:
			logfile.write(entry + '\n')
		self.current_entry += 1
	def logentry_json(self):
		entry = self.logentry[self.current_entry].strip()
		filename = "tempfile.json"
		with tempfile.NamedTemporaryFile(dir=tempfile.gettempdir(), suffix='.json', delete=False) as temp_file:
			filename = temp_file.file.name
			temp_file.write(entry.strip().encode('utf-8'))
		os.system(f'xdg-open file:///{filename} &')



def main_playback(stdscr):
	stdscr.clear()
	playback = Playback(stdscr)
	playback.scan_old_logs();
	while True:
		playback.update()
		key = stdscr.getch()
		if key == ord('q'):
			break
		elif key == ord('p'):
			playback.logfile_previous()
		elif key == ord('c'):
			playback.logfile_openfile()
		elif key == ord('n'):
			playback.logfile_next()
		elif key == ord('s'):
			playback.logentry_step()
		elif key == ord('j'):
			playback.logentry_json()
def main_update_starsystem(stdscr):
	def dump_entry(entry):
		filename = "tempfile.json"
		with tempfile.NamedTemporaryFile(dir=tempfile.gettempdir(), suffix='.json', delete=False) as temp_file:
			filename = temp_file.file.name
			temp_file.write(entry.strip().encode('utf-8'))
		gamedata["logger"].info(f"open file {filename}")
		os.system(f'xdg-open file:///{filename} &')
	page = pages.PageDownloads(config, gamedata)
	try:
		page.downloadAndUnpack()
		page.convertJson2JsonL_FastMode()
		#	page.convertJson2JsonL_LowMemory()
		page.filterStations()
	except Exception as e:
		gamedata["logger"].exception("Error in main_update_starsystem: %s", e)
		# read alle lines in systion.json
		with open("daten/station-debug.json", "r") as f:
			lines = f.readlines()
		count = len(lines)
		dump_entry(lines[count - 1])
		dump_entry(lines[count - 2])
	
	
def main():
	# wrapper(main_playback)
	wrapper(main_update_starsystem)

if __name__ == "__main__":
	config = configparser.ConfigParser()
	config.read('config.ini')
	gamedata = {}
	gamedata["status"] =  [ "", "", "", "", "" ]
	if os.path.exists("esaos.log"): os.remove("esaos.log")
	gamedata["logger"] = logging.getLogger("esaos")
	hdlr = logging.FileHandler("esaos.log")
	hdlr.setFormatter(logging.Formatter('%(levelname)s > %(message)s'))
	gamedata["logger"].addHandler(hdlr)
	gamedata["logger"].setLevel(logging.DEBUG)
	gamedata["logger"].info("Startup")
	main()
	gamedata["logger"].info("Completed")
	gamedata["logger"].removeHandler(hdlr)
	hdlr.close()
