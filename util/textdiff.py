#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
textdiff.py
Original is (C) Ian Bicking <ianb@colorstudy.com>
With changes from Richard Cyganiak <richard@cyganiak.de> and Richard Cyganiak <richard@cyganiak.de>
Modified from https://github.com/cygri/htmldiff/blob/master/htmldiff

Finds the differences between two pieces of TEXT.
*Not* line-by-line comparison (more word-by-word even letter by letter).

"""

from difflib import SequenceMatcher

class TextMatcher(SequenceMatcher):

    def __init__(self, source1, source2):
        SequenceMatcher.__init__(self, None, source1, source2)

    def textDiff(self):
        opcodes = self.get_opcodes()
        a = self.a
        b = self.b
        out = []
        for tag, i1, i2, j1, j2 in opcodes:
            if tag == 'equal':
                for item in a[i1:i2]:
                    out.append(item)
            if tag == 'delete' or tag == 'replace':
                self.textDelete(a[i1:i2], out)
            if tag == 'insert' or tag == 'replace':
                self.textInsert(b[j1:j2], out)
        text = ''.join(out)
        return text

    def textDelete(self, lst, out):
        text = ''
        for item in lst:
            text += item
        self.outDelete(text, out)

    def textInsert(self, lst, out):
        text = ''
        for item in lst:
            text += item
        self.outInsert(text, out)

    def outDelete(self, s, out):
        if s.strip() == '':
            out.append(s)
        else:
            out.append(self.startDeleteText())
            out.append(s)
            out.append(self.endDeleteText())

    def outInsert(self, s, out):
        if s.strip() == '':
            out.append(s)
        else:
            out.append(self.startInsertText())
            out.append(s)
            out.append(self.endInsertText())

    def startInsertText(self):
        return '<span class="insert">'
    def endInsertText(self):
        return '</span>'
    def startDeleteText(self):
        return '<span class="delete">'
    def endDeleteText(self):
        return '</span>'

def textdiff(source1, source2):
    """
    Return the difference between two pieces of TEXT

        >>> textdiff('test1', 'test2')
        'test<span class="delete">1</span><span class="insert">2</span>'
        >>> textdiff('test1', 'test1')
        'test1'
        >>> textdiff(u"再回首",u"在回手")
        '<span class="delete">再</span><span class="insert">在</span>回<span class="delete">首</span><span class="insert">手</span>'
        >>> textdiff(u"this time",u"thi time")
        'thi<span class="delete">s</span> time'
    """
    h = TextMatcher(source1, source2)
    return h.textDiff()

if __name__ == '__main__':
    print textdiff(u"再回首",u"在回手")
    print textdiff(u"this time",u"thi time")
    print textdiff('test1', 'test2')
    print textdiff('test1', 'test1')
