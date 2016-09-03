try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

version = '0.0.2.dev0'
packages = ['aschedule']
install_requires = [
]
classifiers = [
    'Development Status :: 2 - Pre-Alpha',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Natural Language :: English',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: Implementation :: CPython',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Topic :: Utilities'
]

config = {
    'description': 'schedule your co-routines',
    'author': 'Srinivas Devaki',
    'url': 'https://gitlab.com/eightnoteight/aschedule',
    'download_url': 'https://gitlab.com/eightnoteight/aschedule/repository/archive.zip?ref=master',
    'author_email': 'mr.eightnoteight@gmail.com',
    'version': version,
    'install_requires': install_requires,
    'packages': packages,
    'scripts': [],
    'classifiers': classifiers,
    'name': 'aschedule'
}

setup(**config)
