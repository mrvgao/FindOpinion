from stanfordcorenlp import StanfordCoreNLP
from functools import lru_cache
import word_cutter

nlp = StanfordCoreNLP('http://127.0.0.1', port=9000, lang='zh')


self_defined_organizations = [org.strip() for org in open('data/organizations.txt', encoding='utf-8')]


def find_person_entities(text):
    result = get_ner(text)
    return [
        w for w, n in result
        if n in ['PERSON', 'ORGANIZATION'] or w in self_defined_organizations
    ]


@lru_cache(maxsize=128)
def get_ner(text):
    text = word_cutter.cut(text)
    text = " ".join(text)
    return nlp.ner(text)


@lru_cache(maxsize=128)
def get_pos_tag(text):
    text = word_cutter.cut(text)
    text = " ".join(text)
    return nlp.pos_tag(text)


@lru_cache(maxsize=128)
def get_text_dependency_parser_result(text, target_relations=[], verbose=False):
    tokens = nlp.word_tokenize(text)
    dependency_result = nlp.dependency_parse(text)
    results = []
    for r, w1, w2 in dependency_result:
        if verbose: print(r, tokens[w1-1], tokens[w2-1])
        if target_relations != [] and r not in target_relations: continue
        entity_1 = tokens[w1-1] if w1 > 0 else 'None'
        results.append((r, entity_1, tokens[w2-1]))

    return results

