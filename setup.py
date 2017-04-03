#!/usr/bin/env python
from setuptools import setup

setup(
    name='nameko-salesforce',
    version='0.0.1',
    description=(
        'Nameko extension for easy communication with Salesforce '
        '(Including Streaming API)'
    ),
    author='Student.com',
    url='http://github.com/iky/nameko-salesforce',
    py_modules=['nameko_salesforce'],
    install_requires=[
        "nameko>=2.5.1",
    ],
    extras_require={
        'dev': [
            "coverage==4.3.4",
            "flake8==3.2.1",
            "pylint==1.6.5",
            "pytest==3.0.6",
            "redis==2.10.5",
            "requests-mock==1.3.0",
            "simple-salesforce==0.72.2",
        ]
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
