"""A kész dokumentumok mappákba mentése.

A bemeneti PDF-eket nem módosítja: minden dokumentumot új PDF-be másol, az eredeti
oldalakat veszteség nélkül (a szkennelt minőség megmarad). A mappaszerkezet:

    <cél>/<Partner>/<év>/<M###_YY>/M###_YY_NNN.pdf

Ha a munkaszám-mappában már van fájl, a sorszámozás onnan folytatódik (nem ír felül semmit).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF

from .munka import Munkaszam, biztonsagos_mappanev


@dataclass
class MentesiFeladat:
    """Egy menteni kívánt dokumentum: a partner, a munkaszám és az oldalai."""

    partner: str  # végleges partnernév (ékezetes is lehet)
    munkaszam: Munkaszam
    oldalak: list[tuple[str, int]]  # (forrás PDF útja, 0-tól számozott oldalszám)


@dataclass
class MentesiEredmeny:
    """Egy elmentett dokumentum eredménye."""

    utvonal: Path
    oldalszam: int


def _kovetkezo_sorszam(mappa: Path, munkaszam: Munkaszam) -> int:
    """A munkaszám-mappa következő szabad sorszáma (a meglévő fájlok után)."""
    minta = re.compile(rf"^M{re.escape(munkaszam.szam)}_{re.escape(munkaszam.ev)}_(\d+)\.pdf$")
    legnagyobb = 0
    if mappa.exists():
        for fajl in mappa.iterdir():
            talalat = minta.match(fajl.name)
            if talalat:
                legnagyobb = max(legnagyobb, int(talalat.group(1)))
    return legnagyobb + 1


def ment(feladatok: list[MentesiFeladat], cel_mappa: str | Path) -> list[MentesiEredmeny]:
    """Az összes dokumentumot a célmappa megfelelő almappáiba menti.

    A forrás PDF-eket csak olvassa. Visszaadja a létrehozott fájlok listáját.
    """
    cel = Path(cel_mappa)
    megnyitott: dict[str, fitz.Document] = {}
    eredmenyek: list[MentesiEredmeny] = []

    try:
        for feladat in feladatok:
            partner_mappa = biztonsagos_mappanev(feladat.partner)
            celhely = cel / partner_mappa / feladat.munkaszam.teljes_ev / feladat.munkaszam.mappa_nev
            celhely.mkdir(parents=True, exist_ok=True)

            sorszam = _kovetkezo_sorszam(celhely, feladat.munkaszam)
            kimenet = fitz.open()
            try:
                for forras_ut, oldal_index in feladat.oldalak:
                    if forras_ut not in megnyitott:
                        megnyitott[forras_ut] = fitz.open(forras_ut)
                    forras = megnyitott[forras_ut]
                    kimenet.insert_pdf(forras, from_page=oldal_index, to_page=oldal_index)

                fajl_ut = celhely / feladat.munkaszam.fajl_nev(sorszam)
                kimenet.save(str(fajl_ut))
                eredmenyek.append(MentesiEredmeny(utvonal=fajl_ut, oldalszam=len(feladat.oldalak)))
            finally:
                kimenet.close()
    finally:
        for doc in megnyitott.values():
            doc.close()

    return eredmenyek
