#!/usr/bin/env python
# -*- coding: utf-8 -*-
from contracts import contract
from mcdp.logs import logger
from mcdp_utils_xml import add_class
import os
import sys

from bs4 import BeautifulSoup
from bs4.element import Comment, Tag, NavigableString

from .macros import replace_macros
from .read_bibtex import get_bibliography
from .tocs import generate_toc
from mcdp_docs.minimal_doc import add_extra_css
from mcdp_docs.tocs import substituting_empty_links
import random
from collections import OrderedDict
import warnings


def get_manual_css_frag():
    """ Returns fragment of doc with CSS, either inline or linked,
        depending on MCDPConstants.manual_link_css_instead_of_including. """
    from mcdp import MCDPConstants

    link_css = MCDPConstants.manual_link_css_instead_of_including

    frag = Tag(name='fragment-css')
    if link_css:
        link = Tag(name='link')
        link['rel'] = 'stylesheet'
        link['type'] = 'text/css'
        link['href'] = 'VERSIONCSS'
        frag.append(link)

        return frag
    else:
        assert False


@contract(files_contents='list( tuple( tuple(str,str), str) )', returns='str')
def manual_join(template, files_contents, bibfile, stylesheet, remove=None, extra_css=None,
                hook_before_toc=None):
    """
        extra_css: if not None, a string of more CSS to be added
        Remove: selector for elements to remove (e.g. ".draft").

        hook_before_toc if not None is called with hook_before_toc(soup=soup)
        just before generating the toc
    """
    from mcdp_utils_xml import bs

    template = replace_macros(template)

    # cannot use bs because entire document
    template_soup = BeautifulSoup(template, 'lxml', from_encoding='utf-8')
    d = template_soup
    assert d.html is not None
    assert '<html' in str(d)
    head = d.find('head')
    assert head is not None
    for x in get_manual_css_frag().contents:
        head.append(x.__copy__())

    if stylesheet is not None:
        link = Tag(name='link')
        link['rel'] = 'stylesheet'
        link['type'] = 'text/css'
        from mcdp_report.html import get_css_filename
        link['href'] = get_css_filename('compiled/%s' % stylesheet)
        head.append(link)

    basename2soup = OrderedDict()
    for (_libname, docname), data in files_contents:
        frag = bs(data)
        basename2soup[docname] = frag

    fix_duplicated_ids(basename2soup)

    body = d.find('body')
    for docname, content in basename2soup.items():
        logger.debug('docname %r -> %s KB' % (docname, len(data) / 1024))
        from mcdp_docs.latex.latex_preprocess import assert_not_inside
        assert_not_inside(data, 'DOCTYPE')
        body.append(NavigableString('\n\n'))
        body.append(Comment('Beginning of document dump of %r' % docname))
        body.append(NavigableString('\n\n'))
        for x in content:
            x2 = x.__copy__()  # not clone, not extract
            body.append(x2)
        body.append(NavigableString('\n\n'))
        body.append(Comment('End of document dump of %r' % docname))
        body.append(NavigableString('\n\n'))

    logger.info('external bib')
    if bibfile is not None:
        if not os.path.exists(bibfile):
            logger.error('Cannot find bib file %s' % bibfile)
        else:
            bibliography_entries = get_bibliography(bibfile)
            bibliography_entries['id'] = 'bibliography_entries'
            body.append(bibliography_entries)
            bibhere = d.find('div', id='put-bibliography-here')
            do_bib(d, bibhere)

    if True:
        logger.info('reorganizing contents in <sections>')
        body2 = reorganize_contents(d.find('body'))
        body.replace_with(body2)
    else:
        warnings.warn('fix')
        body2 = body

    # Removing
    all_removed = ''
    if remove is not None and remove != '':
        nremoved = 0
#         logger.debug('Removing selector %r' % remove)
        toremove = list(body2.select(remove))
