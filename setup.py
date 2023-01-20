#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
:copyright: (c) 2020 Raul Gomis
:license: MIT, see LICENSE for more details.
"""
import io
import os

from setuptools import setup, find_packages, Command

# Package meta-data.
NAME = 'semversioner'
DESCRIPTION = 'Manage properly semver in your repository'
URL = 'https://github.com/raulgomis/semversioner'
EMAIL = 'raulgomis@gmail.com'
AUTHOR = 'Raul Gomis'
REQUIRES_PYTHON = '>=3.7.0'
VERSION = None
REQUIRED = [
    'click>=8.0.0',
    'jinja2>=3.0.0',
    'packaging>=21.0'
]

here = os.path.abspath(os.path.dirname(__file__))

readme = DESCRIPTION

with io.open(os.path.join(here, "README.md"), "rt", encoding="utf8") as f:
    readme = f.read()

with io.open(os.path.join(here, "CHANGELOG.md"), "rt", encoding="utf8") as f:
    changelog = f.read()

# Load the package's __version__.py module as a dictionary.
if not VERSION:
    with open(os.path.join(here, 'semversioner', '__version__.py')) as f:
        about = {}
        exec(f.read(), about)
        VERSION = about['__version__']

# # Load the package's __version__.py module as a dictionary.
# if not VERSION:
#     with open(os.path.join(here, 'semversioner', '__init__.py')) as f:
#         VERSION = (
#             re.compile(r""".*__version__ = ["'](.*?)['"]""", re.S).match(f.read()).group(1)
#         )


class CleanCommand(Command):
    """Custom clean command to tidy up the project root."""
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        os.system('rm -vrf ./build ./dist ./*.pyc ./*.egg-info')


setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=u"\n\n".join([readme, changelog]),
    long_description_content_type='text/markdown',
    tests_require=['nose'],
    url=URL,
    author=AUTHOR,
    author_email=EMAIL,
    license='MIT',
    packages=find_packages(exclude=('tests',)),
    python_requires=REQUIRES_PYTHON,

    entry_points={
        'console_scripts': [
            'semversioner = semversioner.cli:main'
        ]
    },

    install_requires=REQUIRED,

    classifiers=[
        'Development Status :: 4 - Beta',

        'Environment :: Console',

        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',

        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Operating System :: OS Independent',
    ],

    cmdclass={
        'clean': CleanCommand,
    }
)
