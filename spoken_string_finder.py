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
import csv
from tqdm import tqdm


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
    strings = [(sub, p, extract_spoken_content(string), string) for sub, p, string in strings
               if extract_spoken_content(string) is not None]
    strings = [(sub, p, delete_news_begin(content), string) for sub, p, content, string in strings]

    strings = calculate_confidence(strings)

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
    # print(nsubj_parse_results)

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
    return opinion_extract(text)


if __name__ == '__main__':
    size = None
    articles = get_article_random(file_name='~/Workspace/Lecture/data/sqlResult_1558435.csv',
                                  encoding='gb18030',
                                  size=None, dependancy_injection=None)

    # text = """盘和林财政部中国财政科学研究院应用经济学博士后
# 　　“中共十九大制定了新时代中国特色社会主义的行动纲领和发展蓝图，提出要建设网络强国、数字中国、智慧社会，推动互联网、大数据、人工智能和实体经济深度融合，发展数字经济、共享经济，培育新增长点、形成新动能。”中国国家主席习近平在致第四届世界互联网大会的贺信中说，中国数字经济发展将进入快车道。
# 　　作为在中共十九大之后，中国召开的一次重要的国际性会议，第四届世界互联网大会备受世人瞩目。
# 　　之所以受到世界瞩目一个更为重要的原因是，中国作为一个网络大国，在数字经济发展中取得了惊人的成绩；中国数字经济发展将进入快车道，世界各国以及互联网巨头都希望与中国共商互联网的国际合作，甚至是未来互联网全球治理等话题。
# 　　数字经济又称为信息经济，是数字化、网络化、智能化的时效经济。数字经济是以网络为载体，以数字化的知识与信息为生产要素，以智能制造为动能，以大数据在线模式为物联平台，以分享经济为方向的经济模式。
# 　　当今世界正在经历一场革命性的变化。当今最具影响力的社会思想家之一托夫勒认为，第三次浪潮是信息革命。信息革命也就是数字革命，指由于信息生产、处理手段的高度发展而导致的社会生产力、生产关系的变革，被视为第四次工业革命。可以说是人类有史以来最为迅速、广泛、深刻的变化。
# 　　毫不夸张地说，数字经济是现代经济的绝对主角，在经济社会中如工业生产、人们的衣食住行等都广泛融入了信息技术，使得人类活动各方面表现出信息活动的特征。因此，数字经济发展水平已经成为衡量各国综合国力的重要标准之一，以信息技术为代表的高新技术突飞猛进，以信息化和信息产业发展水平为主要特征的综合国力竞争日趋激烈。
# 　　习近平主席高度重视数字经济发展，多次就信息经济、网络经济发表重要论述，明确指出信息化和经济全球化要相互促进。在3月5日召开的十二届全国人大五次会议上，“数字经济”首次被写入政府工作报告。
# 　　数字经济已经成为我国经济增长的重要驱动力。中国信息化百人会2016年出版的《信息经济崛起：区域发展模式、路径与动力》一书提出，1996年—2014年中国信息经济年均增速高达23.79%，远远高于同期GDP年均增速；2016年我国数字经济规模已达到22.4万亿元人民币，占GDP比重达到30.1%；信息经济正在成为国民经济稳定增长的主要引擎。
# 　　近年来，我国数字经济快速发展，其增速远远快于中美日英等全球主要国家数字经济的增速。根据中国信息通信研究院测算，2016年我国数字经济增速高达16.6%，分别是美国（6.8%）、日本（5.5%）和英国（5.4%）的2.4倍、3.0倍、3.1倍。
# 　　企业强则中国强。具有国际竞争力的企业是一个国家和地区经济实力的象征，企业在某一行业的国际竞争力也代表着一个国家和地区在该行业的影响力和实力。阿里巴巴、腾讯、百度、蚂蚁金服、小米、京东、滴滴出行等7家企业位居全球互联网企业20强，充分说明中国企业在数字经济领域走在了世界前列。
# 　　今年双11全球狂欢节闭幕，毫无悬念再创新高，全天成交额再次刷新纪录达到1682亿元，无线成交占比90%，全天支付总笔数达到14.8亿，全天物流订单达8.12亿，交易覆盖全球225个国家和地区。显然这并不是一场简单拼价格的购物节，背后所代表的新零售、新消费、人工智能、大数据、移动支付等，都是数据经济发展的结晶。正如英国广播公司BBC对天猫双11的总结：“中国已经不再是跟随者，而是世界电商和用户体验的领头羊。当午夜的钟声敲响的时候，世界应该看到，中国已经前行了多远。”
# 　　中国拥有世界上最多的网民和移动网民，拥有智能手机最大规模的群体，加上融合创新的精神以及开放包容的心态，中国已经深深融入了世界互联网各个领域。从人均信息消费来看，目前只有300美元左右，而《国家信息化发展战略纲要》要求2020年人均信息消费约700美元，可谓前景广阔、潜力巨大。
# 　　习近平主席在贺信中提出的“推动世界各国共同搭乘互联网和数字经济发展的快车”，本次大会提出“发展共同推进、安全共同维护、治理共同参与、成果共同分享”，因此，我们有理由相信，中国数字经济发展将进入快车道，不仅是中国经济之福，也为世界经济发展注入强大动力。["""
#
#     articles = [text]

    dataset = open('opinion_set.csv', 'a', encoding='utf-8')
    writer = csv.writer(dataset)
    writer.writerow(['string', 'predicate', 'subject', 'content'])

    index = 0
    articles_bar = tqdm(articles)
    for a in articles_bar:

        try:
            strings = get_an_article_speech(a)
        except AttributeError: continue

        for subj, predicate, content, string, _ in strings:
            writer.writerow([string, predicate, subj, content])
            # print(index)
            index += 1
            articles_bar.update(0.1)
            articles_bar.set_description('No: {}'.format(index), refresh=False)
            articles_bar.set_postfix({'Subj': subj}, refresh=False)
