"""Convert text to CoNLL-U and CoNLL-U to spaCy docs."""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import numpy
from spacy import Errors, Language
from spacy.tokens import Doc, Span, Token
from spacy.training.converters.conllu_to_docs import get_entities
from spacy.training.iob_utils import spans_from_biluo_tags

from spacy_conll.formatter import CONLL_FIELD_NAMES
from spacy_conll.utils import UDPIPE_AVAILABLE

if UDPIPE_AVAILABLE:
    from spacy_udpipe import UDPipeTokenizer

SENT_ID_RE = re.compile(r"(?<=# sent_id = )(\d+)")
NER_TAG_PATTERN = "^((?:name|NE)=)?([BILU])-([A-Z_]+)|O$"


@dataclass(eq=False, repr=False)
class ConllParser:
    """Wrapper around a pipeline with `conll_formatter` that parses text and files.

    The backend (`"spacy"` or `"udpipe"`) is detected from the
    tokenizer of `nlp` and stored in `parser`.

    Args:
        nlp: A pipeline that contains the `conll_formatter` component, for
            example the output of `init_parser`.

    Raises:
        ValueError: If `nlp` has no `conll_formatter` component.
    """

    nlp: Language
    parser: Literal["spacy", "udpipe"] = field(init=False, default="spacy")

    def __post_init__(self):
        """Check the pipeline and detect the backend."""
        if "conll_formatter" not in self.nlp.pipe_names:
            raise ValueError(
                Errors.E001.format(
                    name="conll_formatter", opts=self.nlp.pipe_names
                )
            )

        if UDPIPE_AVAILABLE and isinstance(
            self.nlp.tokenizer, UDPipeTokenizer
        ):
            self.parser = "udpipe"
        else:
            self.parser = "spacy"

    def __repr__(self) -> str:
        """Return the class name and the backend."""
        return f"{self.__class__.__name__}(parser={self.parser})"

    def parse_file_as_conll(
        self,
        input_file: str | os.PathLike[str],
        *,
        input_encoding: str = "utf-8",
        n_process: int = 1,
        renumber_sent_ids: bool = True,
        ignore_pipe_errors: bool = False,
        split_on_newline: bool = True,
    ) -> str:
        """Parse a text file and return its CoNLL-U representation.

        Args:
            input_file: Path to the text file.
            input_encoding: Encoding of `input_file`.
            n_process: See `parse_text_as_conll`.
            renumber_sent_ids: See `parse_text_as_conll`.
            ignore_pipe_errors: See `parse_text_as_conll`.
            split_on_newline: See `parse_text_as_conll`.

        Returns:
            The CoNLL-U string of all sentences in the file.
        """
        text = Path(input_file).resolve().read_text(encoding=input_encoding)

        return self.parse_text_as_conll(
            text,
            n_process=n_process,
            renumber_sent_ids=renumber_sent_ids,
            ignore_pipe_errors=ignore_pipe_errors,
            split_on_newline=split_on_newline,
        )

    def parse_text_as_conll(
        self,
        text: str,
        *,
        n_process: int = 1,
        renumber_sent_ids: bool = True,
        ignore_pipe_errors: bool = False,
        split_on_newline: bool = True,
    ) -> str:
        """Parse a text and return its CoNLL-U representation.

        Each line is a separate doc in `nlp.pipe`, so `# sent_id` would
        restart at 1 for every line. With `renumber_sent_ids`, the sentences
        are numbered 1, 2, 3 and so on over the whole text instead. This only
        matters when the formatter has `include_headers=True`.

        Args:
            text: The text to parse.
            n_process: Number of processes for `nlp.pipe`. -1 uses all
                cores. Values other than 1 require `disable_pandas=True` in
                the formatter, and may not work with UDPipe.
            renumber_sent_ids: Whether to number `# sent_id` consecutively
                over the whole text.
            ignore_pipe_errors: Whether to skip the checks that raise an
                `OSError` when `n_process` is likely to fail on this system.
            split_on_newline: Whether to split the text on newlines and pass
                every line to `nlp.pipe` separately. This is faster for long
                texts.

        Returns:
            The CoNLL-U string, with one empty line between sentences.

        Raises:
            OSError: If `n_process` is not 1, `ignore_pipe_errors` is false,
                and pandas is enabled in the formatter or the backend is
                UDPipe on Windows.
        """
        formatter = self.nlp.get_pipe("conll_formatter")
        if n_process != 1 and not ignore_pipe_errors:
            if not formatter.disable_pandas:
                raise OSError(
                    "Due to pandas serialisation, 'n_process' other than 1 is"
                    " not supported when 'disable_pandas' is False in the"
                    " ConllFormatter. Set 'n_process' to 1 or initialise the"
                    " ConllFormatter with 'disable_pandas=True'"
                )

            # On Windows, UDPipe models cannot be pickled for
            # multiprocessing.
            if os.name == "nt" and self.parser == "udpipe":
                raise OSError(
                    "'n_process' other than 1 is not supported on all"
                    " platforms and parsers. Try again with 'n_process=1',"
                    " or use 'ignore_pipe_errors' to run without this check"
                )

        texts = text.splitlines() if split_on_newline else [text]

        conll_idx = 0
        output = ""
        for doc in self.nlp.pipe(texts, n_process=n_process):
            for sent in doc.sents:
                sent_as_conll = sent._.conll_str
                if not sent_as_conll:
                    continue

                conll_idx += 1
                if formatter.include_headers and renumber_sent_ids:
                    sent_as_conll = SENT_ID_RE.sub(
                        str(conll_idx), sent_as_conll, count=1
                    )

                if conll_idx > 1:
                    sent_as_conll = "\n" + sent_as_conll

                output += sent_as_conll

        return output

    def parse_conll_file_as_spacy(
        self,
        input_file: str | os.PathLike[str],
        *,
        input_encoding: str = "utf-8",
        ner_tag_pattern: str = NER_TAG_PATTERN,
        ner_map: dict[str, str] | None = None,
        strict: bool = True,
    ) -> Doc:
        """Read a CoNLL-U file into a spaCy doc.

        See `parse_conll_text_as_spacy`.

        Args:
            input_file: Path to the CoNLL-U file.
            input_encoding: Encoding of `input_file`.
            ner_tag_pattern: Regex for the entity tag in the MISC field.
            ner_map: Maps old entity labels to new ones. A label that maps to
                `""` becomes `O`.
            strict: See `parse_conll_text_as_spacy`.

        Returns:
            A doc with all sentences of the file and the CoNLL extensions.
        """
        text = Path(input_file).resolve().read_text(encoding=input_encoding)
        return self.parse_conll_text_as_spacy(
            text,
            ner_tag_pattern=ner_tag_pattern,
            ner_map=ner_map,
            strict=strict,
        )

    def parse_conll_text_as_spacy(
        self,
        text: str,
        *,
        ner_tag_pattern: str = NER_TAG_PATTERN,
        ner_map: dict[str, str] | None = None,
        strict: bool = True,
    ) -> Doc:
        r"""Read CoNLL-U text into a spaCy doc.

        Sentences are separated by an empty line, and every sentence block
        becomes one spaCy sentence. Fields that spaCy does not store are kept
        in extensions: DEPS in `Token._.conll_deps_graphs_field`, MISC in
        `Token._.conll_misc_field` and the comment lines in
        `Span._.conll_metadata` of the sentence. A `_` in LEMMA, UPOS, XPOS
        or FEATS leaves that attribute empty in spaCy, and the formatter
        writes `_` again. Multi-word tokens and empty nodes are not
        supported. Adapted from spaCy's `conllu2json` converter.

        With `strict=False`, HEAD and DEPREL may be `_` (both on the same
        line), for example in a file that is tagged but not parsed. Such a
        token has no head in spaCy (`token.has_head()` is false and
        `token.dep_` is `""`), and the formatter writes `_` for both fields.
        The HEAD values of a sentence then do not have to form one tree.

        Args:
            text: CoNLL-U text.
            ner_tag_pattern: Regex for the entity tag in the MISC field.
            ner_map: Maps old entity labels to new ones. A label that maps to
                `""` becomes `O`.
            strict: Whether every token needs a HEAD and a DEPREL, and the
                HEAD values of every sentence must form one tree.

        Returns:
            A doc with all sentences of the text and the CoNLL extensions.

        Raises:
            ValueError: If a line does not have 10 fields, a field is empty,
                a field other than FORM, LEMMA or MISC contains a space, ID
                or HEAD is not a valid number, or only one of HEAD and DEPREL
                is `_`. With `strict=True` also if HEAD or DEPREL is `_`, or
                if the HEAD values of a sentence do not form one tree. The
                message starts with the line number.
            NotImplementedError: If the text has multi-word tokens or empty
                nodes.

        Examples:
            >>> import spacy
            >>> nlp = spacy.blank("en")
            >>> _ = nlp.add_pipe(
            ...     "conll_formatter", config={"include_headers": True}
            ... )
            >>> conll = "\n".join(
            ...     [
            ...         "# sent_id = a1",
            ...         "1\tHi\thi\tINTJ\tUH\t_\t0\troot\t0:root\t_",
            ...         "2\tthere\tthere\tADV\tRB\t_\t1\tadvmod\t1:advmod\tSpaceAfter=No",
            ...     ]
            ... )
            >>> doc = ConllParser(nlp).parse_conll_text_as_spacy(conll)
            >>> [(t.text, t.dep_, t.head.text) for t in doc]
            [('Hi', 'ROOT', 'Hi'), ('there', 'advmod', 'Hi')]
            >>> print(doc._.conll_str.replace("\t", " "))
            # sent_id = a1
            1 Hi hi INTJ UH _ 0 root 0:root _
            2 there there ADV RB _ 1 advmod 1:advmod SpaceAfter=No
            <BLANKLINE>

            A sentence without dependency annotation needs `strict=False`:

            >>> conll = "1\tHi\thi\tINTJ\tUH\t_\t_\t_\t_\t_"
            >>> doc = ConllParser(nlp).parse_conll_text_as_spacy(
            ...     conll, strict=False
            ... )
            >>> [(t.text, t.dep_, t.has_head()) for t in doc]
            [('Hi', '', False)]
            >>> print(doc._.conll_str.replace("\t", " "))
            # sent_id = 1
            # text = Hi
            1 Hi hi INTJ UH _ _ _ _ _
            <BLANKLINE>
        """
        if not Token.has_extension("conll_misc_field"):
            Token.set_extension("conll_misc_field", default="_")
        if not Token.has_extension("conll_deps_graphs_field"):
            Token.set_extension("conll_deps_graphs_field", default="_")
        if not Span.has_extension("conll_metadata"):
            Span.set_extension("conll_metadata", default=None)

        docs = []
        sent_starts = []
        chunk_lineno = 1
        for chunk in text.replace("\r\n", "\n").split("\n\n"):
            numbered_lines = [
                (chunk_lineno + offset, line)
                for offset, line in enumerate(chunk.split("\n"))
                if line.strip() and not line.startswith("#")
            ]
            chunk_lineno += chunk.count("\n") + 2
            if not numbered_lines:
                continue
            lines = [line for _, line in numbered_lines]
            words, spaces, tags, poses, morphs, lemmas, miscs = (
                [],
                [],
                [],
                [],
                [],
                [],
                [],
            )
            heads, deps, deps_graphs = [], [], []
            for lineno, line in numbered_lines:
                parts = line.split("\t")

                if len(parts) != len(CONLL_FIELD_NAMES):
                    raise ValueError(
                        f"Line {lineno}: expected {len(CONLL_FIELD_NAMES)} tab-separated fields but found"
                        f" {len(parts)}. See https://universaldependencies.org/format.html"
                    )

                for name, value in zip(CONLL_FIELD_NAMES, parts, strict=True):
                    if not value:
                        raise ValueError(
                            f"Line {lineno}: the {name} field is empty. According to the CoNLL-U format,"
                            " fields cannot be empty. See https://universaldependencies.org/format.html"
                        )
                    if " " in value and name not in ("FORM", "LEMMA", "MISC"):
                        raise ValueError(
                            f"Line {lineno}: the {name} field contains a space. According to the CoNLL-U"
                            " format, only FORM, LEMMA, and MISC fields can contain spaces. See"
                            " https://universaldependencies.org/format.html"
                        )

                (
                    id_,
                    word,
                    lemma,
                    pos,
                    tag,
                    morph,
                    head,
                    dep,
                    deps_graph,
                    misc,
                ) = parts

                if "." in id_ or "-" in id_:
                    raise NotImplementedError(
                        f"Line {lineno}: multi-word tokens and empty nodes are not supported in spacy_conll"
                    )
                if not id_.isdigit():
                    raise ValueError(
                        f"Line {lineno}: ID must be a number but found {id_!r}"
                    )

                words.append(word)

                if "SpaceAfter=No" in misc:
                    spaces.append(False)
                else:
                    spaces.append(True)

                id_ = int(id_) - 1
                # The token "_" has the lemma "_", so that lemma is not missing.
                lemmas.append("" if lemma == "_" and word != "_" else lemma)
                poses.append("" if pos == "_" else pos)
                tags.append("" if tag == "_" else tag)
                morphs.append(morph if morph != "_" else "")

                if head == "_" or dep == "_":
                    if strict:
                        raise ValueError(
                            f"Line {lineno}: HEAD and DEPREL must be filled in. Use strict=False to read"
                            " sentences without (complete) dependency annotation"
                        )
                    if head != dep:
                        raise ValueError(
                            f"Line {lineno}: HEAD is {head!r} and DEPREL is {dep!r}. Both must be '_' or"
                            " both must be filled in"
                        )
                    heads.append(None)
                    deps.append(None)
                else:
                    if not head.isdigit() or int(head) > len(lines):
                        raise ValueError(
                            f"Line {lineno}: HEAD must be 0 or the ID of a token in the same sentence but"
                            f" found {head!r}"
                        )
                    heads.append((int(head) - 1) if head != "0" else id_)
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

            if strict and (n_sents := len(list(doc.sents))) != 1:
                raise ValueError(
                    f"Line {numbered_lines[0][0]}: the HEAD values of this sentence do not form one tree,"
                    f" so spaCy splits it into {n_sents} sentences. Exactly one token must have HEAD 0."
                    " Use strict=False to read sentences without (complete) dependency annotation"
                )

            # Save the metadata in a custom sentence Span attribute so that the formatter can use it
            metadata = "\n".join(
                [line for line in chunk.splitlines() if line.startswith("#")]
            )
            doc[:]._.conll_metadata = f"{metadata}\n" if metadata else ""

            docs.append(doc)
            sent_starts.extend([1] + [-1] * (len(doc) - 1))

        doc = Doc.from_docs(docs) if docs else Doc(self.nlp.vocab, words=[])
        # Without complete HEAD values, spaCy cannot derive the sentence
        # boundaries from the tree, so every block is marked explicitly.
        doc.from_array(
            ["SENT_START"],
            numpy.array(sent_starts, dtype="int64").astype("uint64"),
        )

        return self.nlp.get_pipe("conll_formatter")(doc)