#         logger.debug('Removing %d objects' % len(toremove))
        for x in toremove:
            nremoved += 1
            nd = len(list(x.descendants))
            logger.debug('removing %s with %s descendants' % (x.name, nd))
            if nd > 1000:
                s =  str(x)[:300]
                logger.debug(' it is %s' %s)
            x.extract()
            
            all_removed += '\n\n' + '-' * 50 + ' chunk %d removed\n' % nremoved 
            all_removed += str(x) 
            all_removed += '\n\n' + '-' * 100 + '\n\n'
            
        logger.info('Removed %d elements of selector %r' % (nremoved, remove))
    with open('all_removed.html', 'w') as f:
        f.write(all_removed)
        
    if hook_before_toc is not None:
        hook_before_toc(soup=d)
    ###
    logger.info('adding toc')
    toc = generate_toc(body2)
    toc_ul = bs(toc).ul
    toc_ul.extract()
    assert toc_ul.name == 'ul'
    toc_ul['class'] = 'toc'
    toc_ul['id'] = 'main_toc'
    toc_selector = 'div#toc'
    tocs = list(d.select(toc_selector))
    if not tocs:
        msg = 'Cannot find any element of type %r to put TOC inside.' % toc_selector
        logger.warning(msg)
    else:
        toc_place = tocs[0]
        toc_place.replaceWith(toc_ul)

    logger.info('substituting empty links')
    substituting_empty_links(d)

    logger.info('checking errors')
    check_various_errors(d)

    from mcdp_docs.check_missing_links import check_if_any_href_is_invalid
    logger.info('checking hrefs')
    check_if_any_href_is_invalid(d)

    warn_for_duplicated_ids(d)

    if extra_css is not None:
        logger.info('adding extra CSS')
        add_extra_css(d, extra_css)

    logger.info('converting to string')
    # do not use to_html_stripping_fragment - this is a complete doc
    res = str(d)
    logger.info('done - %d bytes' % len(res))
    return res


def do_bib(soup, bibhere):
    """ find used bibliography entries put them there """
    used = set()
    unused = set()
    for a in soup.find_all('a'):
        href = a.attrs.get('href', '')
        if href.startswith('#bib:'):
            used.add(href[1:])  # no "#"
    print('I found %d references, to these: %s' % (len(used), used))

    if bibhere is None:
        logger.error('Could not find #put-bibliography-here in document.')
    else:
        cites = list(soup.find_all('cite'))
        # TODO: sort
        for c in cites:
            ID = c.attrs.get('id', None)
            if ID in used:
                # remove it from parent
                c.extract()
                # add to bibliography
                bibhere.append(c)
                add_class(c, 'used')
            else:
                unused.add(ID)
                add_class(c, 'unused')
    print('I found %d unused bibs.' % (len(unused)))


def warn_for_duplicated_ids(soup):
    from collections import defaultdict

    counts = defaultdict(lambda: [])
    for e in soup.select('[id]'):
        ID = e['id']
        counts[ID].append(e)

    problematic = []
    for ID, elements in counts.items():
        n = len(elements)
        if n == 1:
            continue

        ignore_if_contains = ['MathJax',  # 'MJ',
                              'edge', 'mjx-eqn', ]
        if any(_ in ID for _ in ignore_if_contains):
            continue

        inside_svg = False
        for e in elements:
            for _ in e.parents:
                if _.name == 'svg':
                    inside_svg = True
                    break
        if inside_svg:
            continue

        #msg = ('ID %15s: found %s - numbering will be screwed up' % (ID, n))
        # logger.error(msg)
        problematic.append(ID)

        for e in elements:
            t = Tag(name='span')
            t['class'] = 'duplicated-id'
            t.string = 'Error: warn_for_duplicated_ids:  There are %d tags with ID %s' % (
                n, ID)
            # e.insert_before(t)
            add_class(e, 'errored')

        for i, e in enumerate(elements[1:]):
            e['id'] = e['id'] + '-duplicate-%d' % (i + 1)
            #print('changing ID to %r' % e['id'])
    if problematic:
        logger.error('The following IDs were duplicated: %s' %
                     ", ".join(problematic))
        logger.error(
            'I renamed some of them; references and numbering are screwed up')


def fix_duplicated_ids(basename2soup):
    '''
        fragments is a list of soups that might have
        duplicated ids.
    '''
    id2frag = {}
    tochange = []  # (i, from, to)
    for basename, fragment in basename2soup.items():
        # get all the ids for fragment
        for element in fragment.find_all(id=True):
            id_ = element.attrs['id']
            # ignore the mathjax stuff
            if 'MathJax' in id_:  # or id_.startswith('MJ'):
                continue
            # is this a new ID
            if not id_ in id2frag:
                id2frag[id_] = basename
            else:  # already know it
                if id2frag[id_] == basename:
                    # frome the same frag
                    logger.debug(
                        'duplicated id %r inside frag %s' % (id_, basename))
                else:
                    # from another frag
                    # we need to rename all references in this fragment
                    # '%s' % random.randint(0,1000000)
                    new_id = id_ + '-' + basename
                    element['id'] = new_id
                    tochange.append((basename, id_, new_id))
    logger.info(tochange)
    for i, id_, new_id in tochange:
        fragment = basename2soup[i]
        for a in fragment.find_all(href="#" + id_):
            a.attrs['href'] = '#' + new_id


