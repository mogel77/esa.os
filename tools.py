import json





def saveConfig(config, gamedata):
    gamedata["logger"].info("speichere Konfiguration")
    with open(r"config.ini", 'w') as f:
        config.write(f)

def getDictItem(dict, key_normal, key_localized="foo"):
    # liefert das Item, schaut zuerst nach dem
    # für die aktuelle Sprache, wenn nicht dann der English/Game Name
    # oder None - wenn nix vorhanden
    if key_localized in dict: return dict[key_localized].capitalize()
    if key_normal in dict: return dict[key_normal].capitalize()
    return "unnamed"
