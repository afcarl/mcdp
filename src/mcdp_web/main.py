# -*- coding: utf-8 -*-
from ConfigParser import RawConfigParser
from collections import OrderedDict
import datetime
import os
import sys
import time
import traceback
import urlparse
from wsgiref.simple_server import make_server

from contracts.utils import indent, check_isinstance
import git.cmd  # @UnusedImport
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.httpexceptions import HTTPFound
from pyramid.renderers import JSONP, render_to_response
from pyramid.response import Response
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.session import SignedCookieSessionFactory
from quickapp import QuickAppBase

from mcdp import MCDPConstants
from mcdp import logger
from mcdp.exceptions import DPSemanticError, DPSyntaxError
from mcdp_docs import render_complete
from mcdp_hdb.disk_struct import ProxyDirectory

from mcdp_library import MCDPLibrary
from mcdp_repo import MCDPGitRepo, MCDPythonRepo
from mcdp_utils_misc import create_tmpdir, duration_compact, dir_from_package_name, format_list
from mcdp_utils_misc import yaml_dump

from .auhtomatic_auth import get_authomatic_config_, view_authomatic_
from .auhtomatic_auth import view_confirm_bind_,\
    view_confirm_creation_similar_, view_confirm_creation_,\
    view_confirm_creation_create_, view_confirm_bind_bind_
from .confi import describe_mcdpweb_params, parse_mcdpweb_params_from_dict
from .editor_fancy import AppEditorFancyGeneric
from .environment import cr2e
from .images.images import WebAppImages, get_mime_for_format
from .interactive.app_interactive import AppInteractive
from .qr.app_qr import AppQR
from .resource_tree import MCDPResourceRoot, ResourceLibraries, ResourceLibrary,  ResourceLibraryRefresh, ResourceRefresh, ResourceExit, ResourceLibraryDocRender, ResourceLibraryAsset, ResourceRobots, ResourceShelves, ResourceShelvesShelfUnsubscribe, ResourceShelvesShelfSubscribe, ResourceExceptionsFormatted, ResourceExceptionsJSON, ResourceShelf, ResourceLibrariesNewLibname, Resource, context_display_in_detail, ResourceShelfInactive, ResourceThingDelete, ResourceChanges, ResourceTree, ResourceThing, ResourceRepos, ResourceRepo, ResourceThings, ResourceLibraryInteractive
from .resource_tree import ResourceAllShelves, ResourceShelfForbidden,\
    ResourceShelfNotFound, ResourceRepoNotFound, ResourceLibraryAssetNotFound,\
    ResourceLibraryDocNotFound, ResourceNotFoundGeneric, ResourceAbout
from .resource_tree import ResourceAuthomaticProvider, ResourceListUsers,\
    ResourceListUsersUser, ResourceUserPicture
from .resource_tree import ResourceConfirmBind,\
    ResourceConfirmCreationSimilar, ResourceConfirmCreation,\
    ResourceConfirmCreationCreate, ResourceConfirmBindBind
from .resource_tree import ResourceUserImpersonate
from .security import AppLogin, groupfinder
from .sessions import Session
from .solver.app_solver import AppSolver
from .solver2.app_solver2 import AppSolver2
from .status import AppStatus
from .utils.image_error_catch_imp import response_image
from .utils.response import response_data
from .utils0 import add_other_fields, add_std_vars_context
from .utils0 import add_std_vars_context_no_redir
from .visualization.app_visualization import AppVisualization
from mcdp_hdb.pipes import apply_changes_to_disk_and_repo


Privileges = MCDPConstants.Privileges




__all__ = [
    'mcdp_web_main',
    'app_factory',
]


git.cmd.log.disabled = True



