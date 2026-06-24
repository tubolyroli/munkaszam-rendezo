"""A beállítások (config.json) betöltése és mentése.

A beállításfájl a program mellett, a felhasználó gépén él. Tartalma:
  - api_kulcs   : a Claude API kulcs (kezdetben helykitöltő, később beillesztjük)
  - cel_mappa   : ahova a rendezett Partner-mappák kerülnek (egyszer kiválasztva, megjegyezve)
  - partnerek   : az ismert partnerek listája (a felirat-illesztéshez)
  - modell      : melyik Claude modellt használjuk (alapból a legpontosabb)
  - alapertelmezett_ev : a munkaszámokhoz használt kétjegyű év (üres = az aktuális év)
  - sarok_szelesseg_arany / sarok_magassag_arany : mekkora sarkot olvasunk be
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

API_KULCS_HELYKITOLTO = "IDE_JON_A_KULCS"


def aktualis_ev() -> str:
    """Az aktuális év két számjegye, pl. '26'."""
    return date.today().strftime("%y")


@dataclass
class Beallitasok:
    """A program beállításai."""

    api_kulcs: str = API_KULCS_HELYKITOLTO
    cel_mappa: str = ""  # üres = még nincs kiválasztva
    partnerek: list[str] = field(default_factory=list)
    modell: str = "claude-opus-4-8"
    alapertelmezett_ev: str = ""  # üres = az aktuális évet használja
    sarok_szelesseg_arany: float = 0.45
    sarok_magassag_arany: float = 0.18

    @property
    def tartalek_ev(self) -> str:
        """Tartalék kétjegyű év, AMIKOR a munkaszámban nincs leírva az év.
        A beállított alapértelmezett évet adja, vagy ha az üres, a gép szerinti aktuális évet
        (így automatikusan követi a 2027, 2028 … éveket is)."""
        return self.alapertelmezett_ev.strip() or aktualis_ev()

    @property
    def van_api_kulcs(self) -> bool:
        return bool(self.api_kulcs) and self.api_kulcs != API_KULCS_HELYKITOLTO

    @property
    def van_cel_mappa(self) -> bool:
        return bool(self.cel_mappa) and Path(self.cel_mappa).is_dir()


def alap_utvonal() -> Path:
    """A config.json alapértelmezett helye: a csomag melletti mappában."""
    return Path(__file__).resolve().parent.parent / "config.json"


def betolt(utvonal: str | Path | None = None) -> Beallitasok:
    """Beolvassa a beállításokat. Ha a fájl nem létezik, alapértelmezést ad vissza."""
    ut = Path(utvonal) if utvonal else alap_utvonal()
    if not ut.exists():
        return Beallitasok()
    adat = json.loads(ut.read_text(encoding="utf-8"))
    ismert = {mezo for mezo in Beallitasok().__dict__}
    szurt = {kulcs: ertek for kulcs, ertek in adat.items() if kulcs in ismert}
    return Beallitasok(**szurt)


def ment(beallitasok: Beallitasok, utvonal: str | Path | None = None) -> None:
    """Elmenti a beállításokat olvasható (behúzott) JSON-ként, UTF-8-ban."""
    ut = Path(utvonal) if utvonal else alap_utvonal()
    ut.write_text(
        json.dumps(asdict(beallitasok), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
