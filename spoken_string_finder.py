"""
Input an article, find all the spoken strings.
"""

from jieba.posseg import cut
from preprocessing import split_to_sentence
from utils import get_article_random
from utils import get_spoken_closet_words
from itertools import repeat
from structure_parser import find_nsubj_subject
from functools import lru_cache
import re
from format_parser import calculate_confidence


close_words = get_spoken_closet_words()


@lru_cache(maxsize=256)
def get_spoken_strings(article):
    results = []

    def is_special_char(c):
        return c.startswith('v') or c.startswith('p')

    shortest_spoken_length = 5
    for sentence in split_to_sentence(article):
        cut_string = list(map(tuple, cut(sentence)))
        for i in range(len(cut_string)-1):
            if cut_string[i][0] in close_words and is_special_char(cut_string[i][1]) \
               and not cut_string[i+1][1].startswith('u'):
                if len(cut_string) - i > shortest_spoken_length:
                    results.append((cut_string[i][0], i, sentence))
                    break
    return results


def filter_one_spoken_string(strings):
    def get_spoken_v_num(s):
        postags = list(map(tuple, cut(s)))
        spoken_v_num = 0
        for w, t in postags:
            if t.startswith('v') and w in close_words:
                spoken_v_num += 1
        return spoken_v_num

    strings = [s for v, n, s in strings]

    strings = [s for s in strings if get_spoken_v_num(s) == 1]
    strings = [s for s in strings if exist_person(s)]
    strings = [add_sub_and_predicate(s) for s in strings]
    strings = filter(lambda x: x is not None, strings)
    strings = [(sub, p, extract_spoken_content(string)) for sub, p, string in strings
               if extract_spoken_content(string) is not None]

    strings = [(sub, p, delete_news_begin(string)) for sub, p, string in strings]

    return strings


@lru_cache(maxsize=256)
def extract_spoken_content(string):
    quoted_string = get_quoted_string(string)
    quoted_string_threshold = 10
    if len(quoted_string) > quoted_string_threshold:
        content = quoted_string
    else:
        _, p = get_subject_and_predicate_of_speak(string)
        content = string[string.index(p) + len(p):]

        first_unchar_index = len(content)

        for ii, c in enumerate(content):
            if not str.isalnum(c):
                first_unchar_index = ii
                break

        first_char_index_threshold = 3
        if first_unchar_index <= first_char_index_threshold:
            content = content[first_unchar_index+1:]

    content_length_threshold = 5
    if len(content) > content_length_threshold:
        return content
    else:
        return None


@lru_cache(maxsize=256)
def get_speak_words_index(tags, words):
    for ii, t_w in enumerate(zip(tags, words)):
        t, w = t_w
        if t.startswith('v') and w in close_words: return ii
    return None


@lru_cache(maxsize=256)
def exist_person(string):
    for w, t in list(map(tuple, cut(string))):
        if t.startswith('nr'): return True
    return False


@lru_cache(maxsize=256)
def get_quoted_string(string):
    return " ".join(re.findall(r'“(.*?)”', string))


@lru_cache(maxsize=250)
def get_string_postags(string):
    postags = list(map(tuple, cut(string)))
    tags = [t for w, t in postags]
    words = [w for w, t in postags]
    return tags, words


@lru_cache(maxsize=256)
def remove_content_between_p_and_spoken_verb(string):
    tags, words = get_string_postags(string)

    p = 'p'  # proposition mark

    if p in tags:
        preposition_index = tags.index(p)
        spoken_verb_index = get_speak_words_index(tags, words)

        if preposition_index < spoken_verb_index:
            words = words[:preposition_index] + words[spoken_verb_index:]

    return "".join(words)


@lru_cache(maxsize=256)
def get_subject_and_predicate_of_speak(string):
    tags, words = get_string_postags(string)
    nsubj_parse_results = find_nsubj_subject(string)

    for r in nsubj_parse_results:
        _, p, w = r
        if p in words and tags[words.index(p)].startswith('v') and p in close_words and w in words and \
            tags[words.index(w)].startswith('nr'):
                return w, p
    return None


@lru_cache(maxsize=256)
def add_sub_and_predicate(string):
    # string = remove_content_between_p_and_spoken_verb(string)
    sub_pred = get_subject_and_predicate_of_speak(string)
    if sub_pred:
        sub, pred = sub_pred
        string = (sub, pred, string)
    else:
        string = None

    return string


def delete_news_begin(string):
    comma = '，'
    if comma in string and string[:string.index(comma)].find('新闻') >= 0:
        string = string[string.index(comma)+1:]
    return string


def random_generator(size=10):
    L = range(size)
    for l in repeat(L):
        for i in l:
            yield i


def opinion_extract(text):
    return filter_one_spoken_string(get_spoken_strings(text))


def get_a_article_speech(text):
    return calculate_confidence(opinion_extract(text))


if __name__ == '__main__':
    size = 50
    articles = get_article_random(size=size, dependancy_injection=random_generator(size=size))

    for a in articles:
        strings = get_a_article_speech(a)
        for s in strings:
            print(s)
