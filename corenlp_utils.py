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

