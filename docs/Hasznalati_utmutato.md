# Munkaszám-rendező — Használati útmutató

## Mi ez a program?

Ez a kis program a beszkennelt dokumentumokat automatikusan mappákba rendezi.
A gép beolvassa minden oldal **jobb felső sarkát**, ahol kézzel rá van írva a
**partner neve** és a **munkaszám** (pl. `M123`), és ez alapján szétválogatja a
beolvasott PDF-et külön dokumentumokra, majd elmenti őket így:

Partner mappa → Év → Munkaszám → maga a dokumentum.

A program **soha nem írja át** a beolvasott eredeti fájlt, és **semmit nem ment el**
addig, amíg te a "Dokumentumok mentése" gombra nem kattintasz.

## Mire figyelj (a legfontosabb)

A program a kézírást olvassa be, és ez néha téveszt. Ezért **mentés előtt mindig nézd át
a táblázatot** — ez a legfontosabb lépés. Pár perc ellenőrzés megelőzi a rossz helyre
sorolást.

- **Sárga sorok:** ezek bizonytalan beolvasások — ezeket nézd át a legalaposabban.
- **„Új dokumentum" pipa:** ott legyen bepipálva, ahol tényleg új dokumentum kezdődik.
  Ha egy folytatólagos oldal sarkában véletlen folt/pecsét van, a gép tévesen új
  dokumentumnak hiheti — vedd ki a pipát. Ha egy első oldalon a felirat halvány és a gép
  nem vette észre, tedd be a pipát.
