"""A jobb felső sarok beolvasása Claude vision segítségével.

Egy oldal sarkának PNG képét elküldjük a modellnek, és strukturált választ kérünk:
van-e felirat, mi a partner neve, mi a munkaszám, és mennyire megbízható a beolvasás.
"""

from __future__ import annotations

import base64
from typing import Literal, Optional

import anthropic
from pydantic import BaseModel


class SarokOlvasat(BaseModel):
    """A modell strukturált válasza egy oldal sarkáról."""

    van_felirat: bool
    partner: Optional[str] = None
    munkaszam: Optional[str] = None  # ahogy le van írva, pl. "M123/24"
    megbizhatosag: Literal["magas", "alacsony"] = "alacsony"


_UTASITAS = (
    "Ez egy beszkennelt magyar dokumentum oldalának a JOBB FELSŐ SARKA. "
    "Az ügyintéző ide kézzel ráírhatta a PARTNER nevét (cég vagy személy) és egy "
    "MUNKASZÁMOT, ami 'M' betűvel és számjegyekkel kezdődik (pl. M123). Néha egy '/' és egy "
    "kétjegyű év is szerepel (pl. M123/26) — ha látod, írd bele, de a lényeg az M és a szám. "
    "A munkaszámot úgy add vissza, ahogy le van írva (pl. 'M123/26' vagy 'M123'). "
    "FONTOS: csak a KÉZZEL ÍRT feliratot vedd figyelembe. A nyomtatott elemeket — céges "
    "fejléc/logó, e-mail cím, weboldal, előre nyomtatott sorszám vagy iktatószám, bélyegző — "
    "HAGYD FIGYELMEN KÍVÜL, még ha számokat is tartalmaznak. "
    "Ha a sarokban NINCS ilyen kézírásos felirat (üres vagy csak nyomtatott szöveg van), "
    "akkor van_felirat=false, a partner és a munkaszam pedig null. "
    "A megbizhatosag legyen 'alacsony', ha a kézírás nehezen olvasható vagy bizonytalan vagy."
)


def kliens(api_kulcs: str) -> "anthropic.Anthropic":
    """Létrehoz egy Anthropic klienst a megadott API kulccsal."""
    return anthropic.Anthropic(api_key=api_kulcs)


def olvas(
    kl: "anthropic.Anthropic",
    modell: str,
    png_bytes: bytes,
) -> SarokOlvasat:
    """Egy sarok-képet beolvas és strukturált eredményt ad vissza."""
    kep_base64 = base64.standard_b64encode(png_bytes).decode("ascii")
    valasz = kl.messages.parse(
        model=modell,
        max_tokens=512,
        output_format=SarokOlvasat,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": kep_base64,
                        },
                    },
                    {"type": "text", "text": _UTASITAS},
                ],
            }
        ],
    )
    eredmeny = valasz.parsed_output
    if eredmeny is None:  # nagyon ritka: a modell nem adott érvényes választ
        return SarokOlvasat(van_felirat=False)
    return eredmeny
