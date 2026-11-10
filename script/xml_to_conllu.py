#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

"""
Converts the gold standard TEI XML files into a single CoNLL-U file.

For every token, the analysis marked as correct (<ana correct="True">) is
used: its lemma becomes LEMMA, its emMorph <simple> tag becomes XPOS, and
UPOS / FEATS are derived from that tag with emmorph2ud2
(https://github.com/vadno/emmorph2ud2). The token join attributes are encoded
as SpaceAfter=No in MISC. HEAD, DEPREL and DEPS are left empty (_), as the
corpus has no syntactic annotation.

The output contains the following comments:
- ``# newdoc id``: the file name without the annotator suffix (e.g. blog044);
- ``# newpar id``: <doc id>_<xml:id of the <p>>;
- ``# sent_id``: <doc id>_<xml:id of the <s>>;
- ``# text``: the sentence text, reconstructed from the join attributes.

emmorph2ud2 is not on PyPI; install it without its (unneeded) xtsv
dependency:

    pip install --no-deps git+https://github.com/vadno/emmorph2ud2
"""

from argparse import ArgumentParser
from collections.abc import Iterator
import logging
from pathlib import Path
import sys
from typing import TextIO
from xml.etree import ElementTree

from emmorph2ud2 import EmMorph2UD2


XML_ID = '{http://www.w3.org/XML/1998/namespace}id'
# Tokens with these join values are not followed by whitespace
NO_SPACE_AFTER = {'right', 'both'}

logger = logging.getLogger(__name__)


def parse_arguments():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('inputs', type=Path, nargs='+',
                        help='the input .xml files or directories. '
                             'Directories are searched for files matching '
                             '--pattern.')
    parser.add_argument('--output-file', '-o', type=Path,
                        help='the output .conllu file (default: stdout).')
    parser.add_argument('--pattern', '-p', default='*_annot1.xml',
                        help='the glob pattern for selecting files in '
                             'directories (default: %(default)s, i.e. the '
                             'first annotator\'s files).')
    return parser.parse_args()


def collect_files(inputs: list[Path], pattern: str) -> list[Path]:
    """Expands directories in _inputs_ to the files matching _pattern_."""
    files = []
    for path in inputs:
        if path.is_dir():
            files.extend(sorted(path.glob(pattern)))
        else:
            files.append(path)
    return files


def doc_id(xml_file: Path) -> str:
    """blog044_annot1.xml -> blog044."""
    return xml_file.stem.rsplit('_annot', 1)[0]


def simple_from_detailed(detailed: str) -> str:
    """
    Recreates the simple emMorph tag from the detailed analysis, for the few
    tokens where the annotators left it empty. Keeps the last part-of-speech
    tag (or the target POS of the last derivation) and the inflectional tags
    that follow it.

    meg[/Prev]=[] + old[/V] + ani[Inf] -> [/V][Inf]
    """
    pos, infl = None, []
    for morph in detailed.split('+'):
        if '[' not in morph:
            continue
        tag = morph[morph.index('[') + 1:morph.index(']')]
        if tag.startswith('/'):
            pos, infl = tag, []
        elif tag.startswith('_') and '/' in tag:
            pos, infl = '/' + tag.rsplit('/', 1)[1], []
        elif tag:
            infl.append(tag)
    if pos == '/Punct':
        pos = 'Punct'
    return ''.join(f'[{tag}]' for tag in ([pos] if pos else []) + infl)


def correct_analysis(token: ElementTree.Element,
                     where: str) -> tuple[str, str]:
    """Returns the lemma and the simple tag of the correct analysis."""
    anas = [ana for ana in token.iterfind('morph/ana')
            if ana.get('correct') == 'True']
    if len(anas) != 1:
        logger.warning(f'{where}: {len(anas)} correct analyses; '
                       'using the first.')
    if not anas:
        return '_', '_'
    ana = anas[0]

    lemma = (ana.findtext('lemma') or '').strip()
    if lemma == '[None]':
        # emMorph's marker for unknown words: not an error, but no lemma
        lemma = '_'
    elif not lemma:
        logger.warning(f'{where}: no lemma.')
        lemma = '_'

    simple = (ana.findtext('simple') or '').strip()
    if not simple:
        simple = simple_from_detailed(ana.findtext('detailed') or '')
        if simple:
            logger.warning(f'{where}: no simple tag; derived {simple} from '
                           'the detailed analysis.')
        else:
            logger.warning(f'{where}: no simple or detailed tag.')
            simple = '_'
    return lemma, simple


def convert_file(xml_file: Path, converter: EmMorph2UD2) -> Iterator[str]:
    """Yields the CoNLL-U lines for _xml_file_."""
    doc = doc_id(xml_file)
    root = ElementTree.parse(xml_file).getroot()
    yield f'# newdoc id = {doc}'

    for p in root.iterfind('text//p'):
        sentences = [s for s in p.iterfind('s') if s.find('token') is not None]
        if not sentences:
            continue
        yield f'# newpar id = {doc}_{p.get(XML_ID)}'

        for s in sentences:
            rows, text = [], []
            tokens = s.findall('token')
            for i, token in enumerate(tokens, start=1):
                where = f'{xml_file}:{token.get(XML_ID)}'
                form = (token.findtext('form') or '').strip()
                lemma, xpos = correct_analysis(token, where)
                if xpos == '_':
                    upos, feats = '_', '_'
                else:
                    upos, feats = converter.parse(form, lemma, xpos)

                # The join attribute is also set on the first token of the
                # next sentence, but we only need to look forward
                space_after = token.get('join') not in NO_SPACE_AFTER
                if i < len(tokens):
                    space_after &= (tokens[i].get('join')
                                    not in {'left', 'both'})
                text.append(form + (' ' if space_after else ''))
                misc = '_' if space_after else 'SpaceAfter=No'

                rows.append(f'{i}\t{form}\t{lemma}\t{upos}\t{xpos}\t{feats}'
                            f'\t_\t_\t_\t{misc}')

            yield f'# sent_id = {doc}_{s.get(XML_ID)}'
            yield f'# text = {"".join(text).strip()}'
            yield from rows
            yield ''


def convert(files: list[Path], outf: TextIO):
    converter = EmMorph2UD2()
    for xml_file in files:
        logger.info(f'Converting {xml_file}...')
        for line in convert_file(xml_file, converter):
            print(line, file=outf)


def main():
    args = parse_arguments()
    logging.basicConfig(level=logging.INFO,
                        format='%(levelname)s: %(message)s')

    files = collect_files(args.inputs, args.pattern)
    if not files:
        sys.exit('No input files found.')

    if args.output_file:
        args.output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output_file, 'wt', encoding='utf-8') as outf:
            convert(files, outf)
    else:
        convert(files, sys.stdout)


if __name__ == '__main__':
    main()
