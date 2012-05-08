# -*- coding:utf-8 -*-
import unittest
from util.textdiff import textdiff

from df import Application


class MyTestCase(unittest.TestCase):
    def test_delteandinsert(self):
        result = '<span class="delete">a</span><span class="insert">b</span>'
        self.assertEqual(result, textdiff("a","b"))
    def test_delete(self):
        result = 'thi<span class="delete">s</span> time'
        self.assertEqual(result, textdiff(u"this time",u"thi time"))
    def test_diff(self):
        result = '<span class="delete">再</span><span class="insert">在</span>回<span class="delete">首</span><span class="insert">手</span>'
        self.assertEqual(result, textdiff(u"再回首",u"在回手"))

if __name__ == '__main__': 
    unittest.main() 
