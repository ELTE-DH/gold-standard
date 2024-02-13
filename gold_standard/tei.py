#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

"""Contains code to iterate through / edit TEI XML files."""

from collections.abc import Generator
from pathlib import Path
from xml.etree import ElementTree


def sentences(tei_xml_file: Path) -> Generator[tuple[list[str], list[str]]]:
    """
    Iterates through the sentences of a TEI XML file.

    :return: Yields a list of surface forms for each sentence.
    """
    namespaces = {
        '': 'http://www.tei-c.org/ns/1.0',
        'xml': 'http://www.w3.org/XML/1998/namespace'
    }
    # TODO I am not sure this is needed at all
    for prefix, uri in namespaces.items():
        ElementTree.register_namespace(prefix, uri)

    with open(tei_xml_file, 'rt', encoding='utf-8') as inf:
        xml_text = inf.read()

    xml = ElementTree.fromstring(xml_text)
    # TODO: is there a better way? To do this without a namespace?
    id_attr = ElementTree.QName(namespaces['xml'], 'id')
    for p_tag in xml.iterfind('.//text//p'):
        for s_tag in p_tag.iterfind('.//s'):
            tokens = [(t_tag.find('form').text.strip(), t_tag.get(id_attr))
                      for t_tag in s_tag.iterfind('.//token')]
            if tokens:
                words, ids = zip(*tokens)
                yield(' '.join(words), ids)
