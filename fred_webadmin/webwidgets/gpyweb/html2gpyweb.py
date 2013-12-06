#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from HTMLParser import HTMLParser


class GPHTMLParser(HTMLParser):
    def __init__(self):
#        super(GPHTMLParser, self).__init__()
        HTMLParser.__init__(self)
        self.output = ''
        self.level = 0
        self.objects_on_level = {}

    def handle_starttag(self, tag, attrs):
        print "Encountered the beginning of a %s tag, attrs %s" % (tag, attrs)
        if self.objects_on_level.get(self.level):
            self.output += ', '
            if self.level < 1:
                self.output += '\n'
        self.output += tag + '('
        if attrs:
            new_attrs = []
            for attr_key, attr_val in attrs:
                if attr_key == 'class':
                    attr_key = 'cssc'
                attr_key = attr_key.replace('tal:', 'TAL_')
                if attr_val.startswith('here/result'):
                    attr_val = attr_val = 'result.' + attr_val[len('here/result/'):]
                else:
                    attr_val = "'%s'" % attr_val
                new_attrs.append((attr_key, attr_val))
            self.output += 'attr(%s)' % ', '.join(["%s=%s" % (attr_key, attr_val) for attr_key, attr_val in new_attrs])
            self.objects_on_level[self.level + 1] = True
        self.objects_on_level[self.level] = True
        self.level += 1

    def handle_endtag(self, tag):
        self.objects_on_level[self.level] = False
        self.level -= 1

        print "Encountered the end of a %s tag" % tag
        self.output += ')'
#        if self.level < 1:
#            self.output += '\n'

    def handle_data(self, data):
        data = data.strip()
        if data:
            if data[:1] == data[-1:] == ':':
                data = "_('%s')" % data[1:-1]
            else:
                data = "'%s'" % data

            if self.objects_on_level.get(self.level):
                self.output += ', '
            self.output += data
            self.objects_on_level[self.level] = True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print   'Please put filename of file to conversion as argument'
        sys.exit(1)
    filename = sys.argv[1]

    html = open(filename).read()
    parser = GPHTMLParser()
    parser.feed(html)

    print parser.output
