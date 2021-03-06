# -*- coding: utf-8 -*-
from collections import OrderedDict
import logging
import os
import tempfile

from compmake.utils.friendly_path_imp import friendly_path
from contracts import contract
from contracts.utils import raise_wrapped
from mcdp import logger
from mcdp.constants import MCDPConstants
from mcdp.exceptions import DPSyntaxError
from mcdp_library import MCDPLibrary
from mcdp_library.stdlib import get_test_librarian
from mcdp_utils_misc import expand_all, locate_files, get_md5, write_data_to_file
from quickapp import QuickApp
from reprep.utils import natsorted

from .check_bad_input_files import check_bad_input_file_presence
from .github_edit_links import add_edit_links
from .manual_constants import MCDPManualConstants
from .manual_join_imp import DocToJoin, manual_join
from .minimal_doc import get_minimal_document
from .read_bibtex import run_bibtex2html
from .source_info_imp import get_source_info, make_last_modified


class RenderManual(QuickApp):
    """ Renders the PyMCDP manual """

    def define_options(self, params):
        params.add_string('src', help="""
        Directories with all contents; separate multiple entries with a colon.""")

        params.add_string('output_file', help='Output file')
        params.add_string('stylesheet', help='Stylesheet', default=None)
        params.add_int('mathjax', help='Use MathJax (requires node)', default=1)
        params.add_string('symbols', help='.tex file for MathJax', default=None)
        params.add_flag('raise_errors', help='If given, fail the compilation on errors')
        params.add_flag('cache')
        params.add_flag('last_modified', help='Add last modified page')
        params.add_flag('pdf', help='Generate PDF version of code and figures.')
        params.add_string('remove', help='Remove the items with the given selector'
                          ' (so it does not mess indexing)',
                          default=None)
        params.add_flag('no_resolve_references')
        params.add_flag('mcdp_settings')

    def define_jobs_context(self, context):
        options = self.get_options()

        if options.mcdp_settings:
            MCDPManualConstants.activate_tilde_as_nbsp = False
            MCDPConstants.softy_mode = False

        logger.setLevel(logging.DEBUG)

        src = options.src
        src_dirs = [_.strip() for _ in src.split(":") if _ and _.strip()]
        self.info("Src dirs: \n" + "\n -".join(src_dirs))

        raise_errors = options.raise_errors
        out_dir = options.output
        generate_pdf = options.pdf
        output_file = options.output_file
        remove = options.remove
        stylesheet = options.stylesheet
        symbols = options.symbols
        do_last_modified = options.last_modified
        use_mathjax = True if options.mathjax else False

        logger.info('use mathjax: %s' % use_mathjax)
        logger.info('use symbols: %s' % symbols)

        if symbols is not None:
            symbols = open(symbols).read()

        if out_dir is None:
            out_dir = os.path.join('out', 'mcdp_render_manual')

        for s in src_dirs:
            check_bad_input_file_presence(s)

        resolve_references = not options.no_resolve_references

        manual_jobs(context,
                    src_dirs=src_dirs,
                    output_file=output_file,
                    generate_pdf=generate_pdf,
                    stylesheet=stylesheet,
                    remove=remove,
                    use_mathjax=use_mathjax,
                    raise_errors=raise_errors,
                    symbols=symbols,
                    resolve_references=resolve_references,
                    do_last_modified=do_last_modified
                    )


@contract(src_dirs='seq(str)', returns='list(str)')
def get_bib_files(src_dirs):
    """ Looks for .bib files in the source dirs; returns list of filenames """
    return look_for_files(src_dirs, "*.bib")


@contract(src_dirs='seq(str)', returns='list(str)')
def get_markdown_files(src_dirs):
    """ Returns a list of filenames. """
    return look_for_files(src_dirs, "*.md")


def look_for_files(srcdirs, pattern):
    """
        Excludes files with "excludes" in the name.
    """
    results = []
    results_absolute = set()
    for d0 in srcdirs:
        d = expand_all(d0)
        if not os.path.exists(d):
            msg = 'Expected directory %s' % d
            raise Exception(msg)

        filenames = locate_files(d, pattern,
                                 followlinks=True,
                                 include_directories=False,
                                 include_files=True,
                                 normalize=False)

        ok = []
        for fn in filenames:
            fn0 = os.path.realpath(fn)
            if 'exclude' in fn0:
                logger.info('Excluding file %r because of string "exclude" in it' % fn)
            else:
                if fn0 in results_absolute:
                    logger.debug('Reached the file %s twice' % fn0)
                    pass
                else:
                    results_absolute.add(fn0)
                    ok.append(fn)

        results.extend(natsorted(ok))

    logger.info('Found %d files with pattern %s in %s' %
                (len(results), pattern, srcdirs))
    return results


