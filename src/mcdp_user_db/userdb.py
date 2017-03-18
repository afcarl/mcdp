import os
import yaml
from mcdp_user_db.user import userinfo_from_yaml, yaml_from_userinfo
from mcdp.logs import logger
from mcdp_utils_misc import locate_files
from mcdp import MCDPConstants
from contracts.utils import raise_desc
from mcdp_utils_misc.string_utils import format_list


__all__ = ['UserDB']

class UserDB():

    def __init__(self, userdir):
        
        self.users = {}
        us = load_users(userdir)
        self.userdir = userdir
        self.users.update(us)
        
        from mcdp_shelf.access import USER_ANONYMOUS
        if not USER_ANONYMOUS in self.users:
            msg = 'Need account for the anonymous user "%s".' % USER_ANONYMOUS
            raise_desc(ValueError, msg, found=self.users)
            
        
    def __contains__(self, key):
        return key in self.users
    
    def best_match(self, username, name, email):
        if username in self.users:
            return self.users[username]
        for u in self.users.values():
            if u.name == name:
                return u
            if u.email == email:
                return u
        return None
    
    def __getitem__(self, key):
        if key is None:
            key = 'anonymous'
        return self.users[key]
    
    def exists(self, login):
        return login in self
    
    def authenticate(self, login, password):
        user = self.users[login]
        return password == user.password
    
    def save_user(self, username, new_user=False):
        userdir = os.path.join(self.userdir, username + '.' + MCDPConstants.user_extension)
        if not os.path.exists(userdir):
            if new_user:
                os.makedirs(userdir)
            else:
                msg = 'Could not find user dir %r.' % userdir
                raise ValueError(msg)

        filename = os.path.join(userdir,  MCDPConstants.user_desc_file)
        if not os.path.exists(filename) and not new_user:
            msg = 'Could not find user filename %r.' % filename
            raise ValueError(msg)
        user = self.users[username]
        y = yaml_from_userinfo(user)
        s = yaml.dump(y)
        logger.info('Saving %r:\n%s' % (username, s))
        with open(filename, 'w') as f:
            f.write(s)
            
        if user.picture is not None:            
            fn = os.path.join(userdir, MCDPConstants.user_image_file)
            with open(fn, 'wb') as f:
                f.write(user.picture)
        
def load_users(userdir):
    ''' Returns a dictionary of username -> User profile '''
    users = {}
    
    exists = os.path.exists(userdir) 
    if not exists:
        msg = 'Directory %s does not exist' % userdir
        raise Exception(msg)
        
    assert exists
        
    l = locate_files(userdir, 
                     pattern='*.%s' % MCDPConstants.user_extension, 
                     followlinks=True,
                     include_directories=True,
                     include_files=False)
    
    for userd in l:
        username = os.path.splitext(os.path.basename(userd))[0]
        info = os.path.join(userd, MCDPConstants.user_desc_file)
        if not os.path.exists(info):
            msg = 'Info file %s does not exist.'  % info
            raise Exception(msg)
        data = open(info).read()
        s = yaml.load(data)
        
        users[username] = userinfo_from_yaml(s, username)
        
        f = os.path.join(userd, MCDPConstants.user_image_file)
        if os.path.exists(f):
            users[username].picture = open(f, 'rb').read()
        
    if not users:
        msg = 'Could not load any user from %r' % userdir
        raise Exception(msg)
    else:
        logger.info('loaded users: %s.' % format_list(sorted(users)))
        
    return users
        