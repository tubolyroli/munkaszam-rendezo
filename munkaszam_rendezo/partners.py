"""Partnernév illesztése a már ismert partnerek listájához.

Cél: ne jöjjön létre ugyanannak a partnernek több, kissé eltérően írt mappája
("Kovács Bt", "Kovacs bt.", "Kovács Béta"). A kézírásból beolvasott nevet a legközelebbi
ismert partnerhez illesztjük, a felhasználó pedig az ablakban megerősíti vagy újat ad meg.

Tiszta logika: nincs hálózat, nincs fájl.
"""

from __future__ import annotations

import difflib
import unicodedata


def _kulcs(nev: str) -> str:
    """Összehasonlító kulcs: kisbetűs, ékezet nélküli, egyszeres szóközű alak."""
    nev = unicodedata.normalize("NFKD", nev)
    nev = "".join(karakter for karakter in nev if not unicodedata.combining(karakter))
    return " ".join(nev.lower().split())


def illeszt_partner(
    nyers_nev: str | None, ismert_partnerek: list[str], kuszob: float = 0.84
) -> str | None:
    """A beolvasott nevet a legközelebbi ismert partnerhez illeszti.

    Visszaadja a megtalált ismert partner *eredeti* (ékezetes) nevét, vagy ``None``,
    ha nincs elég közeli találat. Az illesztés ékezet- és kisbetű-érzéketlen.

    A gyakorlatban az ügyintéző RÖVID nevet ír (pl. "Grundfos"), a számlázóban viszont
    a TELJES cégnév van (pl. "Grundfos South East Europe Kft."). Ezért a logika:
      1. szó- vagy karakter-szintű TARTALMAZÁS (a beírt név benne van a cégnévben) —
         több találat esetén a legrövidebb (a beírthoz legközelebbi) cégnevet választja;
      2. ha az nincs, akkor difflib hasonlóság (elgépelések kezelésére).
    """
    if not nyers_nev or not ismert_partnerek:
        return None

    nyers_kulcs = _kulcs(nyers_nev)
    if not nyers_kulcs:
        return None

    parok = [(_kulcs(p), p) for p in ismert_partnerek]
    nyers_szavak = set(nyers_kulcs.split())
    nyers_szokoz_nelkul = nyers_kulcs.replace(" ", "")

    # 1. tartalmazás: a beírt szó(ak) a cégnév szavai között, vagy karakterláncként benne
    tartalmazok: list[tuple[str, str]] = []
    for kulcs, eredeti in parok:
        if not kulcs:
            continue
        szavak = set(kulcs.split())
        szo_egyezes = nyers_szavak <= szavak
        # a karakter-szintű tartalmazást csak >=3 hosszú beírtnál engedjük (kevesebb téves)
        karakter_egyezes = (
            len(nyers_szokoz_nelkul) >= 3 and nyers_szokoz_nelkul in kulcs.replace(" ", "")
        )
        if szo_egyezes or karakter_egyezes:
            tartalmazok.append((kulcs, eredeti))
    if tartalmazok:
        tartalmazok.sort(key=lambda par: len(par[0]))  # legrövidebb = legszorosabb
        return tartalmazok[0][1]

    # 2. difflib hasonlóság (elgépelések)
    kulcs_szerint = {kulcs: eredeti for kulcs, eredeti in parok}
    talalatok = difflib.get_close_matches(
        nyers_kulcs, list(kulcs_szerint.keys()), n=1, cutoff=kuszob
    )
    if not talalatok:
        return None
    return kulcs_szerint[talalatok[0]]
