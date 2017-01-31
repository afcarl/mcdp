import os

import pyramid
from pyramid.httpexceptions import HTTPFound
from pyramid.security import remember, forget

from mocdp import logger
from collections import namedtuple
import yaml


USERS = {}

GROUPS = {'editor': ['group:editors']}

UserInfo = namedtuple('UserInfo', 
                      ['username', 
                       'name',
                       'password',
                       'email',
                       'gravatar40',
                       'gravatar20',
                       ])

def load_users(userdir):
    if not os.path.exists(userdir):
        msg = 'Directory %s does not exist' % userdir
        Exception(msg)
    for user in os.listdir(userdir):
        if user.startswith('.'):
            continue
        info = os.path.join(userdir, user, 'user.yaml')
        if not os.path.exists(info):
            msg = 'Info file %s does not exist.'  % info
            raise Exception(msg)
        data = open(info).read()
        s = yaml.load(data)
        
        res = {}
        res['username'] = user
        res['name'] = s['name']
        res['password'] = s['password']
        res['email'] = s['email']
        default = "https://www.example.com/default.jpg"
        
        res['gravatar40'] = gravatar(s['email'], default=default, size=40)
        res['gravatar20'] = gravatar(s['email'], default=default, size=20)
        struct = UserInfo(**res)
        USERS[user] = struct
        
    print USERS
        
def gravatar(email, default, size):
    # import code for encoding urls and generating md5 hashes
    import urllib, hashlib
    gravatar_url = "https://www.gravatar.com/avatar/" + hashlib.md5(email.lower()).hexdigest() + "?"
    gravatar_url += urllib.urlencode({'d':default, 's':str(size)})
    return gravatar_url

URL_LOGIN = '/login/'

class AppLogin():
    def config(self, config):
        config.add_route('login', URL_LOGIN)
        config.add_view(self.login, route_name='login', renderer='login.jinja2',
                        permission=pyramid.security.NO_PERMISSION_REQUIRED)

        config.add_route('logout', '/logout')
        config.add_view(self.logout, route_name='logout', renderer='logout.jinja2',
                         permission=pyramid.security.NO_PERMISSION_REQUIRED)

        config.add_forbidden_view(self.view_forbidden, renderer='forbidden.jinja2')
        
        load_users(self.options.users)
        
    def view_forbidden(self, request):
        logger.error(request.url)
        logger.error(request.referrer)
        logger.error(request.exception.message)
        logger.error(request.exception.result)
        request.response.status = 403
        res = {}
        res['message'] = request.exception.message
        res['result'] = request.exception.result
        
        # path_qs The path of the request, without host but with query string
        res['came_from'] = request.path_qs
        res['referrer'] = request.referrer
        res['login_form'] = self.make_relative(request, URL_LOGIN)
        res['root'] =  self.get_root_relative_to_here(request)
        
        print res
        return res


    def login(self, request): 
#         login_url = request.route_url('login')
#         referrer = request.url
#         if referrer == login_url:
#             referrer = '/'  # never use login form itself as came_from
        came_from = request.params['came_from']
        print('came_from: %r' % came_from)
        message = ''
        error = ''
        if 'form.submitted' in request.params:
            login = request.params['login']
            password = request.params['password']
            if not login in USERS:
                error = 'Could not find user name "%s".' % login
            else:
                password_expected = USERS[login].password
                #if check_password(password, hashed):
                if password == password_expected:
                    headers = remember(request, login)
                    logger.info('successfully authenticated user %s' % login)
                    return HTTPFound(location=came_from, headers=headers)
                else:
                    error = 'Password does not match.'
            
        login_form = self.make_relative(request, URL_LOGIN)
        came_from = self.make_relative(request, came_from)
        return dict(
            name='Login',
            message=message,
            error=error,
            login_form=login_form,
            came_from=came_from,
        )

    def logout(self, request):
        headers = forget(request)
        came_from = request.referrer
        return HTTPFound(location=came_from, headers=headers)
# 
# def hash_password(pw):
#     pwhash = bcrypt.hashpw(pw.encode('utf8'), bcrypt.gensalt())
#     return pwhash.decode('utf8')
# 
# def check_password(pw, hashed_pw):
#     expected_hash = hashed_pw.encode('utf8')
#     return bcrypt.checkpw(pw.encode('utf8'), expected_hash)




def groupfinder(userid, request):  # @UnusedVariable
    if userid in USERS:
        return GROUPS.get(userid, [])
    
    