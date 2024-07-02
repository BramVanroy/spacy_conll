import os
import re
from dataclasses import dataclass, field
from locale import getpreferredencoding
from os import PathLike
from pathlib import Path
from typing import Dict, Union

from spacy import Errors, Language
from spacy.tokens import Doc, Span, Token
from spacy.training.converters.conllu_to_docs import get_entities
from spacy.training.iob_utils import spans_from_biluo_tags
from spacy_conll.utils import STANZA_AVAILABLE, UDPIPE_AVAILABLE


if STANZA_AVAILABLE:
    from spacy_stanza.tokenizer import StanzaTokenizer

if UDPIPE_AVAILABLE:
    from spacy_udpipe import UDPipeTokenizer

SENT_ID_RE = re.compile(r"(?<=# sent_id = )(\d+)")


@dataclass(eq=False, repr=False)
class ConllParser:
    """Constructor for a ConllParser, which is a wrapper around a spaCy-like parser with a ConllFormatter
    component. This class simply provides convenience methods to parse text according to some options.

    Constructor arguments:
    :param nlp: instantiated spaCy-like parser
    """

    nlp: Language
    parser: str = field(init=False, default=None)

    def __post_init__(self):
        if "conll_formatter" not in self.nlp.pipe_names:
            raise ValueError(Errors.E001.format(name="conll_formatter", opts=self.nlp.pipe_names))

        # Figure out what kind of parser was provided (needed during data preparation)
        if STANZA_AVAILABLE and isinstance(self.nlp.tokenizer, StanzaTokenizer):
            self.parser = "stanza"
            import torch

            # Fixes some pickling issues
            # See https://github.com/explosion/spacy-stanza/issues/34
            torch.set_num_threads(1)
        elif UDPIPE_AVAILABLE and isinstance(self.nlp.tokenizer, UDPipeTokenizer):
            self.parser = "udpipe"
        else:
            self.parser = "spacy"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(parser={self.parser})"

    def parse_file_as_conll(
        self, input_file: Union[PathLike, Path, str], input_encoding: str = getpreferredencoding(), **kwargs
    ) -> str:
        """Parses a given input file with self.parser and returns its CoNLL output.
        :param input_file: path to the input file to process
        :param input_encoding: encoding of 'input_file'
        :param kwargs: keyword arguments that will be passed to `parse_text_as_conll`
        """
        text = Path(input_file).resolve().read_text(encoding=input_encoding)

        return self.parse_text_as_conll(text, **kwargs)

    def parse_text_as_conll(
        self,
        text: str,
        n_process: int = 1,
        no_force_counting: bool = False,
        ignore_pipe_errors: bool = False,
        no_split_on_newline: bool = False,
    ) -> str:
        """Parses a given text (string) with self.parser and returns its CoNLL output.
        :param text: input text (string) to process
        :param n_process: number of processes to use in nlp.pipe(). -1 will use as many cores as available. Might not
               work for a 'parser' other than 'spacy' depending on your environment
        :param no_force_counting: whether to  disable force counting the 'sent_id', starting from 1 and increasing for
               each sentence. Instead, 'sent_id' will depend on how spaCy returns the sentences. Must have
               'self.include_headers' enabled
        :param ignore_pipe_errors: whether to ignore a priori errors concerning 'n_process' By default we try to
               determine whether processing works on your system and stop execution if we think it doesn't. If you
               know what you are doing, you can ignore such pre-emptive errors, though, and run the code as-is, which
               will then throw the default Python errors when applicable
        :param no_split_on_newline: by default, the input text will be split on newlines for faster processing. This
               can be disabled with this option
        """
        if n_process > 1 and not ignore_pipe_errors:
            if not self.nlp.get_pipe("conll_formatter").disable_pandas:
                raise OSError(
                    "Due to pandas serialisation, 'n_process' > 1 is not supported when"
                    " 'disable_pandas' is False in the ConllFormatter. Set 'n_process' to 1 or"
                    " initialise the ConllFormatter with 'disable_pandas=True'"
                )

            # Seems that Windows only supports mp on spaCy. Both for UDPipe and Stanza the issue is
            # pickling of the models
            if os.name == "nt" and self.parser in ["udpipe", "stanza"]:
                raise OSError(
                    "'n_process' > 1 is not supported on all platforms/all parsers. Please try again with"
                    " the default value 'n_process' = 1. You can also try to run the code without this pre-emptive"
                    " error message by using the 'ignore_pipe_errors' option"
                )

        if no_split_on_newline:
            text = [text]
        else:
            text = text.splitlines()

        conll_idx = 0
        output = ""
        for doc_idx, doc in enumerate(self.nlp.pipe(text, n_process=n_process)):
            for sent in doc.sents:
                conll_idx += 1

                sent_as_conll = sent._.conll_str
                if self.nlp.get_pipe("conll_formatter").include_headers and not no_force_counting:
                    # nlp.pipe returns different docs, meaning that the generated sentence indices
                    # by ConllFormatter are not consecutive (they reset for each new doc)
                    # We can do a regex replace to fix that, though.
                    sent_as_conll = re.sub(SENT_ID_RE, str(conll_idx), sent_as_conll, 1)

                # Prepend additional newline for all except the very first string.
                if not (doc_idx == 0 and sent.start == 0):
                    sent_as_conll = "\n" + sent_as_conll

                output += sent_as_conll

        return output

    def parse_conll_file_as_spacy(
        self,
        input_file: Union[PathLike, Path, str],
        input_encoding: str = getpreferredencoding(),
        ner_tag_pattern: str = "^((?:name|NE)=)?([BILU])-([A-Z_]+)|O$",
        ner_map: Dict[str, str] = None,
    ) -> Doc:
        """Parses a given CoNLL-U file into a spaCy doc. Parsed sentence section must be separated by a new line.
        See :py:meth:`ConllParser.parse_conll_text_as_spacy`.
        :param input_file: path to the input file to process
        :param input_encoding: encoding of 'input_file'
        :param ner_tag_pattern: Regex pattern for entity tag in the MISC field
        :param ner_map: Map old NER tag names to new ones, '' maps to O
        :return: a spacy Doc containing all the tokens and sentences from the CoNLL file including the custom CoNLL extensions
        """
        text = Path(input_file).resolve().read_text(encoding=input_encoding)
        return self.parse_conll_text_as_spacy(text, ner_tag_pattern=ner_tag_pattern, ner_map=ner_map)

    def parse_conll_text_as_spacy(
        self,
        text: str,
        ner_tag_pattern: str = "^((?:name|NE)=)?([BILU])-([A-Z_]+)|O$",
        ner_map: Dict[str, str] = None,
    ) -> Doc:
        """Parses a given CoNLL-U string into a spaCy doc. Parsed sentence section must be separated by a new line (\n\n).
        Note that we do our best to retain as much information as possible but that not all CoNLL-U fields are
        supported in spaCy. We add a Token._.conll_misc_field extension to save CoNLL-U MISC field, and a
        Token._.conll_deps_graphs_field extension to save CoNLL-U DEPS field. The metadata (lines starting with #)
        is saved in Span._.conll_metadata of sentence Spans.

        This method has been adapted from the work by spaCy.
        See: https://github.com/explosion/spaCy/blob/a1c5b694be117ac92e21f9860309821ad6da06f7/spacy/cli/converters/conllu2json.py#L179

        Multi-word tokens and empty nodes are not supported.

        :param text: CoNLL-U formatted text
        :param ner_tag_pattern: Regex pattern for entity tag in the MISC field
        :param ner_map: Map old NER tag names to new ones, '' maps to O
        :return: a spacy Doc containing all the tokens and sentences from the CoNLL file including
         the custom CoNLL extensions
        """
        if not Token.has_extension("conll_misc_field"):
            Token.set_extension("conll_misc_field", default="_")
        if not Token.has_extension("conll_deps_graphs_field"):
            Token.set_extension("conll_deps_graphs_field", default="_")
        if not Span.has_extension("conll_metadata"):
            Span.set_extension("conll_metadata", default=None)

        docs = []
        for chunk in text.split("\n\n"):
            lines = [l for l in chunk.splitlines() if l and not l.startswith("#")]
            words, spaces, tags, poses, morphs, lemmas, miscs = [], [], [], [], [], [], []
            heads, deps, deps_graphs = [], [], []
            for i in range(len(lines)):
                line = lines[i]
                parts = line.split("\t")

                if any(not p for p in parts):
                    raise ValueError(
                        "According to the CoNLL-U Format, fields cannot be empty. See"
                        " https://universaldependencies.org/format.html"
                    )

                id_, word, lemma, pos, tag, morph, head, dep, deps_graph, misc = parts

                if any(" " in f for f in (id_, pos, tag, morph, head, dep, deps_graph)):
                    raise ValueError(
                        "According to the CoNLL-U Format, only FORM, LEMMA, and MISC fields can contain"
                        " spaces. See https://universaldependencies.org/format.html"
                    )

                if "." in id_ or "-" in id_:
                    raise NotImplementedError("Multi-word tokens and empty nodes are not supported in spacy_conll")

                words.append(word)

                if "SpaceAfter=No" in misc:
                    spaces.append(False)
                else:
                    spaces.append(True)

                id_ = int(id_) - 1
                lemmas.append(lemma)
                poses.append(pos)
                tags.append(pos if tag == "_" else tag)
                morphs.append(morph if morph != "_" else "")
                heads.append((int(head) - 1) if head not in ("0", "_") else id_)
                deps.append("ROOT" if dep == "root" else dep)
                deps_graphs.append(deps_graph)
                miscs.append(misc)

            doc = Doc(
                self.nlp.vocab,
                words=words,
                spaces=spaces,
                tags=tags,
                pos=poses,
                morphs=morphs,
                lemmas=lemmas,
                heads=heads,
                deps=deps,
            )

            # Set custom Token extensions
            for i in range(len(doc)):
                doc[i]._.conll_misc_field = miscs[i]
                doc[i]._.conll_deps_graphs_field = deps_graphs[i]

            ents = get_entities(lines, ner_tag_pattern, ner_map)
            doc.ents = spans_from_biluo_tags(doc, ents)

            # The deprel relations ensure that this CoNLL chunk is one sentence
            # Deprel cannot therefore not be empty or each word is considered a separate sentence
            if len(list(doc.sents)) != 1:
                raise ValueError(
                    "Your data is in an unexpected format. Make sure that it follows the CoNLL-U format"
                    " requirements. See https://universaldependencies.org/format.html. Particularly make"
                    " sure that the DEPREL field is filled in."
                )

            # Save the metadata in a custom sentence Span attribute so that the formatter can use it
            metadata = "\n".join([l for l in chunk.splitlines() if l.startswith("#")])
            # We really only expect one sentence
            for sent in doc.sents:
                sent._.conll_metadata = f"{metadata}\n" if metadata else ""

            docs.append(doc)

        # Add CoNLL custom extensions
        return self.nlp.get_pipe("conll_formatter")(Doc.from_docs(docs))
