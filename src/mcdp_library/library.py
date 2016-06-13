from .utils.locate_files_imp import locate_files
from contextlib import contextmanager
from contracts import contract
from contracts.utils import raise_desc
from copy import deepcopy
from mcdp_lang import parse_ndp, parse_poset
from mcdp_library.utils.memos_selection import memo_disk_cache2
from mcdp_posets.poset import Poset
from mocdp import logger
from mocdp.comp.context import Context
from mocdp.comp.interfaces import NamedDP
from mocdp.exceptions import DPSemanticError, MCDPExceptionWithWhere
import os
import shutil
import sys



__all__ = [
    'MCDPLibrary',
]


class MCDPLibrary():
    """
    
        to document:
        
            '_cached' directory
            
            not case sensitive
            
        delete_cache(): deletes the _cached directory
        
    """

    # These are all the extensions that we care about
    ext_ndps = 'mcdp'
    ext_posets = 'mcdp_poset'
    ext_values = 'mcdp_value'
    ext_templates = 'mcdp_template'  # not implemented yet
    ext_primitivedps = 'mcdp_primitivedp'
    all_extensions = [ext_ndps, ext_posets, ext_values, ext_templates, ext_primitivedps]

    def __init__(self, cache_dir=None, file_to_contents=None, search_dirs=None):
        """ 
            IMPORTANT: modify clone() if you add state
        """
        # basename "x.mcdp" -> dict(data, realpath)
        if file_to_contents is None:
            file_to_contents = {}
        self.file_to_contents = file_to_contents
        
        self.cache_dir = cache_dir

        if search_dirs is None:
            search_dirs = []

        self.search_dirs = search_dirs

    def clone(self):
        fields = ['file_to_contents', 'cache_dir', 'search_dirs']
        contents = {}
        for f in fields:
            if not hasattr(self, f):
                raise ValueError(f)
            contents[f] = deepcopy(getattr(self, f))
        return MCDPLibrary(**contents)

    def use_cache_dir(self, cache_dir):
        self.cache_dir = cache_dir

    def delete_cache(self):
        if self.cache_dir:
            if os.path.exists(self.cache_dir):
                shutil.rmtree(self.cache_dir)

    @contract(returns=NamedDP)
    def load_ndp(self, id_ndp):
        return self._load_generic(id_ndp, MCDPLibrary.ext_ndps,
                                  MCDPLibrary.parse_ndp)

    @contract(returns=Poset)
    def load_poset(self, id_poset):
        return self._load_generic(id_poset, MCDPLibrary.ext_posets,
                                  MCDPLibrary.parse_poset)

    @contract(returns=Poset)
    def load_primitivedp(self, id_primitivedp):
        return self._load_generic(id_primitivedp, MCDPLibrary.ext_primitivedps,
                                  MCDPLibrary.parse_primitivedp)

    def _load_generic(self, name, extension, parsing):
        filename = '%s.%s' % (name, extension)
        f = self._get_file_data(filename)
        data = f['data']
        realpath = f['realpath']

        def actual_load():
            # maybe we should clone
            l = self.clone()
            logger.debug('Parsing %r' % name)
            res = parsing(l, data, realpath)
            setattr(res, '__mcdplibrary_load_name', name)
            return res

        if not self.cache_dir:
            return actual_load()
        else:
            cache_file = os.path.join(self.cache_dir, parsing.__name__,
                                      '%s.cached' % name)
            return memo_disk_cache2(cache_file, data, actual_load)

    load_ndp2 = load_ndp

    def parse_ndp(self, string, realpath=None):
        """ This is the wrapper around parse_ndp that adds the hooks. """
        return self._parse_with_hooks(parse_ndp, string, realpath)

    def parse_poset(self, string, realpath=None):
        return self._parse_with_hooks(parse_poset, string, realpath)

    def parse_primitivedp(self, string, realpath=None):
        from mcdp_lang.parse_interface import parse_primitivedp
        return self._parse_with_hooks(parse_primitivedp, string, realpath)

    def parse_constant(self, string):
        from mcdp_lang.parse_interface import parse_constant
        return self._parse_with_hooks(parse_constant, string, None)


    @contextmanager
    def _sys_path_adjust(self):
        previous = list(sys.path)

        # print('search dirs: %s' % self.search_dirs)
        for d in self.search_dirs:
            sys.path.insert(0, d)

        try:
            yield
        finally:
            sys.path = previous

    def _parse_with_hooks(self, parse_ndp_like, string, realpath):
        with self._sys_path_adjust():
            context = self._generate_context_with_hooks()

            try:
                result = parse_ndp_like(string, context=context)
            except MCDPExceptionWithWhere as e:
                type, value, traceback = sys.exc_info()
                if realpath is not None:
                    e = e.with_filename(realpath)
                else:
                    e = e

                raise e, None, traceback

            return result

    def _generate_context_with_hooks(self):
        context = Context()
        context.load_ndp_hooks = [self.load_ndp]
        context.load_posets_hooks = [self.load_poset]
        context.load_primitivedp_hooks = [self.load_primitivedp]
        return context

    @contract(returns='set(str)')
    def list_ndps(self):
        """ Returns all models defined in this library with .mcdp files. """
        return self._list_with_extension(MCDPLibrary.ext_ndps)

    get_models = list_ndps

    @contract(returns='set(str)')
    def list_posets(self):
        """ Returns all models defined in this library with .mcdp files. """
        return self._list_with_extension(MCDPLibrary.ext_posets)

    @contract(returns='set(str)')
    def list_primitivedps(self):
        """ Returns all models defined in this library with .mcdp files. """
        return self._list_with_extension(MCDPLibrary.ext_primitivedps)

    def _list_with_extension(self, ext):
        r = []
        for x in self.file_to_contents:
            p = '.' + ext
            if x.endswith(p):
                r.append(x.replace(p, ''))
        res = set(r)
        return res

    def file_exists(self, basename):
        for fn in self.file_to_contents:
            if fn.lower() == basename.lower():
                return True
        return False

    def _get_file_data(self, basename):
        """ returns dict with data, realpath """

        for fn in self.file_to_contents:
            if fn.lower() == basename.lower():
                match = fn
                break
        else:
            raise_desc(DPSemanticError, 'Could not find model in library.',
                       model_name=basename, contents=sorted(self.file_to_contents))
        found = self.file_to_contents[match]
        return found

    def add_search_dir(self, d):
        self.search_dirs.append(d)

        if not os.path.exists(d):
            raise_desc(ValueError, 'Directory does not exist', d=d)

        self._add_search_dir(d)

    def _add_search_dir(self, d):
        """ Adds the directory to the search directory list. """
        for ext in MCDPLibrary.all_extensions:
            pattern = '*.%s' % ext
            files_mcdp = locate_files(directory=d, pattern=pattern, followlinks=True)
            for f in files_mcdp:
                self._update_file(f)

    def _update_file(self, f):
        basename = os.path.basename(f)
        data = open(f).read()
        realpath = os.path.realpath(f)
        res = dict(data=data, realpath=realpath)
        self.file_to_contents[basename] = res

    def write_to_model(self, model_name, data):
        basename = model_name + '.mcdp'
        d = self._get_file_data(basename)
        realpath = d['realpath']
        print('writing to %r' % realpath)
        with open(realpath, 'w') as f:
            f.write(data)
        # reload
        self._update_file(realpath)

    # Support for parsing types



