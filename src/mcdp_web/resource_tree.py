import os

from contracts.utils import indent
from pyramid.security import Allow, Authenticated, Everyone

from mcdp import MCDPConstants
from mcdp.logs import logger_web_resource_tree as logger
from mcdp_shelf.access import PRIVILEGE_ACCESS, PRIVILEGE_READ,\
    PRIVILEGE_VIEW_USER_PROFILE_PUBLIC, PRIVILEGE_VIEW_USER_LIST,\
    PRIVILEGE_VIEW_USER_PROFILE_PRIVATE, PRIVILEGE_VIEW_USER_PROFILE_INTERNAL,\
    PRIVILEGE_EDIT_USER_PROFILE


class Resource(object):
    
    def __init__(self, name=None):
        if isinstance(name,unicode):
            name = name.encode('utf-8')
        self.name = name
        
    def get_subs(self):
        #print('iter not implemented for %s' % type(self).__name__)
        return None
        
    def getitem(self, key):  # @UnusedVariable
        subs = self.get_subs()
        if subs is None:
            return None
        return subs.get(key, None)     
    
    def __iter__(self):
        subs = self.get_subs()
        if subs is not None:
            return sorted(subs).__iter__()
        return [].__iter__()
    
    def __repr__(self):
        if self.name is None:
            return '%s()' % type(self).__name__
        else:
            return '%s(%s)' % (type(self).__name__, self.name)
    
    def __getitem__(self, key):
#         if key in ['login']:
#             return None
        r = self.getitem(key)
        if r is None:
            logger.debug('asked for %r - not found' % key)
            return ResourceNotFoundGeneric(key)
        
        if not hasattr(r, '__parent__'):
            r.__parent__ = self
        
        logger.debug('asked for %r - returning %r ' % (key, r))
        return r
    
    def show_ancestors(self):
        cs = get_all_contexts(self)
        s = '/'.join(str(_) for _ in cs)
        return s
    
    def get_request(self):
        ''' Looks up .request in the root '''
        cs = get_all_contexts(self)
        return cs[0].request

    def get_session(self):
        from mcdp_web.main import WebApp
        app = WebApp.singleton
        request = self.get_request()
        session = app.get_session(request)
        return session

class ResourceEndOfTheLine(Resource):
    ''' Always returns a copy of itself '''
    def getitem(self, key):  # @UnusedVariable
        return type(self)(key)
    
class ResourceNotFoundGeneric(ResourceEndOfTheLine):
    pass

def context_display_in_detail(context):
    ''' Returns a string that displays in detail the context tree and acls. '''
    s = ''
    cs = get_all_contexts(context)
    for c in cs:
        s += '%s' % c
        if hasattr(c, '__acl__'):
            s += '\n' + indent('\n'.join(str(_) for _ in c.__acl__), ' | ')
        s += '\n'
    return s
    

class MCDPResourceRoot(Resource):

    def __init__(self, request):  # @UnusedVariable
        self.name = 'root'
        self.request = request
        from mcdp_web.main import WebApp
        options = WebApp.singleton.options    # @UndefinedVariable
        self.__acl__ = [
            (Allow, Authenticated, PRIVILEGE_VIEW_USER_LIST),
            (Allow, Authenticated, PRIVILEGE_VIEW_USER_PROFILE_PUBLIC),
        ]
        if options.allow_anonymous:
            self.__acl__.append((Allow, Everyone, PRIVILEGE_ACCESS))
            #logger.info('Allowing everyone to access')
        else:
            self.__acl__.append((Allow, Authenticated, PRIVILEGE_ACCESS))
            #logger.info('Allowing authenticated to access')
            
    def get_subs(self):
        return {
            'tree': ResourceTree(),
            'repos': ResourceRepos(),
            'changes': ResourceChanges(),
            'exceptions': ResourceExceptionsJSON(),
            'exceptions_formatted': ResourceExceptionsFormatted(),
            'refresh': ResourceRefresh(),
            'exit': ResourceExit(),
            'login': ResourceLogin(),
            'logout': ResourceLogout(),
            'shelves': ResourceAllShelves(),
            'about': ResourceAbout(),
            'robots.txt': ResourceRobots(),
            'authomatic': ResourceAuthomatic(),
            'users': ResourceListUsers(),
        }    
        
class ResourceAbout(Resource): pass          
class ResourceTree(Resource): pass            

class ResourceListUsers(Resource):
    def getitem(self, key):
        return ResourceListUsersUser(key)
        
