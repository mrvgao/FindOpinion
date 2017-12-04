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


def get_an_article_speech(text):
    return calculate_confidence(opinion_extract(text))


if __name__ == '__main__':
    # size = 50
    # articles = get_article_random(size=size, dependancy_injection=random_generator(size=size))
    #

    article = """虎嗅注：如果昨天你有在虎嗅F&M创新节的现场 “围观”这样一场有关创业、有关内容市场的对话，一定会被王利芬作为一个创业人的真诚、自省所打动，亦兴许会有共鸣于她作为前央视媒体人对时下自媒体市场的忧虑。
七年前，作为《赢在中国》节目的总制片人兼主持人的王利芬踏上创业之路，成为了优米网创始人兼CEO。
虎嗅F&M创新节上这场谈话的缘起，是不久前她的一篇文章，王利芬称，在眼下这个时代，除了做马云、马化腾这样的马，其实你还可以去选择做牛；除了选择在互联网领域创业，你还可以有更多的选择。而在对话中，这位资深的内容创业者，有反思亦有批判，一起来感受一番。
以下由虎嗅整理自现场速记。
反思：创业头七年，把能犯的错犯了个遍
李岷：王老师创业已有七年，马云、柳传志、史玉柱都是你的股东，所以第一个问题想问的是，三位大佬当你的股东是一种什么样的体验？
王利芬：这三位，可以说是当时中国最了不起的几位创业者。其实在我眼里，现在，创业者依然是他们最清晰最立体的角色，不仅是 “创业者”代表的永不放弃的精神，还有他们作为创业者与创业者打交道打交道的过程里面释放出来的我非常钦佩的人格魅力。
在我这里的股东不是实实在在的帮我做什么事情，而是从精神力量上，从某些遥远的站台上，都能让我感到他们对我的帮助。
李岷：你最后一次请教是在什么时候？或者说，你记得他们给你最有价值的意见是什么？
王利芬：坦白讲，从开始创业到现在的这七年里，我可以说是犯尽了所有的错误。（我）基本上是不懂商业的。在过去几年里，我也是一直都有在向他们请教。
2012年，在中国大饭店，我曾向马总（马云）请求，能不能给我一个小时的时间帮帮我，我说我们公司今年想要做到160多人。他说你砍一半。我问为什么，他说你就砍一半， “今年阿里也是，员工只进不出，结果人越多越糟糕，砍一半，人少效率反倒提升了。”我那时候也不懂，但也就按照他说的做了。后来想想，当时如果按照我们说的要到160多个人，当年可能也就挂了。最后我们团队就剩80多个人，也把事情干了。不过这么一个小破事，花一个多小时请教这么一位企业家，纯属浪费资源了。
其实在跟他们交流的过程中，他们更多的是给予我一种鼓励。他们对我的这种宽容、理解、甚至有时可以说是 “纵容”，也可能是源于曾经创业经历的一些感同身受。像马总，从1992年到1997年间基本上也是在犯各种错误，柳总本人，从1984年创业，他也是犯了很多错误，那史总就更不用说了。他们为什么对我这么宽容，因为他们知道，在创业的前几年是非常不容易的，任何外在的指手划脚都没办法完成作为一个创始人本身自我的蜕化、迭代和自省。
在创业的时候，人是最贵的时候，能用三个人不要用五个人。我在跟员工的讨论过程中，有三点是非常重要的，一是给员工好的未来，让他了解你的公司是有前途的，其次是匹配的薪资。第三点是他的直接领导和周围的同事，是不是可以构成他不断提升和进化的环境。如果他跟一个猪一样的队友或者是跟一个没有什么营养价值的同仁在一起，他的成长感、幸福感是非常差的，这一点就会拉低你给他的工资、薪水带来的好不容易抬高的好感，所以给他选一些有质量的人在身边，这件事情是我后来深有体会的一点：不是人多越好，要把精干的，有质量的人留在身边。
李岷：您刚才也说到七年创业把创业者该犯的错误都犯过了，能不能举一个你认为犯的最大的错误或者是痛彻心肺的错误？
王利芬：2016年时，我们曾想把整个优米网的收费业务卖掉，这个事情让我想来是非常后怕的。
我们公司是有视听许可证的，当时想买的人、公司非常多，他们就不停地尽调。现在看来，我非常感谢他们尽调的速度缓慢效率低下，以及整个决策过程的郁闷纠葛。他们的缓慢让我们等来了春天。因为2016年下半年的时候，我们内容付费的整个大环境就起来了。我们会发现像诸如爱奇艺、优酷和腾讯这样的视频网站，他的收费业务是超过广告业务的。
这样的一个内容收费的大环境的建立，才会有例如分答这样的各个内容付费业务的崛起。这件事是需要形成一个整体的气候之后才可行的，光靠某一小点的突破是做不起来的。我们其实早从2002年就开始做内容付费业务，当年就收入了两百万，但后来你发现做不下去。实际上，就创业而言，趋势，也就是timing的把握是非常重要的。逆着形势走你的东西根本做不起来。所以当我看到这个趋势终于来了的时候，我说对不起，你们撤退吧，我不卖了。
你看，我试图做了这么一个愚蠢的动作，且最后，是靠一个外在的力量（足够拖延的尽调）挽救了我，真的是觉得自己挺愚蠢的。
创业者不应该犯的第一个错误——不应该放弃，我犯了。
还有一个。在我们走过前七年的时候，商业模式并没有定，我当时认为这样的状态公司就不应该去融资，导致我们推掉了好几家非常棒的风投公司。为什么呢？我那时候，把找风投看作是跟别人交往的方式，我和别人交往就不愿意欠着别人，不然总觉得对不起。所以当很多风投表示他们愿意把钱投给我的时候，我都以没有找到盈利模式拒绝了。
正因为我的这个观念，导致优米很长时间没有融资，这就意味着我们只能在自己仅有的资源里面来做小心翼翼的探索。但其实，创业有时候真的是需要风投垫一步才能往前走的。而我是在用一个非常农村妇女的朴素的思维、所谓的善良价值观和资本市场打交道，这个情商和智商算是双双跌到了负数吧。
对资本的认知是创业者最要跨过的重大认知升级。很多的创业课经常在说，创业一把手的认知升级是创业升级最重要的门槛，认知是一个混合的概念，那最要迈过的门槛实际上是你对资本认知的升级。
李岷：接下来有一个比较尖锐的问题，我在为今天的对谈做功课的时候发现，网上很多人都在问同一个问题，同样是做知识经济，为什么早走那么久的王利芬做不过罗振宇，您怎么看？
王利芬：你提到的这个文章，还是我一个朋友发给我看的。那时候我在湖畔大学上课。他发给我的时候，我们正好是在一个宾馆吃早餐，罗振宇也在。我跟他说，这篇文章写得非常棒，说的非常实事求是，它好就好在它充分肯定了你今天的成绩，对我的现状给予了一针见血的概括，我接受，没有任何问题。
实际上是这样的，作为一个创业公司，它会有高点、低点，而高点低点每天都在发生变化，每天都有你要去抓住的机遇。我认为，创业是一个可持续发展的状态，我们不要把这件事情的结算放在一年或者是两年。所以在一段更长的时间来看，干过谁和干不过谁其实不应该是我跟罗振宇之间的较量，创业者最怕的是和自己的较量。
罗振宇当然有值得人家学他的地方，四年如一日，每天坚持60秒，这个事情太难了。坚持有多么难，这是他该得到的，我前面犯的错误，很多时候我放弃了，这是我应得的评价，谢谢写这个文章的自媒体人。
批判：自媒体的整体状态令人悲哀
李岷：但说到自媒体，他们有些时候的评判体系或者是内心深处的东西，包括对商业判断相对来说还是有点肤浅，片面的。
王利芬：因为这个时代噪音太多了。说老实话，现如今自媒体整体的状态，令我倍感悲哀。原因是绝大部分自媒体他个人的判断，基本上是受到了各种利益的污染的。既然是自媒体，比较率性地呈现自己的判断，无论深浅高低，这都无妨，因为这是受限于你现有的思维高度和水平的。但问题是你在背后哗众取宠，你想用这个来赢粉丝，因为假使赢不来粉丝，你会发现当你跟人家做商务谈判的时候，赤裸裸换回的现金是不够的。
所以我常常想，在这样一个时代，当记者这样的一个集体的阵营没有用武之地的时候，把大家被驱赶或者是被迫的选择在了一个内容通道或者自媒体的通道进行创作到底好还是不好。我自己觉得蛮悲哀的。这是我第二次说 “悲哀”，原因在于记者或者说内容提供者最怕的是有一种力量，凌驾于你的判断之上，你的嘴需要说别人的话，这是一件很悲哀的事情。
识人：读心术
李岷：看到了那么多的公司，那么多的企业家，能成的和不能成的，有没有一到三个核心的区别？
王利芬：你如何去区别一个真正的企业家和一个忽悠的人，很重要的一点你要去读他的内心。
比如贾跃亭，他曾企图把汽车，把大屏幕电视、易到、体育全部张罗在一个地方做大做强，一个千亿级创业板上市值最高的公司，这么短的时间出现在我们的面前，又在这么短的时间里，变成了现在这个样子。
这样一个所谓的 “生态化反”很有意思，（它的核心）并不是所谓的生态，而是因为他自己要做大、做强，要去追逐他的野心。而在这个过程中，际上用了资本的衍生，也就是杠杆的力量，也利用了大家在所谓喧嚣的时代里面不顾一切要赚大钱，热钱的心态。
当年的乐视和十九个演员、导演那么大的阵容在那个地方，所有的演员众星捧月围绕着贾跃亭自拍的时候是什么样的景象？


因为他们要赚更大的钱。演员作为一种独特的才能，在整个的市场上，他已经用他的颜值、专业或者粉丝的力量，利用杠杆赚了很多的钱。但他们又希望到本市场利用杠杆，去拿原始股和投资的钱。这个世界，就是会把有钱的人变的更加有钱。所以大家也能看到非常有意思的现象，所有人都把贾跃亭看作是她致富的手段或者是渠道，因而大家众星捧月般围绕着他一起来自拍。其实我当时看到这照片的时候蛮悲哀的。而现在任何一个出现在这样一个场景里的演员，我相信他们没有任何一个人愿意再把这张照片拿出来。
在那样一个时间段里，每个人都被裹挟了。
再回到刚刚所说的生态的问题。健康的生态，应该是以用户需求去延伸的一个又一个的生态，那，乐视它显然不是。还有一些企业家他在短时间内做得特别大，特别强，想追风口跑起来，我们读到的他的内心，实际上是想和某某某，想和谁谁谁一较高下，实际上这样的事情都走不长的，这都是虚荣所导致的，
所以我看企业家我都会读他的内心，我的结算方式，是在我的有生之年我能看到的这样的时间段。结算是要有时间段的，就像财年一样，月报、季报、年报。
李岷：马云在他的创业初期，很多人都说他忽悠、骗子。你当时是怎么一眼就看中他，知道他不是一个忽悠的？
王利芬：我跟他认识的时间比较早，2005年就认识了。当时我们在达沃斯，在短短的七天时间里面，我们经常在一个论坛听。他那个时候真的是说在找市场，打造团队，想商业模式，资本的力量在那个地方控制得非常好，他并没有被资本主宰。你看，他只有7%的股份，他的公司曾经一度在资本上没有什么优势，但是他们依然还能够牢牢地控制这个公司，以他们自己的节奏在做事情，你看他们是不是在拼市场，是不是在做有机的生态，还有看他们的团队。你去看他做这个事情，是不是一定要证明给某个人或者是某几个人看，或者是源于心理上的某些重大缺陷或者经历。
李岷：企业家不能有心魔。
王利芬：有心魔的企业家是走不长的，因为你知道一个体量大了，体量大了之后，在空中飞行的时候，有一只鸟，有可能让你这个飞机就坠落了，正好那只鸟那么轻的力量撞在最重要的部分的时候，那么一点点的错误，心里一丝的抖动，这个企业就没了。
返回搜狐，查看更多
责任编辑"""
    articles = [article]

    for a in articles:
        strings = get_an_article_speech(a)
        for s in strings:
            print(s)
