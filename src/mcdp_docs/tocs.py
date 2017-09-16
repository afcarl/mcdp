# -*- coding: utf-8 -*-

from collections import namedtuple

from bs4.element import Comment, Tag, NavigableString

from contracts.utils import indent
from mcdp.logs import logger
from mcdp_utils_xml import add_class, bs, note_error2

from .manual_constants import MCDPManualConstants
from .toc_number import render_number, number_styles


figure_prefixes = ['fig', 'tab', 'subfig', 'code']
cite_prefixes = ['bib']
div_latex_prefixes = ['exa', 'rem', 'lem', 'def', 'prop', 'prob', 'thm']


def element_has_one_of_prefixes(element, prefixes):
    eid = element.attrs.get('id', 'notpresent')
    return any(eid.startswith(_ + ':') for _ in prefixes)


class GlobalCounter:
    header_id = 1


def fix_header_id(header, globally_unique_id_part):
    ID = header.get('id', None)
    prefix = None if (ID is None or not ':' in ID) else ID[:ID.index(':')]

    allowed_prefixes_h = {
        'h1': ['sec', 'app', 'part'],
        'h2': ['sub', 'appsub'],
        'h3': ['subsub', 'appsubsub'],
        'h4': ['par'],
    }

    if header.name in allowed_prefixes_h:
        allowed_prefixes = allowed_prefixes_h[header.name]
        default_prefix = allowed_prefixes[0]

        if ID is None:
            header['id'] = '%s:%s-%s' % (default_prefix, globally_unique_id_part, GlobalCounter.header_id)
            GlobalCounter.header_id += 1
        else:
            if prefix is None:
                if ID != 'booktitle':
                    msg = ('Adding prefix %r to current id %r for %s.' %
                           (default_prefix, ID, header.name))
                    header.insert_before(Comment('Warning: ' + msg))
                    header['id'] = default_prefix + ':' + ID
            else:
                if prefix not in allowed_prefixes:
                    msg = ('The prefix %r is not allowed for %s (ID=%r)' %
                           (prefix, header.name, ID))
                    logger.error(msg)
                    header.insert_after(Comment('Error: ' + msg))

def fix_ids_and_add_missing(soup, globally_unique_id_part):
    for h in soup.findAll(['h1', 'h2', 'h3', 'h4']):
        fix_header_id(h, globally_unique_id_part)

def get_things_to_index(soup):
    """
        nothing with attribute "notoc"

        h1, h2, h3, h4
        figure  with id= "fig:*" or "tab:*" or "subfig:*" or code
    """
    formatter = None
    for h in soup.findAll(['h1', 'h2', 'h3', 'h4', 'figure', 'div', 'cite']):

        if formatter is None:
            formatter = h._formatter_for_name("html")

        if h.has_attr('notoc'):
            continue

        if h.name in ['h1', 'h2', 'h3', 'h4']:
#             fix_header_id(h)
            h_id = h.attrs['id']
            if h.name == 'h1':
                if h_id.startswith('part:'):
                    depth = 1
                elif h_id.startswith('app:'):
                    depth = 2
                elif h_id.startswith('sec:'):
                    depth = 3
                else:
                    raise ValueError(h)
            elif h.name == 'h2':
                depth = 4
            elif h.name == 'h3':
                depth = 5
            elif h.name == 'h4':
                depth = 6
            elif h.name == 'h5':
                depth = 7
            elif h.name == 'h6':
                depth = 8

            name = h.decode_contents(formatter=formatter)
            yield h, depth, name

        elif h.name in ['figure']:
            if not element_has_one_of_prefixes(h, figure_prefixes):
                continue

            # XXX: bug because it gets confused with children
            figcaption = h.find('figcaption')
            if figcaption is None:
                name = None
            else:
                name = figcaption.decode_contents(formatter=formatter)
            yield h, 100, name

        elif h.name in ['div']:
            if not element_has_one_of_prefixes(h, div_latex_prefixes):
                continue
            label = h.find(class_='latex_env_label')
            if label is None:
                name = None
            else:
                name = label.decode_contents(formatter=formatter)
            yield h, 100, name
        else:
            pass


