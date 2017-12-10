from corenlp_utils import get_pos_tag, find_person_entities
from functools import reduce
from itertools import product
import structure_parser
from utils import get_spoken_closet_words


spoken_closet_words = get_spoken_closet_words()
self_excluded_entities = [e.strip() for e in open('data/not_is_entity.txt', encoding='utf-8')]


def is_spoken_word(word, pos, clost_dict):
    if pos.startswith('V') and word in clost_dict:
        return True
    else:
        return False


def locate_person_and_spoken_verb(article, output_format='list'):
    pos_tag = get_pos_tag(article)
    persons = find_person_entities(article)

    words = []
    for w, tag in pos_tag:
        if w in spoken_closet_words and tag.startswith('V'):
            words.append((w, 'V'))
        elif w in persons or tag == 'NR' and w not in self_excluded_entities:
            words.append((w, 'E'))
        else:
            words.append((w, ''))

    if output_format == 'list':
        return words
    elif output_format == 'string':
        return ''.join(['{}{}{}'.format(t, w, t) for w, t in words])
    else:
        raise TypeError('unsupported output format. <list, string>')


class Tagger:

    unknown_index = 0
    entity_index = 0

    def __init__(self):
        self.__spoken_tag = '-S-'
        self.__end_speech = '-EOS-'
        self.__unknown = '<UNK>'

    def spoken_tag(self, word=None, verb=None):
        if word is None:
            word = self.__unknown
            word += str(Tagger.unknown_index)
            Tagger.unknown_index += 1
        return word, self.__spoken_tag, verb

    def end_speech(self, word=None, verb=None):
        if word is None:
            word = self.__unknown
            word += str(Tagger.unknown_index)
        return word, self.__end_speech, verb

    def is_unknown_start_mark(self, w, t):
        return str(w).startswith(self.__unknown) and t == self.__spoken_tag

    def is_unknown_end_mark(self, w, t):
        return str(w).startswith(self.__unknown) and t == self.__end_speech

    def is_unknown_mark(self, word):
        return str(word).startswith(self.__unknown)

    def get_unknown_index(self, w):
        assert self.is_unknown_mark(w)
        index = w.replace(self.__unknown, '')
        return int(index)


def is_quote(w):
    return w in ['‘', '“', "'", '"', '“', '‘', '”']


def is_sentence_end(w):
    return w in ['。', '！', '？', '.', '?', '!', ' ']


def find_quotes_format(words_and_tags):
    find_start = False
    tagger = Tagger()
    results = []

    for w, t, v in words_and_tags:
        if is_quote(w) and not find_start:
            results.append(tagger.spoken_tag())
            find_start = True
        elif is_quote(w) and find_start:
            results.append(tagger.end_speech())
            find_start = False
        results.append((w, t, v))

    return results


def split_words_and_tags_to_subsentence(words_and_tags):
    new_subsentence = []
    sentences = []

    for w, t in words_and_tags:
        if is_sentence_end(w):
            new_subsentence.append((w, t))
            sentences.append(new_subsentence)
            new_subsentence = []
        else:
            new_subsentence.append((w, t))

    return sentences


def analysis_sub_string_object_speak_format(substring):
    tags = [t if t != '' else '_' for w, t in substring]
    words = [w for w, t in substring]

    def find_indices(L, element): return [i for i, e in enumerate(L) if e == element]

    text = "".join([w for w, t in substring])
    s_v_structure = structure_parser.find_subject(text)

    found_subject, found_predicate = None, None
    subject_index, predicate_index = None, None

    def find_entity_and_verb(_subject_indices, _predicate_indices):
        for s_i, p_i in product(_subject_indices, _predicate_indices):
            if tags[s_i] == 'E' and tags[p_i].startswith('V') and words[p_i] in spoken_closet_words:
                global subject_index, predicate_index
                global found_subject, found_predicate
                subject_index, predicate_index = s_i, p_i
                found_subject, found_predicate = words[s_i], words[p_i]
                return found_subject, found_predicate
        return None, None

    for relation, predicate, subject in s_v_structure:
        predicate_indices = find_indices(words, predicate)
        subject_indices = find_indices(words, subject)

        entity, predict = find_entity_and_verb(subject_indices, predicate_indices)

        if entity and predict: break

    results = []
    tagger = Tagger()

    index = 0
    for w, t in substring:
        results.append((w, t, ''))

        if index == predicate_index:
            results.append(tagger.spoken_tag(word=found_subject, verb=found_predicate))

    return results


def add_end_of_speech_of_each_speech(words_and_tags):
    tagger = Tagger()
    need_find_end_of_speech = False
    results = []

    subject = None
    for w, t, v in words_and_tags:
        results.append((w, t, v))
        if t == tagger.spoken_tag()[1]:
            need_find_end_of_speech = True
            subject = w

        # TODO : Need merge split sentences into one speech sentence
        if need_find_end_of_speech and is_sentence_end(w):
            results.append(tagger.end_speech(subject, verb=None))
            need_find_end_of_speech = False

    return results