class WebApp(AppVisualization, AppStatus,
             AppQR, AppSolver, AppInteractive,
             AppSolver2, AppEditorFancyGeneric, WebAppImages,
             AppLogin):
    
    singleton = None
    
    def __init__(self, options, settings):
        from mcdp_library_tests.create_mockups import write_hierarchy
        self.options = options
        self.settings = settings
        
        # display options
        for k in sorted(self.options._values):
            v = self.options._values[k]
            logger.debug('option %20s = %r ' % (k,v))
        # display settings
        for k in sorted(self.settings):
            v = self.settings[k]
            logger.debug('setting %20s = %r ' % (k,v))
        
        WebApp.singleton = self
        
        dirname = options.libraries
        if dirname is None:
            package = dir_from_package_name('mcdp_data')
            default_libraries = os.path.join(package, 'libraries')
            msg = ('Option "-d" not passed, so I will open the default libraries '
                   'shipped with PyMCDP. These might not be writable depending on your setup.')
            logger.info(msg)
            dirname = default_libraries

        self.dirname = dirname
 
        AppVisualization.__init__(self)
        AppQR.__init__(self)
        AppSolver.__init__(self)
        AppInteractive.__init__(self)
        AppSolver2.__init__(self)
        AppEditorFancyGeneric.__init__(self)
        WebAppImages.__init__(self)

        # name -> dict(desc: )
        self.views = {}
        self.exceptions = []
        
        self.add_model_view('syntax', 'Source code display')
        self.add_model_view('edit_fancy', 'Editor')
        # self.add_model_view('edit', 'Simple editor for IE')
        self.add_model_view('solver2', desc='Solver interface')
        self.add_model_view('ndp_graph', 'NDP Graph representation')
        self.add_model_view('ndp_repr', 'NDP Text representation')
        self.add_model_view('dp_graph', 'DP graph representation')
        self.add_model_view('dp_tree', 'DP tree representation')
        self.add_model_view('images', 'Other image representations')
        self.add_model_view('solver', 'Graphical solver [experimental]')
        
        # csfr_token -> Session
        self.sessions = OrderedDict()
        
        # str -> Shelf
        self.all_shelves = OrderedDict()
        
        if self.options.users is None:
            logger.info('No user directory passed (%s). Creating user dir.' % self.options.users)
            self.options.users = create_tmpdir('tmp-user-db')
            db = {
                'anonymous.mcdp_user': {
                    'user.yaml' : '''
                        name: Anonimo
                    '''
                },
                'admin.mcdp_user': {
                    'user.yaml' : '''
                        name: Administrator
                        groups:
                        - admin
                        authentication_ids:
                        - provider: password
                          password: admin
                    '''
                }
            }
            if not os.path.exists(self.options.users):
                os.makedirs(self.options.users)
            logger.info('Temporary user dir is %s' % self.options.users) 
            write_hierarchy(self.options.users, db)
            

        self.repos = {}
        REPO_BUNDLED = 'bundled'
        REPO_USERS = 'global'
        if self.options.load_mcdp_data:
            desc_short = 'Contains models bundled with the code.'
            if os.path.exists('.git'):
                logger.info('Loading mcdp_data repo as MCDPGitRepo')
                b = MCDPGitRepo(where='.', desc_short=desc_short)
            else:
                logger.info('Loading mcdp_data repo as MCDPythonRepo')
                b = MCDPythonRepo('mcdp_data', desc_short=desc_short)
                    
            self.repos[REPO_BUNDLED]  = b
        else:
            logger.info('Not loading mcdp_data')
        from mcdp_hdb_mcdp.main_db_schema import DB
        if self.options.users is not None:
            logger.info('Loading user db from %s' % self.options.users)
            dm = DB.dm
            hierarchy = ProxyDirectory.from_disk(self.options.users)
            logger.info('These are the files found:\n%s' % indent(hierarchy.tree(), '  '))
            user_db_schema = DB.user_db
            user_db_data = dm.interpret_hierarchy_(user_db_schema, hierarchy)
            
            logger.debug('user_db schema: \n' + str(user_db_schema) )
            logger.debug('user_db:\n' + indent(yaml_dump(user_db_data), ' > '))
            
            DB.user_db.validate(user_db_data)
            
            user_db_view = DB.view_manager.create_view_instance(user_db_schema, user_db_data)
            user_db_view.set_root() 
            apply_changes_to_disk_and_repo(dm, user_db_view, self.options.users)
            self.user_db = user_db_view
            logger.info('Loaded %s users' % len(self.user_db.users))
            for username, user in self.user_db.users.items():
                user.info.username = username
            desc_short = 'Global database of shared models.'
            is_git = os.path.exists(os.path.join(self.options.users, '.git'))
            if is_git:
                self.repos[REPO_USERS] = MCDPGitRepo(where=self.options.users, desc_short=desc_short)

        shelf2repo = {}
        for id_repo, repo in self.repos.items():
            shelves = repo.get_shelves()
            
            logger.info('repo %s: %s' % (id_repo, sorted(shelves)))
            
            for shelf_name in shelves:
                if shelf_name in shelf2repo:
                    msg = 'Shelf %r in %r and %r' % (shelf_name, id_repo, shelf2repo[shelf_name])
                    raise ValueError(msg)
                shelf2repo[shelf_name] = id_repo

            self.all_shelves.update(shelves)
