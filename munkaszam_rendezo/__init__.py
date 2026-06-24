"""Munkaszám-rendező — beszkennelt dokumentumok szétválogatása partner és munkaszám szerint.

A csomag moduljai külön-külön is tesztelhetők:
  - munka.py     : munkaszám értelmezése és a mappa-/fájlnevek képzése (nincs hálózat, nincs fájl)
  - corner.py    : egy oldal jobb felső sarkának képpé alakítása (PyMuPDF)
  - reader.py    : a sarok beolvasása Claude vision segítségével
  - grouping.py  : oldalakból dokumentumok képzése (tiszta logika)
  - partners.py  : partnernév illesztése a smert partnerek listájához
  - filer.py     : a kész dokumentumok mappákba mentése (PyMuPDF, lapok másolása)
  - config.py    : a beállítások (config.json) betöltése/mentése
  - app.py       : a kattintható ablak, ami mindezt összeköti
"""

__version__ = "1.0.0"
