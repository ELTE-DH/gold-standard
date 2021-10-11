#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-


"""
A szkript beolvassa a level1 mappában lévő TEI XML regényeket,
bekezdésenként (<p> tagenként) lefuttatja rajtuk az e-magyart, az e-magyar
elemzéseit belerakja az XML-ekbe, majd a létrehozott level2 mappába bemásolja
a kimenetet.
Ahhoz, hogy fusson a szkript, abban a mappában, ahol ez a szkript van, ott kell
lennie az e-magyart tartalmazó mappának, vagy egy szimbolikus linknek, ami az
e-magyart tartalmazó mappára utal, valamint egy level1 mappának, amiben a regények
vannak.
"""

import os
from glob import glob
from json import loads
import csv
import ast
from xml.etree import ElementTree
from xml.dom import minidom
from datetime import date, datetime
from emtsv import build_pipeline, jnius_config, tools, presets, singleton_store_factory

jnius_config.classpath_show_warning = False  # To suppress warning
ElementTree.register_namespace("", "http://www.tei-c.org/ns/1.0")
singletons = singleton_store_factory()

TEI_NAMESPACE = {"ns": "http://www.tei-c.org/ns/1.0"}


def remove_empty_p_tags(root):
    """
    Kiszedi az XML-ekből az üres <p> tageket.
    Ezt a függvényt a get_cleaned_teixml függvény hívja.
    :param root: XML root elemként.
    :return: XML root elemként.
    """
    for div_tag in root.iterfind(".//text//div"):
        to_remove = []
        for p_tag in div_tag.iterfind("./p"):
            if p_tag.text is None:  # Ezt lehetne xpath-al is megfogalmazni
                to_remove.append(p_tag)
        for p_tag in to_remove:
            div_tag.remove(p_tag)
    return root


def get_cleaned_teixml(teixml):
    """
    A beolvasott TEI XML-ből kiszedi az üres <p> tageket, a <hi> tageket (a tartalmukat
    viszont bent hagyja), a sorvégkaraktereket ("\n"), a soft hypheneket, valamint a tei-re
    utaló névteret.
    Ez a függvény hívja a remove_empty_p_tags függvényt.
    :param teixml: string, ami a level1 mappában lévő TEI XML file neve.
    :return: XML root elemként.
    """
    with open(teixml, encoding='utf-8') as fh:
        text = fh.read()
    text = text.replace("­", "")  # Ez nem normál kötőjel, hanem soft hyphen, amiket ki kell szedni.
    text = text.replace("\n", "")  # A level1-ben vannak sorvég karakterek, ezeket is ki kell szedni.
    text = text.replace('xmlns="http://www.tei-c.org/ns/1.0" ', "")
    root = ElementTree.fromstring(text)
    root = remove_empty_p_tags(root)
    # Unwrap <hi> tags
    for p_tag in root.iterfind(".//hi/.."):
        p_text = p_tag.text
        to_remove = []
        for hi_tag in p_tag.iterfind("./hi"):
            p_text += hi_tag.text + hi_tag.tail
            to_remove.append(hi_tag)
        for hi_tag in to_remove:
            p_tag.remove(hi_tag)
        p_tag.text = p_text
    return root


def get_stag_from_wtags(e_magyar_out_iter):
    """
    Egy mondat tokeneit tartalmazó listából létrehoz egy <s> XML-elemet, amely
    tartalmazza a mondat tokeneinek a <token> elemeit, amibe belerakja külön elemekként
    az e-magyar elemzési alternatíváit.
    :param e_magyar_out_iter: kétdimenziós lista, amely egy mondat tokeneinek a grammatikai
    tulajdonságait tartalmazza listákként.
    :yield: XML <s> elem, amely tartalmazza a <token> elemeket az e-magyar elemzési
    alternatíváival.
    """
    for list_sentence in e_magyar_out_iter:
        s_tag = ElementTree.Element("s", {"modified": "False"})
        wsbefore = " "
        for form, wsafter, morph, lemma, xpos, upos, feats, *ner in list_sentence:
            if len(wsbefore) == 2 and len(wsafter) == 3:
                direction = "left"
            elif len(wsbefore) == 3 and len(wsafter) == 2:
                direction = "right"
            else:
                direction = "no"
            token_attrib = {"join": direction}
            token_tag = ElementTree.Element("token", token_attrib)
            s_tag.append(token_tag)

            form_attrib = {"modified": "False"}
            form_tag = ElementTree.Element("form", form_attrib)
            form_tag.text = form
            token_tag.append(form_tag)

            morph_attrib = {"check": "False"}
            morph_tag = ElementTree.Element("morph", morph_attrib)
            token_tag.append(morph_tag)

            morph = loads(morph)
            if len(morph) > 0:
                correct = []
                incorrect = []
                for msd_var in morph:
                    ana_tag = ElementTree.Element("ana")

                    lemma_tag = ElementTree.Element("lemma")
                    lemma_tag.text = msd_var["lemma"]
                    ana_tag.append(lemma_tag)

                    detailed_tag = ElementTree.Element("detailed")
                    detailed_tag.text = msd_var["readable"]
                    ana_tag.append(detailed_tag)

                    simple_tag = ElementTree.Element("simple")
                    simple_tag.text = msd_var["tag"]
                    ana_tag.append(simple_tag)
                    if msd_var["tag"] == xpos and msd_var["lemma"] == lemma:
                        ana_tag.set("correct", "True")
                        correct.append(ana_tag)
                    else:
                        ana_tag.set("correct", "False")
                        incorrect.append(ana_tag)
                for ana_tag in correct:
                    morph_tag.append(ana_tag)
                for ana_tag in incorrect:
                    morph_tag.append(ana_tag)
            else:
                ana_attrib = {"correct": "True"}
                ana_tag = ElementTree.Element("ana", ana_attrib)
                morph_tag.append(ana_tag)

                lemma_tag = ElementTree.Element("lemma")
                lemma_tag.text = lemma
                ana_tag.append(lemma_tag)

                detailed_tag = ElementTree.Element("detailed")
                detailed_tag.text = ""
                ana_tag.append(detailed_tag)

                simple_tag = ElementTree.Element("simple")
                simple_tag.text = xpos
                ana_tag.append(simple_tag)


            wsbefore = wsafter
        yield s_tag


