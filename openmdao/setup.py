from setuptools import setup, find_packages
import os

setup(name='openmdao',
      version='0.1',
      description="",
      long_description="",
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='',
      author='',
      author_email='',
      url='',
      license='NOSA',
      #packages=find_packages(exclude=['ez_setup']),
      #namespace_packages=['openmdao'],
      namespace_packages=[],
      packages = [],
      #py_modules = ['nothing'],
      zip_safe=False,
      install_requires=[
          'setuptools',
          'openmdao.lib',
          'openmdao.test',
          'openmdao.recipes',
      ],
      entry_points={
      },
      )
