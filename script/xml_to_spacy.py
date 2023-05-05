#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

"""
Reads a level2 TEI XML (i.e. one that already has the emtsv annotations),
parses it with spaCy and converts it into a CoNLL-U file.
"""

from collections.abc import Generator, Iterator
from argparse import ArgumentParser
import itertools
import os
from pathlib import Path
from typing import TypeVar

import hu_core_news_lg
from spacy.tokens import Doc
# import spacy_conll  # noqa

from xml.etree import ElementTree


def parse_arguments():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('input_file', type=Path, help='the input .xml file.')
    parser.add_argument('output_file', type=Path,
                        help='the output .conllu file.')
    parser.add_argument('--processes', '-P', type=int, default=1,
                        help='number of worker processes to use (max is the '
                             'num of cores, default: 1)')
    args = parser.parse_args()

    num_procs = len(os.sched_getaffinity(0))
    if args.processes < 1 or args.processes > num_procs:
        parser.error('Number of processes must be between 1 and {}'.format(
            num_procs))
    return args


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


T = TypeVar('T')
U = TypeVar('U')


def split_gen(it: Iterator[tuple[T, U]]) -> tuple[Iterator[T], Iterator[U]]:
    """
    Splits the iterator _it_ of tuples into two.

    From https://stackoverflow.com/questions/28030095/.
    """
    it_a, it_b = itertools.tee(it, 2)
    return (a for a, _ in it_a), (b for _, b in it_b)


class WhitespaceTokenizer:
    """
    A tokenizer that splits on whitespaces. Required if we want to run spaCy
    on already tokenized data.
    """
    def __init__(self, vocab):
        self.vocab = vocab

    def __call__(self, text):
        words = text.split(" ")
        spaces = [True] * len(words)
        # Avoid zero-length tokens
        for i, word in enumerate(words):
            if word == "":
                words[i] = " "
                spaces[i] = False
        # Remove the final trailing space
        if words[-1] == " ":
            words = words[0:-1]
            spaces = spaces[0:-1]
        else:
            spaces[-1] = False

        return Doc(self.vocab, words=words, spaces=spaces)


def main():
    args = parse_arguments()

    # Using a white space tokenizer, as the data is already tokenized.
    nlp = hu_core_news_lg.load()
    nlp.tokenizer = WhitespaceTokenizer(nlp.vocab)
    nlp.add_pipe("conll_formatter")

    words_it, ids_it = split_gen(sentences(args.input_file))
    parsed_it = nlp.pipe(words_it, n_process=args.processes,
                         batch_size=args.processes * 5)

    file_stem = args.input_file.stem.rsplit('_', 1)[0]
    out_line = f'{file_stem}/{{}}\t{{}}'
    args.output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output_file, 'wt', encoding='utf-8') as outf:
        print('ID', 'FORM', 'LEMMA', 'UPOS', 'XPOS', 'FEATS', 'HEAD',
              'DEPREL', 'DEPS', 'MISC', sep='\t', file=outf)
        for doc, ids in zip(parsed_it, ids_it):
            t_ids = iter(ids)
            for line in doc._.conll_str.split('\n'):
                # spaCy might split sentences, which might or might not be
                # correct, but we want to keep the original, already gold
                # standard split
                if line:
                    print(out_line.format(next(t_ids), line.split('\t', 1)[1]),
                          file=outf)
            print(file=outf)


if __name__ == '__main__':
    main()
