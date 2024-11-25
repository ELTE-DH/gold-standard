# National laboratory for Digital Heritage -- Gold standard corpus project

The aim of this project is a general-purpose morphologically annotated corpus that represents the diversity of the Hungarian language.

## Texts

The corpus is planned to represent the following domains:

* academic -- academic publications (aca)

* educational -- texts from educational and cultural web sites (cult)

* informal -- texts from blogs and online forums (blog)
   
* ficcion -- texts from 20th century and contemporary prose (lit)

* legal -- laws and legal documents (leg)

The corpus contains texts that are either not copyrighted or the holder of rights has given premission of use.


## Annotation

The corpus was preprocessed with the emMorph and emTag modules of [emtsv](https://github.com/nytud/emtsv/tree/master). The annotations were manually checked and corrected. The XML files containing the gold standard emMorph annotations are located in [this](https://github.com/ELTE-DH/gold-standard/tree/main/corpus/Morph%20annotated) folder, divided into subfolders by genre.

A converted Universal Dependencies version is also provided,. The conversion was made with the [emmorph2ud2](https://github.com/vadno/emmorph2ud2/tree/main) tool. The converted conllu files are located [here](https://github.com/ELTE-DH/gold-standard/tree/main/corpus/conllu). Academic (aca) texts are merged into educational (cult) genre in this format for balanced representation.
  
## Corpus format

The original format of the corpus is XML with a sequential representation form. The XML elements representing the text units are nested, mapping the structure of the text, and the elements of the lowest level represent the tokens and contain the word or punctuation mark itself.

The \<ana\> elements inside \<morph\> elements contain the analysis options provided by e-magyar. An analysis option includes the lemma, the simplified analysis (POS-tag) and the detailed analysis of the word form. The value of the @correct attribute is "True" if the analysis was defined as correct by the POS tagger module of e-magyar. The value of the @check attribute of \<morph\> elements changes from "False" to "True" when the morphological analysis is checked manually by an annotator.

The UD files follow the [conllu](https://universaldependencies.org/format.html) format.


## Corpus size

| Genre   | Tokens |
|:---|-------:|
| blog | 149416
| aca & cult | 154543
| leg | 132032 |
| lit | 61537 |
| **total** | **497528** | 

## License and usage

The project is funded by National Laboratory for Digital Heritage (Digitális Örökség Nemzeti Laboratórium). The project leader is Andrea Dömötör.

The corpus is available under the license CC-BY-SA 4.0.

If you use this corpus, please cite:

```
K. Molnár Emese, Dömötör Andrea: Gondolatok a gondola-tokról. Morfológiai annotációt javító módszerek tesztelése gold standard korpuszon. In: Berend G., Gosztolya G., Vincze V. (szerk.): XIX. Magyar Számítógépes Nyelvészeti Konferencia, Szeged, 2023. 341--356.
```

