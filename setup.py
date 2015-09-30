#!/usr/bin/python3

from os import path
from setuptools import setup
import sys

if sys.version_info < (3,):
    print("Python >= 3.0 required, found " + sys.version)
    sys.exit(1)

here = path.abspath(path.dirname(__file__))

# *If* I even ever upload it to pypi, it should probably still have the same
# description there as on Github.
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="yaamatic",
    version="0.0.1",
    author='Jan Hudec',
    author_email='bulb@ucw.cz',
    description="Tool for converting Yasim(-like) flight dynamic models to JSBSim ones.",
    license='GPL-2+',
    url='https://github.com/jan-hudec/yaamatic',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Games/Entertainment :: Simulation',
        'Topic :: Scientific/Engineering :: Physics',
        ],
    keywords='flightgear jsbsim fdm flight dynamics model',

    packages=['yaamatic'],
    package_data={
        '': ['*.genshi'],
        },
    entry_points={
        'console_scripts': ['yaamatic = yaamatic:main'],
        'setuptools.installation': ['eggsecutable = yaamatic:main'],
        },

    install_requires=[
        'Genshi >= 0.7',
        'Pint >= 0.6',
        ],
    )
