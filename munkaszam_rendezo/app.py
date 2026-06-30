"""A kattintható ablak (Tkinter), ami az egészet összeköti — magyar nyelven.

Folyamat:
  1. "Válassz PDF(ek)et" — kiválasztja a beszkennelt fájl(oka)t.
  2. A program a Claude segítségével beolvassa minden oldal sarkát, és felépít egy
     táblázatot: oldalanként egy sor, kis kép a sarokról, "Új dokumentum" pipa,
     partner (legördülő) és munkaszám. A bizonytalan beolvasásokat kiemeli.
  3. "Dokumentumok mentése" — a megerősített adatok alapján mappákba rendezi a fájlokat.
"""

from __future__ import annotations

import base64
import math
import os
import queue
import subprocess
import sys
import threading
import traceback
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import fitz  # PyMuPDF

from . import config as config_modul
from . import corner, filer, grouping, munka, partners, partnerek_import, reader

ALACSONY_SZIN = "#fff3cd"  # halvány sárga: figyelmet igénylő munkaszám-mező
PARTNER_HIANYZIK_SZIN = "#ffb3b3"  # piros: hiányzó (még kiválasztandó) partner

# A táblázat oszlopai: (fejléc, fix szélesség képpontban). A fejléc ÉS a sorok ugyanezt a
# fix szélességet használják (grid + columnconfigure minsize), így a fejléc mindig pontosan
# a megfelelő oszlop fölött van, és a változó szélességű kis kép sem tolja el a többit.
OSZLOPOK = (
    ("Oldal", 70),
    ("Sarok", 270),
    ("Új dokumentum", 110),
    ("Partner", 240),
    ("Munkaszám", 110),
    ("Teendő", 320),
)


class PartnerMezo(ttk.Frame):
    """Partner beviteli mező automatikus kiegészítéssel.

    Egy ``tk.Entry`` (megbízhatóan színezhető: hiányzó partnernél piros) és egy alatta
    felugró lista. Gépelés közben AZONNAL megjelennek a lehetséges partnerek, ebben a
    sorrendben: előbb azok, amelyek a beírt szöveggel KEZDŐDNEK, alattuk azok, amelyek
    csak TARTALMAZZÁK. Ékezet- és kisbetű-érzéketlen. Ha a beírt név egyikre sem illik,
    nincs felugró lista — marad amit beírt, és mentéskor új partnerként megjegyezzük."""

    def __init__(self, szulo, valtozo: tk.StringVar, partnerek: list[str], szelesseg: int = 28):
        super().__init__(szulo)
        self.valtozo = valtozo
        # (összehasonlító kulcs, eredeti név) párok, egyszer kiszámolva
        self._kulcsok = [(partners._kulcs(p), p) for p in partnerek]

        self.entry = tk.Entry(
            self,
            textvariable=valtozo,
            width=szelesseg,
            disabledbackground="#e9ecef",  # kiszürkített (folytatás-oldal: nem szerkeszthető)
            disabledforeground="#9aa0a6",
        )
        self.entry.pack(fill="x")
        self._alap_szin = self.entry.cget("background")

        self._popup: tk.Toplevel | None = None
        self._lista: tk.Listbox | None = None

        self.entry.bind("<KeyRelease>", self._gepeles)
        self.entry.bind("<Down>", self._listara)
        self.entry.bind("<Return>", self._valaszt)
        self.entry.bind("<Escape>", lambda e: self._elrejt())
        self.entry.bind("<FocusOut>", self._focus_out)

    def _talalatok(self, szoveg: str) -> list[str]:
        """Rangsorolt találatok: előbb a 'kezdődik vele', utána a 'tartalmazza'."""
        kulcs = partners._kulcs(szoveg)
        if not kulcs:
            return []
        kezdo, tartalmazo = [], []
        for k, eredeti in self._kulcsok:
            if k.startswith(kulcs):
                kezdo.append(eredeti)
            elif kulcs in k:
                tartalmazo.append(eredeti)
        kezdo.sort(key=str.lower)
        tartalmazo.sort(key=str.lower)
        return kezdo + tartalmazo

    def _gepeles(self, event) -> None:
        if event.keysym in ("Up", "Down", "Return", "Escape", "Tab", "Left", "Right"):
            return
        szoveg = self.valtozo.get().strip()
        talalatok = self._talalatok(szoveg) if szoveg else []
        if talalatok:
            self._mutat(talalatok)
        else:
            self._elrejt()

    def _mutat(self, talalatok: list[str]) -> None:
        if self._popup is None:
            self._popup = tk.Toplevel(self)
            self._popup.wm_overrideredirect(True)  # keret nélküli felugró lista
            self._lista = tk.Listbox(self._popup, activestyle="none", exportselection=False)
            self._lista.pack(fill="both", expand=True)
            self._lista.bind("<ButtonRelease-1>", self._valaszt_klikk)
            self._lista.bind("<Return>", self._valaszt)
            self._lista.bind("<Escape>", lambda e: (self._elrejt(), self.entry.focus_set()))
            self._lista.bind("<MouseWheel>", self._lista_gorgo)
        self._lista.delete(0, "end")
        for nev in talalatok:
            self._lista.insert("end", nev)
        self._lista.configure(height=min(8, len(talalatok)))
        self.update_idletasks()
        x = self.entry.winfo_rootx()
        y = self.entry.winfo_rooty() + self.entry.winfo_height()
        sz = max(self.entry.winfo_width(), 220)
        self._popup.wm_geometry(f"{sz}x{self._lista.winfo_reqheight()}+{x}+{y}")
        self._popup.deiconify()
        self._popup.lift()

    def _listara(self, event):
        """Le nyíl: belép a felugró listába, hogy nyilakkal lehessen választani."""
        if self._popup is not None and self._lista is not None and self._lista.size():
            self._lista.focus_set()
            self._lista.selection_clear(0, "end")
            self._lista.selection_set(0)
            self._lista.activate(0)
        return "break"

    def _valaszt(self, event=None):
        if self._lista is not None:
            sel = self._lista.curselection()
            if sel:
                self.valtozo.set(self._lista.get(sel[0]))
        self._elrejt()
        self.entry.focus_set()
        self.entry.icursor("end")
        return "break"

    def _valaszt_klikk(self, event):
        if self._lista is not None:
            idx = self._lista.nearest(event.y)
            if idx >= 0:
                self.valtozo.set(self._lista.get(idx))
        self._elrejt()
        self.entry.focus_set()
        self.entry.icursor("end")
        return "break"

    def _lista_gorgo(self, event):
        if self._lista is not None and event.delta:
            self._lista.yview_scroll(-1 if event.delta > 0 else 1, "units")
        return "break"  # ne görgesse a mögötte lévő táblázatot is

    def _focus_out(self, event):
        # késleltetett elrejtés: ha a fókusz épp a felugró listára került (Le nyíl vagy
        # kattintás), NE rejtsük el — minden más esetben (másik mezőre lép) igen.
        def talan_elrejt():
            try:
                fok = self.focus_get()
            except KeyError:
                fok = None
            if fok is not self._lista:
                self._elrejt()

        self.after(120, talan_elrejt)

    def _elrejt(self):
        if self._popup is not None:
            self._popup.withdraw()

    def jelold_hianyt(self, hianyzik: bool) -> None:
        """Hiányzó partnernél pirosra színezi a mezőt, egyébként visszaállítja."""
        self.entry.config(background=PARTNER_HIANYZIK_SZIN if hianyzik else self._alap_szin)

    def allit_allapot(self, aktiv: bool) -> None:
        """Engedélyezi vagy letiltja (kiszürkíti) a mezőt. Folytatás-oldalon letiltjuk,
        hogy ne lehessen véletlenül beleírni."""
        if aktiv:
            self.entry.config(state="normal")
        else:
            self._elrejt()  # ne maradjon nyitva a felugró lista
            self.entry.config(state="disabled")


