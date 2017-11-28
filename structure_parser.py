import re
from corenlp_utils import get_text_dependency_parser_result


def find_nsubj_subject(string):
    results = get_text_dependency_parser_result(string, target_relations=('nsubj'), verbose=False)

    return results


def find_subject(text, predict=None, verbose=False):
    if isinstance(predict, str): predict = [predict]

    comma = ',，:：'
    regx = re.compile('[%s]'.format(re.escape(comma)))
    text = regx.sub("", text)
    auxiliarity = 'aux:asp'
    target_relations = ('nsubj', 'aux:asp')
    results = get_text_dependency_parser_result(text, target_relations, verbose=verbose)

    # if ('aux:asp', predict, *) in results
    if list(filter(lambda r_p__: r_p__[0] == auxiliarity and r_p__[1] == predict, results)):
       return None
    elif predict:
        return [e for e in results if e[1] in predict]
    else:
        return results


if __name__ == '__main__':
    strings = ['在会谈后的联合记者会上，安倍表示“坚决谴责卑劣的恐怖主义行径”',
               '安倍在斯德哥尔摩向随行媒体透露，为应对日本九州暴雨将提前结束欧洲之行回国',
               '有人认为，这凸显了特朗普“任人唯亲”，还有人用“独裁”形容特朗普的做法',
               '批评者认为，特朗普的这种安排是对民主的嘲弄',
               '美国前驻北约大使伯恩斯认为，这起事件是对传统规矩的破坏',
               '俄罗斯卫星通讯社7月9日报道称，星期日，印度军队在克什米尔的印巴两国交界线处发起炮击，摧毁了冲突线地区的至少3个巴基斯坦地堡',
               '对此，美国智库兰德公司曾解释：集团体系崩溃后，组织分散转入地下，仍有能力发起零星战斗和袭击，更容易存活很长时间',
               '泰国总理府副部长戈沙在内阁会议后对媒体说，内阁已批准由泰国铁路局推进曼谷至呵叻府的铁路',
               '威廉王子看着黛妃怀着哈里王子时抱着自己的照片说，“不管你信不信，你和我都在这张照片里，你那时在肚子里.”',
               ]

    for string in strings:
        print(string)
        results = find_nsubj_subject(string)
        print(results)

#    lines = list(open('data/主语测试.txt', encoding='utf-8'))
#    for line in lines[:]:
#        predict = line.split()[0]
#        text = ''.join(line.split()[1:])
#        subject = find_subject(text, predict, verbose=False)
#
#        print(text)
#
#        if subject: print('说话的发出者: ' + subject[0][2])
#        else: print('None')
#
#        print('*'*10)
#
#    print('*'*88)
#    for line in lines[:]:
#        predict = line.split()[0]
#        text = ''.join(line.split()[1:])
#        subject = find_subject(text, verbose=False)

        # print(text)
        #
        # if subject: print('动作的发出者: ' + subject[0][2])
        # else: print('None')
        #
        # print('*'*10)

