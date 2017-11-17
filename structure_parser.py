import re
from corenlp_utils import get_text_dependency_parser_result


def find_subject(text, predict=None, verbose=False):
    if isinstance(predict, str): predict = [predict]

    comma = ',，:：'
    regx = re.compile('[%s]'.format(re.escape(comma)))
    text = regx.sub("", text)
    auxiliarity = 'aux:asp'
    target_relations = ('nsubj', 'aux:asp')
    results = get_text_dependency_parser_result(text, target_relations, verbose=verbose)

    # if ('aux:asp', predict, *) in results
    if len(list(filter(lambda r_p__: r_p__[0] == auxiliarity and r_p__[1] in predict, results))) > 0:
        return None
    elif predict:
        return [e for e in results if e[1] in predict]
    else:
        return results


if __name__ == '__main__':
    lines = list(open('data/subject_test.txt', encoding='utf-8'))
    for line in lines[:]:
        predict = line.split()[0]
        text = ''.join(line.split()[1:])
        subject = find_subject(text, predict, verbose=False)

        print(text)

        if subject: print('说话的发出者: ' + subject[0][2])
        else: print('None')

        print('*'*10)


