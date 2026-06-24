"""Egy oldal jobb felső sarkának képpé alakítása (PyMuPDF).

Csak a sarkot rendereljük, ahol a kézírásos felirat van — így a Claude hívás olcsó marad,
és a beolvasás is pontosabb, mert nem zavar a többi tartalom.
"""

from __future__ import annotations

import fitz  # PyMuPDF


def sarok_png(
    oldal: "fitz.Page",
    dpi: int = 200,
    szelesseg_arany: float = 0.45,
    magassag_arany: float = 0.18,
) -> bytes:
    """Az oldal jobb felső sarkát PNG képként adja vissza (bájtok).

    ``szelesseg_arany``: a kép a lap jobb oldali ~45%-át fogja át.
    ``magassag_arany``: a lap felső ~18%-át.
    A ``dpi`` a felbontás; nagyobb érték a kézírást olvashatóbbá teszi, de drágább.
    Az oldal forgatását a PyMuPDF automatikusan figyelembe veszi.
    """
    teglalap = oldal.rect
    bal = teglalap.x0 + teglalap.width * (1.0 - szelesseg_arany)
    also = teglalap.y0 + teglalap.height * magassag_arany
    vagas = fitz.Rect(bal, teglalap.y0, teglalap.x1, also)

    matrix = fitz.Matrix(dpi / 72.0, dpi / 72.0)
    pixmap = oldal.get_pixmap(matrix=matrix, clip=vagas)
    return pixmap.tobytes("png")