def reorganize_contents(body0):
    """ reorganizes contents 

        h1
        h2
        h1

        section
            h1
            h2
        section 
            h1

    """

    def make_sections(body, is_marker, preserve=lambda _: False, element_name='section', copy=True):
        sections = []
        current_section = Tag(name=element_name)
        current_section['id'] = 'before-any-match-of-%s' % is_marker.__name__
        sections.append(current_section)
        for x in body.contents:
            if is_marker(x):
                #print('starting %s' % str(x))
                if len(list(current_section.contents)) > 0:
                    sections.append(current_section)
                current_section = Tag(name=element_name)
                current_section['id'] = x.attrs.get(
                    'id', 'unnamed-h1') + ':' + element_name
                print('marker %s' % current_section['id'])
                current_section['class'] = x.attrs.get('class', '')
                #print('%s/section %s %s' % (is_marker.__name__, x.attrs.get('id','unnamed'), current_section['id']))
                current_section.append(x.__copy__())
            elif preserve(x):
                sections.append(current_section)
                #current_section['id'] = x.attrs.get('id', 'unnamed-h1') + ':' + element_name
                #print('%s/preserve %s' % (preserve.__name__, current_section['id']))
                sections.append(x.__copy__())
                current_section = Tag(name=element_name)
            else:
                #x2 = x.__copy__() if copy else x
                x2 = x.__copy__() if copy else x.extract()
                current_section.append(x2)
        sections.append(current_section)     # XXX
        new_body = Tag(name=body.name)
#         if len(sections) < 3:
#             msg = 'Only %d sections found (%s).' % (len(sections), is_marker.__name__)
#             raise ValueError(msg)

        logger.info('make_sections: %s found using marker %s' %
                    (len(sections), is_marker.__name__))
        for i, s in enumerate(sections):
            new_body.append('\n')
            new_body.append(
                Comment('Start of %s section %d/%d' % (is_marker.__name__, i, len(sections))))
            new_body.append('\n')
            new_body.append(s)
            new_body.append('\n')
            new_body.append(
                Comment('End of %s section %d/%d' % (is_marker.__name__, i, len(sections))))
            new_body.append('\n')
        return new_body

    def is_section_marker(x):
        return isinstance(x, Tag) and x.name == 'h2'

    def is_chapter_marker(x):
        return isinstance(x, Tag) and x.name == 'h1' and (not 'part' in x.attrs.get('id', ''))

    def is_part_marker(x):
        return isinstance(x, Tag) and x.name == 'h1' and 'part' in x.attrs.get('id', '')

    def is_chapter_or_part_marker(x):
        return is_chapter_marker(x) or is_part_marker(x)

    #body = make_sections(body0, is_section_marker, is_chapter_or_part_marker)
    body = make_sections(body0, is_chapter_marker, is_part_marker)
    body = make_sections(body, is_part_marker)

    def is_h2(x):
        return isinstance(x, Tag) and x.name == 'h2'

    body = make_sections(body, is_h2)

    return body


def check_various_errors(d):
    error_names = ['DPSemanticError', 'DPSyntaxError']
    selector = ", ".join('.' + _ for _ in error_names)
    errors = list(d.find_all(selector))
    if errors:
        msg = 'I found %d errors in processing.' % len(errors)
        logger.error(msg)
        for e in errors:
            logger.error(e.contents)

    fragments = list(d.find_all('fragment'))
    if fragments:
        msg = 'There are %d spurious elements "fragment".' % len(fragments)
        logger.error(msg)


def debug(s):
    sys.stderr.write(str(s) + ' \n')


#
#     for tag in main_body.select("a"):
#         href = tag['href']
#         # debug(href)
#         # http://127.0.0.1:8080/libraries/tour1/types.html
#         if href.endswith('html'):
#             page = href.split('/')[-1]
#             new_ref = '#%s' % page
#             tag['href'] = new_ref
