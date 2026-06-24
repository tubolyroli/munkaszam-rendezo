"""Oldalakból dokumentumok képzése.

A szabály: egy oldal, amelynek a jobb felső sarkában megjelenik egy munkaszám+partner
felirat (``uj_dokumentum=True``), egy ÚJ dokumentum első oldala. A felirat nélküli
oldalak (``uj_dokumentum=False``) az előttük lévő dokumentumhoz tartoznak.

Ez a modul tiszta logika: nincs PDF, nincs hálózat, így könnyen tesztelhető.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class OldalSor:
    """Egy oldal a felülvizsgáló táblázatban.

    A mezők a felhasználói ablak állapotát tükrözik: a kipipálható "Új dokumentum",
    a partner és a munkaszám az ablakban módosítható, ezért ezekből számoljuk a dokumentumokat.
    """

    forras_pdf: str  # a bemeneti PDF elérési útja
    oldal_index: int  # 0-tól számozott oldalszám a forrás PDF-ben
    uj_dokumentum: bool  # itt kezdődik-e új dokumentum
    partner: str | None = None
    munkaszam: str | None = None  # nyers szöveg, pl. "M123/24"
    megbizhato: bool = True  # alacsony megbízhatóság -> az ablakban kiemeljük


@dataclass
class Dokumentum:
    """Egy összetartozó, több oldalból álló dokumentum."""

    partner: str | None
    munkaszam: str | None
    oldalak: list[OldalSor] = field(default_factory=list)


def dokumentumokra_bont(sorok: list[OldalSor]) -> list[Dokumentum]:
    """A per-oldal sorokból összeállítja a dokumentumok listáját.

    Minden ``uj_dokumentum=True`` oldal új dokumentumot kezd. A felirat nélküli
    oldalak az aktuális dokumentumhoz csatlakoznak. Ha az első oldalon nincs felirat
    (pl. szkennelési hiba), akkor is létrejön egy dokumentum partner/munkaszám nélkül,
    amit a felhasználó az ablakban tud javítani.
    """
    dokumentumok: list[Dokumentum] = []
    for sor in sorok:
        if sor.uj_dokumentum or not dokumentumok:
            dokumentumok.append(
                Dokumentum(partner=sor.partner, munkaszam=sor.munkaszam, oldalak=[sor])
            )
        else:
            dokumentumok[-1].oldalak.append(sor)
    return dokumentumok