def generate_toc(soup, max_depth=None):
    stack = [Item(None, 0, 'root', 'root', [])]

    headers_depths = list(get_things_to_index(soup))

    for header, depth, using in headers_depths:
        if max_depth is not None:
            if depth > max_depth:
                continue

        item = Item(header, depth, using, header['id'], [])

        while(stack[-1].depth >= depth):
            stack.pop()
        stack[-1].items.append(item)
        stack.append(item)

    root = stack[0]

    logger.debug('numbering items')
    number_items2(root)
    if False:
        logger.debug(toc_summary(root))
#
#     logger.debug('toc iterating')
#     # iterate over chapters (below each h1)
#     # XXX: this is parts
#     if False:
#         for item in root.items:
#             s = item.to_html(root=True, max_levels=100)
#             stoc = bs(s)
#             if stoc.ul is not None:  # empty document case
#                 ul = stoc.ul
#                 ul.extract()
#                 ul['class'] = 'toc chapter_toc'
#                 # todo: add specific h1
#                 item.tag.insert_after(ul)  # XXX: uses <fragment>
#
#     logger.debug('toc done iterating')
    exclude = ['subsub', 'fig', 'code', 'tab', 'par', 'subfig',
                'appsubsub',
                        'def', 'eq', 'rem', 'lem', 'prob', 'prop', 'exa', 'thm' ]
    without_levels = root.copy_excluding_levels(exclude)
    res = without_levels.to_html(root=True, max_levels=13)
    return res


def toc_summary(root):
    s = ''
    for item in root.depth_first_descendants():
        number = item.tag.attrs.get(LABEL_WHAT_NUMBER, '???')
        display_name = item.name
        if display_name:
            display_name = display_name.replace('\n', ' ')
            display_name = display_name[:100]
        m = ('depth %s tag %s id %-30s %-20s %s %s  ' %
             (item.depth, item.tag.name, item.id[:26],
              number, ' ' * 2 * item.depth, display_name))
        m = m + ' ' * (120 - len(m))
        s += '\n' + m
    return s


class Item(object):

    def __init__(self, tag, depth, name, _id, items):
        self.tag = tag
        self.name = name
        self.depth = depth
        self.id = _id
        self.items = items
        self.number = None
        if ":" in self.id:
            # Get "sub", "sec", "part", etc.
            self.header_level = self.id.split(":")[0]
        else:
            self.header_level = 'unknown'
            logger.warn(self.id)

    def copy_excluding_levels(self, exclude_levels):
        items = []
        for _ in self.items:
            x = _.copy_excluding_levels(exclude_levels)
            if x.header_level not in exclude_levels:
                items.append(x)
        item = Item(
            tag=self.tag, depth=self.depth, name=self.name, _id=self.id, items=items)
        return item

    def to_html(self, root, max_levels, ):
        s = u''
        if not root:
            s += (u"""<a class="toc_link toc_link-depth-%s number_name toc_a_for_%s" href="#%s"></a>""" %
                  (self.depth, self.header_level, self.id))

        if max_levels and self.items:
            s += '<ul class="toc_ul-depth-%s toc_ul_for_%s">' % (
                self.depth, self.header_level)
            for item in self.items:
                sitem = item.to_html(root=False, max_levels=max_levels - 1)
                sitem = indent(sitem, '  ')
                s += ('\n  <li class="toc_li-depth-%s toc_li_for_%s">\n%s\n  </li>' %
                      (self.depth, self.header_level, sitem))
            s += '\n</ul>'

        return s

    def depth_first_descendants(self):
        for item in self.items:
            yield item
            for item2 in item.depth_first_descendants():
                yield item2

Label = namedtuple('Label', 'what number label_self')

Style = namedtuple('Style', 'resets labels')

