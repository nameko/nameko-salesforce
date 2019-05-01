#!/usr/bin/env python
from setuptools import find_packages, setup


setup(
    name="nameko-salesforce",
    version="1.2.0",
    description=(
        "Nameko extension for easy communication with Salesforce "
        "(Including Streaming API)"
    ),
    long_description=open("README.rst").read(),
    author="Student.com",
    author_email="ondrej.kohout@gmail.com",
    url="http://github.com/nameko/nameko-salesforce",
    packages=find_packages(exclude=["test", "test.*"]),
    install_requires=[
        "cachetools",
        "nameko>=2.8.5",
        "nameko-bayeux-client",
        "redis",
        "simple-salesforce>=0.72.2",
    ],
    extras_require={
        "dev": ["coverage", "pre-commit", "pylint", "pytest", "requests-mock"],
        "docs": ["Sphinx", "sphinx-rtd-theme"],
    },
    dependency_links=[],
    zip_safe=True,
    license="Apache License, Version 2.0",
    classifiers=[
        "Programming Language :: Python",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Intended Audience :: Developers",
    ],
)
