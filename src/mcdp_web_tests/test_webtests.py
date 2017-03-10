import os
import unittest
import urlparse

from git import Repo

from mcdp.constants import MCDPConstants
from mcdp_library_tests.create_mockups import write_hierarchy
from mcdp_repo.repo_interface import repo_commit_all_changes
from mcdp_user_db import UserDB
from mcdp_utils_misc import tmpdir
# from mcdp_utils_xml import bs
from mcdp_web.confi import parse_mcdpweb_params_from_dict
from mcdp_web.main import WebApp


def create_empty_repo(d, bname):
    repo0 = Repo.init(d)
    filename = os.path.join(d, 'readme.txt')
    
    open(filename, 'wb').close()
    repo0.index.add([filename])
    repo0.index.commit("Adding "+filename+ "to repo")

    new_branch = repo0.create_head(bname)
    new_branch.checkout()
    fn = os.path.join(d, 'readme')
    with open(fn, 'w') as f:
        f.write('ciao')
    repo0.index.add([fn])
    repo0.index.commit('msg')
    return repo0

def create_user_db_repo(where, bname):
    user_db_skeleton = {
        'anonymous.%s' % MCDPConstants.user_extension: {
            MCDPConstants.user_desc_file: '''
            name: Anonymous user
            ''',
        }
    }
    repo0 = create_empty_repo(where, bname)
    write_hierarchy(where, user_db_skeleton)
    repo_commit_all_changes(repo0)
    # checks that it use well formed
    UserDB(where)


class FunctionalTests(unittest.TestCase):
    def setUp(self):
        from webtest import TestApp
        
        with tmpdir(erase=False) as d:
            # create a db
            bname = 'master'
            userdb_remote = os.path.join(d, 'userdb_remote')
            create_user_db_repo(userdb_remote, bname)
           
            userdb = os.path.join(d, 'userdb')
            repo = Repo.init(userdb)
            origin = repo.create_remote('origin', url=userdb_remote)
            origin.fetch()

            head = repo.create_head(bname, origin.refs[bname])
            head.set_tracking_branch(origin.refs[bname])  # set local "master" to track remote "master
            head.checkout()
            settings = {
                'users': userdb,
                'load_mcdp_data': '0',
            }
            options = parse_mcdpweb_params_from_dict(settings)
            wa = WebApp(options)
            app = wa.get_app()
            self.testapp = TestApp(app)

    def test_tree(self):
        url_start = '/tree/'
        res = self.testapp.get(url_start, status=200)
#         if '302' in res.status:
#             res = res.follow()
        html = res.body
        frag = res.html
        tocheck = []
        url_base =url_start
        print('url_base: %s' % url_base)
        for a in frag.select('a[href]'):
            href = a['href']
            if 'exit' in href:
                continue
            url = urlparse.urljoin(url_base, href)
            tocheck.append(url)
            
        for url in tocheck: 
            print('getting url %s' % url)
            r = self.testapp.get(url)
            r = r.maybe_follow()
            print('%s %s' % (r.status, url))
            
        
        
        
        