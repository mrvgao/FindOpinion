import jieba

jieba.load_userdict('data/dict.txt')


def cut(string):
    return list(jieba.cut(string))