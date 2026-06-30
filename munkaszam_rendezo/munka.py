"""Munkaszám értelmezése és a mappa-/fájlnevek képzése.

A munkaszám alakja ``M`` + PONTOSAN három számjegy, utána (általában) egy ``/`` és egy
kétjegyű év, pl. ``M123/26``. Az ügyintéző a papírra úgyis ráírja az évet (a fizikai tárolás miatt),
ezért a LEÍRT ÉV az igazodási pont: ha szerepel, azt használjuk (így a digitális mappa
egyezik a papíros tárolással). Ha az évet nem írta oda, akkor egy tartalék évet kapunk
kívülről (a beállításból: alapértelmezett év, vagy ha az üres, a gép órája szerinti aktuális
év — ez automatikusan követi a 2027, 2028 … éveket is).

Ez a modul szándékosan tiszta: nincs hálózat, nincs fájlművelet, így könnyen tesztelhető.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

# M (kis/nagy) + PONTOSAN 3 számjegy, majd OPCIONÁLISAN egy elválasztó (/, -, _ vagy szóköz)
# és kétjegyű év. Ha az év szerepel, azt használjuk; ha nincs, a kívülről kapott tartalék évet.
# A TELJES szöveget illesztjük (^…$), hogy a 3-nál több (vagy kevesebb) jegyű szám — pl. egy
# beolvasási hiba miatti M1248 — NE csússzon át érvényesként (a vége levágásával M124-re).
_MUNKASZAM_RE = re.compile(r"^\s*[Mm]\s*(\d{3})(?:\s*[/\-_ ]\s*(\d{2}))?\s*$")

# Windowson tiltott karakterek fájl- és mappanevekben.
_TILTOTT_KARAKTEREK = r'<>:"/\|?*'


@dataclass(frozen=True)
class Munkaszam:
    """Egy értelmezett munkaszám: a szám része és a kétjegyű év."""

    szam: str  # pl. "123" (a vezető nullák megmaradnak, ha az ember úgy írta)
    ev: str  # pl. "24"

    @property
    def teljes_ev(self) -> str:
        """Négyjegyű év, pl. '2024'."""
        return f"20{self.ev}"

    @property
    def mappa_nev(self) -> str:
        """A munkaszám-mappa neve, pl. 'M123_24'."""
        return f"M{self.szam}_{self.ev}"

    def fajl_nev(self, sorszam: int) -> str:
        """A dokumentum fájlneve, pl. 'M123_24_001.pdf'."""
        return f"M{self.szam}_{self.ev}_{sorszam:03d}.pdf"

    def __str__(self) -> str:  # ember által olvasható, eredeti alak
        return f"M{self.szam}/{self.ev}"


def ertelmez_munkaszam(nyers: str | None, tartalek_ev: str) -> Munkaszam | None:
    """A nyers (kézírásból beolvasott) munkaszámból összeállít egy :class:`Munkaszam`-ot.

    A SZÁMOT mindig a kézírásból olvassuk. Az ÉVET is a kézírásból vesszük, ha le van írva
    (pl. ``M123/26`` -> 26); ha nincs leírva (pl. csak ``M123``), akkor a ``tartalek_ev``-et
    használjuk (a beállított alapértelmezett, vagy az aktuális év).
    Visszaad ``None``-t, ha a szövegben nincs ``M`` + szám alak.
    """
    if not nyers:
        return None
    talalat = _MUNKASZAM_RE.match(nyers)
    if not talalat:
        return None
    ev = talalat.group(2) or tartalek_ev
    return Munkaszam(szam=talalat.group(1), ev=ev)


def biztonsagos_mappanev(nev: str) -> str:
    """Windowson is használható mappanevet képez a partnernévből.

    Az ékezeteket meghagyja (a Windows támogatja), csak a tiltott karaktereket
    cseréli szóközre, és levágja a végén lévő pontokat/szóközöket (amiket a Windows nem enged).
    """
    nev = unicodedata.normalize("NFC", nev.strip())
    tisztitott = "".join(" " if karakter in _TILTOTT_KARAKTEREK else karakter for karakter in nev)
    # több szóköz összevonása + végek levágása (a Windows nem enged pont/szóköz véget)
    tisztitott = re.sub(r"\s+", " ", tisztitott).strip().rstrip(".")
    return tisztitott or "ismeretlen_partner"
