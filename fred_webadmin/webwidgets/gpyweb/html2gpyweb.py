#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2018  CZ.NIC, z. s. p. o.
#
# This file is part of FRED.
#
# FRED is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# FRED is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with FRED.  If not, see <https://www.gnu.org/licenses/>.

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
