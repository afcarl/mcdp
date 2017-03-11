from collections import OrderedDict
import os

from contracts import contract
from contracts.utils import raise_desc

from mcdp.logs import logger
from mcdp_library import Librarian
from mcdp_shelf import PRIVILEGE_DISCOVER, PRIVILEGE_READ, Shelf
from mcdp_utils_misc import natural_sorted
from mcdp_user_db.user import UserInfo


_ = Shelf

class Session():
    
    @contract(shelves_all='dict(str:$Shelf)')
    def __init__(self, app, request, shelves_all):
        ''' dirnames: list of directories where to find shelves '''
        self.app = app
        self.shelves_all = shelves_all
        self.request = request
        self.repos = app.repos
        
        self.librarian = Librarian()
        self.authenticated_userid = request.authenticated_userid
        self.recompute_available()

    def set_last_request(self, request):
        self.request = request
        if self.authenticated_userid != request.authenticated_userid:
            logger.debug('login/logout detected')
            self.authenticated_userid = request.authenticated_userid
            self.recompute_available()
    
    def _get_app(self):
        from mcdp_web.main import WebApp
        return WebApp.singleton
    
    def get_user(self, username=None):
        ''' Returns a UserInfo struct. It is the user 'anonymous' if no login was given.
        
            self.request.authenticated_userid == None == get_user().username == 'anonymous'
            
            
        '''
        userdb = self.app.user_db  # @UndefinedVariable
        if username is None:
            username = self.request.authenticated_userid 
        if username is not None:
            username = username.encode('utf8')
            if username in userdb:
                return userdb[username]
            else:
                return UserInfo(username, name=username, password=None, email=None, website=None, affiliation=None, 
                                groups=[], subscriptions=[])
        else:
            # username is None:
            return userdb['anonymous']
    
    def save_user(self):
        userdb = self.app.user_db  # @UndefinedVariable
        user = self.get_user()
        userdb.save_user(user.username)
        
    def notify_created_library(self, shelf_name, library_name):  # @UnusedVariable
        ''' Called when we just created the library. '''
        self.get_shelf(shelf_name).update_libraries()
        self.recompute_available()
        
    def notify_deleted_file(self, shelf_name, library_name, filename):  # @UnusedVariable
        self.get_shelf(shelf_name).update_libraries()
        self.recompute_available()
        
    def recompute_available(self):
        # all the ones we can discover
        self.shelves_available = OrderedDict()
        
        # the ones that are actually in use
        self.shelves_used = OrderedDict()
        user = self.get_user()
        for sname, shelf in self.shelves_all.items():
            if shelf.get_acl().allowed2(PRIVILEGE_DISCOVER, user):
                self.shelves_available[sname] = shelf
            else:
                #print('hiding shelf %r from %r' % (sname, user))
                print shelf.get_acl()
        
        #print('shelves all: %s' % list(self.shelves_all))
        #print('shelves available: %s' % list(self.shelves_available))

        for sname in user.get_subscriptions():
            if sname in self.shelves_available:
                shelf = self.shelves_available[sname]
                acl = shelf.get_acl()
                if acl.allowed2(PRIVILEGE_READ, user):
                    self.shelves_used[sname] = self.shelves_available[sname]
                else:
                    msg = 'User %r does not have %r for %r' % (user.username, PRIVILEGE_READ, sname)
                    msg += '\n%s' % acl
                    logger.error(msg)
            else:
                msg = 'Could not find shelf %r to which user %r is subscribed to.' % (sname, user.username)
                msg += '\n Available: %s' % list(self.shelves_available)
                logger.error(msg)

        #print('shelves used: %s' % list(self.shelves_used))
    
        self.librarian = Librarian()
        
        self.libname2shelfname = {}
        for sname, shelf in self.shelves_all.items():
            for libname in shelf.get_libraries_path():
                self.libname2shelfname[libname] = sname
                
        for sname, shelf in self.shelves_used.items():
            for libname, libpath in shelf.get_libraries_path().items():
                self.librarian.add_lib_by_path(libpath)                
                
        self.libraries = self.librarian.get_libraries()
        for _short, data in self.libraries.items():
            l = data['library']
            path = data['path']
            cache_dir = os.path.join(path, '_cached/mcdpweb_cache')
            l.use_cache_dir(cache_dir)
            
    def get_shelf_for_libname(self, libname):
        return self.libname2shelfname[libname]
    
    def get_shelf(self, shelfname):
        return self.shelves_all[shelfname]
    
    @contract(returns='list(str)')
    def list_libraries(self):
        """ Returns the list of libraries """
        return sorted(self.libraries) 

    def get_library(self, library_name): 
        if not library_name in self.libraries:
            msg = 'Could not find library %r.' % library_name
            raise_desc(ValueError, msg, available=self.libraries)
        return self.libraries[library_name]['library'] 

    def refresh_libraries(self):
        for l in [_['library'] for _ in self.libraries.values()]:
            l.delete_cache()

        from mcdp_report.gdc import get_images
        assert hasattr(get_images, 'cache')  # in case it changes later
        get_images.cache = {}
        
    def get_libraries_indexed_by_shelf(self):
        """
            returns a list of tuples (dirname, list(libname))
        """
        res = []
        for sname, shelf in self.shelves_used.items():
            libnames = natural_sorted(shelf.get_libraries_path())
            res.append((sname, libnames))
        return res 
    
    def get_shelves_used(self):
        ''' Returns an ordered dict of shelves '''
        return self.shelves_used
    
    def get_shelves_available(self):
        ''' Returns an ordered dict of shelves '''
        return self.shelves_available
    
    