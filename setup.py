#!/usr/bin/env python3
import os
from setuptools import setup, find_namespace_packages

setup(  name="smurf"
        ,version="0.1"
        ,description="scripts to handle simulations"
        ,author="Thomas Rometsch"
        ,package_dir={'': 'src'}
        ,package_data = { "" : ["*.sh", ".shell*"] }
        ,packages=find_namespace_packages(where="src")
        ,install_requires=[
          'argcomplete',
        ]
        ,zip_safe=False
        ,entry_points = {
            'console_scripts': ['smurf=smurf._command_line_:main'],
        }
)