def get_style_book():

    resets = {
        'part': [],
        'sec': ['sub', 'subsub', 'par'],
        'sub': ['subsub', 'par'],
        'subsub': ['par'],
        'app': ['appsub', 'appsubsub', 'par'],
        'appsub': ['appsubsub', 'par'],
        'appsubsub': ['par'],
        'par': [],
        'fig': ['subfig'],
        'subfig': [],
        'tab': [],
        'code': [],
        'exa': [],
        'rem': [],
        'lem': [],
        'def': [],
        'prop': [],
        'prob': [],
        'thm': [],
    }

    labels = {
        'part': Label('Part', '${part}', ''),
        'sec': Label('Chapter', '${sec}', ''),
        'sub': Label('Section', '${sec}.${sub}', ''),
        'subsub': Label('Subsection', '${sec}.${sub}.${subsub}', '${subsub}) '),
        'par': Label('Paragraph', '${par|lower-alpha}', ''),
        'app': Label('Appendix', '${app|upper-alpha}', ''),
        'appsub': Label('Section', '${app|upper-alpha}.${appsub}', ''),
        'appsubsub': Label('Subsection', '${app|upper-alpha}.${appsub}.${appsubsub}', ''),
        # global counters
        'fig': Label('Figure', '${fig}', ''),
        'subfig': Label('Figure', '${fig}${subfig|lower-alpha}', '(${subfig|lower-alpha})'),
        'tab': Label('Table', '${tab}', ''),
        'code': Label('Listing', '${code}', ''),
        'rem': Label('Remark', '${rem}', ''),
        'lem': Label('Lemma', '${lem}', ''),
        'def': Label('Definition', '${def}', ''),
        'prob': Label('Problem', '${prob}', ''),
        'prop': Label('Proposition', '${prop}', ''),
        'thm': Label('Theorem', '${thm}', ''),
        'exa': Label('Example', '${exa}', ''),

    }
    return Style(resets, labels)

def get_style_duckietown():
    resets = {
        'part': ['sec'],
        'sec': ['sub', 'subsub', 'par', 'fig', 'tab'],
        'sub': ['subsub', 'par'],
        'subsub': ['par'],
        'app': ['appsub', 'appsubsub', 'par'],
        'appsub': ['appsubsub', 'par'],
        'appsubsub': ['par'],
        'par': [],
        'fig': ['subfig'],
        'subfig': [],
        'tab': [],
        'code': [],
        'exa': [],
        'rem': [],
        'lem': [],
        'def': [],
        'prop': [],
        'prob': [],
        'thm': [],
    }


    labels = {
        'part': Label('Part', '${part|upper-alpha}', ''),
        'sec': Label('Unit', '${part|upper-alpha}-${sec}', ''),
        'sub': Label('Section', '${sec}.${sub}', ''),
        'subsub': Label('Subsection', '${sec}.${sub}.${subsub}', '${subsub}) '),
        'par': Label('Paragraph', '${par|lower-alpha}', ''),
        'app': Label('Appendix', '${app|upper-alpha}', ''),
        'appsub': Label('Section', '${app|upper-alpha}.${appsub}', ''),
        'appsubsub': Label('Subsection', '${app|upper-alpha}.${appsub}.${appsubsub}', ''),
        # global counters
        'fig': Label('Figure', '${sec}.${fig}', ''),
        'subfig': Label('Figure', '${sec}.${fig}${subfig|lower-alpha}', '(${subfig|lower-alpha})'),
        'tab': Label('Table', '${sec}.${tab}', ''),
        'code': Label('Listing', '${sec}.${code}', ''),
        'rem': Label('Remark', '${rem}', ''),
        'lem': Label('Lemma', '${lem}', ''),
        'def': Label('Definition', '${def}', ''),
        'prob': Label('Problem', '${prob}', ''),
        'prop': Label('Proposition', '${prop}', ''),
        'thm': Label('Theorem', '${thm}', ''),
        'exa': Label('Example', '${exa}', ''),

    }

    return Style(resets, labels)

def number_items2(root):
    counters = set(['part', 'app', 'sec', 'sub', 'subsub', 'appsub', 'appsubsub', 'par']
                   + ['fig', 'tab', 'subfig', 'code']
                   + ['exa', 'rem', 'lem', 'def', 'prop', 'prob', 'thm'])

    style = get_style_book()
    style = get_style_duckietown()
    resets = style.resets
    labels = style.labels

    for c in counters:
        assert c in resets, c
        assert c in labels, c
    from collections import defaultdict
    counter_parents = defaultdict(lambda: set())
    for c, cc in resets.items():
        for x in cc:
            counter_parents[x].add(c)

    counter_state = {}
    for counter in counters:
        counter_state[counter] = 0

    for item in root.depth_first_descendants():
        counter = item.id.split(":")[0]