#         
#         picture = 'http://graph.facebook.com/10154724108563171/picture?type=large'
#         h = urllib2.urlopen(picture)
#         logger.info('urlp opened  %s' % h)
#         jpg = h.read()
#         h.close()
#         logger.info('read %s bytes' % len(jpg)) 
        
    def add_model_view(self, name, desc):
        self.views[name] = dict(desc=desc, order=len(self.views))

    def get_session(self, request):
        token = request.session.get_csrf_token()
        if not token in self.sessions:
            # print('creating new session for token %r' % token)
            self.sessions[token] = Session(app=self, request=request, shelves_all=self.all_shelves)
        session = self.sessions[token]
        session.set_last_request(request)
        return session
    
    def _get_views(self):
        return sorted(self.views, key=lambda _:self.views[_]['order'])
       
    @add_std_vars_context
    @cr2e
    def view_dummy(self, e):  # @UnusedVariable
        return {}
    
    @add_std_vars_context_no_redir
    @cr2e
    def view_resource_not_found(self, e):  
        e.request.response.status = 404
        return {}
    
    @add_std_vars_context_no_redir
    @cr2e
    def view_resource_forbidden(self, e): 
        e.request.response.status = 403
        return {}
    
    @add_std_vars_context
    @cr2e
    def view_index(self, e):
        return {
            'changes': self._get_changes(e),
        }
    @add_std_vars_context
    @cr2e
    def view_tree(self, e):
        root = MCDPResourceRoot(e.request)
        
        def get_pages(node, prefix):
            
            for child in node:
                yield "/".join(prefix + (child,))
                for _ in get_pages(node[child], prefix + (child,)):
                    yield _
                    
        pages = list(get_pages(node=root, prefix=()))
        pages = [(_, len(_.split('/'))) for _ in pages]
        return {'pages': pages}
        
    @add_std_vars_context
    @cr2e
    def view_shelf(self, e):
        desc_long_md = e.shelf.get_desc_long()
        if desc_long_md is None:
            desc_long = ''
        else:
            library = MCDPLibrary()
            desc_long = render_complete(library, desc_long_md, raise_errors=True, realpath=e.shelf_name, do_math=False)
        res = {
            'shelf': e.shelf, 
            'sname': e.shelf_name, 
            'desc_long': unicode(desc_long, 'utf8'),
        }
        return res
    
    @add_std_vars_context 
    @cr2e
    def view_shelves_subscribe(self, e):  
        if not e.shelf_name in e.user.subscriptions:
            e.user.subscriptions.append(e.shelf_name)
#             e.session.save_user()
            e.session.recompute_available()
        raise HTTPFound(e.request.referrer)
    
    @cr2e
    def view_shelf_library_new(self, e):
        new_library_name = e.context.name
        url_edit = get_url_library(e, e.shelf_name, new_library_name)

        if new_library_name in e.shelf.libraries:
            error = 'The library "%s" already exists.' %new_library_name
            
            res = {
                'error': error,
                'library_name': new_library_name,
                'url_edit': url_edit,
            }
            add_other_fields(self, res, e.request, context=e.context)
            template = 'error_library_exists.jinja2'
            e.request.response.status = 409  # Conflict
            return render_to_response(template, res, request=e.request, 
                                      response=e.request.response)
        else:
            # does not exist
            dirname = os.path.join(e.shelf.write_to, new_library_name + '.' + MCDPConstants.library_extension)
            if os.path.exists(dirname):
                logger.error('Directory %s already exists.' % dirname)
            else:
                os.makedirs(dirname)
                one = os.path.join(dirname, '.gitignore')
                with open(one, 'w') as f:
                    f.write("")
                    
                logger.info('Created library %r in %r' % (new_library_name, dirname))
            
            e.session.notify_created_library(e.shelf_name,new_library_name)
            raise HTTPFound(url_edit) 
         
    @cr2e
    def view_shelves_unsubscribe(self, e):
        sname = e.context.name
        #print('unsubscribe %r' % sname)
        if sname in e.user.subscriptions:
            e.user.subscriptions.remove(sname)
