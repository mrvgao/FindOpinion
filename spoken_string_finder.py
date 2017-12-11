"""
Input an article, find all the spoken strings.
"""

from jieba.posseg import cut
from preprocessing import split_to_sentence
from utils import get_article_random
from utils import get_spoken_closet_words
from itertools import repeat
# from structure_parser import find_nsubj_subject
from functools import lru_cache
import re
import csv
from tqdm import tqdm
from pyltp_parser import get_dparser_from_ltp
from self_defined_parser import nsubj_parser


close_words = get_spoken_closet_words()


def is_spoken_verb(w, tag, after_tag='n'):
    # w the current word
    # tag the current word's tag
    # the tag of the after this word
    def is_special_char(c):
        return c.startswith('v') or c.startswith('p')

    colon = '：'
    if w == colon: return True
    if w in close_words and is_special_char(tag) and not after_tag.startswith('u'):
        return True
    return False


@lru_cache(maxsize=256)
def get_strings_with_spoken_format(article):
    results = []

    shortest_spoken_length = 5
    for sentence in split_to_sentence(article):
        cut_string = list(map(tuple, cut(sentence)))
        for i in range(len(cut_string)-1):
            if is_spoken_verb(cut_string[i][0], cut_string[i][1], cut_string[i+1][1]):
                if len(cut_string) - i > shortest_spoken_length:
                    results.append((cut_string[i][0], i, sentence))
                    break
    return results


def char_index_is_in_quotes(char_index, string):
    left_quote = '“'
    right_quotes = '”'

    char_index_to_left = char_index
    char_index_to_right = char_index

    while char_index_to_left >= 0:
        if string[char_index_to_left] == left_quote:
            return True
        if string[char_index_to_right] == right_quotes:
            break
        char_index_to_left -= 1

    while char_index_to_right <= len(string) - 1:
        if string[char_index_to_right] == right_quotes:
            return True
        if string[char_index_to_right] == left_quote:
            break
        char_index_to_right += 1
    return False


def extract_quote_line_by_line(strings):

    def get_spoken_v_num(s):
        postags = list(map(tuple, cut(s)))
        spoken_v_num = 0
        char_index = 0
        for i, w_t in enumerate(postags[:-1]):
            w, t = w_t
            if is_spoken_verb(w, t, postags[i+1][1]) and not char_index_is_in_quotes(char_index, s):
                spoken_v_num += 1
            char_index += len(w)
        return spoken_v_num

    strings = [s for v, n, s in strings]
    # strings = [s for s in strings if get_spoken_v_num(s) > 0]
    strings = [(get_exist_persons(s), s) for s in strings]
    # strings = [s for s in strings if exist_person(s)]
    # strings = [add_sub_and_predicate(s) for s in strings]
    strings = [(entities, s) for entities, s in strings if len(entities) > 0]
    strings = [(get_entity_and_verb_from_ltp(s, tuple(entities)), s) for entities, s in strings if len(entities) > 0]
    strings = [(subj_pred[-1][0], subj_pred[-1][1], s) for subj_pred, s in strings if len(subj_pred) > 0]
    strings = [(sub, p, extract_spoken_content(string, p), string) for sub, p, string in strings
               if extract_spoken_content(string, p) is not None]
    strings = [(sub, p, delete_news_begin(content), string) for sub, p, content, string in strings]
    strings = [(sub, p, delete_end_none_characters(content), delete_end_none_characters(delete_news_begin(string)))
               for sub, p, content, string in strings]
    strings = [(sub, p, content, recovery_from_colon(string, content)) for sub, p, content, string in strings]
    strings = calculate_confidence(strings)

    return strings


def delete_end_none_characters(string):
    string = string[::-1]
    for ii, c in enumerate(string):
        if str(c).isalpha(): break

    string = string[ii:][::-1]
    return string


@lru_cache(maxsize=256)
def extract_spoken_content(string, predicate):
    quoted_string = get_quoted_string(string)
    quoted_string_threshold = 10
    if len(quoted_string) > quoted_string_threshold:
        content = quoted_string
    else:
        # _, p = get_subject_and_predicate_of_speak(string)
        predicate = predicate[::-1]
        predicate_index = len(string) - string[::-1].index(predicate)
        content = string[predicate_index - 1 + len(predicate):]

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
def get_exist_persons(string):
    entities = []
    for w, t in list(map(tuple, cut(string))):
        if t.startswith('nr'): entities.append(w)
    return entities


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


