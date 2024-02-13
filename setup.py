#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

# I used the following resources to compile the packaging boilerplate:
# https://python-packaging.readthedocs.io/en/latest/
# https://packaging.python.org/distributing/#requirements-for-packaging-and-distributing

from setuptools import find_packages, setup

def readme():
    with open('README.md') as f:
        return f.read()


setup(name='gold-standard',
      version='0.2.0',
      description='This package contains scripts used in creating or testing '
                  'the corpus.',
      long_description=readme(),
      url='https://github.com/ELTE-DH/gold-standard',
      author='Andrea Dömötör, Dávid Márk Nemeskey',
      license='LGPL',
      classifiers=[
          # How mature is this project? Common values are
          #   3 - Alpha
          #   4 - Beta
          #   5 - Production/Stable
          'Development Status :: 3 - Alpha',

          # Indicate who your project is intended for
          'Intended Audience :: Science/Research',
          'Topic :: Scientific/Engineering :: Information Analysis',
          # This one is not in the list...
          'Topic :: Scientific/Engineering :: Natural Language Processing',

          # Environment
          'Operating System :: POSIX :: Linux',
          'Environment :: Console',
          'Natural Language :: English',

          # Pick your license as you wish (should match "license" above)
          'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',

          # Specify the Python versions you support here. In particular, ensure
          # that you indicate whether you support Python 2, Python 3 or both.
          'Programming Language :: Python :: 3.10',
      ],
      keywords='gold standard corpus hungarian',
      packages=find_packages(exclude=['scripts']),
      # Install the scripts
      scripts=[
          'scripts/xml_to_spacy.py',
      ],
      install_requires=[
          'spacy',
          'tqdm',
      ],
      # zip_safe=False,
      use_2to3=False)
