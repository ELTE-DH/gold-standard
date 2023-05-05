import sys
import argparse
import xml.etree.ElementTree as ET


def parse_user_input():
    parser = argparse.ArgumentParser(description="Kiszámolja a két annotátor közti várható- és "
                                                 "véletlenszerű megegyezés értékét",
                                     usage=f'{__file__} ')
    parser.add_argument(dest="target_files", nargs=2, metavar="FILES",
                        help="Add meg az egyes annotátorokhoz tartozó fájlokat egymás után felsorolva.")

    options = parser.parse_args()
    if not len(options.target_files):
        parser.print_help(sys.stderr)
        exit(2)
    return options.target_files


class AnnotatorAgreementCalculator:
    """
        Annotátorok közti várható- és véletlenszerű megegyezés értékének kiszámítása.
        Cohen-féle Kappa együttható megállapítása.
    """
    def __init__(self, annotator_file1, annotator_file2):
        self.token_differences = dict()
        self.id_attrib = '{http://www.w3.org/XML/1998/namespace}id'

        a1_tokens = self.parse_xml(annotator_file1)
        a2_tokens = self.parse_xml(annotator_file2)

        token_objects = self.create_token_objects(a1_tokens, a2_tokens)
        results = self.extract_results(token_objects)
        self.calculate_differences(results)
        self.list_differences(results)


    def create_token_objects(self, a, b):
        """
            Végigmegy az A és B annotátortól érkező tokeneken és token id alapján berendezi az azonos tokeneket a
            token objects dictionary-be, aztán kiszűri az egyes annotátoroknál eltérő tokeneket.
            Ezek a token_differences dictionary-be kerülnek és a későbbi vizsgálatból kimaradnak.
            :param a: 1es annotátor tokenek
            :param b: 2es annotátor tokenek
            :return: token_objects = { token_id: token_a, token_b }
        """
        token_objects = dict()
        each_token = set(
            [a[token].attrib[self.id_attrib] for token in a] +
            [b[token].attrib[self.id_attrib] for token in b]
        )
        for token in each_token:
            token_objects[token] = dict()
            token_objects[token]["modified_a"] = False
            token_objects[token]["modified_b"] = False
            if token in a:
                if a[token][0].attrib["modified"] == 'True':
                    token_objects[token]["modified_a"] = a[token][0].text
                token_objects[token]["a"] = a[token]
                if token in b:
                    if b[token][0].attrib["modified"] == 'True':
                        token_objects[token]["modified_b"] = b[token][0].text
                    token_objects[token]["b"] = b[token]
                else:
                    token_objects[token]["b"] = None
                    self.token_differences[token] = token_objects[token]
            elif token in b:
                if b[token][0].attrib["modified"] == 'True':
                    token_objects[token]["modified_b"] = b[token][0].text

                token_objects[token]["b"] = b[token]
                token_objects[token]["a"] = None
                self.token_differences[token] = token_objects[token]

            if token_objects[token]["modified_a"] and token_objects[token]["modified_b"]:
                if token_objects[token]["modified_a"] != token_objects[token]["modified_b"]:
                    self.token_differences[token] = token_objects[token]
            elif token_objects[token]["modified_a"]:
                self.token_differences[token] = token_objects[token]
            elif token_objects[token]["modified_b"]:
                self.token_differences[token] = token_objects[token]

        for token in self.token_differences:
            token_objects.pop(token)

        return token_objects

    def extract_results(self, token_objects):
        """
            Kinyeri az annotátorok egyes tokenekre adott válaszait, majd a válaszok egyezését True / False -al jelöli.
            Végül visszaadja az egyes válaszokat egy token_id alapján rendezett dictionary-ben
            :param token_objects: token_objects dictionary from self.create_token_objects method
            :return: answers = { token_id: a, b, results }
        """
        answers = dict()
        for token in token_objects:
            answers[token] = dict()
            for ana in token_objects[token]["a"][1]:
                if ana.attrib["correct"] == 'True':
                    answers[token]["a"] = {
                        "lemma": ana[0].text,
                        "detailed": ana[1].text,
                        "simple": ana[2].text
                    }
                    try:
                        answers[token]["a"]["ana_modified"] = ana.attrib["modified"]
                    except KeyError:
                        answers[token]["a"]["ana_modified"] = False

            for ana in token_objects[token]["b"][1]:
                if ana.attrib["correct"] == 'True':
                    answers[token]["b"] = {
                        "lemma": ana[0].text,
                        "detailed": ana[1].text,
                        "simple": ana[2].text
                    }
                    try:
                        answers[token]["b"]["ana_modified"] = ana.attrib["modified"]
                    except KeyError:
                        answers[token]["b"]["ana_modified"] = False

            answers[token]["results"] = {
                "lemma": True if answers[token]["a"]["lemma"] == answers[token]["b"]["lemma"] else False,
                "detailed": True if answers[token]["a"]["detailed"] == answers[token]["b"]["detailed"] else False,
                "simple": True if answers[token]["a"]["simple"] == answers[token]["b"]["simple"] else False
            }

        return answers

    def calculate_differences(self, results):
        """
        Két annotátor közti megegyezés kiszámítása ( Várható- és véletlenszerű megegyezés)
        Cohen-féle kappa együttható meghatározása
        :param results: results from self.extract_results method
        """
        lemma = [0, 0]
        detailed = [0, 0]
        simple = [0, 0]
        lemma_values = dict()
        detailed_values = dict()
        simple_values = dict()
        for token in results:
            for element in results[token]["results"]:
                if results[token]["results"][element]:
                    eval(element)[0] += 1
                else:
                    eval(element)[1] += 1
                    self.token_differences[token] = results[token]

                values = eval(f'{element}_values')
                for annotator in ("a", "b"):
                    if results[token][annotator][element] not in values:
                        values[results[token][annotator][element]] = dict()
                        values[results[token][annotator][element]]["a"] = 0
                        values[results[token][annotator][element]]["b"] = 0
                        values[results[token][annotator][element]][annotator] += 1
                    else:
                        values[results[token][annotator][element]][annotator] += 1

        # # megegyezés elvárható értéke
        all = len(results)
        po_lemma = lemma[0]/all
        po_detailed = detailed[0]/all
        po_simple = simple[0]/all

        # Egyes kategória értékekhez (pl.: simple [/N][Nom]) tartozó p-k megállapítása
        for data_dict in (lemma_values, detailed_values, simple_values):
            for value in data_dict:
                a = data_dict[value]["a"]
                b = data_dict[value]["b"]
                p_value = (a/all) * (b/all)

                data_dict[value] = {
                    "a": a,
                    "b": b,
                    "p": p_value
                }

        # Véletlenszerű megegyezés értéke
        pe_lemma = sum(lemma_values[p_lemma]["p"] for p_lemma in lemma_values)
        pe_detailed = sum(detailed_values[p_detailed]["p"] for p_detailed in detailed_values)
        pe_simple = sum(simple_values[p_simple]["p"] for p_simple in simple_values)

        # Kappa értéke
        k_lemma = (po_lemma - pe_lemma) / (1 - pe_lemma)
        k_detailed = (po_detailed - pe_detailed) / (1 - pe_detailed)
        k_simple = (po_simple - pe_simple) / (1 - pe_simple)

        datas = 'Annotátorok közti megegyezés várható értéke:\n' \
                f'p_o Lemma: {po_lemma}\n' \
                f'p_o Detailed: {po_detailed}\n' \
                f'p_o Simple: {po_simple}\n\n' \
                'Annotátorok közti véletlenszerű megegyezés értéke:\n' \
                f'p_e Lemma: {pe_lemma}\n' \
                f'p_e Detailed: {pe_detailed}\n' \
                f'p_e Simple: {pe_simple}\n\n' \
                'Cohen-féle Kappa értéke:\n' \
                f'k Lemma: {k_lemma}\n' \
                f'k Detailed: {k_detailed}\n' \
                f'k Simple: {k_simple}'
        print(datas)

    def list_differences(self, results):
        """
            Kiírja a két annotátor munkájában talált összes különbséget a meghatározott fájl-ba.
            :param results: results from self.extract_results method
        """
        for result in results:
            for annotator in results[result]:
                for attribute_matches in results[result][annotator]:
                    if not attribute_matches:
                        self.token_differences[result] = results[result]

        with open("annotator_differences.txt", "w", encoding="utf-8") as file:
            for token in sorted(self.token_differences):
                if "modified_a" in self.token_differences[token]:
                    a = self.token_differences[token]["a"][0].text if self.token_differences[token]["a"] else None
                    b = self.token_differences[token]["b"][0].text if self.token_differences[token]["b"] else None
                    line = f'Token: {token} \tEltérő tokenek.\nAnnotátor 1: {a}\nAnnotátor 2: {b}'
                    print(line, sep=", ", flush=True, file=file)
                else:
                    line = f'Token: {token} \tEltérő elemzés.\n' \
                           f'Annotátor 1:\tana modified={self.token_differences[token]["a"]["ana_modified"]}\t' \
                           f'(lemma: {self.token_differences[token]["a"]["lemma"]} | ' \
                           f'detailed: {self.token_differences[token]["a"]["detailed"]} | ' \
                           f'simple: {self.token_differences[token]["a"]["simple"]})\n' \
                           f'Annotátor 2:\tana modified={self.token_differences[token]["b"]["ana_modified"]}\t' \
                           f'(lemma: {self.token_differences[token]["b"]["lemma"]} | ' \
                           f'detailed: {self.token_differences[token]["b"]["detailed"]} | ' \
                           f'simple: {self.token_differences[token]["b"]["simple"]})'
                    print(line, sep=", ", flush=True, file=file)
                file.write("\n")

    def parse_xml(self, file):
        """
            XML fájl feldolgozása az ElementTree python library használatával.
            :param file: annotátor fájl
            :return: tokens = { token_id: token }
        """
        tree = ET.parse(file)
        root = tree.getroot()
        tokens = dict()
        for token in root.findall(".//token"):
            token_id = token.attrib[self.id_attrib]
            tokens[token_id] = token

        return tokens


if __name__ == '__main__':
    annotator_files = parse_user_input()

    aac = AnnotatorAgreementCalculator(
        annotator_file1=annotator_files[0],
        annotator_file2=annotator_files[1]
    ) 