def calculate_confidence(results):
    max_pro_verb = max(close_words.values())

    def confidence(verb): return close_words[verb] / max_pro_verb

    return [
        (name, verb, speech, string.replace('.', '。'), confidence(verb))
        for name, verb, speech, string in results
    ]


# @lru_cache(maxsize=256)
# def get_subject_and_predicate_of_speak(string):
#     tags, words = get_string_postags(string)
#     nsubj_parse_results = find_nsubj_subject(string)
#     print(list(zip(tags, words)))
#     print(nsubj_parse_results)
#
#     def merge_noun(word, tag, words, tags):
#         if tag.startswith('n'):
#             pass
#
#     for r in nsubj_parse_results:
#         _, p, w = r
#         if p in words and is_spoken_verb(p, tags[words.index(p)]) and tags[words.index(w)].startswith('nr'):
#                 return w, p
#     return None


# @lru_cache(maxsize=256)
# def add_sub_and_predicate(string):
#     string = remove_content_between_p_and_spoken_verb(string)
    # sub_pred = get_subject_and_predicate_of_speak(string)
    # if sub_pred:
    #     sub, pred = sub_pred
    #     string = (sub, pred, string)
    # else:
    #     string = None
    #
    # return string
#

@lru_cache(maxsize=256)
def get_entity_and_verb_from_ltp(string, entities):
    tags, words = get_string_postags(string)

    results = get_dparser_from_ltp(words)

    nsubj = []
    for w1, w2, ii1, ii2, relation in results:
        if relation != 'SBV': continue

        if ii2 + 1 < len(tags): after_tag = tags[ii2 + 1]
        else: after_tag = 'n'

        if w1 in entities and is_spoken_verb(w2, tags[ii2], after_tag):
            nsubj.append((w1, w2))

    return nsubj


def get_subject_from_parse(string, entities):
    nsubjs = get_entity_and_verb_from_ltp(string, entities)
    if len(nsubjs) == 0:
        nsubjs = nsubj_parser(string, entities)
    return nsubjs


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


def pre_processing(text):
    # colon = '：'
    # say = '说，'
    # text = text.replace(colon, say)
    return text


def opinion_extract(text):
    text = pre_processing(text)
    return extract_quote_line_by_line(get_strings_with_spoken_format(text))


def get_an_article_speech(text):
    return opinion_extract(text)


def recovery_from_colon(original_string, spoken_content):
    say = '说，'
    colon = '：'
    if spoken_content in original_string:
        content_index = original_string.index(spoken_content)
        if original_string[content_index - 2: content_index] == say:
            original_string = original_string[: content_index -2] + colon + original_string[content_index:]
    return original_string


if __name__ == '__main__':
    # print('hello')
    # size = 100
    # articles = get_article_random(file_name='~/Workspace/Lecture/data/sqlResult_1558435.csv',
    #                               encoding='gb18030',
    #                               size=None, dependancy_injection=None)

    text = """
    （原标题： 习近平同布特弗利卡总统互致贺电庆祝阿尔及利亚一号通信卫星发射成功）
新华社北京12月11日电 国家主席习近平12月11日同阿尔及利亚总统布特弗利卡互致贺电，祝贺阿尔及利亚一号通信卫星在西昌发射成功。
习近平在贺电中指出，阿尔及利亚一号通信卫星项目是中阿全面战略伙伴关系的重要体现，开创了中国同阿拉伯国家开展航天领域合作的成功先例，将为推动阿尔及利亚经济发展、民生改善、社会进步发挥重要作用。明年是中阿两国建交60周年。中方愿同阿方一道努力，加强各领域交流合作，推动中阿全面战略伙伴关系深入发展，更好造福两国和两国人民。
布特弗利卡在贺电中表示，阿尔及利亚一号通信卫星成功发射是阿中两国航天合作的重大成就，体现了双方深厚的传统友谊。阿方愿同中方共同推动各领域合作取得更多成果。
    """
    articles = [text]

    # dataset = open('opinion_set.csv', 'a', encoding='utf-8')
    # writer = csv.writer(dataset)
    # writer.writerow(['string', 'predicate', 'subject', 'content'])
    #
    index = 0
    articles_bar = articles
    for a in articles_bar:

        try:
            strings = get_an_article_speech(a)
        except AttributeError: continue

        for s in strings: print(s)
        # for subj, predicate, content, string, _ in strings:
        #     writer.writerow([string, predicate, subj, content])
        #     print(index)
            # index += 1
            # articles_bar.update(0.1)
            # articles_bar.set_description('No: {}'.format(index), refresh=False)
            # articles_bar.set_postfix({'Subj': subj}, refresh=False)
