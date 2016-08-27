try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

version = '0.0.1'
packages = ['aschedule']
install_requires = [
    'nose',
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
    'name': 'aschedule'
}

setup(**config)