def find_object_speak_format(words_and_tags):
    """
    return: [(word, tag)] if find object speak sth. format, word will be '-S-', tag will be '-S-'
    """

    sub_sentences = split_words_and_tags_to_subsentence(words_and_tags)

    sub_sentence_o_v_format = [analysis_sub_string_object_speak_format(s) for s in sub_sentences]

    sub_sentences_join = reduce(lambda a, b: a + b, sub_sentence_o_v_format, [])

    results = add_end_of_speech_of_each_speech(sub_sentences_join)

    return results


def extract_speech_from_words(words_and_tags):
    tagger = Tagger()
    results = []
    for ii, w_t_v in enumerate(words_and_tags):
        w, t, v = w_t_v
        if t == tagger.spoken_tag()[1]:  # it's speech start flag.
            speech = []
            for w2, t2, v2 in words_and_tags[ii+1:]:
                if w2 == w and t2 == tagger.end_speech()[1]: break # it's speech end flag.
                elif t2 == tagger.end_speech()[1] or t2 == tagger.spoken_tag()[1]: continue
                speech.append(w2)
            results.append((w, speech, v))

    def is_long_special_string(s):
        if is_quote(s[0]) and len(s) <= 6: return True
        if len(s) < 3: return True
        return False

    def strip(string):
        new_s = ""
        for s in string:
            if new_s == "" and not str(s).isalnum(): continue
            new_s += s

        return new_s

    results = [(w, v, strip(''.join(s))) for w, s, v in results if not is_long_special_string(s)]

    return results


def find_s_v_structure(words_and_tags, direction='right'):
    target_structure = ['E', 'V'] if direction == 'right' else ['V', 'E']

    find_structure = []

    def append_word(word_tag, found_structure):
        if len(found_structure) == 0: found_structure.append(word_tag)
        elif word_tag == found_structure[-1]: pass
        else: found_structure.append(word_tag)
        return found_structure

    entity_records = []
    find_subject = False

    verb = None

    for w, t, _ in words_and_tags:
        if is_sentence_end(w): break

        if t in target_structure:
            find_structure = append_word(t, find_structure)
            # TODO find subject is wrong here, need use
            if t == 'E': entity_records.append(w)
            if t == 'V': verb = w
            if find_structure[len(find_structure)-1] != target_structure[len(find_structure)-1]:
                break

        if find_structure == target_structure:
            find_subject = True
            break

    if find_subject:
        if direction == 'left':
            entity_records.reverse()
        return ''.join(entity_records), verb
    else:
        return None, verb


def find_quote_subject(words_and_tags):
    tagger = Tagger()

    unknown_index_real_subject_map = {}

    for ii, w_t in enumerate(words_and_tags):
        w, t, v = w_t
        if tagger.is_unknown_start_mark(w, t):
            subject, verb = find_s_v_structure(words_and_tags[:ii][::-1], direction='left')

            if subject is not None:
                unknown_index_real_subject_map[w] = (subject, verb)
            else:  # not find subject before quote
                for jj, w2_t2_v2 in enumerate(words_and_tags[ii:]):
                    w2, t2, v2 = w2_t2_v2
                    if tagger.is_unknown_end_mark(w2, t2) and w2 == w:
                        subject = find_s_v_structure(words_and_tags[ii+jj:], direction='right')
                        if subject is not None:
                            unknown_index_real_subject_map[w] = (subject, v2)
                            break

    words_and_tags = list(map(list, words_and_tags))

    for index in range(len(words_and_tags)):
        word = words_and_tags[index][0]
        if word in unknown_index_real_subject_map:
            words_and_tags[index][0] = unknown_index_real_subject_map[word][0]
            words_and_tags[index][2] = unknown_index_real_subject_map[word][1]  # set verb

    words_and_tags = [(w, t, v) for w, t, v in words_and_tags if not tagger.is_unknown_mark(w)]

    return words_and_tags


def get_an_article_speech(article, verbose=False):
    entities_and_verbs = locate_person_and_spoken_verb(article)
    o_v_format = find_object_speak_format(entities_and_verbs)

    quote_format = find_quotes_format(o_v_format)

    # with open('result_1.txt', 'w', encoding='utf-8') as result_f:
    #     for w, t in quote_format:
    #         print('{} {}'.format(w, t))
    #         result_f.write('{} {} \n'.format(w, t))

    quote_format_with_subject = find_quote_subject(quote_format)

    results = extract_speech_from_words(quote_format_with_subject)

    results = remove_not_predicate_words(results)

    results = calculate_confidence(results)

    if verbose:
        for r in results: print(r)

    return results


# def remove_not_predicate_words(results):
#     """
#     Some string like "表示了复杂的心情"， 等并不是表示态度的。 所以需要过滤掉。
#     过滤的时候， 用的是Dependency paring的方式。
#     :param results:
#     :return:
#     """
#
#     def find_spoker(string, predicate):
#         subjects = find_subject(string, predicate)
#         return subjects[0][2] if subjects else None
#
#     results = filter(lambda s_p_o: find_spoker("".join(s_p_o), s_p_o[1]) is not None, results)
#
#     return results


if __name__ == '__main__':
    articles = [line.replace(r'\n', '。') for line in open('test_article.txt', encoding='utf-8')]

    for ii, a in enumerate(articles):
        print('-----------{}----------'.format(ii))
        article = ''.join(a)
        get_an_article_speech(article)

