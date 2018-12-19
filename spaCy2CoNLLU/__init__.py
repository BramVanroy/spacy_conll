import sys
from pathlib import Path
from locale import getpreferredencoding
import spacy


class Spacy2ConllParser:
    def __init__(self, input_file=None, input_str=None, input_encoding=getpreferredencoding(), output_file=None,
                 output_encoding=getpreferredencoding(), model='en_core_web_sm'):
        self.input = None
        self.input_is_file = None
        self.input_encoding = input_encoding
        self._set_input(input_file, input_str)

        self.output_file = Path(output_file).resolve() if output_file else None
        self.output_encoding = output_encoding
        self.h_out = None

        self.nlp = spacy.load(model)
        self.tagmap = self.nlp.Defaults.tag_map

    def _open_h_out(self):
        if self.output_file:
            self.h_out = open(self.output_file, mode='w', encoding=self.output_encoding)
        else:
            self.h_out = sys.stdout

    def _close_h_out(self):
        if self.h_out is not sys.stdout:
            self.h_out.close()

    def _sentences_to_conllu(self, doc, line_idx):
        for sent in doc.sents:
            line_idx += 1
            self.h_out.write(f'# sent_id = {str(line_idx)}\n')
            self.h_out.write(f'# text = {sent.sent}\n')

            for idx, word in enumerate(sent, 1):
                if word.dep_.lower().strip() == 'root':
                    head_idx = 0
                else:
                    head_idx = word.head.i + 1 - sent[0].i

                tok_tuple = (
                    idx,
                    word.text,
                    word.lemma_,
                    word.pos_,
                    word.tag_,
                    self._get_morphology(word.tag_),
                    head_idx,
                    word.dep_,
                    '_',
                    '_'
                )
                self.h_out.write('\t'.join(map(lambda x: str(x), tok_tuple))+'\n')
            self.h_out.write('\n')
        return line_idx

    def _get_morphology(self, tag):
        if not self.tagmap or tag not in self.tagmap:
            return '_'
        else:
            feats = [f'{p}={v}' for p, v in self.tagmap[tag].items() if not Spacy2ConllParser._is_number(p)]
            return '|'.join(feats)

    def _iterate(self, text):
        line_idx = 0
        for line in text:
            doc = self.nlp(line.strip())
            line_idx = self._sentences_to_conllu(doc, line_idx)
        return None

    def parse(self, input_file=None, input_str=None, input_encoding=None):
        self._open_h_out()

        self._set_input(input_file, input_str)
        self.input_encoding = input_encoding if input_encoding else self.input_encoding
        if self.input_is_file:
            with open(self.input, mode='r', encoding=self.input_encoding) as fhin:
                self._iterate(fhin)
        else:
            self._iterate(self.input.split('\n'))

        self._close_h_out()

    def _set_input(self, input_file, input_str):
        if input_file:
            self.input = Path(input_file).resolve()
            if not self.input.exists() or not self.input.is_file():
                raise ValueError(f"'input_file' must be a file. '{str(self.input)}' given.")
            self.input_is_file = True
        elif input_str:
            self.input = input_str
            self.input_is_file = False

    @staticmethod
    def _is_number(s):
        try:
            float(s)
            return True
        except ValueError:
            return False


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--input_file", help="Path to file with sentences to parse.")
    parser.add_argument("--input_str", help="Input string to parse.")
    parser.add_argument("--output_file", default='', help="Path to output file. If not specified, the output will be "
                                                          "printed on standard output.")
    parser.add_argument("--model", default='en_core_web_sm', help="Spacy model to use (e.g. 'es_core_news_md').")
    args = parser.parse_args()

    spacyconll = Spacy2ConllParser(input_str="Hello world. How are you today?", output_file="test.txt", input_encoding='utf-8')

    spacyconll.parse()
