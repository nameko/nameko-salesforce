#!/usr/bin/env python
from setuptools import find_packages, setup

setup(
    name='nameko-salesforce',
    version='1.0.1',
    description=(
        'Nameko extension for easy communication with Salesforce '
        '(Including Streaming API)'
    ),
    author='Student.com',
    url='http://github.com/iky/nameko-salesforce',
    packages=find_packages(exclude=['test', 'test.*']),
    install_requires=[
        "cachetools==2.0.0",
        "nameko>=2.5.1",
        "nameko-bayeux-client==0.0.1",
        "redis==2.10.5",
        "simple-salesforce==0.72.2",
    ],
    extras_require={
        'dev': [
            "coverage==4.3.4",
            "flake8==3.3.0",
            "pylint==1.7.1",
            "pytest==3.0.6",
            "requests-mock==1.3.0",
        ],
        'docs': [
            'Sphinx==1.6.2',
            'sphinx-rtd-theme==0.2.4',
        ],
    },
    dependency_links=[],
    zip_safe=True,
    license='Apache License, Version 2.0',
    classifiers=[
        "Programming Language :: Python",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Intended Audience :: Developers",
    ]
)
