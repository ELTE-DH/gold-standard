from pathlib import Path
from itertools import pairwise
from typing import Iterator, Any
from xml.etree import ElementTree

XML_NS = '{http://www.w3.org/XML/1998/namespace}'

LEFT = {'left', 'both'}
RIGHT = {'right', 'both'}


def validate_joins(tokens):
    # Boundary checks
    if tokens[0]['join'] in LEFT:
        yield f'Token ({tokens[0]["id"]}) \'{tokens[0]["form"]}\'' \
              f' requires a left join ({tokens[0]["join"]}) but has no left neighbour'

    if tokens[-1]['join'] in RIGHT:
        yield f'Token ({tokens[-1]["id"]}) \'{tokens[-1]["form"]}\'' \
              f' requires a right join ({tokens[-1]["join"]}) but has no right neighbour'

    # Check every adjacent pair
    for left, right in pairwise(tokens):
        left_wants_right = left['join'] in RIGHT
        right_wants_left = right['join'] in LEFT

        if left_wants_right != right_wants_left:
            if left_wants_right:
                yield f'Token ({left["id"]}) \'{left["form"]}\' wants to join right ({left["join"]}),' \
                      f' but \'{right["form"]}\' does not accept a left join ({right["join"]})'
            else:
                yield f'Token ({right["id"]}) \'{right["form"]}\' wants to join left ({right["join"]}),' \
                      f' but \'{left["form"]}\' does not accept a right join ({left["join"]})'


def none_or_text_none_or_empty(element):
    if element is None or element.text is None:
        return True

    return len(element.text.strip()) == 0


def stripped_text_or_empty(element):
    if element is None or element.text is None:
        return ''

    return element.text.strip()


def parse_tei(filename) -> Iterator[dict[str, Any]]:
    try:
        tree = ElementTree.parse(filename)
    except ElementTree.ParseError:
        print(filename)
        raise
    root = tree.getroot()

    text = root.find('.//text')
    if text is None:
        raise NotImplementedError('Text tag not found!')

    # Paragraphs
    paragraphs = text.findall('.//p')
    if len(paragraphs) == 0:
        raise NotImplementedError('No paragraph found!')

    for p in paragraphs:
        sentences = p.findall('./s')
        if len(sentences) == 0:
            raise NotImplementedError('Empty paragraph!')
        for s in sentences:
            out_sentence = {'id': s.attrib[XML_NS + 'id'], 'tokens': []}

            try:
                tokens = s.findall('./token')
                if len(tokens) == 0:
                    raise NotImplementedError('Empty sentence!')
                for tok in tokens:
                    form = tok.find('form')
                    if none_or_text_none_or_empty(form):
                        raise NotImplementedError('Empty form!')

                    morph = tok.find('morph')
                    if morph is None:
                        raise NotImplementedError('No morph tag found!')
                    anas = morph.findall('ana')
                    if len(anas) == 0:
                        raise NotImplementedError('Empy ana!')

                    for ana in anas:
                        if ana.attrib.get('correct') != 'True':
                            continue

                        lemma = ana.find('lemma')
                        detailed = ana.find('detailed')
                        simple = ana.find('simple')

                        if none_or_text_none_or_empty(lemma) or none_or_text_none_or_empty(simple):
                            raise NotImplementedError('Missing analyse field!')

                        lemma_val = stripped_text_or_empty(lemma)
                        detailed_val = stripped_text_or_empty(detailed)
                        simple_val = stripped_text_or_empty(simple)
                        break
                    else:
                        raise NotImplementedError('No correct ana!')

                    join_attr = tok.attrib['join']
                    if join_attr not in {'left', 'right', 'both', 'no'}:
                        raise ValueError('Join has incorrect value!')

                    token = {'form': stripped_text_or_empty(form), 'join': join_attr, 'lemma': lemma_val,
                             'detailed': detailed_val, 'simple': simple_val, 'id': tok.attrib[XML_NS + 'id']}

                    out_sentence['tokens'].append(token)
            except NotImplementedError:
                continue

            yield out_sentence


def iter_xml_files(directory):
    directory = Path(directory)

    if not directory.is_dir():
        raise NotADirectoryError(directory)

    yield from sorted(directory.glob('**/*.xml'))


if __name__ == '__main__':
    for xml_file in iter_xml_files('../corpus/Morph annotated'):
        sents = parse_tei(xml_file)
        for sent in sents:
            sent_tokens: list[dict] = sent['tokens']
            for err in validate_joins(sent_tokens):
                print(xml_file, sent['id'], err)
                print(*(tok['form'] for tok in sent['tokens']))