class ResourceListUsersUser(Resource):
    def __init__(self, name):
        Resource.__init__(self, name)
        self.__acl__ = [
            (Allow, name, PRIVILEGE_VIEW_USER_PROFILE_PRIVATE),
            (Allow, name, PRIVILEGE_EDIT_USER_PROFILE),
            (Allow, 'group:admin', PRIVILEGE_EDIT_USER_PROFILE),
            (Allow, 'group:admin', PRIVILEGE_VIEW_USER_PROFILE_PRIVATE),
            (Allow, 'group:admin', PRIVILEGE_VIEW_USER_PROFILE_INTERNAL),
        ]

    def getitem(self, key):
        #print('key : %s' % key)
        if key == 'large.jpg':
            return ResourceUserPicture(self.name, 'large', 'jpg')
        if key == 'small.jpg':
            return ResourceUserPicture(self.name, 'small', 'jpg')

class ResourceUserPicture(Resource): 
    def __init__(self, name, size, data_format):
        self.name = name
        self.size = size
        self.data_format = data_format

    
class ResourceExit(Resource): pass
class ResourceLogin(Resource): pass
class ResourceLogout(Resource): pass
class ResourceChanges(Resource): pass
class ResourceAllShelves(Resource): pass

class ResourceShelves(Resource):
    
    def get_repo(self):
        session = self.get_session()
        repos = session.repos
        repo_name = self.__parent__.name
        repo = repos[repo_name]
        return repo
    def getitem(self, key):
        session = self.get_session()
        user = session.get_user()
        repo = self.get_repo()
        shelves = repo.get_shelves()
        
        if not key in shelves:
            return ResourceShelfNotFound(key)
        shelf = shelves[key]
        if not shelf.get_acl().allowed2(PRIVILEGE_READ, user):
            return ResourceShelfForbidden(key)
                
        return ResourceShelf(key)
    
    def __iter__(self):
        session = self.get_session()
        user = session.get_user()
        repo = self.get_repo()

        shelves = repo.get_shelves()
        for id_shelf, shelf in shelves.items():
            if shelf.get_acl().allowed2(PRIVILEGE_READ, user):
                yield id_shelf

class ResourceShelfForbidden(ResourceEndOfTheLine): pass        
class ResourceShelfNotFound(ResourceEndOfTheLine): pass
class ResourceLibraryDocNotFound(ResourceEndOfTheLine): pass
class ResourceLibraryAssetNotFound(ResourceEndOfTheLine): pass

class ResourceShelvesShelfSubscribe(Resource): pass
class ResourceShelvesShelfUnsubscribe(Resource): pass
class ResourceExceptionsFormatted(Resource): pass 
class ResourceExceptionsJSON(Resource): pass
class ResourceRefresh(Resource): pass 

class ResourceLibrariesNew(Resource):
    def getitem(self, key):
        return ResourceLibrariesNewLibname(key)
    
class ResourceLibrariesNewLibname(Resource): pass 
        
class ResourceLibraries(Resource): 
    
    def getitem(self, key):
        subs = {
            ':new': ResourceLibrariesNew(),
        }    
        if key in subs: return subs[key]
        
        libname = key 
        shelf = context_get_shelf(self)
        if not libname in shelf.get_libraries_path():
            return ResourceLibraryNotFound(libname)
        return ResourceLibrary(libname)
    
    def __iter__(self):
        shelf = context_get_shelf(self)
        libraries = sorted(shelf.get_libraries_path())
        return libraries.__iter__()
        

class ResourceShelf(Resource): 
        
    @property
    def __acl__(self):
        session = self.get_session()
        shelf = session.get_shelf(self.name)
        return shelf.get_acl().as_pyramid_acl()
        
    def __iter__(self):
        return ['libraries'].__iter__()
        
    def getitem(self, key):
        subs =  {
            ':subscribe': ResourceShelvesShelfSubscribe(self.name),
            ':unsubscribe': ResourceShelvesShelfUnsubscribe(self.name),
        }    
        if key in subs: return subs[key]
    
        if key == 'libraries':
            session = self.get_session()
            if not self.name in session.shelves_used:
                msg = 'Cannot access libraries if not subscribed to shelf "%s".' % self.name
                msg += ' user: %s' % self.get_session().get_user()
                logger.debug(msg)
                return ResourceShelfInactive(self.name)
            
            return ResourceLibraries()

    
class ResourceShelfInactive(ResourceEndOfTheLine): 
    pass
  

