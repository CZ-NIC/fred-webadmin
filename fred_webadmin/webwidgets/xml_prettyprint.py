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

from fred_webadmin.webwidgets.gpyweb.gpyweb import escape, noesc, pre

# XML formatter / PythonXML PrettyPrint
try:
    # formating using PythonXML
    import StringIO
    from xml.dom.ext import PrettyPrint
    from xml.dom.ext.reader import Sax2
    python_xml_imported = True
except ImportError:
    python_xml_imported = False

try:
    # syntax highlighting using pygments
    from pygments import highlight
    from pygments.lexers import XmlLexer
    from pygments.formatters import HtmlFormatter
    pygments_imported = True
except ImportError:
    pygments_imported = False


def format_xml(xml_string):
    if xml_string:
        reader = Sax2.Reader()
        doc = reader.fromString(xml_string)
        doc.normalize()
        f = StringIO.StringIO()
        PrettyPrint(doc, f)
        f.seek(0, 0)
        formated_xml = f.read().decode('utf-8')
        return formated_xml
    else:
        return ''


def xml_highlight(xml_string):
    if xml_string:
        formated_xml = format_xml(xml_string)
        highlight_xml = highlight(formated_xml, XmlLexer(), HtmlFormatter(linenos=True))
        return highlight_xml
    else:
        return ''


def uglify(xml):
    return '\n'.join('\n<'.join('>\n'.join(xml.split('>')).split('<')).split('\n\n'))


if python_xml_imported:
    if pygments_imported:
        xml_prettify = xml_highlight
    else:
        xml_prettify = format_xml
else:
    xml_prettify = uglify  # :-)


def xml_prettify_webwidget(xml_string):
    xml_output_string = xml_prettify(xml_string)
    if python_xml_imported:
        if pygments_imported:
            result = noesc(xml_output_string)
        else:
            result = pre(xml_output_string)
    else:
        result = noesc(escape(xml_output_string).replace('\n', '<br />\n'))
    return result
