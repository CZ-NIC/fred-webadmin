from fred_webadmin.webwidgets.gpyweb.gpyweb import escape, noesc, pre

# XML formatter / PythonXML PrettyPrint
try:
    # formating using PythonXML
    import StringIO
    from xml.dom.ext import PrettyPrint
    import xml.dom.minidom
    python_xml_imported = True
except ImportError:
    python_xml_imported = False

try :
    # syntax highlighting using pygments
    from pygments import highlight
    from pygments.lexers import XmlLexer
    from pygments.formatters import HtmlFormatter
    pygments_imported = True
except ImportError:
    pygments_imported = False


def format_xml(xml_string):
    doc = xml.dom.minidom.parseString(xml_string)
    doc.normalize()
    f = StringIO.StringIO()
    PrettyPrint(doc, f)
    f.seek(0,0)
    formated_xml = f.read()
    return formated_xml

def xml_highlight(xml_string):
    formated_xml = format_xml(xml_string)
    highlight_xml = highlight(formated_xml, XmlLexer(), HtmlFormatter(linenos=True))
    return highlight_xml
    
def uglify(xml):
    return '\n'.join('\n<'.join('>\n'.join(xml.split('>')).split('<')).split('\n\n'))



if python_xml_imported:
    if pygments_imported:
        xml_prettify =  xml_highlight
    else:
        xml_prettify = format_xml 
else:
    xml_prettify = uglify # :-)


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
        

