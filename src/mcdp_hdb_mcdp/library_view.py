from contextlib import contextmanager
from contracts import contract
from mcdp import MCDPConstants
from mcdp.exceptions import DPSemanticError
from mcdp.logs import logger
from mcdp_library import MCDPLibrary
from mcdp_library.specs_def import specs
from mcdp_utils_misc import format_list
from mcdp_utils_misc.memoize_simple_imp import memoize_simple
from mocdp.comp.context import Context

from contracts.utils import  raise_desc


class LibraryView():
    pass 


class TheContext(Context):
    
    def __init__(self, host_cache, db_view, subscribed_shelves, current_library_name):
        self.host_cache = host_cache
        self.db_view = db_view
        self.subscribed_shelves = subscribed_shelves
        self.current_library_name = current_library_name
        Context.__init__(self)
        self.load_ndp_hooks = [self.load_ndp]
        self.load_posets_hooks = [self.load_poset]
        self.load_primitivedp_hooks = [self.load_primitivedp]
        self.load_template_hooks = [self.load_template]
        self.load_library_hooks = [self.load_library]
    
    @memoize_simple
    def load_library(self, library_name, context=None):  # @UnusedVariable
#         logger.debug('load_library(%r)'  % library_name)
        repos = self.db_view.repos
        all_shelves = set()
        all_libraries = set()
        for repo_name, repo in repos.items():
            all_shelves.update(repo.shelves)
            for shelf_name, shelf in repo.shelves.items():
                all_libraries.update(shelf.libraries)
            for shelf_name in self.subscribed_shelves:
                if shelf_name in repo.shelves:
                    shelf = repo.shelves[shelf_name]
                    if library_name in shelf.libraries:
                        return self.make_library(repo_name, shelf_name, library_name)
        msg = 'Could not find library %r.' % library_name
        msg += '\n Subscribed shelves: %s.' % format_list(sorted(self.subscribed_shelves))
        msg += '\n All shelves: %s.' % format_list(sorted(all_shelves))
        msg += '\n All libraries: %s.' % format_list(sorted(all_libraries))
        raise ValueError(msg)
    
    @memoize_simple
    @contract(returns=MCDPLibrary)
    def make_library(self, repo_name, shelf_name, library_name): 
        #logger.debug('make_library(%r, %r, %r)'  % (repo_name, shelf_name, library_name))
        l = TheContextLibrary(self, repo_name, shelf_name, library_name)
        return l
    
    def get_library(self):
        return self.load_library(self.current_library_name)
    
    def load_ndp(self, name, context=None):
        #logger.debug('load_ndp(%r)' % name)
        return self.get_library().load_ndp(name, context)
    
    def load_poset(self, name, context=None):
        #logger.debug('load_poset(%r)' % name)
        res = self.get_library().load_poset(name, context)
        return res
    
    def load_primitivedp(self, name, context=None):
        return self.get_library().load_primitivedp(name, context)
    
    def load_template(self, name, context=None):
        return self.get_library().load_template(name, context)
    
        
class TheContextLibrary(MCDPLibrary):
    
    @contract(the_context=TheContext)
    def __init__(self, the_context, repo_name, shelf_name, library_name):
        self.the_context = the_context
        self.repo_name = repo_name
        self.shelf_name = shelf_name
        self.library_name = library_name
        MCDPLibrary.__init__(self)
#         logger.warn('Cache activated but not sure the semantics is correct if things change.')
#         self.use_tmp_cache()
        
    def _generate_context_with_hooks(self):
        c = TheContext(db_view=self.the_context.db_view,
                       host_cache=self.the_context.host_cache,
                       subscribed_shelves=self.the_context.subscribed_shelves,
                       current_library_name=self.library_name)
        return c 
      
    def _load_spec_data(self, spec_name, thing_name):
        shelf = self.the_context.db_view.repos[self.repo_name].shelves[self.shelf_name]
        library = shelf.libraries[self.library_name]
        things = library.things.child(spec_name)
        
        try:
            match = get_soft_match(thing_name, list(things))
        except KeyError:
            msg = 'Soft match failed: Could not find %r in %s.' % (thing_name, spec_name)
            available = sorted(things)

            if available:
                msg += ("\n Available %s: %s." %
                        (spec_name, format_list(sorted(available))))
            else:
                msg += "\n None available."
            
            raise_desc(DPSemanticError, msg)
        else:

            if match != thing_name:
                if MCDPConstants.allow_soft_matching:
                    logger.warning('Soft matching %r to %r (deprecated)' % (match, thing_name))
                else:
                    msg = 'Found case in which the user relies on soft matching (%r to refer to %r).' % (thing_name, match)
                    raise DPSemanticError(msg)
                # TODO: add warning 

            data = things[match]
            spec = specs[spec_name]
            basename  = match + '.' + spec.extension
            realpath = '%s in library %r in shelf %r in repo %r' % (basename, self.library_name,
                                                                    self.shelf_name, self.repo_name) 
            return dict(data=data, realpath=realpath)

    @contract(name=str)
    def _load_generic(self, name, spec_name, parsing_function, context):
        """
             
        """        
        context = self._generate_context_with_hooks()
        
        params= dict(repo_name=self.repo_name,
                     shelf_name=self.shelf_name,
                     library_name=self.library_name, 
                     spec_name=spec_name,
                     thing_name=name)
        host_cache = self.the_context.host_cache
        return host_cache.load_spec(context=context, **params)
    
    def clone(self):
        return self
    
    @contextmanager
    def _sys_path_adjust(self):
        yield

def get_soft_match(x, options):
    ''' Get a soft match or raise KeyError '''
    options = list(options)
    res = []
    for o in options:
        if x.lower() == o.lower():
            res.append(o)
    if not res:
        msg = 'Could not find any soft match for "%s" in %s.' % (x, format_list(options))
        raise KeyError(msg)
    if len(res) > 1:
        msg = 'Too many matches (%s) for "%s" in %s.' % (format_list(res), x, format_list(options))
        raise KeyError(msg)
    return res[0]