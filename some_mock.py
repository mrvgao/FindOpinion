import word_cutter
from stanfordcorenlp import StanfordCoreNLP

nlp = StanfordCoreNLP('http://127.0.0.1', port=9000, lang='zh')

words = word_cutter.cut()