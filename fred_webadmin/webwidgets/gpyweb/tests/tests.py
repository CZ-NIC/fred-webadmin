#!/usr/bin/env python
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

from nose.tools import assert_equal

from fred_webadmin.webwidgets.gpyweb.gpyweb import *


def test_change_tag():
    pp = p('text')
    output1 = str(pp)
    pp.tag = 'span'
    assert str(pp) != output1

    pp = p('text', tag='span')
    ss = span('text')

    assert_equal(str(pp), str(ss))


def test_content_kwd_attr():
    pp1 = p(attr(style='color: red'), 'text', br())

    pp2 = p(style='color: red', content='text')
    pp2.add(br())

    pp3 = p(style='color: red', content=['text', br()])

    pp4 = p('text', style='color: red', content=br())

    assert_equal(str(pp1), str(pp2))
    assert_equal(str(pp1), str(pp3))
    assert_equal(str(pp1), str(pp4))


def test_parent():
    p1 = p()
    span(parent=p1)

    p2 = p(span())

    assert_equal(str(p1), str(p2))


def test_gpyweb_tagid_save():
    mydiv = div()

    myspan = span(attr(style='color: red'), span(save(mydiv, 'spaninspan')))

    mydiv.add(p(tagid('myp'),
                'Text of p'),
                myspan
             )
    mydiv.myp.add('additional p text')
    mydiv.spaninspan.add('text in span')
    mydiv.style = 'color: blue'

    desired_output = '''<div style="color: blue">
\t<p>
\t\tText of p
\t\tadditional p text
\t</p>
\t<span style="color: red">
\t\t<span>
\t\t\ttext in span
\t\t</span>
\t</span>
</div>
'''

    assert_equal(str(mydiv), desired_output)

#def test_media():
#    med = Media('ahoj.js')
#    print med
#    assert med.render_after() == '<script src="ahoj.js" type="text/javascript"></script>\n'
#
#    med = Media(['ahoj.js', 'cau.css'])
#    assert med.render_after() == '''<script src="ahoj.js" type="text/javascript"></script>
#<link href="cau.css" type="text/css" rel="stylesheet" />
#''', 'Note: if this test failes, it is possible that it only is due to different order of media fields (because they are stored in unordered set)'
#
#    med.media_files.update(['ajaj.js'])
#    assert med.render_after() == '''<script src="ajaj.js" type="text/javascript"></script>
#<script src="ahoj.js" type="text/javascript"></script>
#<link href="cau.css" type="text/css" rel="stylesheet" />
#''', 'Note: if this test failes, it is possible that it only is due to different order of media fields (because they are stored in unordered set)'


def test_getitem_notation():
    p1 = p(attr(cssc='top'), 'Hi ', i('how'), 'are you?')  # tradicional notation
    p2 = p(cssc='top')['Hi ', i()['how'], 'are you?']  # empty field for attributes is ugly
    p3 = p(cssc='top')['Hi ', i('how'), 'are you?']  # shortest but combination of () a [] for inserting content can be confusing
    p4 = p(cssc='top')['Hi ', i['how'], 'are you?']  # and finally shortest and withou mixing () and [] for inseting context!!! :) (must be added metaclass

    assert_equal(str(p1), str(p2))
    assert_equal(str(p1), str(p3))
    assert_equal(str(p1), str(p4))


def test_getitem_notation2():
    p1 = p(cssc='ca')[
           div(cssc='top')[
               'ahoj',
               i['svete']
              ]
          ]
    p2 = p(cssc='ca')[div(cssc='top')['ahoj', i['svete']]]
    p3 = p(attr(cssc='ca'), div(attr(cssc='top'), 'ahoj', i('svete')))
    p4 = p(attr(cssc='ca'),
           div(attr(cssc='top'),
               'ahoj',
               i('svete')
              )
          )

    assert_equal(str(p1), str(p2))
    assert_equal(str(p1), str(p3))
    assert_equal(str(p1), str(p4))


def test_getitem_nontation3():
    page1 = html[head[link(href='neco'),
                      script(type='javascript')['nakej script']
                ],
                body(id='blue')[
                     div(id='main-content')[
                         h1['nadpis'],
                         p['odstave plny dlouheho a ',
                           i['napinaveho'],
                           ' textu'
                         ]
                     ]
                ]
            ]
    page2 = html(head(link(href='neco'),
                     script(attr(type='javascript'), 'nakej script')
                    ),
                 body(attr(id='blue'),
                      div(attr(id='main-content'),
                          h1('nadpis'),
                          p('odstave plny dlouheho a ',
                            i('napinaveho'),
                            ' textu'
                           )
                      )
                 )
                )
    assert_equal(str(page1), str(page2))

#def test_benchmark_getitem_notation():
#    exp = 4
#    import time
#
#    t = time.time()
#    for q in xrange(10**exp):
#        unicode(p(cssc='top')['ahoj', i['jou']])
#    print time.time() - t
#
#    t = time.time()
#    for q in xrange(10**exp):
#        unicode(p(attr(cssc='top'), 'ahoj', i('jou')))
#    print time.time() - t
#
#    assert False
    # results: both notation have the same speed (about 1.5sec for exp = 4)


