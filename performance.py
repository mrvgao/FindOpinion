import pandas as pd
import csv
from spoken_string_finder import opinion_extract


def batch_process_csv(src_file, target_file):
    content = pd.read_csv(src_file, encoding='utf-8')
    result = csv.writer(open(target_file, 'w', encoding='utf-8'))
    result.writerow(['content', 'opinion'])

    target_indices = []

    for ii, row in enumerate(content.iterrows()):
        if len(target_indices) != 0 and (ii + 2) not in target_indices: continue
        print(ii)
        news = row[1]['content']
        # print(news)
        opinions = opinion_extract(news)
        opinions = "\n".join(map(str, opinions))
        # print(opinions)
        result.writerow([news, opinions])
    print('write done!')


def process_text():
    text = "".join(open('data/test_file.txt', encoding='utf-8'))
    print(opinion_extract(text))


if __name__ == '__main__':
    # process_text()
    batch_process_csv('data/news-1k-test-opinion-extract-src.csv', 'news-1k-test-opinion-extract-result.csv')

