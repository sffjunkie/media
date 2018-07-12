# Copyright (c) 2015 Simon Kennedy <sffjunkie+code@gmail.com>

from setuptools import setup

setup(name='mogul.media',
    version="0.1",
    description="""mogul.media is a small library to manipulate media files.""",
#    long_description=open('README.txt').read(),
    author='Simon Kennedy',
    author_email='code@sffjunkie.co.uk',
    url="http://www.sffjunkie.co.uk/python-mogul.html",
    license='Apache-2.0',
    
    package_dir={'': 'src'},
    packages=['mogul.media'],
    namespace_packages=['mogul',],
)