#         print('counter %s id %s %s' % (counter, item.id, counter_state))
        if counter in counters:
            counter_state[counter] += 1
            for counter_to_reset in resets[counter]:
                counter_state[counter_to_reset] = 0

            label_spec = labels[counter]
            what = label_spec.what
            number = render(label_spec.number, counter_state)

            item.tag.attrs[LABEL_NAME] = item.name
            item.tag.attrs[LABEL_WHAT] = what
            item.tag.attrs[LABEL_SELF] = render(
                label_spec.label_self, counter_state)

            if item.name is None:
                item.tag.attrs[LABEL_WHAT_NUMBER_NAME] = what + ' ' + number
            else:
                item.tag.attrs[LABEL_WHAT_NUMBER_NAME] = what + \
                    ' ' + number + ' - ' + item.name
            item.tag.attrs[LABEL_WHAT_NUMBER] = what + ' ' + number
            item.tag.attrs[LABEL_NUMBER] = number

            allattrs = [LABEL_NAME, LABEL_WHAT,
                        LABEL_WHAT_NUMBER_NAME, LABEL_NUMBER, LABEL_SELF]
            for c in counters:
                if c in counter_parents[counter] or c == counter:
                    attname = 'counter-%s' % c
                    allattrs.append(attname)
                    item.tag.attrs[attname] = counter_state[c]

            if item.tag.name == 'figure':
                # also copy to the caption
                for figcaption in item.tag.findAll(['figcaption']):
                    if figcaption.parent != item.tag:
                        continue
                    for x in allattrs:
                        figcaption.attrs[x] = item.tag.attrs[x]

LABEL_NAME = 'label-name'
LABEL_NUMBER = 'label-number'
LABEL_WHAT = 'label-what'
LABEL_SELF = 'label-self'
LABEL_WHAT_NUMBER_NAME = 'label-what-number-name'
LABEL_WHAT_NUMBER = 'label-what-number'


def render(s, counter_state):
    reps = {}
    for c, v in counter_state.items():
        for style in number_styles:
            reps['${%s|%s}' % (c, style)] = render_number(v, style)
        reps['${%s}' % c] = render_number(v, 'decimal')

    for k, v in reps.items():
        s = s.replace(k, v)
    return s


def substituting_empty_links(soup, raise_errors=False):
    '''

        default style is [](#sec:systems)  "Chapter 10"

        You can also use "class":

            <a href='#sec:name' class='only_number'></a>

    '''

#     logger.debug('substituting_empty_links')

#     n = 0
    for le in get_empty_links_to_fragment(soup):
        a = le.linker
        element_id = le.eid
        element = le.linked
        sub_link(a, element_id, element, raise_errors)
        
    # Now mark as errors the ones that 
    for a in get_empty_links(soup):
        href = a.attrs.get('href', '(not present)')
        if href.startswith('http:') or href.startswith('https:'):
            msg  = """
This link text is empty. 

Note that the syntax for links in Markdown is

    [link text](URL)

For the internal links (where URL starts with "#"), then the documentation
system can fill in the title automatically, leading to the format:

    [](#other-section)

However, this does not work for external sites, such as:

    [](MYURL)
    
So, you need to provide some text, such as:

    [this useful website](MYURL)
            
"""
            msg = msg.replace('MYURL', href)
            note_error2(a, 'syntax error', msg.strip())
            
        else:
            msg = """
This link is empty. It might be that the writer intended for this 
link to point to something, but they got the syntax wrong.

    href = %s
    
As a reminder, to refer to other parts of the document, use
the syntax "#ID", such as: 

    See [](#fig:my-figure).
    
    See [](#section-name).
    
""" % href
        note_error2(a, 'syntax error', msg.strip())
#         n += 1
#     logger.debug('substituting_empty_links: %d total, %d errors' %
#                  (n, nerrors))



def sub_link(a, element_id, element, raise_errors):
    """
        a: the link with href= #element_id
        element: the link to which we refer
    """
    CLASS_ONLY_NUMBER = MCDPManualConstants.CLASS_ONLY_NUMBER
    CLASS_NUMBER_NAME = MCDPManualConstants.CLASS_NUMBER_NAME
    CLASS_ONLY_NAME = MCDPManualConstants.CLASS_ONLY_NAME

    if not element:
        msg = ('Cannot find %s' % element_id)
        note_error2(a, 'Ref. error', 'substituting_empty_links():\n'+msg)
        #nerrors += 1
        if raise_errors:
            raise ValueError(msg)
        return
    # if there is a query, remove it
