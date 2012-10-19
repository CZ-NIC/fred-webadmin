from xml.parsers.xmlproc import xmldtd
from xml.parsers.xmlproc.dtdparser import DTDParser
from xml.parsers.xmlproc.utils import ErrorRaiser

def load_dtd(dtd_filename='xhtml1-strict.dtd', dtd_root_elem='html'):
    dtd_parser = DTDParser()
    dtd_parser.set_error_handler(ErrorRaiser(dtd_parser))
    dtd = xmldtd.CompleteDTD(dtd_parser)
    dtd_parser.set_dtd_consumer(dtd)
    dtd_parser.parse_resource(dtd_filename)
    dtd.root_elem = dtd_root_elem
    return dtd

if __name__ == "__main__":
    # elements with enclose_content flag
    enclose_elems = ['a', 'b', 'i', 'title']

    attr_translation = {
            'xmllang': 'xml:lang',
            'httpequiv': 'http-equiv',
            'cssc': 'class'
        }

    output = ''

    dtd = load_dtd()
    for elem in dtd.elems.values():
        output += "class %s(WebWidget):\n" % elem.name
        if elem.name in enclose_elems:
            output += "    enclose_content = True\n"
        tattr_string = "    tattr_list=%s\n\n" % elem.attrlist
        for t_to, t_from in attr_translation.items():
            tattr_string = tattr_string.replace(t_from, t_to)
        output += tattr_string

    print output
