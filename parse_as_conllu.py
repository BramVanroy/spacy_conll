"""
__author__ = "Raquel G. Alhama"
__email__ = "rgalhama@gmail.com"

Parse text with spaCy and print the output in CoNLL-U format.

References:
https://spacy.io/
http://universaldependencies.org/format.html

"""
import sys
import argparse
from pathlib import Path
import spacy


def sentences_to_conllu(doc, sent_id, prefix = ""):
    """ Prints parsed sentences in CONLL-U format (as used in Universal Dependencies).
        The format is specified at http://universaldependencies.org/docs/format.html
    """
    for sent in doc.sents:
        print("# sent_id = %s"%(prefix+str(sent_id)))
        print("# text = %s"%sent.sent)

        for i, word in enumerate(sent):
            #Find head
            if word.dep_.lower().strip() == 'root':
                head_idx = 0
            else:
                head_idx = word.head.i + 1 - sent[0].i

            #Find feature tag (if available)
            ftidx = word.tag_.find("__") + 2
            feature_tag=word.tag_[ftidx:]

            linetuple = (
                i+1,                                        #ID: Word index.
                word,                                       #FORM: Word form or punctuation symbol.
                word.lemma_.lower(),                        #LEMMA: Lemma or stem of word form.
                word.pos_,                                  #UPOSTAG: Universal part-of-speech tag drawn
                                                            # from revised version of the Google universal
                                                            # POS tags.
                '_',                                        #XPOSTAG: Language-specific part-of-speech tag;                                            # underscore if not available.
                '_' if feature_tag == "" else feature_tag,  #FEATS: List of morphological features from the
                                                            # universal feature inventory or from a defined
                                                            # language-specific extension; underscore if not
                                                            # available.
                head_idx,                                   #HEAD: Head of the current token, which is
                                                            # either a value of ID or zero (0).
                word.dep_.lower(),                          #DEPREL: Universal Stanford dependency relation
                                                            # to the HEAD (root iff HEAD = 0) or a defined
                                                            # language-specific subtype of one.
                '_',                                        #DEPS: List of secondary dependencies.
                '_'                                         #MISC: Any other annotation.
            )
            print("%i\t%s\t%s\t%s\t%s\t%s\t%i\t%s\t%s\t%s"%linetuple)

        sent_id+=1
        print("\n")
    return sent_id


def main(input_file, output_file, prefix = ""):

    nlp = spacy.load(args.model)

    if output_file:
        sys.stdout=open(output_file, "w")

    with open(input_file, "r", encoding='utf-8') as fh:
        sent_id = 1
        for nl,line in enumerate(fh):
            doc = nlp(line.strip())
            sent_id = sentences_to_conllu(doc, sent_id, prefix=prefix)

    sys.stdout = sys.__stdout__

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--input_file", required=True, type=Path, help="Path to file with sentences to parse.")
    parser.add_argument("--output_file", default=None, type=Path, help="Path to output file. If not specified, the output will be printed on standard output.")
    parser.add_argument("--model", required=True, type=str, help="Spacy model to use (e.g. 'es_core_news_md').")
    args = parser.parse_args()

    in_file = Path.expanduser(args.input_file)
    out_file = args.output_file if args.output_file is None else Path.expanduser(args.output_file)

    if not Path.exists(in_file):
        raise Exception(in_file, " does not exist!")

    main(in_file, out_file, args.model)

