#!/usr/bin/env python
from setuptools import find_packages, setup

setup(
    name='nameko-salesforce',
    version='1.2.0',
    description=(
        'Nameko extension for easy communication with Salesforce '
        '(Including Streaming API)'
    ),
    long_description=open('README.rst').read(),
    author='Student.com',
    author_email='wearehiring@student.com',
    url='http://github.com/Overseas-Student-Living/nameko-salesforce',
    packages=find_packages(exclude=['test', 'test.*']),
    install_requires=[
        "cachetools==2.0.0",
        "nameko>=2.5.1",
        "nameko-bayeux-client==1.0.0",
        "redis==2.10.5",
        "simple-salesforce==0.72.2",
    ],
    extras_require={
        'dev': [
            "coverage==4.3.4",
            "flake8==3.3.0",
            "pylint==1.8.2",
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
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Intended Audience :: Developers",
    ]
)
