import pandas as pd
import random

content = pd.read_csv('data/zhaiyao-100days-format.csv', encoding='utf-8')


def get_article_random(size=10, dependancy_injection=None):
    results = []
    for r in content.iterrows():
        if dependancy_injection:
            random.seed(next(dependancy_injection))
        if random.random() < 0.7: continue
        results.append(r[1].content)
        if len(results) >= size: break
    return results


spoken_closet_words = {}
with open('data/spoken_close_words.txt', encoding='utf-8') as f:
    for line in f:
        w, p = line.split()
        if w.startswith('#'):continue
        spoken_closet_words[w] = float(p)


def get_spoken_closet_words():
    return spoken_closet_words


if __name__ == '__main__':
    print(get_article_random(10))

