"""A program magját ellenőrző tesztek (valódi szkennelt fájl és hálózat nélkül).

Futtatás a projekt gyökeréből:  python tests/test_core.py
A teszt szintetikus PDF-et készít, így a szétválogatás és a mentés logikája
ellenőrizhető anélkül, hogy felirattal ellátott valódi dokumentumokra várnánk.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import fitz  # PyMuPDF

from munkaszam_rendezo import config as cfg
from munkaszam_rendezo import filer, grouping, munka, partnerek_import, partners


def test_munkaszam_ertelmezes() -> None:
    # ha az ÉV le van írva, AZT használjuk (a papíros tárolással egyezik)
    m = munka.ertelmez_munkaszam("M123/26", "99")  # tartalék "99" nem számít, mert van leírt év
    assert m is not None and m.szam == "123" and m.ev == "26"
    assert m.mappa_nev == "M123_26"
    assert m.teljes_ev == "2026"
    assert m.fajl_nev(1) == "M123_26_001.pdf"
    assert m.fajl_nev(42) == "M123_26_042.pdf"
    # leírt év nyer akkor is, ha az nem az aktuális (pl. egy 2025-ös munka)
    assert munka.ertelmez_munkaszam("M124/25", "26").mappa_nev == "M124_25"
    # ha NINCS leírva év -> a tartalék évet használja
    assert munka.ertelmez_munkaszam("M070", "26").mappa_nev == "M070_26"
    # rugalmas elválasztó a leírt évhez
    assert munka.ertelmez_munkaszam("M 045 - 26", "99").mappa_nev == "M045_26"
    # vezető nulla megmarad
    assert munka.ertelmez_munkaszam("M007/26", "26").mappa_nev == "M007_26"
    # hibás alakok (nincs M + szám)
    assert munka.ertelmez_munkaszam("123/26", "26") is None
    assert munka.ertelmez_munkaszam("", "26") is None
    assert munka.ertelmez_munkaszam(None, "26") is None
    # PONTOSAN 3 számjegy kell: a 4 jegyű (pl. beolvasási hibás) és a 2 jegyű is hibás,
    # és NEM csonkul érvényessé (a 'M1248' nem lesz 'M124')
    assert munka.ertelmez_munkaszam("M1248/26", "26") is None
    assert munka.ertelmez_munkaszam("M12/26", "26") is None
    assert munka.ertelmez_munkaszam("M1234", "26") is None


def test_biztonsagos_mappanev() -> None:
    assert munka.biztonsagos_mappanev("Kovács Bt.") == "Kovács Bt"
    assert munka.biztonsagos_mappanev('A/B: "C"') == "A B C"
    assert munka.biztonsagos_mappanev("   ") == "ismeretlen_partner"


def test_partner_illesztes() -> None:
    ismert = ["Kovács Bt.", "Nagy és Társa Kft.", "Szabó Árpád"]
    # ékezet- és kisbetű-érzéketlen közelítés
    assert partners.illeszt_partner("kovacs bt", ismert) == "Kovács Bt."
    assert partners.illeszt_partner("Szabo Arpad", ismert) == "Szabó Árpád"
    # túl messze -> nincs találat (új partner)
    assert partners.illeszt_partner("Teljesen Más Zrt.", ismert) is None
    assert partners.illeszt_partner(None, ismert) is None

    # RÖVID kézírásos név -> TELJES cégnév (a számlázós valós eset)
    cegek = [
        "Grundfos South East Europe Kft.",
        "BERNER KFT",
        "Profilaxis Kft.",
        "PROFILAXIS KFT EUR",
        "PROFILAXIS PUMP AND CONTROL SRL",
        "FGFZRT",
    ]
    assert partners.illeszt_partner("Grundfos", cegek) == "Grundfos South East Europe Kft."
    assert partners.illeszt_partner("Berner", cegek) == "BERNER KFT"
    # több cég tartalmazza a "Profilaxis" szót -> a legrövidebbet (legszorosabbat) választja
    assert partners.illeszt_partner("Profilaxis", cegek) == "Profilaxis Kft."
    # karakter-szintű tartalmazás (a "FGF" benne van a "FGFZRT"-ben)
    assert partners.illeszt_partner("FGF", cegek) == "FGFZRT"


def test_dokumentumokra_bontas() -> None:
    def sor(pdf, idx, uj, partner=None, munka_sz=None):
        return grouping.OldalSor(pdf, idx, uj, partner, munka_sz)

    # 1. dok: 3 oldal; 2. dok: 1 oldal (UGYANAZ a partner+munkaszám, mégis külön dokumentum)
    sorok = [
        sor("a.pdf", 0, True, "Kovács Bt.", "M1/24"),
        sor("a.pdf", 1, False),
        sor("a.pdf", 2, False),
        sor("a.pdf", 3, True, "Kovács Bt.", "M1/24"),
    ]
    dokik = grouping.dokumentumokra_bont(sorok)
    assert len(dokik) == 2
    assert len(dokik[0].oldalak) == 3
    assert len(dokik[1].oldalak) == 1
    assert dokik[1].partner == "Kovács Bt."

    # ha az első oldalon nincs felirat, akkor is létrejön egy (javítandó) dokumentum
    sorok2 = [sor("b.pdf", 0, False), sor("b.pdf", 1, True, "X", "M2/25")]
    dokik2 = grouping.dokumentumokra_bont(sorok2)
    assert len(dokik2) == 2
    assert dokik2[0].partner is None


def test_filer_mentes_es_sorszamozas() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        # szintetikus 4 oldalas forrás PDF
        forras_ut = tmp / "beolvasott.pdf"
        doc = fitz.open()
        for _ in range(4):
            doc.new_page()
        doc.save(str(forras_ut))
        doc.close()
        forras_meret = forras_ut.stat().st_size

        cel = tmp / "rendezett"
        m = munka.ertelmez_munkaszam("M009/24", "24")
        feladatok = [
            filer.MentesiFeladat("Kovács Bt.", m, [(str(forras_ut), 0), (str(forras_ut), 1)]),
            filer.MentesiFeladat("Kovács Bt.", m, [(str(forras_ut), 2)]),  # ugyanaz a munkaszám
        ]
        eredmenyek = filer.ment(feladatok, cel)
        assert len(eredmenyek) == 2

        mappa = cel / "Kovács Bt" / "2024" / "M009_24"
        assert (mappa / "M009_24_001.pdf").exists()
        assert (mappa / "M009_24_002.pdf").exists()
        # az első dokumentum 2 oldalas, a második 1
        assert fitz.open(str(mappa / "M009_24_001.pdf")).page_count == 2
        assert fitz.open(str(mappa / "M009_24_002.pdf")).page_count == 1

        # újabb mentés -> a sorszám folytatódik, nem ír felül
        filer.ment([filer.MentesiFeladat("Kovács Bt.", m, [(str(forras_ut), 3)])], cel)
        assert (mappa / "M009_24_003.pdf").exists()

        # a forrás PDF érintetlen
        assert forras_ut.stat().st_size == forras_meret


def test_partner_import_csv() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        ut = Path(tmp) / "export.csv"
        # magyar Excel-export jellegű: pontosvessző elválasztó, cp1250 kódolás, több oszlop
        tartalom = (
            "Azonosító;Partner név;Adószám\n"
            "1;Kovács Bt.;111\n"
            "2;Nagy és Társa Kft.;222\n"
            "3;Kovács Bt.;111\n"  # ismétlődés -> egyszer szerepeljen
            "4;;333\n"  # üres név -> kimarad
        )
        ut.write_bytes(tartalom.encode("cp1250"))
        fejlecek, sorok = partnerek_import.oszlopok_beolvas(ut)
        assert fejlecek == ["Azonosító", "Partner név", "Adószám"]
        ertekek = partnerek_import.oszlop_ertekei(fejlecek, sorok, "Partner név")
        assert ertekek == ["Kovács Bt.", "Nagy és Társa Kft."]


def test_partner_import_xlsx() -> None:
    import openpyxl

    with tempfile.TemporaryDirectory() as tmp:
        ut = Path(tmp) / "export.xlsx"
        wb = openpyxl.Workbook()
        lap = wb.active
        lap.append(["Azonosító", "Partner", "Város"])
        lap.append([1, "Szabó Árpád", "Győr"])
        lap.append([2, "Tóth és Fiai Zrt.", "Pécs"])
        lap.append([3, None, "Eger"])  # üres név -> kimarad
        wb.save(str(ut))
        fejlecek, sorok = partnerek_import.oszlopok_beolvas(ut)
        assert "Partner" in fejlecek
        ertekek = partnerek_import.oszlop_ertekei(fejlecek, sorok, "Partner")
        assert ertekek == ["Szabó Árpád", "Tóth és Fiai Zrt."]


def test_ev_beallitas() -> None:
    # üres alapértelmezett tartalék-év -> az aktuális évet használja (órától, követi 2027/28-at)
    assert cfg.Beallitasok(alapertelmezett_ev="").tartalek_ev == cfg.aktualis_ev()
    # beállított tartalék-év -> azt használja
    assert cfg.Beallitasok(alapertelmezett_ev="26").tartalek_ev == "26"
    assert len(cfg.aktualis_ev()) == 2 and cfg.aktualis_ev().isdigit()


def main() -> None:
    tesztek = [
        test_munkaszam_ertelmezes,
        test_biztonsagos_mappanev,
        test_partner_illesztes,
        test_dokumentumokra_bontas,
        test_filer_mentes_es_sorszamozas,
        test_partner_import_csv,
        test_partner_import_xlsx,
        test_ev_beallitas,
    ]
    for teszt in tesztek:
        teszt()
        print(f"OK  {teszt.__name__}")
    print(f"\nMind a {len(tesztek)} teszt sikeres.")


if __name__ == "__main__":
    main()