def create_xmlid(root, tag_names=None):
    """
    Belerakja az XML-be a <div> (fejezet), <p> (bekezdés), <s> (mondat) és <token>
    elemek azonosítóját az @xml:id értékeként.
    :param root: XML root elemként
    :param tag_names:
    :return: XML root elemként
    """
    if tag_names is None:
        tag_names = ("div", "p", "s", "token")
    for tag_name in tag_names:
        for tag_id, tag in enumerate(root.iterfind(f".//text//{tag_name}", TEI_NAMESPACE), start=1):
            tag.set("xml:id", f"{tag_name[0]}{tag_id}")
    return root


def add_change(root):
    """
    Belerakja az XML header részének a <revisionDesc> tagjébe a létrehozás dátumát.
    :param root: XML root elemként
    :return root: XML root elemként
    """
    change = ElementTree.Element("change", {"when": date.today().isoformat()})
    change.text = "creating emMorph annotations"
    for revisionDesc in root.iterfind(".//revisionDesc", TEI_NAMESPACE):
        revisionDesc.append(change)
    return root


def emagyar_api(input_data, used_tools=('tok', 'morph', 'pos', 'conv-morph')):
    """
    Ez egy generátor, ami egy regény bekezdésén (<p> tag) futtatja az e-magyart,
    és soronként adja vissza a TSV formátumú kiemenetet.
    Az e-magyar dokumentációját lásd itt: https://github.com/dlt-rilmta/emtsv
    :param input_data: string, amely egy bekezdés szövegét tartalmazza.
    :param used_tools: tuple, ami az e-magyarnak a használt funkcióit sorolja fel.
    :return: háromdimenziós lista, amelyben listaelemekként a mondatok szerepelnek, a
    mondatokon belül listaelemekként a tokenek, a tokeneken beül listaelemekkémt pedig
    a tokeneknek az e-magyar által megadott jellemzői.
    """
    sent = []
    conll_comments = True
    for i, line in enumerate(build_pipeline(input_data, used_tools, tools, presets, conll_comments,
                                            singleton_store=singletons)):
        if i > 0:
            line = line.rstrip()
            if len(line) > 0:
                sent.append(line.split('\t'))
            else:
                yield sent
                sent = []
        else:
            continue  # Ommit header

    if len(sent) > 0:  # Should not be necessary
        yield sent


def process_one_file(input_file_name, output_file_name):
    """
    Ez a metódus egy fájlon lefuttatja bekezdésenként (<p> tagenként) az e-magyart,
    az e-magyar kimenetét belerakja az XML-be, és kiírja a level2 mappába a fájlt.
    :param input_file_name: string, a bemeneti TEI XML fájl neve.
    :param output_file_name: string, a kimeneti XML fájl neve.
    """
    teixml = get_cleaned_teixml(input_file_name)
    for p in teixml.iterfind(".//text//p"):
        text_p = p.text + " " # A bekezdések végére kell egy szóközt rakni, hogy a bekezdések végén lévő írásjel tapadását helyesen állapítsa meg a szkript.
        # A sima idézőjeltől valamiért kiakad a szkript, ezért ezeket le kell cserélni.
        # Ezekből az idézőjelekből csak véletlenül van pár a szövegekben.
        #text_p = text_p.replace('"', '”')
        text_p = text_p.replace('”', '"')  # a nem sima idézőjeleket valamiért főnévként elemzi az e-magyar (állítólag a tanítóanyag miatt)
        text_p = text_p.replace('“', '"')
        text_p = text_p.replace('„', '"')
        text_p = text_p.replace("’", "'")
        used_tools = ('tok', 'morph', 'pos', 'conv-morph')

        # Az emagyar_api függvény lefuttatja az e magyart a bekezdés szövegén, és kiadja az elemzést.
        p.clear()
        p.extend([s for s in get_stag_from_wtags(emagyar_api(text_p, used_tools))])

    teixml = create_xmlid(teixml)
    teixml = add_change(teixml)

    # Prettify
    xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>'
    teixml_as_string = ElementTree.tostring(teixml, encoding="unicode")
    teixml_as_string = xml_declaration + teixml_as_string
    xmlstr = minidom.parseString(teixml_as_string).toprettyxml(newl='\n', encoding='utf-8')
    xmlstr = os.linesep.join(s for s in xmlstr.decode("utf-8").splitlines() if s.strip())
    with open(output_file_name, "w", encoding="utf-8") as output:
        output.write(xmlstr)


def main():
    """
    Ez a metódus végigiterál a level1 mappában lévő TEI XML fájlokon, amelyek az egyes
    regényeket tartalmazzák, megállapítja a bemeneti és a kimeneti fájlok neveit, és
    minden fájl esetében hívja a process_one_file metódust.
    """
    os.mkdir("level2")
    for input_file_name in glob("level1/*.xml"):
        print(input_file_name, datetime.now(), end="\n\n")
        dir_name_ind = input_file_name.index("/") + 1
        output_file_name = f"level2/{input_file_name[dir_name_ind:]}"
        process_one_file(input_file_name, output_file_name)


if __name__ == '__main__':
    main()