class App:
    def __init__(self) -> None:
        self.beallitasok = config_modul.betolt()
        self.kep_hivatkozasok: list[tk.PhotoImage] = []  # hogy a Tk ne dobja el a képeket
        self.sor_widgetek: list[dict] = []  # soronként a változók + adatok
        self.feldolgozo_sor: queue.Queue = queue.Queue()
        self.nyers_sorok: list[dict] = []

        self.gyoker = tk.Tk()
        self.gyoker.title("Munkaszám-rendező")
        # Teljes méretben (maximalizálva) nyit, hogy a Teendő oszlop is rögtön látsszon.
        # Windowson a 'zoomed' állapot maximalizál; máshol (pl. fejlesztés Macen) a képernyő
        # méretére állítjuk.
        self.gyoker.geometry("1100x700")
        self.gyoker.minsize(820, 520)
        try:
            self.gyoker.state("zoomed")
        except tk.TclError:
            self.gyoker.update_idletasks()
            self.gyoker.geometry(
                f"{self.gyoker.winfo_screenwidth()}x{self.gyoker.winfo_screenheight()}+0+0"
            )
        # Ha bármelyik gomb hibába futna, ne csak a háttér-konzolba írjon (amit az
        # édesapa nem lát), hanem jelenjen meg érthető, fényképezhető üzenet.
        self.gyoker.report_callback_exception = self._kezeletlen_hiba

        self._epit_fejlec()
        # A láblécet (Mentés gomb) a táblázat ELŐTT, az ablak aljára rögzítjük, hogy
        # kis képernyőn se vágódjon le — különben a gomb lecsúszhat a látható terület alól.
        self._epit_lablec()
        self._epit_tabla_terulet()

        # Első indításkor figyelmeztetés, ha hiányzik a kulcs vagy a célmappa.
        self.gyoker.after(200, self._elso_inditas_ellenorzes)

    # ------------------------------------------------------------------ felépítés
    def _epit_fejlec(self) -> None:
        keret = ttk.Frame(self.gyoker, padding=10)
        keret.pack(fill="x")

        ttk.Button(keret, text="Válassz PDF(ek)et", command=self._valassz_pdf).pack(side="left")
        ttk.Button(keret, text="Beállítások", command=self._beallitas_ablak).pack(side="left", padx=8)
        ttk.Button(
            keret, text="Használati útmutató", command=self._utmutato_megnyit
        ).pack(side="left")

        self.allapot_szoveg = tk.StringVar(value="Készen áll.")
        ttk.Label(keret, textvariable=self.allapot_szoveg).pack(side="left", padx=12)

        self.folyamat = ttk.Progressbar(keret, mode="determinate", length=200)
        self.folyamat.pack(side="right")

    def _epit_tabla_terulet(self) -> None:
        keret = ttk.Frame(self.gyoker, padding=(10, 0))
        keret.pack(fill="both", expand=True)

        tipp = (
            "Tipp: a sárgával jelölt sorok igényelnek figyelmet. Új partnert egyszerűen "
            "beírhatsz a Partner mezőbe — következő futtatáskor már kiválasztható lesz."
        )
        ttk.Label(keret, text=tipp, foreground="#555555", wraplength=860, justify="left").pack(
            anchor="w", pady=(6, 4)
        )

        # fejléc sor — grid + fix oszlopszélesség, hogy pontosan a sorok fölött legyen
        fejlec = ttk.Frame(keret)
        fejlec.pack(fill="x")
        for i, (szoveg, px) in enumerate(OSZLOPOK):
            fejlec.columnconfigure(i, minsize=px)
            ttk.Label(fejlec, text=szoveg, anchor="w").grid(row=0, column=i, sticky="w", padx=2)

        # görgethető terület a sorokhoz
        vaszon = tk.Canvas(keret, borderwidth=0, highlightthickness=0)
        self.vaszon = vaszon
        gorgeto = ttk.Scrollbar(keret, orient="vertical", command=vaszon.yview)
        self.sorok_keret = ttk.Frame(vaszon)
        self.sorok_keret.bind(
            "<Configure>", lambda e: vaszon.configure(scrollregion=vaszon.bbox("all"))
        )
        vaszon.create_window((0, 0), window=self.sorok_keret, anchor="nw")
        vaszon.configure(yscrollcommand=gorgeto.set)
        vaszon.pack(side="left", fill="both", expand=True)
        gorgeto.pack(side="right", fill="y")

        # Egérgörgővel is lehessen görgetni (eddig csak a csúszkával ment). Windows/Mac:
        # <MouseWheel>; Linux: Button-4/5. Egyetlen görgethető terület van, ezért bind_all.
        vaszon.bind_all("<MouseWheel>", self._egergorgo)
        vaszon.bind_all("<Button-4>", lambda e: vaszon.yview_scroll(-1, "units"))
        vaszon.bind_all("<Button-5>", lambda e: vaszon.yview_scroll(1, "units"))

    def _egergorgo(self, event) -> None:
        """Egérgörgő -> a táblázat görgetése (Windowson event.delta a 120 többszöröse)."""
        if event.delta:
            self.vaszon.yview_scroll(-1 if event.delta > 0 else 1, "units")

    def _epit_lablec(self) -> None:
        keret = ttk.Frame(self.gyoker, padding=10)
        keret.pack(side="bottom", fill="x")
        self.mentes_gomb = ttk.Button(
            keret, text="Dokumentumok mentése", command=self._ment, state="disabled"
        )
        self.mentes_gomb.pack(side="right")
        self.teendo_szoveg = tk.StringVar(value="")
        self.also_teendo_cimke = tk.Label(keret, textvariable=self.teendo_szoveg, fg="#a06000")
        self.also_teendo_cimke.pack(side="left")

    # ------------------------------------------------------------- első indítás
    def _elso_inditas_ellenorzes(self) -> None:
        if not self.beallitasok.van_api_kulcs or not self.beallitasok.van_cel_mappa:
            messagebox.showinfo(
                "Beállítás szükséges",
                "Az első használat előtt töltsd ki a beállításokat:\n"
                "• a Claude API kulcsot, és\n"
                "• a célmappát (ahova a rendezett mappák kerülnek).",
            )
            self._beallitas_ablak()

    # ------------------------------------------------------------- PDF kiválasztás
    def _valassz_pdf(self) -> None:
        if not self.beallitasok.van_api_kulcs:
            messagebox.showwarning("Hiányzó kulcs", "Előbb add meg a Claude API kulcsot a Beállításokban.")
            return
        if not self.beallitasok.van_cel_mappa:
            messagebox.showwarning("Hiányzó célmappa", "Előbb válassz célmappát a Beállításokban.")
            return

        fajlok = filedialog.askopenfilenames(
            title="Válaszd ki a beszkennelt PDF-(ek)et",
            filetypes=[("PDF fájlok", "*.pdf")],
        )
        if not fajlok:
            return

        # A fájlokat névsorban dolgozzuk fel, hogy egy dokumentum akár két fájl határán
        # is folytatódhasson, ha a szkenner kettévágta.
        fajlok = sorted(fajlok)
        self._tabla_torles()
        self.mentes_gomb.config(state="disabled")
        self.teendo_szoveg.set("")
        self.allapot_szoveg.set("Beolvasás folyamatban…")
        self.folyamat.config(value=0)

        szal = threading.Thread(target=self._beolvas_szal, args=(fajlok,), daemon=True)
        szal.start()
        self.gyoker.after(100, self._figyeld_a_szalat)

    def _beolvas_szal(self, fajlok: tuple[str, ...]) -> None:
        """Háttérszál: minden oldal sarkát beolvassa. Tk widgetekhez NEM nyúl."""
        try:
            kl = reader.kliens(self.beallitasok.api_kulcs)
            # összes oldal megszámolása a folyamatjelzőhöz
            osszes = 0
            dokumentumok = []
            for ut in fajlok:
                doc = fitz.open(ut)
                dokumentumok.append((ut, doc))
                osszes += doc.page_count
            self.feldolgozo_sor.put(("max", osszes))

            eredmeny: list[dict] = []
            for ut, doc in dokumentumok:
                for index in range(doc.page_count):
                    oldal = doc.load_page(index)
                    png = corner.sarok_png(
                        oldal,
                        szelesseg_arany=self.beallitasok.sarok_szelesseg_arany,
                        magassag_arany=self.beallitasok.sarok_magassag_arany,
                    )
                    olvasat = reader.olvas(kl, self.beallitasok.modell, png)
                    illesztett = partners.illeszt_partner(olvasat.partner, self.beallitasok.partnerek)
                    eredmeny.append(
                        {
                            "forras_pdf": ut,
                            "oldal_index": index,
                            "oldal_cimke": f"{Path(ut).name} / {index + 1}",
                            "uj_dokumentum": olvasat.van_felirat,
                            "partner": illesztett or (olvasat.partner or ""),
                            "munkaszam": olvasat.munkaszam or "",
                            "megbizhato": olvasat.megbizhatosag == "magas",
                            "thumb_base64": base64.standard_b64encode(png).decode("ascii"),
                        }
                    )
                    self.feldolgozo_sor.put(("halad", 1))
                doc.close()

            self.feldolgozo_sor.put(("kesz", eredmeny))
        except Exception as hiba:  # noqa: BLE001 — a felhasználónak érthető üzenetet adunk
            self.feldolgozo_sor.put(("hiba", str(hiba)))

    def _figyeld_a_szalat(self) -> None:
        try:
            while True:
                tipus, adat = self.feldolgozo_sor.get_nowait()
                if tipus == "max":
                    self.folyamat.config(maximum=adat, value=0)
                elif tipus == "halad":
                    self.folyamat.step(adat)
                elif tipus == "kesz":
                    self.nyers_sorok = adat
                    self._tabla_felepit(adat)
                    self.allapot_szoveg.set(
                        f"{len(adat)} oldal beolvasva. Ellenőrizd, majd mentsd."
                    )
                    self.mentes_gomb.config(state="normal")
                    return
                elif tipus == "hiba":
                    self.allapot_szoveg.set("Hiba történt.")
                    messagebox.showerror(
                        "Hiba a beolvasás közben",
                        "Nem sikerült beolvasni az oldalakat.\n\n"
                        f"Részletek: {adat}\n\n"
                        "Ellenőrizd az internetkapcsolatot és az API kulcsot a Beállításokban.",
                    )
                    return
        except queue.Empty:
            pass
        self.gyoker.after(100, self._figyeld_a_szalat)

    # ------------------------------------------------------------- táblázat
    def _tabla_torles(self) -> None:
        for widget in self.sorok_keret.winfo_children():
            widget.destroy()
        self.sor_widgetek.clear()
        self.kep_hivatkozasok.clear()

    def _tabla_felepit(self, sorok: list[dict]) -> None:
        self._tabla_torles()
        partner_lista = sorted(self.beallitasok.partnerek)

        for adat in sorok:
            sor = ttk.Frame(self.sorok_keret)
            sor.pack(fill="x", pady=1)
            for i, (_, px) in enumerate(OSZLOPOK):
                sor.columnconfigure(i, minsize=px)

            # Oldal: csak az oldalszámot mutatjuk (a hosszú szkenner-fájlnév csak zavarna és
            # széttolná az oszlopokat); a teljes azonosító a mentési hibaüzenetben szerepel.
            ttk.Label(sor, text=f"{adat['oldal_index'] + 1}. oldal", anchor="w").grid(
                row=0, column=0, sticky="w", padx=2
            )

            # kis kép a sarokról
            try:
                kep = tk.PhotoImage(data=adat["thumb_base64"])
                # felfelé kerekített osztó -> a szélesség garantáltan <= 250 képpont, így a
                # kép sosem lóg túl az oszlopán (különben széttolná a fejléchez igazítást)
                oszto = max(1, math.ceil(kep.width() / 250))
                if oszto > 1:
                    kep = kep.subsample(oszto, oszto)
                self.kep_hivatkozasok.append(kep)
                ttk.Label(sor, image=kep).grid(row=0, column=1, sticky="w", padx=2)
            except Exception:  # noqa: BLE001 — ha a kép nem jeleníthető, ne álljon le minden
                ttk.Label(sor, text="(kép)").grid(row=0, column=1, sticky="w", padx=2)

            uj_valt = tk.BooleanVar(value=adat["uj_dokumentum"])
            ttk.Checkbutton(sor, variable=uj_valt).grid(row=0, column=2, sticky="w", padx=2)

            partner_valt = tk.StringVar(value=adat["partner"])
            partner_mezo = PartnerMezo(sor, partner_valt, partner_lista, szelesseg=28)
            partner_mezo.grid(row=0, column=3, sticky="w", padx=2)

            munka_valt = tk.StringVar(value=adat["munkaszam"])
            munka_mezo = tk.Entry(
                sor,
                textvariable=munka_valt,
                width=14,
                disabledbackground="#e9ecef",  # kiszürkített, ha nem dokumentum-kezdő sor
                disabledforeground="#9aa0a6",
            )
            munka_mezo.grid(row=0, column=4, sticky="w", padx=2)

            # nincs fix szélesség: a (néha hosszabb) teendő-szöveg teljesen kiférjen
            teendo_cimke = tk.Label(sor, text="", anchor="w")
            teendo_cimke.grid(row=0, column=5, sticky="w", padx=2)

            self.sor_widgetek.append(
                {
                    "forras_pdf": adat["forras_pdf"],
                    "oldal_index": adat["oldal_index"],
                    "oldal_cimke": adat["oldal_cimke"],
                    "uj": uj_valt,
                    "partner": partner_valt,
                    "partner_mezo": partner_mezo,
                    "munkaszam": munka_valt,
                    "munka_mezo": munka_mezo,
                    "munka_alap_hatter": munka_mezo.cget("background"),
                    "teendo_cimke": teendo_cimke,
                    "teendo_alap_hatter": teendo_cimke.cget("background"),
                }
            )

            # bármelyik mező változása frissíti a kiemeléseket: ahogy javít, a sárga eltűnik
            for valt in (uj_valt, partner_valt, munka_valt):
                valt.trace_add("write", lambda *_: self._frissit_kiemelesek())

        self._frissit_kiemelesek()

    def _frissit_kiemelesek(self) -> None:
        """A figyelmet igénylő sorokat kiemeli (sárga munkaszám-mező + rövid teendő-szöveg).

        Csak a dokumentum-KEZDŐ oldalakat ellenőrizzük (ahol felirat van, vagy az első sor):
        ezeknek kell partner és értelmezhető munkaszám. A felirat nélküli (folytatás) oldalak
        az előző dokumentumhoz tartoznak, ezért azokat nem jelöljük. Így csak a ténylegesen
        hiányos sorok lesznek sárgák — nem mind, mint korábban."""
        figyelmet_igenyel = 0
        volt_mar_sor = False
        for w in self.sor_widgetek:
            kezdo = bool(w["uj"].get()) or not volt_mar_sor
            volt_mar_sor = True
            if not kezdo:  # folytatás-oldal: a mezők kiszürkítve, nem szerkeszthetők
                w["munka_mezo"].config(state="disabled")
                w["partner_mezo"].allit_allapot(False)
                w["teendo_cimke"].config(text="", background=w["teendo_alap_hatter"])
                continue

            # dokumentum-kezdő sor: a partner és a munkaszám mező szerkeszthető
            w["munka_mezo"].config(state="normal")
            w["partner_mezo"].allit_allapot(True)
            partner_hianyzik = not w["partner"].get().strip()
            w["partner_mezo"].jelold_hianyt(partner_hianyzik)
            nyers_munkaszam = w["munkaszam"].get().strip()
            munkaszam_hibas = (
                munka.ertelmez_munkaszam(nyers_munkaszam, self.beallitasok.tartalek_ev) is None
            )

            uzenetek = []
            if partner_hianyzik:
                uzenetek.append("hiányzik a partner")
            if not nyers_munkaszam:
                uzenetek.append("hiányzik a munkaszám")
            elif munkaszam_hibas:
                # van beírva valami, de nem M + 3 számjegy alakú (pl. egy beolvasási hibás M1248)
                uzenetek.append("hibás munkaszám (M### kell)")

            # A munkaszám-mezőt CSAK akkor emeljük ki sárgával, ha tényleg a munkaszámmal
            # van baj — különben félrevezető (a sárga a hibás mezőre mutasson).
            w["munka_mezo"].config(
                background=ALACSONY_SZIN if munkaszam_hibas else w["munka_alap_hatter"]
            )

            if uzenetek:
                figyelmet_igenyel += 1
                w["teendo_cimke"].config(
                    text="⚠ " + ", ".join(uzenetek),
                    fg="#a06000",
                    background=ALACSONY_SZIN,
                )
            else:
                w["teendo_cimke"].config(
                    text="✓ rendben", fg="#2e7d32", background=w["teendo_alap_hatter"]
                )

        if figyelmet_igenyel:
            self.teendo_szoveg.set(
                f"{figyelmet_igenyel} sor igényel figyelmet (sárgával/pirossal jelölve)."
            )
            self.also_teendo_cimke.config(fg="#a06000")  # narancs: még van teendő
        else:
            self.teendo_szoveg.set("Minden sor rendben, mehet a mentés.")
            self.also_teendo_cimke.config(fg="#2e7d32")  # zöld: minden rendben

    # ------------------------------------------------------------- mentés
    def _ment(self) -> None:
        sorok = [
            grouping.OldalSor(
                forras_pdf=w["forras_pdf"],
                oldal_index=w["oldal_index"],
                uj_dokumentum=bool(w["uj"].get()),
                partner=w["partner"].get().strip(),
                munkaszam=w["munkaszam"].get().strip(),
            )
            for w in self.sor_widgetek
        ]
        dokumentumok = grouping.dokumentumokra_bont(sorok)

        feladatok: list[filer.MentesiFeladat] = []
        hibak: list[str] = []
        uj_partnerek: set[str] = set()

        for sorszam, dok in enumerate(dokumentumok, start=1):
            elso = dok.oldalak[0]
            cimke = f"{Path(elso.forras_pdf).name} / {elso.oldal_index + 1}. oldal"
            partner = (dok.partner or "").strip()
            munkaszam = munka.ertelmez_munkaszam(dok.munkaszam, self.beallitasok.tartalek_ev)
            if not partner:
                hibak.append(f"{sorszam}. dokumentum ({cimke}): hiányzik a partner.")
                continue
            if munkaszam is None:
                hibak.append(
                    f"{sorszam}. dokumentum ({cimke}): "
                    f"hibás vagy hiányzó munkaszám ('{dok.munkaszam}'). Helyes alak: M### (pl. M123)."
                )
                continue
            if partner not in self.beallitasok.partnerek:
                uj_partnerek.add(partner)
            feladatok.append(
                filer.MentesiFeladat(
                    partner=partner,
                    munkaszam=munkaszam,
                    oldalak=[(o.forras_pdf, o.oldal_index) for o in dok.oldalak],
                )
            )

        if hibak:
            messagebox.showwarning(
                "Javítás szükséges",
                "Néhány dokumentumot nem lehet menteni, amíg ki nem javítod:\n\n"
                + "\n".join(hibak),
            )
            return

        try:
            eredmenyek = filer.ment(feladatok, self.beallitasok.cel_mappa)
        except Exception as hiba:  # noqa: BLE001
            messagebox.showerror("Hiba a mentés közben", f"Nem sikerült menteni a fájlokat.\n\n{hiba}")
            return

        # új partnerek megjegyzése a következő alkalomra
        if uj_partnerek:
            self.beallitasok.partnerek = sorted({*self.beallitasok.partnerek, *uj_partnerek})
            config_modul.ment(self.beallitasok)

        # a már elmentett listát ne lehessen véletlenül még egyszer menteni (duplikátum _NNN)
        self.mentes_gomb.config(state="disabled")
        self.allapot_szoveg.set(f"{len(eredmenyek)} dokumentum elmentve.")
        self._mentes_kesz_ablak(eredmenyek)

    # --------------------------------------------------------- mentés utáni ablak
    def _mentes_kesz_ablak(self, eredmenyek: list[filer.MentesiEredmeny]) -> None:
        """A mentés után megjelenő ablak: pontosan mi mentődött el, hova, és mi a következő lépés."""
        cel = self.beallitasok.cel_mappa
        ablak = tk.Toplevel(self.gyoker)
        ablak.title("Kész — elmentve")
        ablak.geometry("640x460")
        ablak.transient(self.gyoker)
        ablak.grab_set()
        keret = ttk.Frame(ablak, padding=12)
        keret.pack(fill="both", expand=True)

        ttk.Label(
            keret,
            text=f"{len(eredmenyek)} dokumentum elmentve ide:",
            font=("Arial", 11, "bold"),
        ).pack(anchor="w")
        ttk.Label(keret, text=cel, foreground="#0050a0").pack(anchor="w", pady=(0, 8))

        ttk.Label(keret, text="Elmentett fájlok:").pack(anchor="w")
        lista_keret = ttk.Frame(keret)
        lista_keret.pack(fill="both", expand=True, pady=(2, 10))
        gorgeto = ttk.Scrollbar(lista_keret, orient="vertical")
        lista = tk.Listbox(lista_keret, yscrollcommand=gorgeto.set)
        gorgeto.config(command=lista.yview)
        gorgeto.pack(side="right", fill="y")
        lista.pack(side="left", fill="both", expand=True)

        cel_path = Path(cel)
        for e in eredmenyek:
            try:
                megjelenit = e.utvonal.relative_to(cel_path)
            except ValueError:  # ha valamiért nem a célmappa alatt van
                megjelenit = e.utvonal
            lista.insert("end", f"{megjelenit}   ({e.oldalszam} oldal)")

        gomb_sor = ttk.Frame(keret)
        gomb_sor.pack(fill="x")
        ttk.Button(gomb_sor, text="Bezárás", command=ablak.destroy).pack(side="right")
        ttk.Button(
            gomb_sor, text="Új rendezés", command=lambda: self._uj_rendezes(ablak)
        ).pack(side="right", padx=6)
        ttk.Button(
            gomb_sor, text="Mappa megnyitása", command=lambda: self._mappa_megnyit(cel)
        ).pack(side="right", padx=6)

    def _uj_rendezes(self, ablak: tk.Toplevel) -> None:
        """Letörli a táblázatot és előkészít egy új beolvasást."""
        ablak.destroy()
        self._tabla_torles()
        self.nyers_sorok = []
        self.folyamat.config(value=0)
        self.teendo_szoveg.set("")
        self.allapot_szoveg.set("Készen áll. Válassz új PDF-(ek)et.")

    def _rendszerrel_megnyit(self, ut: str) -> None:
        """A megadott fájlt vagy mappát a rendszer alapértelmezett alkalmazásával nyitja meg
        (Windowson Intéző / PDF-néző, macOS-en open, Linuxon xdg-open)."""
        if sys.platform.startswith("win"):
            os.startfile(ut)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", ut], check=False)
        else:
            subprocess.run(["xdg-open", ut], check=False)

    def _mappa_megnyit(self, mappa: str) -> None:
        """Megnyitja a megadott mappát a rendszer fájlkezelőjében (Windowson az Intézőben)."""
        try:
            self._rendszerrel_megnyit(mappa)
        except Exception as hiba:  # noqa: BLE001
            messagebox.showerror("Hiba", f"Nem sikerült megnyitni a mappát.\n\n{hiba}")

    def _utmutato_megnyit(self) -> None:
        """Megnyitja a használati útmutató PDF-et a rendszer alapértelmezett PDF-nézőjében."""
        # A PDF a repo gyökerében, az output/ mappában van (app.py a csomagban → két szint fel).
        pdf = Path(__file__).resolve().parent.parent / "output" / "Hasznalati_utmutato.pdf"
        if not pdf.exists():
            messagebox.showerror(
                "Útmutató", f"A használati útmutató nem található itt:\n{pdf}"
            )
            return
        try:
            self._rendszerrel_megnyit(str(pdf))
        except Exception as hiba:  # noqa: BLE001
            messagebox.showerror(
                "Útmutató", f"Nem sikerült megnyitni a használati útmutatót.\n\n{hiba}"
            )

    def _kezeletlen_hiba(self, kivetel_tipus, kivetel, nyomkoveto) -> None:
        """Bármilyen váratlan hiba esetén érthető, fényképezhető üzenetet mutat.

        Enélkül a Tkinter csak a háttér-konzolba írná a hibát (amit az édesapa nem lát),
        és a gomb látszólag 'nem csinálna semmit'."""
        reszletek = "".join(traceback.format_exception(kivetel_tipus, kivetel, nyomkoveto))
        messagebox.showerror(
            "Váratlan hiba",
            "Valami hiba történt a művelet közben. A program nem áll le, de ez a lépés "
            "nem fejeződött be.\n\n"
            "Kérlek, készíts erről egy képernyőképet és küldd el.\n\n"
            f"Részletek:\n{reszletek}",
        )

    # ------------------------------------------------------------- beállítások
    def _beallitas_ablak(self) -> None:
        ablak = tk.Toplevel(self.gyoker)
        ablak.title("Beállítások")
        ablak.geometry("560x520")
        ablak.transient(self.gyoker)
        ablak.grab_set()

        keret = ttk.Frame(ablak, padding=12)
        keret.pack(fill="both", expand=True)

        ttk.Label(keret, text="Claude API kulcs:").pack(anchor="w")
        kulcs_valt = tk.StringVar(value=self.beallitasok.api_kulcs)
        ttk.Entry(keret, textvariable=kulcs_valt, width=64).pack(fill="x", pady=(0, 10))

        ttk.Label(keret, text="Célmappa (ide kerülnek a rendezett mappák):").pack(anchor="w")
        cel_sor = ttk.Frame(keret)
        cel_sor.pack(fill="x", pady=(0, 10))
        cel_valt = tk.StringVar(value=self.beallitasok.cel_mappa)
        ttk.Entry(cel_sor, textvariable=cel_valt, width=52).pack(side="left", fill="x", expand=True)

        def tallozas() -> None:
            mappa = filedialog.askdirectory(title="Válassz célmappát")
            if mappa:
                cel_valt.set(mappa)

        ttk.Button(cel_sor, text="Tallózás…", command=tallozas).pack(side="left", padx=6)

        partner_fejlec = ttk.Frame(keret)
        partner_fejlec.pack(fill="x")
        ttk.Label(partner_fejlec, text="Ismert partnerek (soronként egy):").pack(side="left")
        ttk.Button(
            partner_fejlec,
            text="Importálás Excel/CSV fájlból…",
            command=lambda: self._partnerek_importal(ablak, partner_szoveg),
        ).pack(side="right")

        partner_szoveg = tk.Text(keret, height=12, width=60)
        partner_szoveg.insert("1.0", "\n".join(self.beallitasok.partnerek))
        partner_szoveg.pack(fill="both", expand=True, pady=(4, 10))

        def mentes() -> None:
            self.beallitasok.api_kulcs = kulcs_valt.get().strip() or config_modul.API_KULCS_HELYKITOLTO
            self.beallitasok.cel_mappa = cel_valt.get().strip()
            nyers = partner_szoveg.get("1.0", "end").splitlines()
            self.beallitasok.partnerek = sorted({p.strip() for p in nyers if p.strip()})
            config_modul.ment(self.beallitasok)
            messagebox.showinfo("Mentve", "A beállításokat elmentettük.")
            ablak.destroy()

        ttk.Button(keret, text="Mentés", command=mentes).pack(side="right")

    # -------------------------------------------------- partnerek importálása
    def _partnerek_importal(self, szulo: tk.Toplevel, partner_szoveg: tk.Text) -> None:
        """A számlázó program exportjából (Excel/CSV) importálja a partnereket."""
        utvonal = filedialog.askopenfilename(
            parent=szulo,
            title="Válaszd ki a számlázó program exportját",
            filetypes=[("Excel és CSV fájlok", "*.xlsx *.xlsm *.csv"), ("Minden fájl", "*.*")],
        )
        if not utvonal:
            return
        try:
            fejlecek, sorok = partnerek_import.oszlopok_beolvas(utvonal)
        except Exception as hiba:  # noqa: BLE001
            messagebox.showerror("Hiba a fájl olvasásakor", str(hiba), parent=szulo)
            return
        if not fejlecek:
            messagebox.showwarning("Üres fájl", "A fájlban nem találtam adatot.", parent=szulo)
            return

        # oszlopválasztó ablak: melyik oszlop a partnernév?
        valaszto = tk.Toplevel(szulo)
        valaszto.title("Melyik oszlop a partner neve?")
        valaszto.geometry("440x420")
        valaszto.transient(szulo)
        valaszto.grab_set()
        keret = ttk.Frame(valaszto, padding=12)
        keret.pack(fill="both", expand=True)

        ttk.Label(keret, text="Válaszd ki a partnernevet tartalmazó oszlopot:").pack(anchor="w")
        oszlop_valt = tk.StringVar(value=fejlecek[0])
        ttk.Combobox(
            keret, textvariable=oszlop_valt, values=fejlecek, state="readonly", width=40
        ).pack(fill="x", pady=(2, 10))

        ttk.Label(keret, text="Előnézet (az oszlop első értékei):").pack(anchor="w")
        elonezet = tk.Listbox(keret, height=12)
        elonezet.pack(fill="both", expand=True, pady=(2, 10))

        def elonezet_frissit(*_):
            elonezet.delete(0, "end")
            for ertek in partnerek_import.oszlop_ertekei(fejlecek, sorok, oszlop_valt.get())[:50]:
                elonezet.insert("end", ertek)

        oszlop_valt.trace_add("write", elonezet_frissit)
        elonezet_frissit()

        def importal() -> None:
            ujak = partnerek_import.oszlop_ertekei(fejlecek, sorok, oszlop_valt.get())
            if not ujak:
                messagebox.showwarning(
                    "Üres oszlop", "Ebben az oszlopban nincs partnernév.", parent=valaszto
                )
                return
            meglevok = [s.strip() for s in partner_szoveg.get("1.0", "end").splitlines() if s.strip()]
            egyesitett = sorted({*meglevok, *ujak})
            partner_szoveg.delete("1.0", "end")
            partner_szoveg.insert("1.0", "\n".join(egyesitett))
            valaszto.destroy()
            messagebox.showinfo(
                "Importálva",
                f"{len(ujak)} partner beolvasva. A lista most {len(egyesitett)} nevet tartalmaz.\n"
                "A 'Mentés' gombbal véglegesítsd.",
                parent=szulo,
            )

        gomb_sor = ttk.Frame(keret)
        gomb_sor.pack(fill="x")
        ttk.Button(gomb_sor, text="Mégse", command=valaszto.destroy).pack(side="right", padx=(6, 0))
        ttk.Button(gomb_sor, text="Importál", command=importal).pack(side="right")

    # ------------------------------------------------------------- futtatás
    def fut(self) -> None:
        self.gyoker.mainloop()


def main() -> None:
    App().fut()
