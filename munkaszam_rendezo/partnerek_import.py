"""Partnerlista importálása a számlázó program exportjából (Excel vagy CSV).

A számlázó programból kijövő táblázatnak több oszlopa van; a felhasználó az ablakban
kiválasztja, melyik oszlop tartalmazza a partner nevét. Ez a modul a fájl beolvasásáért
és az oszlopértékek kinyeréséért felel — a tényleges kiválasztás az ablakban történik.

Támogatott: ``.xlsx`` (openpyxl) és ``.csv``. A CSV-nél a magyar Excel-exportokra jellemző
pontosvessző elválasztót és a közép-európai (cp1250) kódolást is kezeljük.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path


def oszlopok_beolvas(utvonal: str | Path) -> tuple[list[str], list[list[str]]]:
    """Beolvassa a fájlt, és visszaadja: (fejlécek, sorok).

    Az első sort tekinti fejlécnek. Minden cellát szöveggé alakít és levág.
    A kiterjesztés alapján dönti el, hogy Excel vagy CSV.
    """
    ut = Path(utvonal)
    if ut.suffix.lower() in (".xlsx", ".xlsm"):
        return _excel_beolvas(ut)
    return _csv_beolvas(ut)


def oszlop_ertekei(fejlecek: list[str], sorok: list[list[str]], oszlop_nev: str) -> list[str]:
    """Egy megnevezett oszlop nem üres, egyedi értékei, az első előfordulás sorrendjében."""
    try:
        index = fejlecek.index(oszlop_nev)
    except ValueError:
        return []
    latott: set[str] = set()
    eredmeny: list[str] = []
    for sor in sorok:
        if index < len(sor):
            ertek = sor[index].strip()
            if ertek and ertek not in latott:
                latott.add(ertek)
                eredmeny.append(ertek)
    return eredmeny


# --------------------------------------------------------------------------- Excel
def _excel_beolvas(ut: Path) -> tuple[list[str], list[list[str]]]:
    try:
        import openpyxl  # lazy import: csak Excel esetén kell
    except ImportError as hiba:  # érthető üzenet, ha hiányzik a csomag
        raise RuntimeError(
            "Az Excel (.xlsx) importhoz az 'openpyxl' csomag kell. "
            "Futtasd a telepites.bat-ot, vagy mentsd a fájlt CSV formátumban."
        ) from hiba

    munkafuzet = openpyxl.load_workbook(str(ut), read_only=True, data_only=True)
    lap = munkafuzet.active
    sorok_nyers = list(lap.iter_rows(values_only=True))
    munkafuzet.close()
    if not sorok_nyers:
        return [], []

    def cella(ertek) -> str:
        return "" if ertek is None else str(ertek).strip()

    fejlecek = [cella(c) for c in sorok_nyers[0]]
    sorok = [[cella(c) for c in sor] for sor in sorok_nyers[1:]]
    return fejlecek, sorok


# ----------------------------------------------------------------------------- CSV
def _csv_beolvas(ut: Path) -> tuple[list[str], list[list[str]]]:
    nyers = ut.read_bytes()
    # kódolás: előbb UTF-8 (BOM-mal is), majd a windowsos közép-európai cp1250
    for kodolas in ("utf-8-sig", "cp1250", "latin-1"):
        try:
            szoveg = nyers.decode(kodolas)
            break
        except UnicodeDecodeError:
            continue
    else:
        szoveg = nyers.decode("utf-8", errors="replace")

    elvalaszto = _elvalaszto_kitalal(szoveg)
    olvaso = csv.reader(io.StringIO(szoveg), delimiter=elvalaszto)
    sorok_nyers = [sor for sor in olvaso if any(cella.strip() for cella in sor)]
    if not sorok_nyers:
        return [], []

    fejlecek = [c.strip() for c in sorok_nyers[0]]
    sorok = [[c.strip() for c in sor] for sor in sorok_nyers[1:]]
    return fejlecek, sorok


def _elvalaszto_kitalal(szoveg: str) -> str:
    """Megpróbálja kitalálni a CSV elválasztót (pontosvessző, vessző, tab)."""
    elso_sor = szoveg.splitlines()[0] if szoveg.splitlines() else ""
    jeloltek = {";": elso_sor.count(";"), ",": elso_sor.count(","), "\t": elso_sor.count("\t")}
    legjobb = max(jeloltek, key=jeloltek.get)
    return legjobb if jeloltek[legjobb] > 0 else ","
