# National laboratory for Digital Heritage -- Gold standard corpus project

The aim of this project is a general-purpose treebank which represents the diversity of the Hungarian language.

## Texts

The corpus is planned to represent the following domains:

* academic -- theses, dissertations, academic publications

* press -- texts of online news portals

* educational -- texts from educational and cultural web sites

* informal -- texts from blogs and online forums
   
* literature -- texts from 20th century and contemporary prose

* technical -- field-specific texts (legal, medical, IT, etc.)

* legal -- laws and legal documents

The corpus will only contain texts that are either not copyrighted or the holder of rights has given premission of use. Currently, the project is in the phase of morphological annotation. The repository is updated with new annotated texts weekly.


## Annotation

The annotation of the corpus will contain all levels of linguistic analysis from lemmatization to dependency parsing. The levels of annotation will get separate representations and our label sets follow the state-of-the-art Hungarian (emMorph) and international (Universal Dependencies) standards.

The current texts in the repository contain the emMorph annotations of morphology.

  
## Corpus format

The format of the corpus is XML with a sequential representation form. The XML elements representing the text units are nested, mapping the structure of the text, and the elements of the lowest level represent the tokens and contain the word or punctuation mark itself.

The \<ana\> elements inside \<morph\> elements contain the analysis options provided by e-magyar. An analysis option includes the lemma, the simplified analysis (POS-tag) and the detailed analysis of the word form. The value of the @correct attribute is "True" if the analysis was defined as correct by the POS tagger module of e-magyar. The value of the @check attribute of \<morph\> elements changes from "False" to "True" when the morphological analysis is checked manually by an annotator.


## Content of this repository

The "pilot" subdirectory of the repository contains the pilot annotations, which were made between May and August 2021. The repository also contains the annotation guidelines (in Hungarian), and the scripts that we used for the preprocessing of the texts and the measurement of inter-annotator agreement. The "corpus" subfolder contains the preprocessed xml files. The commit message "original files" indicates that the annotations of the file have not been manually checked yet.

## Corpus size

Corpus building and annotation are in progress. Size information is updated weekly (usually on Mondays).

Last update: 2023. 06. 05.

|    | Tokens |
|:---|-------:|
| Texts uploaded | 485908
| Morphology manually corrected | 417239
| Morphology validated | 0 |

## License and usage

The project is funded by National Laboratory for Digital Heritage (Digitális Örökség Nemzeti Laboratórium). The project leader is Andrea Dömötör.

The corpus is available under the license CC-BY-SA 4.0.

If you use this corpus, please cite:

```
K. Molnár Emese, Dömötör Andrea: Gondolatok a gondola-tokról. Morfológiai annotációt javító módszerek tesztelése gold standard korpuszon. In: Berend G., Gosztolya G., Vincze V. (szerk.): XIX. Magyar Számítógépes Nyelvészeti Konferencia, Szeged, 2023. 341--356.
```

