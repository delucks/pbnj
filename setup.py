#!/usr/bin/env python
from setuptools import setup
import sys

sys.path.extend('.')
from pbnj import __version__

test_requirements = ['pytest>=2.8.0', 'pytest-cov']

setup(
    name = 'pbnj',
    packages = ['pbnj'],
    version = __version__,
    description = 'an IRC bot library and framework, focused on simplicity and portability',
    author = 'James Luck',
    author_email = 'me@jamesluck.com',
    license='GNU GPLv3',
    url = 'https://github.com/delucks/pbnj',
    download_url = 'https://github.com/delucks/pbnj/tarball/v{}'.format(__version__),
    tests_requirements=test_requirements,
    keywords = ['irc', 'chatbot', 'bot', 'portable', 'framework'],
    classifiers = [],
)
