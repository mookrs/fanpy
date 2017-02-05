import re
from setuptools import setup

install_requires = []

tests_require = ['nose']

with open('fanpy/__init__.py', 'r') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        fd.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError('Cannot find version information')

setup(
    name='fanpy',
    version=version,
    description='An API and cli toolset for Fanfou.com',
    long_description=open('README.md').read(),
    keywords='fanfou, cli',
    author='mookrs',
    author_email='mookrs+fanpy@gmail.com',
    url='https://github.com/mookrs/fanpy',
    packages=['fanpy'],
    license='MIT',
    install_requires=install_requires,
    tests_require=tests_require,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'Natural Language :: English',
        'Natural Language :: Chinese (Simplified)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Communications :: Chat :: Internet Relay Chat',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content :: CGI Tools/Libraries',
        'Topic :: Utilities',
        'License :: OSI Approved :: MIT License',
    ],
    entry_points={
        'console_scripts': [
            'fanpy=fanpy.cli:main',
            'fanpy-log=fanpy.logger:main',
            'fanpy-archiver=fanpy.archiver:main',
        ],
    }
)