#             e.session.save_user()
            e.session.recompute_available()
        raise HTTPFound(e.request.referrer)

    def refresh_library(self, e):
        # nuclear option
        e.session.refresh_libraries()

    @cr2e
    def view_refresh_library(self, e):  # @UnusedVariable
        """ Refreshes the current library (if external files have changed) 
            then reloads the current url. """
#         self._refresh_library(request) 
        # Note this currently is equivalent to global refresh
        return self.view_refresh(e.context, e.request);

    @cr2e
    def view_refresh(self, e): 
        """ Refreshes all """
        self.refresh_library(e) 
        if e.request.referrer is None:
            redirect = self.get_root_relative_to_here(e.request)
            logger.info('REFRESH')
            logger.info('context.url = %s' % e.request.url)
            logger.info('redirect = %s' % redirect)
        else:
            redirect = e.request.referrer
        raise HTTPFound(redirect)

    @cr2e
    def view_not_found(self, e):
        e.request.response.status = 404
        url = e.request.url
        referrer = e.request.referrer
        #print('context: %s' % e.context)
        self.exceptions.append('Path not found.\n url: %s\n referrer: %s' % (url, referrer))
        res = {
            'url': url,
             'referrer': referrer,
             'root': e.root,
             'static': e.root + '/static',
        }

        return res

    @add_std_vars_context
    @cr2e
    def view_exceptions_occurred(self, e):  # @UnusedVariable
        exceptions = []
        for e in self.exceptions:
            u = unicode(e, 'utf-8')
            exceptions.append(u)
        return {'exceptions': exceptions}

    @cr2e
    def view_exceptions_occurred_json(self, e):  # @UnusedVariable
        exceptions = []
        for e in self.exceptions:
            u = unicode(e, 'utf-8')
            exceptions.append(u)
        return {'exceptions': exceptions}

    def view_exception(self, exc, request):
        request.response.status = 500  # Internal Server Error

        if hasattr(request, 'context'):
            if isinstance(request.context, Resource):
                logger.debug(context_display_in_detail(request.context))
            
        compact = (DPSemanticError, DPSyntaxError)
        if isinstance(exc, compact):
            s = exc.__str__()
        else:
            s = traceback.format_exc(exc)

        self.note_exception(exc, request=request)
 
        u = unicode(s, 'utf-8')
        logger.error(u.encode('utf8'))
        root = self.get_root_relative_to_here(request)
        res = {
            'exception': u,
            # 'url_refresh': url_refresh,
            'root': root,
            'static': root + '/static'
        }  
        return res
 
    def note_exception(self, exc, request=None, context=None):
        check_isinstance(exc, BaseException)
        n = ''
        if request is not None:   
            url = request.url
            referrer = request.referrer
            n += 'Error during serving this URL:'
            n += '\n url: %s' % url
            n += '\n referrer: %s' % referrer

        if context is not None:
            n += '\n\n' + context_display_in_detail(context) + '\n'
            
        ss = traceback.format_exc(exc)
        n += '\n' + indent(ss, '| ')
        self.exceptions.append(n)
    
    def png_error_catch2(self, request, func):
        """ func is supposed to return an image response.
            If it raises an exception, we create
            an image with the error and then we add the exception
            to the list of exceptions.
            
             """
        try:
            return func()
        except Exception as e:
            s = traceback.format_exc(e)

            try:
                logger.error(s)
            except UnicodeEncodeError:
                pass

            self.note_exception(e, request=request)            
            return response_image(request, s) 

    # This is where we keep all the URLS
    def make_relative(self, request, url):
        if not url.startswith('/'):
            msg = 'Expected url to start with /: %r' % url
            raise ValueError(msg)
        root = self.get_root_relative_to_here(request)
        comb = root + url
        return comb

    def get_root_relative_to_here(self, request):
        if request is None:
            raise ValueError()
        
        parsed = urlparse.urlparse(request.url) 
        path = parsed.path
        
        if not path.endswith('/'):
            last = path.rfind('/')
            path = path[:last]

        if path == '':
            return '/'
        r = os.path.relpath('/', path)
        return r

    @add_std_vars_context_no_redir
    @cr2e
    def view_library_asset_not_found(self, e):
        e.request.response.status = 404
        return {}

    @add_std_vars_context_no_redir
    @cr2e
    def view_library_doc_not_found(self, e):
        e.request.response.status = 404
        return {}
    
    @add_std_vars_context_no_redir
    @cr2e
    def view_library_doc(self, e):
        """ '/libraries/{library}/{document}.html' """
        # f['data'] not utf-8
        # reopen as utf-8
        document = e.context.name
