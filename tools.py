import json





def saveConfig(config, gamedata):
    gamedata["logger"].info("speichere Konfiguration")
    with open(r"config.ini", 'w') as f:
        config.write(f)

def getDictItem(dict, key_normal, key_localized="foo"):
    # liefert das Item, schaut zuerst nach dem
    # für die aktuelle Sprache, wenn nicht dann der English/Game Name
    # oder None - wenn nix vorhanden
    if key_localized in dict: return dict[key_localized] # -- .capitalize()
    if key_normal in dict: return dict[key_normal] # -- .capitalize()
    return "unnamed"

def convertTemperaturUnit(destination):
    if destination == "Celsius": return "C"
    if destination == "Fahrenheit": return "F"
    if destination == "Rankine": return "Ra"
    if destination == "Delisle": return "D"
    if destination == "Reaumur": return "Re"
    if destination == "Newton": return "N"
    if destination == "Romer": return "Ro"
    return "K"
def convertTemperatur(kelvin, destination):
    if destination == "Celsius": return convertTemperatur_Celcius(kelvin)
    if destination == "Fahrenheit": return convertTemperatur_Fahrenheit(kelvin)
    if destination == "Rankine": return convertTemperatur_Rankine(kelvin)
    if destination == "Delisle": return convertTemperatur_Delisle(kelvin)
    if destination == "Reaumur": return convertTemperatur_Reaumur(kelvin)
    if destination == "Newton": return convertTemperatur_Newton(kelvin)
    if destination == "Romer": return convertTemperatur_Romer(kelvin)
    return kelvin
def convertTemperatur_Celcius(kelvin):
    return kelvin - 273
def convertTemperatur_Fahrenheit(kelvin):
    return (kelvin - 273) * 9 / 5 + 32
def convertTemperatur_Rankine(kelvin):
    return (kelvin - 273) * 1.8 + 492
def convertTemperatur_Delisle(kelvin):
    return (kelvin - 273) * 1.5 - 100
def convertTemperatur_Reaumur(kelvin):
    return (kelvin - 273) * 0.8
def convertTemperatur_Newton(kelvin):
    return (kelvin - 273) * 0.33
def convertTemperatur_Romer(kelvin):
    return (kelvin - 273) * 0.525 + 7.5
