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


close_words = get_spoken_closet_words()


def is_spoken_verb(w, tag, after_tag='n'):
    # w the current word
    # tag the current word's tag
    # the tag of the after this word
    def is_special_char(c):
        return c.startswith('v') or c.startswith('p')

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
    strings = [s for s in strings if get_spoken_v_num(s) > 0]
    strings = [(get_exist_persons(s), s) for s in strings]
    # strings = [s for s in strings if exist_person(s)]
    # strings = [add_sub_and_predicate(s) for s in strings]
    strings = [(entities, s) for entities, s in strings if len(entities) > 0]
    strings = [(get_entity_and_verb_from_ltp(s, tuple(entities)), s) for entities, s in strings if len(entities) > 0]
    strings = [(subj_pred[-1][0], subj_pred[-1][1], s) for subj_pred, s in strings if len(subj_pred) > 0]
    strings = [(sub, p, extract_spoken_content(string, p), string) for sub, p, string in strings
               if extract_spoken_content(string, p) is not None]
    strings = [(sub, p, delete_news_begin(content), string) for sub, p, content, string in strings]
    strings = [(sub, p, delete_end_none_characters(content), string) for sub, p, content, string in strings]
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
        content = string[string.index(predicate) + len(predicate):]

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
        (name, verb, speech, confidence(verb))
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
    text = text.replace('：', '说，')
    return text


def opinion_extract(text):
    text = pre_processing(text)
    return extract_quote_line_by_line(get_strings_with_spoken_format(text))


def get_an_article_speech(text):
    return opinion_extract(text)


if __name__ == '__main__':
    # print('hello')
    # size = 100
    # articles = get_article_random(file_name='~/Workspace/Lecture/data/sqlResult_1558435.csv',
    #                               encoding='gb18030',
    #                               size=None, dependancy_injection=None)

    text = """
    第四届世界互联网大会闭幕：中国的数字经济发展将进入快车道
　　央视网消息：中国的数字经济发展将进入快车道，这是本届世界互联网大会的一个热门话题。
　　在4日召开的“数字丝绸之路”国际合作论坛上，专家首次提出要参与制定国际数字贸易标准，作为数字经济的核心，数字贸易的标准制定，对于我国数字经济的发展能带来什么？对于中国企业走向海外又会有哪些帮助呢？
　　4日，由中国人民外交学会主办的“数字丝绸之路”国际合作论坛在乌镇会展中心举行，本次论坛以“跨境电商，共享繁荣”为议题，有来自国内外的多名专家和互联网企业家共同讨论。


中国人民大学国际关系学院教授王义桅
　　中国人民大学国际关系学院教授王义桅：中国是数字经济发展最为迅猛的一个国家，我们有7.5亿网民，我们的电子商务占美国、日本，还有欧洲他们总和还要多，我们现在在创造数字经济的一个模式。
　　根据统计，目前有超过12%的全球跨境实物贸易通过数字平台完成，50%的跨境服务贸易以数字化的形式实现，其中跨境电商平台起到了非常重要的桥梁作用，而我国在跨境电商领域也已经走在世界的最前列，在论坛上专家和互联网企业家指出，我国正在从跨境电商进化到数字贸易时代。


敦煌网首席执行官王树彤
　　敦煌网首席执行官王树彤：我们今天看到由消费互联网在迈向产业互联网，我觉得这个已经是全球的一个趋势。所以未来的贸易，主流应该是数字贸易。电子商务也好，数字贸易也好，是一个前所未有的机会，能够让中小企业以低门槛的方式，能够进入到全球市场。
　　专家指出，美国在数字产品及贸易领域占据全球竞争优势，在相关规则制定方面也处于引领地位，但由于数字产品本身的复杂性和快速发展，很多领域不仅没有定论，也存在很多值得探讨和谈判的空间。所以，中国必须要在将来的数字贸易标准制定中起到重要的作用。


中国与全球化智库理事长王耀辉
　　中国与全球化智库理事长王耀辉：如果说我们在这领域里面参与国际规则的制定，包括打造了全球治理的互联网数字贸易的新规则的话，对于推动中国未来的发展，包括落实习主席说的，共商共建共享，打造数字丝绸之路，会起到一个决定性的巨大作用。
进入【新浪财经股吧】讨论
    """
    articles = [text]

    dataset = open('opinion_set.csv', 'a', encoding='utf-8')
    writer = csv.writer(dataset)
    writer.writerow(['string', 'predicate', 'subject', 'content'])

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