#         filename = '%s.%s' % (document, MCDPConstants.ext_doc_md)
#         if not e.library.file_exists(filename):
#             res = {}
#             add_other_fields(self, res, e.request, context=e.context)
#             response = e.request.response
#             response.status = 404 # not found
#             template = 'library_doc_not_found.jinja2'
#             return render_to_response(template, res, request=e.request, response=response)

        try:
            html = self._render_library_doc(e, document)
        except DPSyntaxError as exc:
            res = {}
            res['error'] = exc
            res['title'] = document
            return res 
        # we work with utf-8 strings
        assert isinstance(html, str)
        # but we need to convert to unicode later
        html = unicode(html, 'utf-8')
        res = {}
        res['contents'] = html
        res['title'] = document
        res['print'] = bool(e.request.params.get('print', False))
        return res

    def _render_library_doc(self, e, document):
        strict = int(e.request.params.get('strict', '0'))
        filename = '%s.%s' % (document, MCDPConstants.ext_doc_md)
            
        f = e.library._get_file_data(filename)
        
        realpath = f['realpath']
        # read unicode
        import codecs 
        data_unicode = codecs.open(realpath, encoding='utf-8').read()
        data_str = data_unicode.encode('utf-8')
        raise_errors = bool(strict)
        html = render_complete(library=e.library, s=data_str, 
                               realpath=realpath, raise_errors=raise_errors)
        return html

    @cr2e
    def view_library_asset(self, e):
        name = e.context.name
        asset = os.path.splitext(name)[0]
        ext = os.path.splitext(name)[1][1:]
        filename = '%s.%s' % (asset, ext)
        try:
            f = e.library._get_file_data(filename)
        except DPSemanticError as exc:
            res = {
                'error': exc, 
            }
            add_other_fields(self, res, e.request, context=e.context)
            response = e.request.response
            response.status = 404 # not found
            template = 'asset_not_found.jinja2'
            return render_to_response(template, res, request=e.request, response=response)
        data = f['data']
        content_type = get_mime_for_format(ext)
        return response_data(e.request, data, content_type)

    @cr2e
    def exit(self, e):  # @UnusedVariable
        sys.exit(0)
        setattr(self.server, '_BaseServer__shutdown_request', True)
        howlong = duration_compact(self.get_uptime_s())
        return "Bye. Uptime: %s." % howlong

    def get_uptime_s(self):
        return time.time() - self.time_start
    
    def serve(self, port):
        app = self.get_app()
        self.server = make_server('0.0.0.0', port, app)
        self.server.serve_forever()
        
    def get_app(self): 
        self.time_start = time.time()

        secret = 'itsasecreet' # XXX
        
        self.my_session_factory = SignedCookieSessionFactory(secret+'sign')
        root_factory =MCDPResourceRoot
        config = Configurator(root_factory=root_factory, settings=self.settings)
        config.set_session_factory(self.my_session_factory)

        # config.include('pyramid_debugtoolbar')

        authn_policy = AuthTktAuthenticationPolicy(secret+'authn', hashalg='sha512', callback=groupfinder )
        authz_policy = ACLAuthorizationPolicy()
        config.set_authentication_policy(authn_policy)
        config.set_authorization_policy(authz_policy)
        config.set_default_permission(Privileges.ACCESS)

        config.add_renderer('jsonp', JSONP(param_name='callback'))

        config.add_static_view(name='static', path='static', cache_max_age=3600)
        config.include('pyramid_jinja2')

        AppStatus.config(self, config)
        AppVisualization.config(self, config)
        AppQR.config(self, config)
        AppSolver.config(self, config)
        AppInteractive.config(self, config)
        AppEditorFancyGeneric.config(self, config)
        WebAppImages.config(self, config)
        AppLogin.config(self, config)
        AppSolver2.config(self, config)

        config.add_view(self.view_dummy, context=ResourceAbout, renderer='about.jinja2')
        config.add_view(self.view_index, context=MCDPResourceRoot, renderer='index.jinja2')
        config.add_view(self.view_dummy, context=ResourceLibraries, renderer='list_libraries.jinja2')
        config.add_view(self.view_dummy, context=ResourceRepos, renderer='repos.jinja2')
        config.add_view(self.view_dummy, context=ResourceLibraryInteractive, renderer='empty.jinja2')
        
        config.add_view(self.view_dummy, context=ResourceLibrary, renderer='library_index.jinja2', permission=Privileges.READ)
        config.add_view(self.view_dummy, context=ResourceThings, renderer='library_index.jinja2', permission=Privileges.READ)  # same as above
    
        config.add_view(self.view_dummy, context=ResourceRepo, renderer='shelves_index.jinja2')
        config.add_view(self.view_dummy, context=ResourceShelves, renderer='shelves_index.jinja2') # same as above
        config.add_view(self.view_dummy, context=ResourceAllShelves, renderer='shelves_index.jinja2') # same as above
        config.add_view(self.view_changes, context=ResourceChanges, renderer='changes.jinja2')
        config.add_view(self.view_tree, context=ResourceTree, renderer='tree.jinja2')
        config.add_view(self.view_not_found_generic, context=ResourceNotFoundGeneric, renderer='not_found_generic.jinja2', permission=NO_PERMISSION_REQUIRED)
        config.add_view(self.view_shelf_library_new, context=ResourceLibrariesNewLibname, permission=Privileges.WRITE)
        config.add_view(self.view_shelf, context=ResourceShelf, renderer='shelf.jinja2', permission=Privileges.DISCOVER)
        config.add_view(self.view_shelves_subscribe, context=ResourceShelvesShelfSubscribe, permission=Privileges.SUBSCRIBE)
        config.add_view(self.view_shelves_unsubscribe, context=ResourceShelvesShelfUnsubscribe, permission=Privileges.SUBSCRIBE)
        config.add_view(self.view_library_doc, context=ResourceLibraryDocRender, renderer='library_doc.jinja2', permission=Privileges.READ)
        config.add_view(self.view_library_doc_not_found, context=ResourceLibraryDocNotFound, renderer='library_doc_not_found.jinja2', permission=Privileges.READ)
        config.add_view(self.view_library_asset_not_found, context=ResourceLibraryAssetNotFound, renderer='asset_not_found.jinja2', permission=Privileges.READ)
        config.add_view(self.view_library_asset, context=ResourceLibraryAsset, permission=Privileges.READ)
        config.add_view(self.view_refresh_library, context=ResourceLibraryRefresh, permission=Privileges.READ)
        config.add_view(self.view_refresh, context=ResourceRefresh)
        config.add_view(self.view_users, context=ResourceListUsers, renderer='users.jinja2', permission=Privileges.VIEW_USER_LIST)
        config.add_view(self.view_users_user, context=ResourceListUsersUser, renderer='user_page.jinja2',
                                              permission=Privileges.VIEW_USER_PROFILE_PUBLIC)
        
        config.add_view(self.view_impersonate, context=ResourceUserImpersonate,
                                                permission=Privileges.IMPERSONATE_USER)
        
        config.add_view(self.view_exception, context=Exception, renderer='exception.jinja2')
        config.add_view(self.exit, context=ResourceExit, renderer='json', permission=NO_PERMISSION_REQUIRED)

        config.add_view(self.view_exceptions_occurred_json, context=ResourceExceptionsJSON, renderer='json', permission=NO_PERMISSION_REQUIRED)
        config.add_view(self.view_exceptions_occurred, context=ResourceExceptionsFormatted, renderer='exceptions_formatted.jinja2', permission=NO_PERMISSION_REQUIRED)
        
        config.add_view(self.view_dummy, context=ResourceShelfNotFound, renderer='shelf_not_found.jinja2')
        config.add_view(self.view_dummy, context=ResourceShelfForbidden, renderer='shelf_forbidden.jinja2')
        config.add_view(self.view_dummy, context=ResourceShelfInactive, renderer='shelf_inactive.jinja2')
        config.add_view(self.view_resource_not_found, context=ResourceRepoNotFound, renderer='repo_not_found.jinja2')
        config.add_view(self.view_thing_delete, context=ResourceThingDelete)
        config.add_view(self.view_thing, context=ResourceThing)
        config.add_view(self.view_picture, context=ResourceUserPicture)
        
        config.add_view(self.view_confirm_bind, http_cache=0, context=ResourceConfirmBind, renderer='confirm_bind.jinja2', permission=NO_PERMISSION_REQUIRED)
        config.add_view(self.view_confirm_bind_bind, http_cache=0, context=ResourceConfirmBindBind, renderer='confirm_bind_bind.jinja2', permission=NO_PERMISSION_REQUIRED)
        config.add_view(self.view_confirm_creation_similar, http_cache=0, context=ResourceConfirmCreationSimilar, renderer='confirm_creation_similar.jinja2', permission=NO_PERMISSION_REQUIRED)
        config.add_view(self.view_confirm_creation, http_cache=0, context=ResourceConfirmCreation, renderer='confirm_creation.jinja2', permission=NO_PERMISSION_REQUIRED)
        config.add_view(self.view_confirm_creation_create, http_cache=0, context=ResourceConfirmCreationCreate, renderer='confirm_creation_create.jinja2', permission=NO_PERMISSION_REQUIRED)
        
        config.add_view(serve_robots, context=ResourceRobots, permission=NO_PERMISSION_REQUIRED)
        config.add_notfound_view(self.view_not_found, renderer='404.jinja2')
        config.scan()
    
        config.add_view(self.view_authomatic, context=ResourceAuthomaticProvider, permission=NO_PERMISSION_REQUIRED)
        self.get_authomatic_config()
        app = config.make_wsgi_app()
        return app
   
    def show_error(self, e, msg, status=500):
        ''' Redirects the user to an error page with the message specified. 
        
            return self.show_error(e, 'invalid session')
        '''
        res = {
            'error': msg,
        }
        e.request.response.status = status
        add_other_fields(self, res, e.request, context=e.context)
        return render_to_response('generic_error.jinja2', res, request=e.request, 
                                      response=e.request.response)
    
    def get_authomatic_config(self):
        return get_authomatic_config_(self)
    
    @cr2e
    def view_authomatic(self, e):
        config = self.get_authomatic_config()
        return view_authomatic_(self, config, e)

    @cr2e
    def view_impersonate(self, e):
        from mcdp_web.auhtomatic_auth import success_auth
        username = e.context.name
        next_location = '..'
        return success_auth(self, e.request, username, next_location)

    @add_std_vars_context
    @cr2e
    def view_confirm_bind(self, e):
        return view_confirm_bind_(self, e)
    
    @add_std_vars_context
    @cr2e
    def view_confirm_bind_bind(self, e):
        return view_confirm_bind_bind_(self, e)
    
    
    @add_std_vars_context
    @cr2e
    def view_confirm_creation_similar(self, e):
        return view_confirm_creation_similar_(self, e)
    @add_std_vars_context
    @cr2e
    def view_confirm_creation(self, e):
        return view_confirm_creation_(self, e)
    @add_std_vars_context
    @cr2e
    def view_confirm_creation_create(self, e):
        return view_confirm_creation_create_(self, e)
        
    @cr2e
    def view_picture(self, e):
        username = e.context.name
        _size = e.context.size # Not used so far
        data_format = e.context.data_format
        assert data_format == 'jpg'
        u = self.user_db.users[username]
        picture_data = u.get_picture_jpg()
        if picture_data is None:
            url = e.root + '/static/nopicture.jpg'
            raise HTTPFound(url)
        else: 
            mime = get_mime_for_format(data_format)
            data = picture_data 
            return response_data(request=e.request, data=data, content_type=mime)
        
    @cr2e
    def view_thing(self, e):
        url = e.request.url
        if not url.endswith('/'):
            url += '/'
        url2 = url + 'views/syntax/'
        logger.debug('Redirect to  ' + url2)
        raise HTTPFound(url2)
    
    def _get_changes(self, e):
        def shelf_privilege(repo_name, sname, privilege):
            repo = e.session.repos[repo_name]
            if not sname in repo.shelves:
                msg = 'Cannot find shelf "%s" in repo "%s".' % (sname, repo_name)
                msg += '\n available: ' + format_list(repo.shelves)
                raise ValueError(msg)
            acl = repo.shelves[sname].get_acl()
            return acl.allowed2(privilege, e.user)
        
        def shelf_subscribed(repo_name, shelf_name):# @UnusedVariable
            return shelf_name in e.user.subscriptions # XXX

        changes = []
        for id_repo, repo in self.repos.items():   
            for change in repo.get_changes():
                
                if not shelf_privilege(id_repo, change['shelf_name'], Privileges.READ):
                    continue
                
                change['repo_name'] = id_repo
                a = change['author']
                if a in e.session.app.user_db:
                    u = e.session.app.user_db[a]
                else:
                    #logger.debug('Cannot find user %r' % a )
                    u = e.session.app.user_db.get_unknown_user_struct(a).info
                    
                change['user'] = u
                p = '{root}/repos/{repo_name}/shelves/{shelf_name}/libraries/{library_name}/{spec_name}/{thing_name}/views/syntax/'
                
                subscribed = shelf_subscribed(id_repo, change['shelf_name'])
                
                if change['exists'] and subscribed:
                    change['url'] = p.format(root=e.root, **change)
                else:
                    change['url'] = None
 
                
                #print('change: %s url = %s' % (change, change['url']))
                change['date_human'] =  datetime.datetime.fromtimestamp(change['date']).strftime('%b %d, %H:%M')
                changes.append(change)

        return changes

    @add_std_vars_context
    @cr2e
    def view_changes(self, e):
        return {
            'changes': self._get_changes(e),
        } 

    @add_std_vars_context
    @cr2e
    def view_not_found_generic(self, e):
        e.request.response.status = 404
        res = {
            'context_detail': context_display_in_detail(e.context)
        }
        return res

    @add_std_vars_context
    @cr2e
    def view_users(self, e):  # @UnusedVariable
        return {}
    
    @add_std_vars_context
    @cr2e
    def view_users_user(self, e): # @UnusedVariable
        return {}

    @add_std_vars_context
    @cr2e
    def view_thing_delete(self, e):
        name = e.thing_name
        basename = "%s.%s" % (name, e.spec.extension)
        logger.error('Deleting %s' % basename)
        filename = e.library.delete_file(basename)
        e.session.notify_deleted_file(e.shelf_name, e.library_name, filename)
        raise HTTPFound(e.request.referrer)


