import sys
from pathlib import Path
from locale import getpreferredencoding

from spacy.tokens import Doc


class Spacy2ConllParser:
    def __init__(self, model='en_core_web_sm', nlp=None, disable_sbd=False, verbose=False):
        self.h_out = None
        if nlp is not None:
            self.nlp = nlp
        else:
            model = __import__(model)
            self.nlp = model.load()

        if disable_sbd:
            self.nlp.add_pipe(Spacy2ConllParser.prevent_sbd, name='prevent-sbd', before='parser')

        self.disable_sbd = disable_sbd

        # To get the morphological info, we need a tag map
        self.tagmap = self.nlp.Defaults.tag_map

        self.verbose = verbose
        self.is_tokenized = self.include_headers = False

    def _close_h_out(self):
        # Close output stream
        if self.h_out is not sys.stdout:
            self.h_out.close()

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
        tagger = self.nlp.get_pipe('tagger')
        sbd_preventer = self.nlp.get_pipe('prevent-sbd') if self.disable_sbd else None
        parser = self.nlp.get_pipe('parser')

        line_idx = 0
        for line in text:
            # Only strip new lines and carriages returns. Other space characters might be meaningful
            line = line.strip('\r\n')
            if self.is_tokenized:
                # Remove empty strings from tokens
                tokens = list(filter(None, line.split(' ')))
                doc = Doc(self.nlp.vocab, words=tokens)
            else:
                doc = self.nlp(line)

            tagger(doc)
            if self.disable_sbd:
                sbd_preventer(doc)
            parser(doc)

            last_idx = line_idx
            for idx, parsed_sent in self._sentences_to_conllu(doc, line_idx):
                yield parsed_sent
                last_idx = idx
            line_idx = last_idx

    def _open_h_out(self, output_file, output_encoding):
        # Open output stream
        if output_file:
            self.h_out = open(Path(output_file).resolve(), mode='w', encoding=output_encoding)
        else:
            self.h_out = sys.stdout

    def _sentences_to_conllu(self, doc, line_idx):
        for sent in doc.sents:
            line_idx += 1
            parsed_sent = ''

            if self.include_headers:
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

            if self.h_out is not sys.stdout and self.verbose:
                print(parsed_sent)

            yield line_idx, parsed_sent

    def parse(self, input_file=None, input_str=None, input_encoding=getpreferredencoding(), is_tokenized=False,
              include_headers=False):
        self.is_tokenized = is_tokenized
        inp_p, inp_str = self._set_input(input_file, input_str)
        self.include_headers = include_headers

        if inp_p:
            with open(inp_p, mode='r', encoding=input_encoding) as fhin:
                yield from self._iterate(fhin)
        else:
            yield from self._iterate(inp_str.split('\n'))

    def parseprint(self, input_file=None, input_str=None, input_encoding=getpreferredencoding(), is_tokenized=False,
                   output_file=None, output_encoding=getpreferredencoding(), include_headers=False):
        self._open_h_out(output_file, output_encoding)

        # Get parsed sentences
        for parsed_sent in self.parse(input_file=input_file, input_str=input_str, input_encoding=input_encoding,
                                      is_tokenized=is_tokenized, include_headers=include_headers):
            self.h_out.write(parsed_sent + '\n')

        self._close_h_out()

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

    @staticmethod
    def prevent_sbd(doc):
        """ Disables spaCy's sentence boundary detection """
        for token in doc:
            token.is_sent_start = False
        return doc
