import sys
from pathlib import Path

import spacy


def _sentences_to_conllu(doc, sent_id, tagmap, handle):
    for sent in doc.sents:
        handle.write(f'# sent_id = {str(sent_id)}\n')
        handle.write(f'# text = {sent.sent}\n')

        for word in sent:
            if word.dep_.lower().strip() == 'root':
                head_idx = 0
            else:
                head_idx = word.head.i + 1 - sent[0].i

            tok_tuple = (
                word.i+1,
                word.text,
                word.lemma_,
                word.pos_,
                word.tag_,
                _get_morphology(word.tag_, tagmap),
                head_idx,
                word.dep_,
                '_',
                '_'
            )

            handle.write('\t'.join(map(lambda x: str(x), tok_tuple))+'\n')
        handle.write('\n')
    return None


def _get_morphology(tag, tagmap):
    if not tagmap or tag not in tagmap:
        return '_'
    else:
        return '|'.join([f'{prop}={val}' for prop, val in tagmap[tag].items() if not _is_number(prop)])


def _is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def _iterate(main_in, handle, nlp):
    tagmap = nlp.Defaults.tag_map
    for idx, line in enumerate(main_in, 1):
        doc = nlp(line.strip())
        _sentences_to_conllu(doc, idx, tagmap, handle)
    return None


def main(main_in, is_file, handle=sys.stdout, nlp='en_core_web_sm'):
    nlp = spacy.load(nlp)

    if is_file:
        with open(main_in, "r", encoding='utf-8') as fhin:
            _iterate(fhin, handle, nlp)
    else:
        _iterate(main_in.split('\n'), handle, nlp)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--input_file", help="Path to file with sentences to parse.")
    parser.add_argument("--input_str", help="Input string to parse.")
    parser.add_argument("--output_file", default='', help="Path to output file. If not specified, the output will be "
                                                          "printed on standard output.")
    parser.add_argument("--model", default='en_core_web_sm', help="Spacy model to use (e.g. 'es_core_news_md').")
    args = parser.parse_args()

    inp_is_file = False
    if args.input_file:
        inp = Path(args.input_file)
        if not inp.exists() or not inp.is_file():
            raise ValueError("'input_file' must be a file")
        inp_is_file = True
    elif args.input_str:
        inp = args.input_str
    else:
        raise ValueError('No input specified')

    h_out = open(Path(args.output_file).resolve(), 'w', encoding='utf-8') if args.output_file else sys.stdout

    main(inp, inp_is_file, h_out, args.model)

    if h_out is not sys.stdout:
        h_out.close()
