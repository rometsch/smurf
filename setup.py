#!/usr/bin/env python3
from setuptools import setup, find_namespace_packages

setup(
    name="smurf",
    version="0.1",
    description="Simulation Management using Unique Resource Fingerprints",
    author="Thomas Rometsch",
    author_email="thomas.rometsch@uni-tuebingen.de",
    url="https://github.com/rometsch/smurf",
    package_dir={'': 'src'},
    package_data = { "" : ["*.sh", "shell*"] },
    packages=find_namespace_packages(where="src"),
    install_requires=[
        'argcomplete',
    ],
    zip_safe=False,
    entry_points = {
        'console_scripts': ['smurf=smurf._command_line_:main'],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Operating System :: Unix",
        "Topic :: Scientific/Engineering :: Physics",
        "Topic :: Utilities"
    ],
    python_requires='>=3.6',
)