@contract(src_dirs='seq(str)')
def manual_jobs(context, src_dirs, output_file, generate_pdf, stylesheet,
                use_mathjax, raise_errors, resolve_references=True,
                remove=None, filter_soup=None, extra_css=None, symbols=None,
                do_last_modified=False):
    """
        src_dirs: list of sources
        symbols: a TeX preamble (or None)
    """
    filenames = get_markdown_files(src_dirs)
    print('using:')
    print("\n".join(filenames))

    if not filenames:
        msg = 'Could not find any file for composing the book.'
        raise Exception(msg)

    files_contents = []
    for i, filename in enumerate(filenames):
        if is_ignored_by_catkin(filename):
            logger.debug('Ignoring because of CATKIN_IGNORE: %s' % filename)
            continue
        logger.info('adding document %s ' % friendly_path(filename))

        docname, _ = os.path.splitext(os.path.basename(filename))

        contents = open(filename).read()
        contents_hash = get_md5(contents)[:8]
        # because of hash job will be automatically erased if the source changes
        out_part_basename = '%03d-%s-%s' % (i, docname, contents_hash)
        job_id = '%s-%s-%s' % (docname, get_md5(filename)[:8], contents_hash)

        source_info = get_source_info(filename)

        # find the dir
        for d in src_dirs:
            if os.path.realpath(d) in filename:
                break
        else:
            msg = 'Could not find dir for %s in %s' % (filename, src_dirs)

        html_contents = context.comp(render_book, generate_pdf=generate_pdf,
                                     src_dirs=src_dirs,
                                   data=contents, realpath=filename,
                                   use_mathjax=use_mathjax,
                                   symbols=symbols,
                                    raise_errors=raise_errors,
                                   main_file=output_file,
                                   out_part_basename=out_part_basename,
                                   filter_soup=filter_soup,
                                   extra_css=extra_css,
                                   job_id=job_id)

        doc = DocToJoin(docname=out_part_basename, contents=html_contents,
                        source_info=source_info)
        files_contents.append(tuple(doc))  # compmake doesn't do namedtuples

    bib_files = get_bib_files(src_dirs)

    logger.debug('Found bib files:\n%s' % "\n".join(bib_files))
    if bib_files:
        bib_contents = job_bib_contents(context, bib_files)
        entry = DocToJoin(docname='bibtex', contents=bib_contents,
                           source_info=None)
        files_contents.append(tuple(entry))

    if do_last_modified:
        data = context.comp(make_last_modified, files_contents=files_contents)
        entry = DocToJoin(docname='last_modified', contents=data,
                           source_info=None)
        files_contents.append(tuple(entry))

    root_dir = src_dirs[0]

    template = get_main_template(root_dir)

    references = OrderedDict()
#     base_url = 'http://book.duckietown.org/master/duckiebook/pdoc'
#     for extra_dir in extra_dirs:
#         res = read_references(extra_dir, base_url, prefix='python:')
#         references.update(res)

#     extra = look_for_files(extra_dirs, "*.html")
#
#     for filename in extra:
#         contents = open(filename).read()
#         docname = os.path.basename(filename) + '_' + get_md5(filename)[:5]
#         c = (('unused', docname), contents)
#         files_contents.append(c)

    d = context.comp(manual_join, template=template, files_contents=files_contents,
                     stylesheet=stylesheet, remove=remove, references=references,
                     resolve_references=resolve_references)

    context.comp(write, d, output_file)

    if os.path.exists(MCDPManualConstants.pdf_metadata_template):
        context.comp(generate_metadata, root_dir)


def is_ignored_by_catkin(dn):
    """ Returns true if the directory is inside one with CATKIN_IGNORE """
    while dn != '/':
        i = os.path.join(dn, "CATKIN_IGNORE")
        if os.path.exists(i):
            return True
        dn = os.path.dirname(dn)
        if not dn:
            return False
    return False


def job_bib_contents(context, bib_files):
    bib_files = natsorted(bib_files)
    # read all contents
    contents = ""
    for fn in bib_files:
        contents += open(fn).read() + '\n\n'
    h = get_md5(contents)[:8]
    job_id = 'bibliography-' + h
    return context.comp(run_bibtex2html, contents, job_id=job_id)


def get_main_template(root_dir):
    fn = os.path.join(root_dir, MCDPManualConstants.main_template)
    if not os.path.exists(fn):
        msg = 'Could not find template %s' % fn
        raise ValueError(msg)

    template = open(fn).read()
    return template


def generate_metadata(src_dir):
    template = MCDPManualConstants.pdf_metadata_template
    if not os.path.exists(template):
        msg = 'Metadata template does not exist: %s' % template
        raise ValueError(msg)

    out = MCDPManualConstants.pdf_metadata
    s = open(template).read()

    from .pipeline import replace_macros

    s = replace_macros(s)
    write_data_to_file(s, out)


def write(s, out):
    write_data_to_file(s, out)


def render_book(src_dirs, generate_pdf,
                data, realpath,
                main_file, use_mathjax, out_part_basename,
                raise_errors,
                 filter_soup=None,
                extra_css=None, symbols=None):
    from mcdp_docs.pipeline import render_complete

    librarian = get_test_librarian()
    # XXX: these might need to be changed
    if not MCDPConstants.softy_mode:
        librarian.find_libraries('.')

    load_library_hooks = [librarian.load_library]
    library = MCDPLibrary(load_library_hooks=load_library_hooks)

    for src_dir in src_dirs:
        library.add_search_dir(src_dir)

    d = tempfile.mkdtemp()
    library.use_cache_dir(d)

    def filter_soup0(soup, library):
        if filter_soup is not None:
            filter_soup(soup=soup, library=library)
        add_edit_links(soup, realpath)

    try:
        html_contents = render_complete(library=library,
                                    s=data,
                                    raise_errors=raise_errors,
                                    realpath=realpath,
                                    use_mathjax=use_mathjax,
                                    symbols=symbols,
                                    generate_pdf=generate_pdf,
                                    filter_soup=filter_soup0)
    except DPSyntaxError as e:
        msg = 'Could not compile %s' % realpath
        raise_wrapped(DPSyntaxError, e, msg, compact=True)

    doc = get_minimal_document(html_contents,
                               add_markdown_css=True, extra_css=extra_css)
    dirname = main_file + '.parts'
    if dirname and not os.path.exists(dirname):
        try:
            os.makedirs(dirname)
        except:
            pass
    fn = os.path.join(dirname, '%s.html' % out_part_basename)
    write_data_to_file(doc, fn)

    return html_contents


mcdp_render_manual_main = RenderManual.get_sys_main()
