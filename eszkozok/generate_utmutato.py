"""A magyar használati útmutató (docs/Hasznalati_utmutato.md) PDF-be renderelése.

A PDF helyes magyar ékezetekkel (ő, ű is) készül egy Unicode TTF betűtípussal.
Az útmutató Markdown-részhalmazát közvetlenül, soronként rendereljük (nem HTML-en át),
hogy a tördelés rendben legyen (ne kerüljenek listaelemek külön, üres oldalakra).

Futtatás:  python eszkozok/generate_utmutato.py
Eredmény:  output/Hasznalati_utmutato.pdf
"""

from __future__ import annotations

import re
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

# Ez a fájl az eszkozok\ mappában van; a repo gyökere egy szinttel feljebb.
GYOKER = Path(__file__).resolve().parent.parent
FORRAS = GYOKER / "docs" / "Hasznalati_utmutato.md"
KIMENET = GYOKER / "output" / "Hasznalati_utmutato.pdf"

# macOS-en elérhető Unicode betűtípus (tartalmazza az ő, ű karaktereket is)
ARIAL = "/System/Library/Fonts/Supplemental/Arial.ttf"
ARIAL_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

BAL_MARGO = 18


def _tisztit(szoveg: str) -> str:
    """A backtick-eket eltávolítja (a **félkövért** meghagyja az fpdf markdownjának)."""
    return szoveg.replace("`", "")


def renderel(pdf: FPDF, markdown: str) -> None:
    kodban = False
    for nyers_sor in markdown.splitlines():
        if nyers_sor.strip().startswith("```"):
            kodban = not kodban
            if kodban:
                pdf.ln(1)
                pdf.set_font("Courier", size=9.5)
            else:
                pdf.set_font("Arial", size=11)
                pdf.ln(1)
            continue

        if kodban:  # kódblokk: monospace, behúzva, sorról sorra
            pdf.set_x(BAL_MARGO + 4)
            pdf.cell(0, 4.6, nyers_sor.rstrip(), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            continue

        sor = nyers_sor.rstrip()
        if not sor:
            pdf.ln(2.5)
            continue

        pdf.set_x(BAL_MARGO)
        if sor.startswith("# "):
            pdf.set_font("Arial", "B", 16)
            pdf.multi_cell(0, 8, _tisztit(sor[2:].strip()), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(2)
            pdf.set_font("Arial", size=11)
        elif sor.startswith("## "):
            pdf.ln(2)
            pdf.set_font("Arial", "B", 13)
            pdf.multi_cell(0, 7, _tisztit(sor[3:].strip()), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(1)
            pdf.set_font("Arial", size=11)
        elif re.match(r"^\d+\.\s", sor):  # számozott lépés
            pdf.set_font("Arial", size=11)
            pdf.multi_cell(0, 5.6, _tisztit(sor.strip()), markdown=True,
                           new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        elif sor.lstrip().startswith("- "):  # felsorolás (a behúzás szintez)
            behuzas_szint = (len(sor) - len(sor.lstrip())) // 2
            pdf.set_font("Arial", size=11)
            pdf.set_x(BAL_MARGO + 3 + behuzas_szint * 4)
            pdf.multi_cell(0, 5.6, "•  " + _tisztit(sor.lstrip()[2:]), markdown=True,
                           new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        else:  # sima bekezdés
            pdf.set_font("Arial", size=11)
            pdf.multi_cell(0, 5.6, _tisztit(sor), markdown=True,
                           new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def main() -> None:
    md = FORRAS.read_text(encoding="utf-8")
    pdf = FPDF()
    pdf.add_font("Arial", style="", fname=ARIAL)
    pdf.add_font("Arial", style="B", fname=ARIAL_BOLD)
    pdf.set_margins(BAL_MARGO, 16, BAL_MARGO)
    pdf.set_auto_page_break(True, margin=16)
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    renderel(pdf, md)

    KIMENET.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(KIMENET))
    print(f"Elkészült: {KIMENET}")


if __name__ == "__main__":
    main()
