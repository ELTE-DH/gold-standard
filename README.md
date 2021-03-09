# Digitális Örökség Nemzeti Laboratórium - Gold standard korpusz projekt

Magyarország Kormánya 2020 nyarán hozta nyilvánosságra, hogy több éves, kiemelt nemzeti program keretében 18 nemzeti laboratóriumot alapít, összefogva a nemzetgazdaság számára különösen ígéretes tématerületek hazai tudáscentrumait. 2020 őszén az Eötvös Loránd Tudományegyetem vezetésével megalakult egy konzorcium, melynek feladata a Digitális Örökség Nemzeti Laboratórium (DH-LAB) célkitűzéseinek valóra váltása.   
A DH-LAB a nemzeti örökség mesterséges intelligencia alapú feldolgozásának, kutatásának és oktatásának, valamint a lehető legszélesebb körű közzétételi módszertanának a kidolgozása érdekében jött létre. A számítógépes nyelvfeldolgozás alapvető feltétele, hogy rendelkezésre álljanak nagyméretű és jó minőségű szöveges adatbázisok, amelyek felhasználhatók gépi tanuláshoz. Éppen ezért a DH-LAB fő célkitűzései közé tartozik egy magyar nyelvű kézzel annotált referencia korpusz (gold standard korpusz) létrehozása. Az általunk tervezett korpusz általános célú, azaz a magyar nyelvet összességében szeretné reprezentálni. Célunk, hogy a korpusz adatvezérelt kutatások adatbázisaként és a természetes nyelvet feldolgozó gépi tanulásos algoritmusok tanítóanyagaként is felhasználható legyen.

1. A korpusz szövegei

A DH-LAB célkitűzése egy olyan korszerű korpusz létrehozása, amely a legkülönfélébb szövegtípusokat foglalja magába, több dimenziójú szempontrendszer alapján igyekszik reprezentatívan lefedni a mai magyar írott nyelvhasználatot. Az egyik dimenzió a térbeliség, mely szerint különböző alkorpuszokban kapnak helyet az anyaországi és a határontúli szövegek. Másrészt törekszünk a műfaji változatosságra is, a különböző regisztereket különböző szövegtípusok menténfogjuk reprezentálni. A korpusz szövegei a következő műfajokból és forrásokból kerülnek ki:

- tudományos szövegek

  szakdolgozatok, tudományos publikációk szövegei
- sajtó szövegek

  online hírportálok szövegei
- ismeretterjesztő szövegek

  tudományos-ismeretterjesztő célú weboldalak szövegei
- beszélt nyelvi(t közelítő) szövegek

  blogok, online fórumok szövegei
- jogi szövegek


2. Annotáció

A korpusz annotációja a szöveges adatok feldolgozását jelenti, melynek során a szöveget különféle nyelvi vagy világismereti információval dúsítjuk fel, ami hatékonyabb számítógépes feldolgozást tesz lehetővé. Az általunk tervezett gold standard korpusz számára grammatikai, névelem- és szentimentannotáció is készül. A nyelvtani annotáció a lemmatizálástól a szintaktikai elemzésig felöleli a fő elemzési szinteket. A névelem-annotáció a tulajdonnevek jelölését jelenti, míg a szentimentannotáció során az egyes szövegegységek érzelmi töltetéről adunk információt.

A korpusz szövegeinek nyelvi feldolgozása egy többlépcsős folyamat, ahol az egyes szintek kimenete bemenetként szolgál a további szintekhez. Ezek a feldolgozási lépések a következők:

- Szegmentálás, tokenizálás

  A feldolgozás első lépéseként a szövegeket mondat és szó egységekre (tokenekre) bontjuk. A token az a legkisebb nyelvi egység, amelyhez annotáció tartozik (szavak, írásjelek).
- Lemmatizálás

 A tokenek lemmatizálása az egyes szóelemek, azaz a szótő és a toldalékok meghatározását jelenti. A magyarhoz hasonló gazdag morfológiájú nyelvekben a szótövesítés különösen fontos lépése a nyelvfeldolgozásnak, hiszen egy szónak (szótőnek) számtalan formájú előfordulása (szóalakja) lehet. A szótövesítés lehetővé teszi, hogy a különböző ragozott szóalakokat egy szóhoz tartozó alakokként tudjuk kezelni, ezáltal a korpusz alkalmassá válik az intelligens keresésre.
- Morfológiai elemzés

  A tokenek morfológiai elemzése a szóalakok morfoszintaktikai jegyeiről ad információt, ilyenek a szófaj és a különféle nyelvtani kategóriák: pl. névszóknál szám, eset; igéknél idő, mód, szám, személy, stb. Az automatikus feldolgozás során ennek rendszerint két lépése van: először egy morfológiai elemző meghatározza a szóalakhoz tartozó lehetséges elemzések halmazát, majd egy úgynevezett szófaji egyértelműsítő a szó kontextusa alapján kiválasztja ezekből a legvalószínűbb elemzést.
- Szintaktikai elemzés

  A szintaktikai elemzés az egyes szavak közötti mondattani relációkat, és ezáltal a mondatszerkezetet adja meg. Ennek egyik, általunk is követett megközelítése a függőségi elemzés, melynek alapvetése, hogy a mondat minden szavának van egy "feje", a mondatszerkezet így egy gráf struktúrában ábrázolható. A mondat szavai az elemzési fa egy-egy csomópontjának felelnek meg, a köztük levő élek pedig a szavak közötti relációkat határozzák meg. A fa egy virtuális gyökércsomópontból indul ki, a szavakat reprezentáló csomópontok ebből ágaznak el, szigorúan hierarchikus struktúrában, azaz egymásnak alárendelve. Az egymásnak alárendelt szavak között különbözö, általábana szintaktikai szerepeket jelölő relációk állhatnak fenn.
  
3. A korpusz formátuma

A korpusz alapvetően számítógépes feldolgozásra készül, így a formátum megválasztásánál is a gépi feldolgozhatóság volt az elsődleges szempont. A szövegek, annotációk és metaadatok tárolására ezért a nemzetközi sztenderdeknek is megfelelő TEI XML formátumot választottuk. Ez a formátum gépi eszközzel kereshető és feldolgozható adatbázisként szolgál, emberi szövegolvasásra azonban nem alkalmas.
A korpuszt alkotó TEI XML fájlok felépítése a tei_pelda.xml fájlban látható.
