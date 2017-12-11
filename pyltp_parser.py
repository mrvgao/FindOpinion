import requests
from functools import lru_cache
import jieba


@lru_cache(maxsize=256)
def cut(string): return list(jieba.cut(string))


def get_r_from_ltp(words, url):
    # words = cut(string)
    r = requests.post(url, json={'words': words})
    if r.status_code == 200: return r.json()['result']
    else: return None


host = 'http://127.0.0.1:3334/{}/'


def get_postag_from_ltp(string):
    url = host.format('pos')
    return get_r_from_ltp(string, url)


def get_dparser_from_ltp(words):
    url = host.format('dparser')
    dparse_result = get_r_from_ltp(words, url)

    # cut_words = cut(string)
    cut_words = words

    results_two_words_pair = []

    assert len(cut_words) == len(dparse_result)

    for ii, relation in enumerate(dparse_result):
        index, relation = relation
        if index == 0: words_2 = 'ROOT'
        else: words_2 = cut_words[index-1]
        results_two_words_pair.append([cut_words[ii], words_2, ii, index-1, relation])

    return results_two_words_pair


if __name__ == '__main__':
    text = '（原标题：伊朗总统鲁哈尼：沙特满足两个条件 伊朗可与其复交）'
    print(get_postag_from_ltp(text))
    print(get_dparser_from_ltp(cut(text)))