class ResourceRepos(Resource):
    
    def getitem(self, key):
        session = self.get_session()
        repos = session.repos
        if not key in repos:
            #msg = 'Could not find repository "%s".' % key
            return ResourceRepoNotFound(key)
        return ResourceRepo(key)
        
    def __iter__(self):
        session = self.get_session()
        repos = list(session.repos)
        return list(repos).__iter__()
    
class ResourceRepoNotFound(ResourceEndOfTheLine):
    pass

class ResourceRepo(Resource):
    def get_subs(self):
        return {'shelves':ResourceShelves()}
    
class ResourceLibraryNotFound(ResourceEndOfTheLine):
    pass

class ResourceLibrary(Resource): 
    
    def __iter__(self):
        from mcdp_library.specs_def import specs
        options = list(specs)
        options.append('interactive')
        return options.__iter__()
    
    def getitem(self, key):
        if key == 'refresh_library':
            return ResourceLibraryRefresh()
        if key == 'interactive':
            return ResourceLibraryInteractive()
        
        library = context_get_library(self)
        
        if key.endswith('.html'):
            docname = os.path.splitext(key)[0]
            filename = '%s.%s' % (docname, MCDPConstants.ext_doc_md)
            if not library.file_exists(filename):
                return ResourceLibraryDocNotFound(docname)

            return ResourceLibraryDocRender(docname)
        
        if '.' in key:
            if not library.file_exists(key):
                return ResourceLibraryAssetNotFound(key)
            return ResourceLibraryAsset(key)
        return ResourceThings(key)

class ResourceLibraryDocRender(Resource): pass
class ResourceLibraryAsset(Resource): pass

class ResourceLibraryInteractive(Resource): 
    def getitem(self, key):
        if key == 'mcdp_value':
            return ResourceLibraryInteractiveValue()

class ResourceLibraryInteractiveValue(Resource): 
    def getitem(self, key):
        if key == 'parse':
            return ResourceLibraryInteractiveValueParse()


class ResourceLibraryInteractiveValueParse(Resource): pass

class ResourceLibraryRefresh(Resource): pass
    
class ResourceThings(Resource):
    def __init__(self, specname):
        Resource.__init__(self, specname)
        self.specname = self.name
        
    def __iter__(self):
        library = context_get_library(self)
        spec = context_get_spec(self)
        x = library._list_with_extension(spec.extension)
        return x.__iter__()
        
    def getitem(self, key):
        if key == 'new': return ResourceThingsNewBase()
        return ResourceThing(key)
    
    def __repr__(self):
        return '%s(specname=%s)' % (type(self).__name__, self.specname)

    
class ResourceThingsNewBase(Resource):
    def getitem(self, key):
        return ResourceThingsNew(key)
    
class ResourceThingsNew(Resource): pass

class ResourceThing(Resource): 
    
    def __iter__(self):
        return ['views'].__iter__()
    
    def getitem(self, key):
        subs =  {
            'views': ResourceThingViews(),
            ':delete': ResourceThingDelete(),
        }
        return subs.get(key, None)

class ResourceThingDelete(Resource):
    pass

class ResourceThingViews(Resource):
    
    def __iter__(self):
        options = ['syntax', 'edit_fancy']
        if self.__parent__.__parent__.specname == 'models':
            options.extend(['dp_graph', 'dp_tree', 'ndp_graph', 'ndp_repr', 'solver2', 'images', 'solver'])
        return options.__iter__()
    
    def getitem(self, key):
        subs =  {
            'syntax': ResourceThingViewSyntax(),
            'edit_fancy': ResourceThingViewEditor(),
        }
        if self.__parent__.__parent__.specname == 'models':
            subs2 = {
                'dp_graph': ResourceThingViewDPGraph(),
                'dp_tree': ResourceThingViewDPTree(),
                'ndp_graph': ResourceThingViewNDPGraph(),
                'ndp_repr': ResourceThingViewNDPRepr(),
                'solver2': ResourceThingViewSolver(),
                'images': ResourceThingViewImages(),
                'solver': ResourceThingViewSolver0(),
            }
            subs.update(**subs2)
            
        return subs.get(key, None)
    
class ResourceThingViewImages(Resource):
    def getitem(self, key):
        which, data_format = key.split('.')
        return ResourceThingViewImagesOne(which.encode('utf8'), data_format.encode('utf8'))
     
class ResourceThingView(Resource): pass
class ResourceThingViewSyntax(ResourceThingView): pass
class ResourceThingViewDPGraph(ResourceThingView): pass
class ResourceThingViewDPTree(ResourceThingView): pass
class ResourceThingViewNDPGraph(ResourceThingView): pass
class ResourceThingViewNDPRepr(ResourceThingView): pass
class ResourceThingViewSolver(ResourceThingView): 
    def getitem(self, key):
        subs =  {
            'submit': ResourceThingViewSolver_submit(),
            'display.png': ResourceThingViewSolver_display_png(),
            'display1u': ResourceThingViewSolver_display1u(),
            'display1u.png': ResourceThingViewSolver_display1u_png(),
        }
        return subs.get(key, None)

