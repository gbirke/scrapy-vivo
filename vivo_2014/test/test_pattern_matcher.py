import unittest
import regex
from nose.tools import *

from vivo_2014.pattern_matcher import DateMatcher, PatternCompiler, PatternNotInDictionaryError


class PatternMatcherTestCase(unittest.TestCase):

    def test_pattern_compile_without_replacement(self):
        c = PatternCompiler({})
        expected = regex.compile(".+")
        self.assertEqual(c.compile_pattern(".+"), expected)

    def test_pattern_compile_with_replacement(self):
        c = PatternCompiler({"TEST1": ".*"})
        expected = regex.compile(".*")
        self.assertEqual(c.compile_pattern("%{TEST1}"), expected)

    def test_pattern_compile_with_pattern_replacement(self):
        c = PatternCompiler({"TEST1": "foo %{TEST2}", "TEST2":"bar"})
        expected = regex.compile("foo bar")
        self.assertEqual(c.compile_pattern("%{TEST1}"), expected)

    def test_pattern_compile_fails_when_pattern_is_missing(self):
        c = PatternCompiler({})
        with self.assertRaises(PatternNotInDictionaryError) as cm:
            c.compile_pattern("%{TEST1}")
        self.assertRegexpMatches(str(cm.exception), r"'TEST1'")

    def test_pattern_compile_fails_when_pattern_is_circular(self):
        c = PatternCompiler({"TEST1":"%{TEST2}", "TEST2":"%{TEST1}"})
        with self.assertRaises(Exception) as cm:
            c.compile_pattern("%{TEST1}")
        self.assertRegexpMatches(str(cm.exception), r"'TEST1'")


def test_date_matching():
    dates = [
        '2009',
        'SS 2013',
        #'12. 2012',
        '05.09. 2008',
        '01. 10. 2009',
        'WS 2010/2011',
        '05.-07.09 2012',
        '09.-10.09.2010',
        '08.-10.11. 2010',
        '19.-20. 07.2010',
        '01.- 03.04. 2009',
        '26. - 28.11. 2012',
        '28.07.-01.08. 2013',
        '20. - 22. 10. 2010',
        '29. 07.- 01. 08.2008',
        '06 - 09. Oktober 2009'
    ]
    for d in dates:
        yield check_date, d

def check_date(date_string):
    date_match = DateMatcher()
    print date_match.matcher
    match_result = date_match.match(date_string)
    assert_is_not_none(match_result, "'%s was not matched'" % date_string)
    assert_equal(match_result.group(0), date_string)


