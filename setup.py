#!/usr/bin/env python3
"""
Setup script for the autoimmune disease journal scraper.
"""

from setuptools import setup, find_packages
import os

# Read README for long description
def read_readme():
    try:
        with open("README.md", "r", encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        return "Autoimmune Disease Journal Scraper"

# Read requirements
def read_requirements():
    try:
        with open("requirements.txt", "r", encoding="utf-8") as fh:
            return [line.strip() for line in fh if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        return [
            "requests>=2.31.0",
            "pandas>=2.0.3",
            "beautifulsoup4>=4.12.2",
            "lxml>=4.9.3",
            "python-dateutil>=2.8.2",
            "tqdm>=4.65.0"
        ]

setup(
    name="autoimmune-journal-scraper",
    version="1.0.0",
    author="Autoimmune Research Team",
    author_email="researcher@example.com",
    description="A functional programming approach to scraping autoimmune disease papers from academic journals",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/autoimmune-journal-scraper",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.1",
            "pytest-mock>=3.11.1",
            "black>=23.7.0",
            "flake8>=6.0.0",
            "mypy>=1.5.1",
        ],
        "async": [
            "aiohttp>=3.8.5",
            "asyncio>=3.4.3",
        ],
    },
    entry_points={
        "console_scripts": [
            "autoimmune-scraper=src.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.yml", "*.yaml"],
    },
    zip_safe=False,
    keywords="autoimmune disease research papers scraping pubmed openalex functional-programming",
    project_urls={
        "Bug Reports": "https://github.com/your-username/autoimmune-journal-scraper/issues",
        "Source": "https://github.com/your-username/autoimmune-journal-scraper",
        "Documentation": "https://github.com/your-username/autoimmune-journal-scraper/blob/main/README.md",
    },
) 