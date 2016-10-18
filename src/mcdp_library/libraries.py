# -*- coding: utf-8 -*-
import os

from contracts import contract
from contracts.utils import raise_desc, check_isinstance
from mocdp.exceptions import DPSemanticError

from .library import MCDPLibrary
from .utils import locate_files


__all__ = [
    'Librarian',
]


class Librarian():
    
    """ 
        Indexes several libraries. 
        
        A hook is created so that each one can find the others.
       
        l = Librarian()
        l.find_libraries(dirname)
        
        lib = l.load_library('short') # returns MCDPLibrary
    """

    def __init__(self):
        self.libraries = {}
    
    @contract(returns='dict(str:dict)')
    def get_libraries(self):
        """ Returns dict libname => dict(path, library:MCDPLibrary) """
        return self.libraries
    
    @contract(dirname=str, returns='None')
    def find_libraries(self, dirname):

        if dirname.endswith('.mcdplib'):
            libraries = [dirname]
        else:
            libraries = locate_files(dirname, "*.mcdplib",
                                 followlinks=False,
                                 include_directories=True,
                                 include_files=False)
            if not libraries:
                # use dirname as library path
                libraries = [dirname]
        
        for path in libraries:
            short, data = self._load_entry(path)
            if short in self.libraries:
                msg = 'I already know library.'
                raise_desc(ValueError, msg, short=short,
                           available=list(self.libraries))
            self.libraries[short] = data
            
        # get all the images
        allimages = {}
        for short, data in self.libraries.items():
            l = data['library']
            for ext in MCDPLibrary.exts_images:
                basenames = l._list_with_extension(ext)
                for b in basenames:
                    basename = b + '.' + ext
                    allimages[basename] = l.file_to_contents[basename]
        for short, data in self.libraries.items():
            l = data['library']
            for basename, d in allimages.items():
                if not basename in l.file_to_contents:
                    l.file_to_contents[basename] = d

    @contract(dirname=str, returns='tuple(str, dict)')
    def _load_entry(self, dirname):
        if dirname == '.':
            dirname = os.path.realpath(dirname)
        library_name = os.path.splitext(os.path.basename(dirname))[0]
        library_name = library_name.replace('.', '_')

        load_library_hooks = [self.load_library]
        l = MCDPLibrary(load_library_hooks=load_library_hooks)
        l.add_search_dir(dirname)

        data = dict(path=dirname, library=l)
        l.library_name = library_name
        return library_name, data
        
    @contract(libname=str, returns='isinstance(MCDPLibrary)')
    def load_library(self, libname):
        check_isinstance(libname, str)
        """ hook to pass to MCDPLibrary instances to find their sisters. """
        if not libname in self.libraries:
            s = ", ".join(sorted(self.libraries))
            msg = 'Cannot find library %r. Available: %s.' % (libname, s)
            raise_desc(DPSemanticError, msg)
        l = self.libraries[libname]['library']
        return l
     
    @contract(returns='isinstance(MCDPLibrary)')
    def get_library_by_dir(self, dirname):
        """ 
            Returns the library corresponding to the dirname, 
            if it was already loaded.
            
            Otherwise a new MCDPLibrary is created. 
        """
        rp = os.path.realpath
        # check if it is already loaded
        for _short, data in self.libraries.items():
            if rp(data['path']) == rp(dirname):
                return data['library']
        # otherwise load it
        # Note this does not add it to the list
        _short, data = self._load_entry(dirname)
        data['library'].library_name = _short
        return data['library']
