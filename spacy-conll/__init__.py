import sys
from pathlib import Path
from locale import getpreferredencoding


class Spacy2ConllParser:
    def __init__(self, model='en_core_web_sm', nlp=None):
        self.h_out = None

        if nlp is not None:
            self.nlp = nlp
        else:
            model = __import__(model)
            self.nlp = model.load()

        # To get the morphological info, we need a tag map
        self.tagmap = self.nlp.Defaults.tag_map

    def _sentences_to_conllu(self, doc, line_idx):
        for sent in doc.sents:
            line_idx += 1

            parsed_sent = f'# sent_id = {str(line_idx)}\n'
            parsed_sent += f'# text = {sent.sent}\n'
            for idx, word in enumerate(sent, 1):
                if word.dep_.lower().strip() == 'root':
                    head_idx = 0
                else:
                    head_idx = word.head.i + 1 - sent[0].i

                line_tuple = (
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
                parsed_sent += '\t'.join(map(lambda x: str(x), line_tuple)) + '\n'
            yield line_idx, parsed_sent

    def _get_morphology(self, tag):
        if not self.tagmap or tag not in self.tagmap:
            return '_'
        else:
            feats = [f'{prop}={val}' for prop, val in self.tagmap[tag].items() if not Spacy2ConllParser._is_number(prop)]
            if feats:
                return '|'.join(feats)
            else:
                return '_'

    def _iterate(self, text):
        line_idx = 0
        for line in text:
            doc = self.nlp(line.strip())
            for idx, parsed_sent in self._sentences_to_conllu(doc, line_idx):
                yield parsed_sent
            line_idx = idx

    def parse(self, input_file=None, input_str=None, input_encoding=getpreferredencoding()):
        inp_p, inp_str = self._set_input(input_file, input_str)

        if inp_p:
            with open(inp_p, mode='r', encoding=input_encoding) as fhin:
                return self._iterate(fhin)
        else:
            return self._iterate(inp_str.split('\n'))

    def parseprint(self, input_file=None, input_str=None, input_encoding=getpreferredencoding(),
                   output_file=None, output_encoding=getpreferredencoding()):
        # Open output stream
        if output_file:
            h_out = open(Path(output_file).resolve(), mode='w', encoding=output_encoding)
        else:
            h_out = sys.stdout

        # Get parsed sentences
        for parsed_sent in self.parse(input_file, input_str, input_encoding):
            h_out.write(parsed_sent + '\n')

        # Close output stream
        if h_out is not sys.stdout:
            h_out.close()

    @staticmethod
    def _set_input(input_file, inp_str):
        if input_file:
            inp_p = Path(input_file).resolve()
            if not inp_p.exists() or not inp_p.is_file():
                raise ValueError(f"'input_file' must be a file. '{str(inp_p)}' given.")
            return inp_p, None
        elif inp_str:
            return None, inp_str
        else:
            raise ValueError("No input given. Use 'input_file' or 'input_str'.")

    @staticmethod
    def _is_number(s):
        try:
            float(s)
            return True
        except ValueError:
            return False
