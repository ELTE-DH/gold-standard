#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

"""
Reads a level2 TEI XML (i.e. one that already has the emtsv annotations),
parses it with spaCy and converts it into a CoNLL-U file.
"""

from argparse import ArgumentParser
import os
from pathlib import Path
import sys

# import spacy_conll  # noqa
import spacy

from gold_standard.spacy import WhitespaceTokenizer
from gold_standard.tei import sentences
from gold_standard.utils import split_gen


def parse_arguments():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('input_file', type=Path, help='the input .xml file.')
    parser.add_argument('output_file', type=Path,
                        help='the output .conllu file.')
    parser.add_argument('--spacy-model', '-s', default='hu_core_news_lg',
                        help='the spaCy model to load (hu_core_news_lg).')
    parser.add_argument('--processes', '-P', type=int, default=1,
                        help='number of worker processes to use (max is the '
                             'num of cores, default: 1)')
    args = parser.parse_args()

    num_procs = len(os.sched_getaffinity(0))
    if args.processes < 1 or args.processes > num_procs:
        parser.error('Number of processes must be between 1 and {}'.format(
            num_procs))
    return args


def main():
    args = parse_arguments()

    # Using a white space tokenizer, as the data is already tokenized.
    try:
        nlp = spacy.load(args.spacy_model)
    except OSError:
        print(f'Model {args.spacy_model} is not available. Please download it '
              'via `python -m spacy download <model>` or via pip.')
        sys.exit(-1)
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
