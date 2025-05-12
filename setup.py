#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Setup script for Core Banking System package.
"""

import os
from setuptools import setup, find_packages

# Get the long description from the README file
with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Package metadata
setup(
    name="core-banking-system",
    version="1.0.0",
    description="A Core Banking System implementation in Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="CBS Team",
    author_email="example@example.com",
    url="https://github.com/your-username/CBS-python",
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business :: Financial",
        "Topic :: Software Development :: Libraries",
    ],
    python_requires=">=3.9",
    packages=find_packages(exclude=["tests", "tests.*"]),
    package_data={
        "": ["*.yaml", "*.json", "*.sql"],
    },
    include_package_data=True,
    install_requires=[
        "fastapi>=0.100.0",
        "flask>=2.3.0",
        "sqlalchemy>=2.0.0",
        "pydantic>=2.0.0",
        "cryptography>=41.0.0",
        "PyYAML>=6.0",
        "python-dotenv>=1.0.0",
        "requests>=2.30.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "isort>=5.10.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "gui": ["PyQt5>=5.15.0"],
        "postgresql": ["psycopg2-binary>=2.9.0"],
        "mysql": ["mysql-connector-python>=8.0.0"],
    },
    entry_points={
        "console_scripts": [
            "cbs=app.bin.cli:main",
        ],
    },
    zip_safe=False,
)
