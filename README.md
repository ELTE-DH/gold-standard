# Digitális Örökség Nemzeti Laboratórium - Gold standard korpusz projekt

Magyarország Kormánya 2020 nyarán hozta nyilvánosságra, hogy több éves, kiemelt nemzeti program keretében 18 nemzeti laboratóriumot alapít, összefogva a nemzetgazdaság számára különösen ígéretes tématerületek hazai tudáscentrumait. 2020 őszén az Eötvös Loránd Tudományegyetem vezetésével megalakult egy konzorcium, melynek feladata a Digitális Örökség Nemzeti Laboratórium (DH-LAB) célkitűzéseinek valóra váltása.   
A DH-LAB a nemzeti örökség mesterséges intelligencia alapú feldolgozásának, kutatásának és oktatásának, valamint a lehető legszélesebb körű közzétételi módszertanának a kidolgozása érdekében jött létre. A számítógépes nyelvfeldolgozás alapvető feltétele, hogy rendelkezésre álljanak nagyméretű és jó minőségű szöveges adatbázisok, amelyek felhasználhatók gépi tanuláshoz. Éppen ezért a DH-LAB fő célkitűzései közé tartozik egy magyar nyelvű kézzel annotált referencia korpusz (gold standard korpusz) létrehozása.

1. A korpusz szövegei

A korpusz a szövegtípusok és nyelvváltozatok széles skáláját kívánja lefedni. A korpusz szövegei a következő műfajokból és forrásokból kerülnek ki:

- tudományos szövegek

  szakdolgozatok, tudományos publikációk szövegei
- sajtó szövegek

  online hírportálok szövegei
- ismeretterjesztő szövegek

  tudományos-ismeretterjesztő célú weboldalak szövegei
- beszélt nyelvi(t közelítő) szövegek

  blogok, online fórumok szövegei
- jogi szövegek

A különböző műfajok reprezentálásán túl célunk, hogy a határon túli magyar nyelvű digitális szövegek is részét a korpusz részét képezzék.

2. Annotáció

A korpusz a szövegeket nyelvi szempontból feldolgozott, kézzel annotált formában tartalmazza. A nyelvészeti annotáció a nyers szövegeket többszintű nyelvi információval gazdagítja, ami hatékonyabb számítógépes feldolgozást tesz lehetővé. A korpuszba kerülő szövegek feldolgozásának lépései a következők:

- Szegmentálás, tokenizálás

  A feldolgozás első lépéseként a szövegeket mondat és szó egységekre (tokenekre) bontjuk. A token az a legkisebb nyelvi egység, amelyhez annotáció tartozik (szavak, írásjelek).
- Lemmatizálás

  A tokenek lemmatizálása a szótő megállapítását jelenti. A magyarhoz hasonló gazdag morfológiájú nyelvekben a szótövesítés különösen fontos lépése a nyelvfeldolgozásnak, hiszen egy szónak (szótőnek) számtalan formájú előfordulása (szóalakja) lehet. A szótövesítés lehetővé teszi, hogy a különböző ragozott szóalakokat egy szóhoz tartozó alakokként tudjuk kezelni, ezáltal a korpusz alkalmassá válik az intelligens keresésre.
- Morfológiai elemzés

  A tokenek morfológiai elemzése a szóalakok morfo-szintaktikai jegyeiről ad információt, ilyenek a szófaj és a különféle nyelvtani kategóriák: pl. névszóknál szám, eset; igéknél idő, mód, szám, személy, stb.
- Szintaktikai elemzés

  A szintaktikai elemzés az egyes szavak közötti mondattani relációkat, és ezáltal a mondatszerkezetet adja meg.
  
3. A korpusz formátuma

A korpusz alapevtően számítógépes feldolgozásra készül, így a formátum megválasztásánál is a gépi feldolgozhatóság volt az elsődleges szempont. A szövegek, annotációk és metaadatok tárolására ezért a nemzetközi sztenderdeknek is megfelelő TEI XML formátumot választottuk. Ez a formátum kereshető és feldolgozható adatbázisként szolgál, emberi szövegolvasásra azonban nem alkalmas.
A korpuszt alkotó TEI XML fájlok felépítése a tei_pelda.xml fájlban látható.
