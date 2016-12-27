# -*- coding: utf-8 -*-
import logging
import os
import tempfile

from mcdp_library import MCDPLibrary
from mcdp_library_tests.tests import get_test_librarian
from mcdp_web.renderdoc.highlight import get_minimal_document
from mcdp_web.renderdoc.main import render_complete, replace_macros
from mocdp import logger
from quickapp import QuickApp

from .manual_join_imp import manual_join
from mcdp_library.utils.locate_files_imp import locate_files
from reprep.utils.natsorting import natsorted
from mcdp_docs.manual_constants import MCDPManualConstants
from compmake.context import Context
from compmake.structures import Promise
from contracts import contract
from contracts.utils import check_isinstance
from compmake.jobs.storage import get_job_cache
from compmake.jobs.actions import mark_to_remake
import time

def get_manual_contents():
    root = os.getcwd()
    directory = root
    pattern = '*.md'
    filenames = locate_files(directory, pattern, followlinks=True,
                 include_directories=False,
                 include_files=True,
                 normalize=False)
    ok = []
    for fn in filenames:
        fn = os.path.relpath(fn, root)
        # only root files
        is_root = os.path.dirname(fn) == ''
        if not is_root: 
            continue
        b, _extension = os.path.splitext(os.path.basename(fn))
        ok.append(b)
        
    filenames = natsorted(ok)
    for f in filenames:
        yield 'manual', f
                 
class RenderManual(QuickApp):
    """ Renders the PyMCDP manual """

    def define_options(self, params):
        params.add_string('output_file', help='Output file')
        params.add_flag('cache')
        params.add_flag('pdf', help='Generate PDF version of code and figures.')

    def define_jobs_context(self, context):
        logger.setLevel(logging.DEBUG)

        options = self.get_options()
        out_dir = None

        if out_dir is None:
            out_dir = os.path.join('out', 'mcdp_render_manual')

        generate_pdf = options.pdf
        files_contents = []
        
        manual_contents = list(get_manual_contents())
        
        insert_after = ('manual', '10_scenarios')
        
        extra = [
            ('rover_energetics', 'energy_choices'),
            ('rover_energetics', 'energy_choices2'),
            ('rover_energetics', 'energy_choices3'),
        
            ('plugs', 'sockets'),
            ('plugs', 'sockets2'),
            ('droneD_complete_v2', 'drone_complete'),
            ('actuation', 'actuation_tour'),
        # 3d printing
        # processors: composition
        ]
        
        at = manual_contents.index(insert_after) + 1
        manual_contents = manual_contents[:at] + extra + manual_contents[at:] 
        
        # check that all the docnames are unique
        pnames = [_[1] for _ in manual_contents]
        if len(pnames) != len(set(pnames)):
            msg = 'Repeated names detected: %s' % pnames
            raise ValueError(msg)
        
        print('manual contents: %s' % manual_contents)
        for libname, docname in manual_contents:
            print('%s - %s' % (libname, docname))
            res = context.comp(render, libname, docname, generate_pdf,
                               job_id=docname)
#                                job_id='render-%s-%s' % (libname, docname))
            if libname == 'manual':
                source = '%s.md' % docname
                erase_job_if_files_updated(context.cc, promise=res, filenames=[source])
            
            files_contents.append(res)

        d = context.comp(manual_join, files_contents)
        context.comp(write, d, options.output_file)
        
        context.comp(generate_metadata)

@contract(compmake_context=Context, promise=Promise, filename='seq(str)')
def erase_job_if_files_updated(compmake_context, promise, filenames):
    """ Invalidates the job if the filename is newer """
    check_isinstance(promise, Promise)
    check_isinstance(filenames, (list, tuple))
    
    def friendly_age(ts):
        age = time.time() - ts
        return '%.3fs ago' % age
    #    if age > 0.5:
    #        ages = '%.3fs ago' % age
    
    filenames = list(filenames)
    for _ in filenames:
        if not os.path.exists(_):
            raise ValueError(_)
    last_update = max(os.path.getmtime(_) for _ in filenames)
    db = compmake_context.get_compmake_db()
    job_id = promise.job_id
    cache = get_job_cache(job_id, db)
    if cache.state == cache.DONE:
        done_at = cache.timestamp
        if done_at < last_update:
            logger.info('Cleaning job %r because files updated %r' % (job_id, filenames))
            logger.info('  files last updated: %s' % friendly_age(last_update))
            logger.info('       job last done: %s' % friendly_age(done_at))
                    
#             mark_to_remake(job_id, db)
    
def generate_metadata():
    template = MCDPManualConstants.pdf_metadata_template
    if not os.path.exists(template):
        msg = 'Metadata template does not exist: %s' % template
        raise ValueError(msg)

    out = MCDPManualConstants.pdf_metadata
    s = open(template).read()
    s = replace_macros(s)
    with open(out, 'w') as f:
        f.write(s)
    print(s)
    

def write(s, out):
    dn = os.path.dirname(out)
    if not os.path.exists(dn):
        os.makedirs(dn)
    with open(out, 'w') as f:
        f.write(s)
    print('Written %s ' % out)


def render(libname, docname, generate_pdf):
    librarian = get_test_librarian()
    library = librarian.load_library('manual')

    d = tempfile.mkdtemp()
    library.use_cache_dir(d)

    l = library.load_library(libname)
    basename = docname + '.' + MCDPLibrary.ext_doc_md
    f = l._get_file_data(basename)
    data = f['data']
    realpath = f['realpath']

    html_contents = render_complete(library=l,
                                    s=data, raise_errors=True, realpath=realpath,
                                    generate_pdf=generate_pdf)

    doc = get_minimal_document(html_contents, add_markdown_css=True)
    dirname = 'out-html'
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    fn = os.path.join(dirname, 'part-%s.html' % docname)
    with open(fn, 'w') as f:
        f.write(doc)
        
    return ((libname, docname), html_contents)

    

mcdp_render_manual_main = RenderManual.get_sys_main()

