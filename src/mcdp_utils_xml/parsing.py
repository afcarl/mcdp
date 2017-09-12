
from bs4 import BeautifulSoup
from contracts.utils import raise_desc
from contracts import contract
from mcdp_utils_misc.fileutils import write_data_to_file


def bs(fragment):
    """ Returns the contents wrapped in an element called "fragment".
        Expects fragment as a str in utf-8 """
    if isinstance(fragment, unicode):
        fragment = fragment.encode('utf8')
    s = '<fragment>%s</fragment>' % fragment
    
    parsed = BeautifulSoup(s, 'lxml', from_encoding='utf-8')
    res = parsed.html.body.fragment
    assert res.name == 'fragment'
    return res

    

def to_html_stripping_fragment(soup):
    """ Returns a string encoded in UTF-8 """
    assert soup.name == 'fragment'
    s = str(soup)
    check_html_fragment(s)
    s = s.replace('<fragment>','')
    s = s.replace('</fragment>','')
    return s

def to_html_stripping_fragment_document(soup):
    """ Assumes it is <fragment>XXXX</fragment> and strips the fragments. """
    assert soup.html is not None, str(soup)
    s = str(soup)
    s = s.replace('<fragment>','')
    s = s.replace('</fragment>','')
    return s
    

def check_html_fragment(m, msg=None):
    if '<html>' in m or 'DOCTYPE' in m:
        if msg is None:
            msg2 = ""
        else:
            msg2 = msg + ' '
        msg2 += 'This appears to be a complete document instead of a fragment.'
        raise_desc(ValueError, msg2, m=m)
        
## Use these for entire documents

@contract(s=str)
def bs_entire_document(s):
    parsed = BeautifulSoup(s, 'lxml', from_encoding='utf-8')
    if parsed.find('body') is None:
        msg ='The provided string was not an entire document.'
        raise ValueError(msg, s=s[:200])
    return parsed

def to_html_entire_document(soup):
    return str(soup)

def read_html_doc_from_file(filename):
    """ Reads an entire document from the file """
    data = open(filename).read()
    return bs_entire_document(data)

def write_html_doc_to_file(soup, filename):
    html = to_html_entire_document(soup)
    write_data_to_file(html, filename)