class ResourceThingViewSolver_submit(Resource): pass
class ResourceThingViewSolver_display_png(Resource): pass
class ResourceThingViewSolver_display1u(Resource): pass
class ResourceThingViewSolver_display1u_png(Resource): pass

class ResourceThingViewSolver0(ResourceThingView): 
    def getitem(self, key):
        return ResourceThingViewSolver0Axis( key) 
    
class ResourceThingViewSolver0Axis(ResourceThingView): 
    def getitem(self, key):
        return ResourceThingViewSolver0AxisAxis(self.name, key) 
    
class ResourceThingViewSolver0AxisAxis(ResourceThingView): 
    def __init__(self, fun_axes, res_axes):
        self.fun_axes = fun_axes
        self.res_axes = res_axes
        self.name = '%s-%s' % (fun_axes, res_axes)
    def getitem(self, key):
        subs = {
            'addpoint': ResourceThingViewSolver0AxisAxis_addpoint(),
            'getdatasets': ResourceThingViewSolver0AxisAxis_getdatasets(),
            'reset': ResourceThingViewSolver0AxisAxis_reset(),
        }
        return subs.get(key, None)
        
class ResourceThingViewSolver0AxisAxis_addpoint(Resource): pass
class ResourceThingViewSolver0AxisAxis_getdatasets(Resource): pass
class ResourceThingViewSolver0AxisAxis_reset(Resource): pass

class ResourceThingViewEditor(ResourceThingView):
    def getitem(self, key): 
        subs =  {
            'ajax_parse': ResourceThingViewEditorParse(),
            'save': ResourceThingViewEditorSave(),
        }
        if key in subs:
            return subs[key]
        
        if key.startswith('graph.'):
            _, text_hash, data_format = key.split('.')
            return ResourceThingViewEditorGraph(text_hash.encode('utf8'), data_format.encode('utf8'))


class ResourceThingViewEditorParse(Resource): pass
class ResourceThingViewEditorSave(Resource): pass

class ResourceThingViewEditorGraph(Resource): 
    def __init__(self, text_hash, data_format):
        self.text_hash = text_hash
        self.data_format = data_format
        self.name = 'graph.%s.%s' % (text_hash, data_format)
         
class ResourceThingViewImagesOne(Resource):
    def __init__(self, which, data_format):
        self.which = which
        self.data_format = data_format
        self.name = '%s.%s' % (which, data_format)
        
class ResourceRobots(Resource): pass
class ResourceAuthomatic(Resource):
    def get_subs(self):
        subs =  {
            'github': ResourceAuthomaticProvider('github'),
            'facebook': ResourceAuthomaticProvider('facebook'),
            'google': ResourceAuthomaticProvider('google'),
            'linkedin': ResourceAuthomaticProvider('linkedin'),
        }
        return subs
    
class ResourceAuthomaticProvider(Resource): pass 

def get_all_contexts(context):
    if hasattr(context, '__parent__'):
        return get_all_contexts(context.__parent__) + (context,)
    else:
        return (context,)

def get_from_context(rclass, context):
    a = get_all_contexts(context)
    for _ in a:
        if isinstance(_, rclass):
            return _
    return None

def is_in_context(rclass, context):
    return get_from_context(rclass, context) is not None

def context_get_shelf_name(context):
    return get_from_context(ResourceShelf, context).name

def context_get_repo_name(context):
    return get_from_context(ResourceRepo, context).name

def context_get_repo(context):
    session = context.get_session()
    repo_name = context_get_repo_name(context)
    repo = session.repos[repo_name]
    return repo

def context_get_shelf(context):
    repo = context_get_repo(context)
    shelf_name = context_get_shelf_name(context)
    shelf = repo.get_shelves()[shelf_name]
    return shelf

def context_get_library(context): 
    library_name = context_get_library_name(context) 
    session = context.get_session()
    library = session.get_library(library_name)
    return library 

def context_get_library_name(context):
    library_name = get_from_context(ResourceLibrary, context).name
    return library_name
 
def context_get_spec(context):
    from mcdp_web.editor_fancy.app_editor_fancy_generic import specs
    specname = get_from_context(ResourceThings, context).specname
    spec = specs[specname]
    return spec 