def serve_robots(request):  # @UnusedVariable
    body = "User-agent: *\nDisallow:"
    return Response(content_type='text/plain', body=body)

def get_url_library(e, shelf_name, library_name):
    url = '{root}/repos/{repo_name}/shelves/{shelf_name}/libraries/{library_name}'
    url = url.format(root=e.root, shelf_name=shelf_name, repo_name=e.repo_name, library_name=library_name)
    return url

class MCDPWeb(QuickAppBase):
    """ Runs the MCDP web interface. """

    def define_program_options(self, params):
        describe_mcdpweb_params(params)
        
    def go(self):
        options = self.get_options()
        
        if options.config is not None:
            logger.info('Reading configuration from %s' % options.config)
            logger.warn('Other options from command line will be ignored. ')
            parser = RawConfigParser()
            parser.read(options.config)
            sections = parser.sections()
            logger.info('sections: %s' % sections)
            s = 'app:main'
            if not s in sections:
                msg = 'Could not find section "%s": available are %s.' % (s, format_list(sections))
                msg += '\n file %s' % options.config
                raise Exception(msg) # XXX
            settings = dict((k, parser.get(s, k)) for k in parser.options(s))
            
            prefix = 'mcdp_web.'
            mcdp_web_settings = get_only_prefixed(settings, prefix, delete=True)
