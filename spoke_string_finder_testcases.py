from unittest import TestCase
from spoken_string_finder import delete_end_none_characters


class SpokenFinderTestCases(TestCase):
    def test_delete_end_none_characters(self):
        string = '中国这几年的互联网技术迅猛发展，技术创新不断涌现，中国正在引领全球数字技术的创新和发展...'
        string = delete_end_none_characters(string)
        self.assertEqual(string, '中国这几年的互联网技术迅猛发展，技术创新不断涌现，中国正在引领全球数字技术的创新和发展')


class SelfDefinedParserTestCases(TestCase):
    def test_get_single_entity_single_verb(self):
        pass


if __name__ == '__main__':
    TestCase.run()