def test_http_page():
    context = {
        'doctype': 'xhtml10strict',
        'charset': 'utf-8',
        'lang': 'cs',
        'title': 'titulka',
        'media_files': ['ahoj.css', 'zdar.js', 'cus.js']
    }
    page = HTMLPage(context)
    page.body.add(div('Hello world!'))

    assert_equal(str(page), '''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="cs">
\t<head>
\t\t<meta content="text/html; charset=utf-8" http-equiv="Content-Type" />
\t\t<title>titulka</title>
\t\t<link href="ahoj.css" type="text/css" rel="stylesheet" />
\t\t<script src="zdar.js" type="text/javascript"></script>
\t\t<script src="cus.js" type="text/javascript"></script>
\t</head>
\t<body>
\t\t<div>
\t\t\tHello world!
\t\t</div>
\t</body>
</html>
''')
    page.add_media_files('caues.css')
    page.add_media_files(['cusik.js', 'ahojik.css'])

    assert_equal(str(page), '''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="cs">
\t<head>
\t\t<meta content="text/html; charset=utf-8" http-equiv="Content-Type" />
\t\t<title>titulka</title>
\t\t<link href="ahoj.css" type="text/css" rel="stylesheet" />
\t\t<script src="zdar.js" type="text/javascript"></script>
\t\t<script src="cus.js" type="text/javascript"></script>
\t\t<link href="caues.css" type="text/css" rel="stylesheet" />
\t\t<script src="cusik.js" type="text/javascript"></script>
\t\t<link href="ahojik.css" type="text/css" rel="stylesheet" />
\t</head>
\t<body>
\t\t<div>
\t\t\tHello world!
\t\t</div>
\t</body>
</html>
''')


def test_media_in_childs():
    context = {
        'doctype': 'xhtml10strict',
        'charset': 'utf-8',
        'lang': 'cs',
        'title': 'titulka',
        'media_files': ['ahoj.css', 'zdar.js']
    }
    page = HTMLPage(context)
    page.body.add(div(attr(media_files='cus.js'), 'Hello world!'))

    assert_equal(str(page), '''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="cs">
\t<head>
\t\t<meta content="text/html; charset=utf-8" http-equiv="Content-Type" />
\t\t<title>titulka</title>
\t\t<link href="ahoj.css" type="text/css" rel="stylesheet" />
\t\t<script src="zdar.js" type="text/javascript"></script>
\t\t<script src="cus.js" type="text/javascript"></script>
\t</head>
\t<body>
\t\t<div>
\t\t\tHello world!
\t\t</div>
\t</body>
</html>
''')


def test_root_tag():
    'Test when widget is addet to another widget during render(), if root_widget is really root of tree, after calling render()'
    class MyWidget(WebWidget):
        def render(self, indent_level=0):
            my_p = p(tagid('my_p'))
            self.add(my_p)
            return super(MyWidget, self).render(indent_level)
    d = div()
    mv = MyWidget()
    d.add(mv)

    d.render()

    assert_equal(mv.my_p.root_widget, d)


def test_escape():
    p1 = p('first<br />second')
    assert str(p1) == '''<p>
\tfirst&lt;br /&gt;second
</p>
'''

    p2 = p(noesc('first<br />second'))
    assert_equal(str(p2), '''<p>
\tfirst<br />second
</p>
''')


def test_enclose():
    p1 = p(attr(enclose_content=True), 'Visit our ', a(attr(href='http://www.example.com'), 'website'), '.',
           input(attr(type="submit", value="+Like")), 'Like us.')  # tag "a" has enclose_content = True by default
    corect_result = '''<p>Visit our <a href="http://www.example.com">website</a>.<input type="submit" value="+Like" />Like us.</p>
'''
    assert_equal(str(p1), corect_result)


def test_cssc_manipulation():
    b1 = b('ahoj')
    b1.add_css_class('myclass')
    assert_equal(str(b1), '<b class="myclass">ahoj</b>\n')

    assert_equal(b1.remove_css_class('myclass'), True)
    assert_equal(str(b1), '<b>ahoj</b>\n')

    b2 = b(attr(cssc="myclass1 myclass2 myclass3"), 'ahoj')
    assert_equal(b2.remove_css_class('myclass2'), True)
    assert_equal(str(b2), '<b class="myclass1 myclass3">ahoj</b>\n')
    b2.add_css_class('myclass4')
    assert_equal(str(b2), '<b class="myclass1 myclass3 myclass4">ahoj</b>\n')

    # return False when webwidged didn't have such a class:
    assert_equal(b2.remove_css_class('non_existent_class'), False)


def test_join():
    result = br().join(['a', 'b', 'c'])
    assert_equal(str(result), '''\ta
\t<br />
\tb
\t<br />
\tc
''')