#             mcdp_web_settings = {}
#             for k,v in list(settings.items()):
#                 if k.startswith(prefix):
#                     mcdp_web_settings[k[len(prefix):]] = v
#                     del settings[k]
            options = parse_mcdpweb_params_from_dict(mcdp_web_settings)
            
            logger.debug('Using these options: %s' % options)
        else:
            logger.info('No configuration .ini specified (use --config).')   
            settings = {}

        wa = WebApp(options, settings=settings)
        msg = """Welcome to PyMCDP!
        
To access the interface, open your browser at the address
    
    http://127.0.0.1:%s/
    
Use Chrome, Firefox, or Opera - Internet Explorer is not supported.
""" % options.port

        if options.delete_cache:
            logger.info('Deleting cache...')
            #wa._refresh_library(None)
        logger.info(msg)
        wa.serve(port=options.port)

def get_only_prefixed(settings, prefix, delete=False):
    res = {}
    for k, v in list(settings.items()):
        if k.startswith(prefix):
            k2 = k[len(prefix):]
            res[k2]= v
            if delete:
                del settings[k]
    return res
            
def app_factory(global_config, **settings0):  # @UnusedVariable
    settings = get_only_prefixed(settings0, 'mcdp_web.', delete=True)
    #print('app_factory settings %s' % settings)
    options = parse_mcdpweb_params_from_dict(settings)
    wa = WebApp(options, settings=settings0)
    app = wa.get_app()
    return app

mcdp_web_main = MCDPWeb.get_sys_main()

