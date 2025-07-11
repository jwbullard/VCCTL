#!/usr/bin/env python3
"""
Setup script for VCCTL GTK3 Application
"""

from setuptools import setup, find_packages
import os

# Read the contents of README.md for long description
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Read requirements from requirements.txt
with open(os.path.join(this_directory, 'requirements.txt'), encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="vcctl-gtk",
    version="1.0.0",
    author="NIST Building and Fire Research Laboratory",
    author_email="vcctl@nist.gov",
    description="Virtual Cement and Concrete Testing Laboratory - GTK3 Desktop Application",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nist/vcctl-gtk",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Chemistry",
        "Topic :: Scientific/Engineering :: Physics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Environment :: X11 Applications :: GTK",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ],
        "gui": [
            "cairo-cffi>=1.6.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "vcctl-gtk=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "app": ["resources/*"],
    },
    keywords="cement concrete materials simulation modeling GTK desktop scientific",
    project_urls={
        "Bug Reports": "https://github.com/nist/vcctl-gtk/issues",
        "Source": "https://github.com/nist/vcctl-gtk/",
        "Documentation": "https://vcctl.nist.gov/",
    },
)