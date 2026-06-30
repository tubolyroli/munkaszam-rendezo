# Munkaszám-rendező

Asztali program (Python + Tkinter), ami a beszkennelt PDF-eket a lapok **jobb felső
sarkába kézzel írt** partner + munkaszám alapján szétválogatja, és
`Partner / Év / M###_ÉV / M###_ÉV_NNN.pdf` szerkezetbe menti. Egy átnézhető/​javítható
ablakban erősíted meg a beolvasást, mielőtt bármit mentene; az eredeti PDF-et soha nem
módosítja.

## Mappaszerkezet

```
munkaszam-rendezo/
├─ indito/              ← amire az APA duplán kattint
│  ├─ inditas.bat         a program indítása
│  ├─ frissites.bat       frissítés a legújabb verzióra (git pull)
│  ├─ telepites.bat       egyszeri telepítés (függőségek + asztali ikon)
│  └─ parancsikon.bat     asztali parancsikon létrehozása
├─ eszkozok/            ← segéd- és fejlesztői fájlok
│  ├─ parancsikon.ps1     a parancsikont létrehozó PowerShell-szkript
│  ├─ ikon.ico            az alkalmazás ikonja
│  └─ generate_utmutato.py  a használati útmutató PDF-jét generálja
├─ munkaszam_rendezo/   ← maga a program (Python csomag)
├─ tests/               ← tesztek (API/szkennelés nélkül: python tests/test_core.py)
├─ docs/                ← Hasznalati_utmutato.md (a forrás)
├─ output/              ← Hasznalati_utmutato.pdf (az apának)
├─ requirements.txt
└─ config.example.json  ← minta beállítás (a valódi config.json HELYI, nincs a repóban)
```

## Telepítés (első alkalom)

1. `git clone https://github.com/tubolyroli/munkaszam-rendezo`
2. Másold be a meglévő **`config.json`-t** a repo gyökerébe (ez tartalmazza az API kulcsot,
   a partnerlistát és a célmappát — szándékosan **nincs** a repóban).
3. Futtasd: `indito\telepites.bat` (függőségek + asztali ikon).
4. Indítás: az asztali **Munkaszám-rendező** ikon, vagy `indito\inditas.bat`.

## Frissítés

Az **`indito\inditas.bat`** (= az asztali ikon) **induláskor magától frissít**: csendben
`git pull --ff-only`, és csak akkor futtat `pip install`-t, ha a `requirements.txt` változott.
Ha nincs internet vagy a pull nem fast-forward, a program a meglévő verzióval indul (best
effort). A `config.json` mindig megmarad.

Kézi/erőltetett frissítés: **`indito\frissites.bat`** (git pull + `pip install`).

> Ezért az `inditas.bat`-ot lehetőleg **ne** változtasd jövőbeli commitban — mivel önmagát is
> frissítheti, egy futó `.bat` átírása megzavarhatja a `cmd`-t.

## Fejlesztés

- Tesztek: `python tests/test_core.py`
- Útmutató PDF újragenerálása: `python eszkozok/generate_utmutato.py`
