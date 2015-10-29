import os
from setuptools import setup, find_packages

def get_version(filename):
    import ast
    version = None
    with file(filename) as f:
        for line in f:
            if line.startswith('__version__'):
                version = ast.parse(line).body[0].value.s
                break
        else:
            raise ValueError('No version found in %r.' % filename)
    if version is None:
        raise ValueError(filename)
    return version

version = get_version(filename='src/mocdp/__init__.py')

setup(name='PyMCDP',
      url='http://github.com/AndreaCensi/mcdp',
      description='Interpreter and solver for Monotone Co-Design Problems',
      long_description='',
      package_data={'':['*.*', '*.mcdp', '*.cdp', '*.png']},
      keywords="Optimization",
      license="MIT",
      classifiers=[
        'Development Status :: 4 - Beta',
      ],
      version=version,

      download_url=
        'http://github.com/AndreaCensi/mcdp/tarball/%s' % version,

      package_dir={'':'src'},
      packages=find_packages('src'),
      install_requires=[
        'ConfTools>=1.0,<2',
        'PyContracts>=1.2,<2',
        'quickapp', 
        'reprep',
        'gvgen',
        'pint',
        'watchdog',
        'networkx',
      ],

      tests_require=[
        'nose>=1.1.2,<2',
        'comptests',
        'compmake',
      ],

      entry_points={
         'console_scripts': [
            'mcdp_plot = cdpview:mcdp_plot_main',
            'mcdp_solve = cdpview:mcdp_solve_main',
        ]
      }
)

