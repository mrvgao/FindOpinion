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
    print(nsubj_parse_results)

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


def pre_processing(text):
    text = text.replace('：', '说，')
    return text


def opinion_extract(text):
    text = pre_processing(text)
    return filter_one_spoken_string(get_spoken_strings(text))


def get_an_article_speech(text):
    return calculate_confidence(opinion_extract(text))


if __name__ == '__main__':
    size = 50
    articles = get_article_random(size=size, dependancy_injection=random_generator(size=size))

    text = """
    新华网北京12月6日电（马芸菲 关心）第四届世界互联网大会昨日在乌镇闭幕啦！大咖来聚会，黑科技来“走台“，新观点来荟萃……让我们跟着这些关乎未来的话题来回顾这届有饭局、有衣品，更有思想碰撞的”新潮“大会。
如果你是一只独角兽……


在风险投资行业，估值超过10亿美元的创业公司被成为“独角兽”公司，创造出一家“独角兽“公司是怎样的体验？今天的“独角兽”能成为明天的“巨无霸”吗？


优客工场创始人、董事长毛大庆：我都不知道什么叫“独角兽”，后来找人问了半天，意思大概是说这个东西一下子刺破了人类对各种认知的天花板，所以叫“独角兽”。后来我觉得它是一个什么荣誉，要不然是一种身份的象征。实际上你变成“独角兽”以后，除了压力以外，没有什么特别好的东西，带来的都是压力和问题，尤其是你这个行业里面如果只有你一个独角兽的话更糟糕，所有的人都看着你。


紫牛基金联合创始人张泉灵：很多已经成为独角兽的公司，起步的时候或者行进过程中，都会说他们要有情怀，最开始的情怀不是做一家伟大的公司，而是我们要做一个改变世界的产品，这样开始的。所以他们考虑的不是一家公司，而是一个产品、一个情怀。这是创业者们共同的想法。


红杉资本全球执行合伙人、红杉资本中国基金创始及执行合伙人沈南鹏： 今天我们看到了一个趋势，那就是越来越多的创新创业是黑科技、硬科技驱动，而这意味着长期对技术的投入和积累。在这个过程中，风险投资能够扮演更重要的角色，去推动科技创新和产品转化，因为大量的研发投入是公司长期竞争力的保证。在长的周期中，风险投资有长期的观点，同时又有足够的战略资源，在帮助企业家产品转化的过程中扮演重要角色，帮助企业家完成创业的梦想。
人工智能真能改变世界？


人工智能真的会改变人、改变企业、改变未来世界吗？当“狼”真的来了？我们应该怎么办？


小米创始人兼ceo雷军:人工智能这个时代来了以后，很多互联网的企业家都觉得自己过时了，变成了传统的产业。所以我就说人工智能是一次技术革命，就像当年移动互联网来的时候，所有的企业都要拥抱移动互联网，今天人工智能来的时候，可能我们所有的企业都需要拥抱人工智能。


百度公司董事长兼首席执行官李彦宏：搜索引擎本身就是一个人工智能的问题，用户用自然语言输入他的需求，计算机猜测用户想要找什么，然后给他提供相应的答案。人工智能就是要让计算机懂得人，给人提供需求。我们的社会会因为人工智能的到来而发生大的改变。


中国联通总经理陆益民：大家知道过去运营商的传统网络是提供人与人之间连接的，但随着网络能力的扩充，我们现在在提供人与物之间的连接，人和信息点之间的连接，还有物与物之间的连接。到今年年底，我们今年年底物与物之间的连接总数要超过了过去传统人与人之间或智能设备与智能设备之间的连接总数，到2020年将达到200亿个连接点。这些连接产生的一个很重要的就是数据，有了这些数据才有了人工智能真正爆发式的成长基础。
当我们向数字经济时代走去……


尼采说，当你在凝视深渊，深渊也在凝视着你。当我们创造出一个数字经济时代，这个时代将给我们带来什么？


阿里巴巴董事局主席马云：阿里巴巴怎么转型？什么叫我们走向数字经济？9年前决定我们整个阿里巴巴走向大数据、云计算的时候，我在公司内部说：“我们一切业务数据化，一切数据业务化”。我们所有的业务必须数据化，因为只有所有的业务变成数据，我们才有可能进入数据时代。


联想集团董事长兼CEO杨元庆： 未来商业的比拼，一定是业务模式的比拼，而业务模式之中的智能化程度决定了企业竞争力的强弱。如果我国能更多地强调数字经济和智能化，那未来我国的企业就会比别的国家更领先一步。


腾讯公司控股董事会主席兼首席执行官马化腾：过去一年，数字经济是创新最快的经济活动，全球互联网公司都站在了风口上，获得了高速发展。全球市值最大的公司里，7家科技公司里包括5家互联网公司。新年代里，新产品的迭代速度以天为单位，大公司也是如此。过去中国企业扮演新技术跟随者，今天要成为新技术的驱动者。
网络世界里的社会责任是什么？


网络给我们带来了千万里间的无障碍交流，带来了方便好骑的共享单车，带来了蓬勃发展的网购经济……然而在这样一个虚拟的世界里，是否存在着与现实社会同样的社会责任？这种社会责任如何体现出来？


新华社社长蔡名照：我们的世界已经成为“地球村”，但不同文明之间的藩篱仍然根深蒂固，这也成为世界不安定的重要因素。我们应当把网络传播作为沟通的桥梁纽带，增进理解而不是挑动仇恨，化解偏见而不是宣扬歧视，努力促进不同国家、不同文明的相互理解、相互尊重。


阿里巴巴董事局主席马云：如果网络传播乐衷于情绪化的传播而不是理性思考，乐衷于谣言而不是事实，甚至乐衷于靠水军来赢得市场竞争，那是对未来，对下一代非常不负责任的做法。因此，今天网络传播必须把社会责任放在第一位，这是媒体的责任，也是互联网企业的责任，应该共同担当。


摩拜联合创始人兼CEO王晓峰：目前快速发展的共享单车，也产生了一些困扰。我们非常希望在每个城市拥有的数以十万辆的摩拜单车某种意义上成为城市交通基础设施的组成部分之一，能够把产生的每一天实名用户的出行数据结合起来，为城市的交通、为城市更好的科学规划做出自己的一些努力和贡献，真正的做到企业公民应该承担的社会责任。
[责任编辑：杨凡、张弛]"""

    articles = [text]

    for a in articles:
        strings = get_an_article_speech(a)
        for s in strings:
            print(s)