- **Partner:** a legördülőből a helyeset válaszd. Több hasonló nevű is lehet
  (pl. több „Profilaxis"), ezért nézd meg, tényleg a jó-e.
- **Munkaszám és év:** ellenőrizd a számot és az évet.

Nyugodtan javíts bármit a mentés előtt. És jó hír: a program **az eredeti fájlt nem
módosítja, semmit nem töröl és nem ír felül** — ha mégis rossz helyre kerülne egy
dokumentum, egyszerűen áthelyezheted kézzel. **Ugyanazt a PDF-et ne dolgozd fel kétszer**,
mert akkor kétszer menti el.

## Hogyan írd a sarkot?

- A partner nevét és a munkaszámot **csak a dokumentum első oldalára** írd, a jobb
  felső sarokba. A többi oldal (2., 3. …) sarka maradjon üres.
- A munkaszám alakja: `M`, utána a szám, majd az év. Például: `M123/26`.
- A **leírt évet a program is felhasználja**, így a digitális mappa egyezik a papíros
  tárolással. Ha valamiért nem írsz oda évet (csak `M123`), akkor a program az **aktuális
  évet** veszi (most 2026), és ez magától követi a jövő éveket (2027, 2028 …) is.
- Írd szépen, jól olvashatóan — a gép a kézírást olvassa be.

## Egyszeri beállítás (ezt elég egyszer megcsinálni)

1. **Telepítés.** Kattints duplán a `telepites.bat` fájlra, és várd meg, amíg lefut.
   (Ezt segít beállítani a fiad — Python is kell hozzá a gépre.)
2. **Indítás.** Kattints duplán az `inditas.bat` fájlra. Megjelenik a program ablaka.
3. **Beállítások.** Kattints a "Beállítások" gombra, és add meg:
   - a **Claude API kulcsot** (ezt a fiad adja meg);
   - a **célmappát** (a "Tallózás…" gombbal válaszd ki, hova kerüljenek a rendezett
     mappák — pl. a Dokumentumok mappádba). Ezt elég egyszer kiválasztani, a program
     megjegyzi.
   - az **ismert partnerek** listáját. Ez segít, hogy ugyanaz a partner mindig ugyanabba
     a mappába kerüljön. Kétféleképpen töltheted fel:
     - **Importálás a számlázó programból (ajánlott).** A számlázó programból mentsd ki a
       partnereket Excel (`.xlsx`) vagy CSV fájlba. A Beállításokban kattints az
       **"Importálás Excel/CSV fájlból…"** gombra, válaszd ki a fájlt, majd a felugró
       ablakban válaszd ki, **melyik oszlop** tartalmazza a partner nevét (az előnézet
       segít ellenőrizni), és kattints az "Importál" gombra.
     - **Kézzel.** A nagy mezőbe soronként egy partnert is beírhatsz.
     Új partnert a mentéskor is megadhatsz, és a program automatikusan megjegyzi.
4. Kattints a "Mentés" gombra.

## Napi használat — lépésről lépésre

1. **Mentsd le a fájlt.** A beszkennelt PDF-et az e-mailből mentsd le egy mappába a
   gépeden.
2. **Indítsd el a programot.** Dupla kattintás az `inditas.bat` fájlra.
   (Felvillanhat egy kis fekete ablak — ez normális, nem kell bezárni.)
3. **Válaszd ki a fájlt.** Kattints a "Válassz PDF(ek)et" gombra, és jelöld ki a
   beolvasott PDF-et. Ha a szkenner több fájlra vágta szét, jelöld ki mindet egyszerre.
4. **Várj a beolvasásra.** A program minden oldal sarkát beolvassa. Ez eltarthat egy
   kis ideig; a folyamatjelző mutatja, hol tart.
5. **Nézd át a táblázatot.** Minden oldal egy sor. A soron látod:
   - **kis képet** a sarokról (amit a gép beolvasott);
   - **"Új dokumentum"** pipát — ez azt jelzi, hogy itt **új dokumentum kezdődik**.
     Ha a gép tévedett, vedd ki vagy tedd be a pipát;
   - **Partner** — válaszd a listából, vagy írj be újat;
   - **Munkaszám** — ellenőrizd, hogy jó-e (`M` + szám, pl. `M123`).
   - A **sárgával jelölt sorok** bizonytalan beolvasások — ezeket nézd át figyelmesen.
6. **Mentés.** Ha mindent rendben találtál, kattints a "Dokumentumok mentése" gombra.
   A program a megfelelő mappákba teszi a fájlokat, és kiírja, hány dokumentum készült.

## Hogyan néz ki az eredmény?

```
Célmappa/
  Kovács Bt/
    2026/
      M123_26/
        M123_26_001.pdf
        M123_26_002.pdf
```

- Egy munkaszám alatt **több dokumentum** is lehet — ezek sorszámot kapnak
  (`_001`, `_002`, …). Ha később ugyanahhoz a munkaszámhoz újabb dokumentum kerül,
  a program a következő sorszámmal folytatja, és **semmit nem ír felül**.
- A partner mappa neve a listából vett, pontos név. Az **év mappa** a munkaszámban leírt
  évből lesz (`/26` → `2026`); ha nem írtál évet, az aktuális évből.

## Ha valami nem stimmel

- **"Hiányzik a partner" vagy "hibás munkaszám" üzenet a mentésnél:** a program
  megmondja, melyik dokumentumnál. Javítsd a táblázatban (partner kiválasztása vagy a
  munkaszám `M` + szám alakra javítása, pl. `M123`), majd mentsd újra.
- **"Hiba a beolvasás közben":** általában az internet vagy az API kulcs a gond.
  Ellenőrizd az internetkapcsolatot, és a kulcsot a Beállításokban.
- **A kis fekete ablakban hibaüzenet jelenik meg:** készíts róla képernyőképet, és
  küldd el a fiadnak.

## Fontos tudnivalók

- A program **internetkapcsolatot igényel** (a kézírás beolvasásához).
- Az **eredeti beolvasott PDF-ek érintetlenek maradnak** — a program csak másol.
- **Semmi nem kerül mentésre**, amíg rá nem kattintasz a "Dokumentumok mentése" gombra,
  szóval nyugodtan átnézheted és javíthatod a táblázatot.
