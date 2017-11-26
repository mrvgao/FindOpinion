"""
Pro-precessing text into sentences. And replace the stop words in quotes.
"""
import re


def split_to_sentence(line, need_get_substring=True):
    line = change_text_english(line)
    hidden_marks = r"""[\u3000\xa0@▌]"""
    line = re.compile(hidden_marks).sub("", line)
    split = '||'
    end_marks = r"""{}""".format(get_end_marks())
    line = replace_in_quote_end_mark(line, end_marks)
    white_space_regex = re.compile(end_marks)
    content = white_space_regex.sub(split, line)
    dont_need_mark = re.compile(r"[\"]")
    content = dont_need_mark.sub(split, content)

    if need_get_substring:
        split_mark = re.compile(r"""[,，<> · ；() （）：)（））]""")
        content = split_mark.sub(split, content)

    # content = re.sub(split, content).strip()
    # content = re.sub("\s+", ' ', content).strip()
    sentences = content.split(split)
    sentences = filter(lambda x: len(x) >= 1, sentences)
    sentences = list(map(recovery_from_english, sentences))
    return sentences


def change_text_english(text):
    if len(text) <= 1:
        return text

    new_text = text[0]
    placeholder = u'\U0001f604'
    for i in range(1, len(text)-1):
        current_char = text[i]
        if (is_space(current_char) and forward_is_english(i, text)) or (is_space(current_char) and 0 <= ord(text[i-1]) <= 127):
            new_text += placeholder
        else:
            new_text += current_char

    new_text += text[-1]

    return new_text


def is_space(char):
    if char == ' ':
        return True
    else:
        return False


def forward_is_english(index, text):
    while index < len(text):
        if is_space(text[index]):
            index += 1
            continue
        elif 0 <= ord(text[index]) <= 127:
            return True
        else:
            return False


def recovery_from_english(sentence):
    assert len(sentence) >= 1, sentence

    placeholder = u'\U0001f604'

    new_sentence = sentence[0] if sentence[0] != placeholder else ""

    for index in range(1, len(sentence)-1):
        current_char = sentence[index]
        if current_char == placeholder:
            if is_between_english(sentence[index-1], sentence[index+1]):
                new_sentence += ' '
        else:
            new_sentence += current_char

    if sentence[-1] != placeholder:
        new_sentence += sentence[-1]

    return new_sentence


def is_between_english(previus, after):
    if ord(previus) >= 0 and ord(after) <= 127:
        return True
    else:
        return False


def get_end_marks():
    end_marks = """[\u3000\n\r\t@。？！?？|;!！【】]"""
    return end_marks


def replace_in_quote_end_mark(string, end_marks):
    quote_begin = ['‘', '“']
    quote_end = ['’', '”']
    replace_by = '.'
    new_str = ""
    start_replace = False
    for c in string:
        if c in quote_begin:
            start_replace = True

        if start_replace and c in end_marks:
            new_str += replace_by
        else:
            new_str += c

        if start_replace and c in quote_end:
            start_replace = False

    return new_str


if __name__ == '__main__':
    pass