#     if le.query is not None:
#         new_href = '#' + le.eid
#         a.attrs['href'] = new_href
#         logger.info('setting new href= %s' % (new_href))

    if (not LABEL_WHAT_NUMBER in element.attrs) or \
            (not LABEL_NAME in element.attrs):
        msg = ('substituting_empty_links: Could not find attributes %s or %s in %s' %
               (LABEL_NAME, LABEL_WHAT_NUMBER, element))
        if True:
            logger.warning(msg)
        else:
#                 note_error_msg(a, msg)
            note_error2(a, 'Ref. error', 'substituting_empty_links():\n'+msg)
#             nerrors += 1
            if raise_errors:
                raise ValueError(msg)
        return

    label_what_number = element.attrs[LABEL_WHAT_NUMBER]
    label_number = element.attrs[LABEL_NUMBER]
    label_what = element.attrs[LABEL_WHAT]
    label_name = element.attrs[LABEL_NAME]

    classes = list(a.attrs.get('class', [])) # bug: I was modifying

#     if le.query is not None:
#         classes.append(le.query)

    if 'toc_link' in classes:
        s = Tag(name='span')
        s.string = label_what
        add_class(s, 'toc_what')
        a.append(s)

        a.append(' ')

        s = Tag(name='span')
        s.string = label_number
        add_class(s, 'toc_number')
        a.append(s)

        s = Tag(name='span')
        s.string = ' - '
        add_class(s, 'toc_sep')
        a.append(s)

        if label_name is not None and '<' in label_name:
            contents = bs(label_name)
            # sanitize the label name
            for br in contents.findAll('br'):
                br.replaceWith(NavigableString(' '))
            for _ in contents.findAll('a'):
                _.extract()

            contents.name = 'span'
            add_class(contents, 'toc_name')
            a.append(contents)
            #logger.debug('From label_name = %r to a = %r' % (label_name, a))
        else:
            if label_name is None:
                s = Tag(name='span')
                s.string = '(unnamed)'  # XXX
            else:
                s = bs(label_name)
                assert s.name == 'fragment'
                s.name = 'span'
                #add_class(s, 'produced-here') # XXX
            add_class(s, 'toc_name')
            a.append(s)

    else:

        if CLASS_ONLY_NUMBER in classes:
            label = label_number
        elif CLASS_NUMBER_NAME in classes:
            if label_name is None:
                label = label_what_number + \
                    ' - ' + '(unnamed)'  # warning
            else:
                label = label_what_number + ' - ' + label_name
        elif CLASS_ONLY_NAME in classes:
            if label_name is None:
                label = '(unnamed)'  # warning
            else:
                label = label_name
        else:
            # default behavior
            if string_starts_with(['fig:','tab:', 'bib:', 'code:'], element_id):
                label = label_what_number
            elif label_name is None:
                label = label_what_number 
            else:
                label = label_what_number + ' - ' + label_name

        frag = bs(label)
        assert frag.name == 'fragment'
        frag.name = 'span'
        add_class(frag, 'reflabel')
        a.append(frag)

def string_starts_with(prefixes, s):
    return any([s.startswith(_) for _ in prefixes])

LinkElement = namedtuple('LinkElement', 'linker eid linked query')

def is_empty_link(a):
    empty = len(list(a.descendants)) == 0
    return empty

def get_empty_links(soup):
    """ Yields all the empty links """
    for element in soup.find_all('a'):
        if not is_empty_link(element):
            continue
        yield element
    
def get_empty_links_to_fragment(soup):
    """
        Find all empty links that have a reference to a fragment.
        yield LinkElement
    """ 
    logger.debug('building index')
    # first find all elements by id
    id2element = {}
    for x in list(soup.descendants):
        if isinstance(x, Tag) and 'id' in x.attrs:
            id2element[x.attrs['id']] = x

    logger.debug('building index done')

    for element in get_empty_links(soup):
        if not 'href' in element.attrs:
            continue

        href = element.attrs['href']
        if not href.startswith('#'):
            continue
        rest = href[1:]
        if '/' in rest:
            i = rest.index('/')
            eid = rest[:i]
            query = rest[i+1:]
        else:
            eid = rest
            query = None

        linked = id2element.get(eid, None)
        yield LinkElement(linker=element, eid=eid, linked=linked, query=query)


def get_ids_from_soup(soup):
    id2e = {}
    for e in soup.select('[id]'):
        id_ = e.attrs['id']
        id2e[id_] = e
    return id2e
