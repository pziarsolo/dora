from pathlib import Path

import setuptools
from setuptools import find_packages

from dora import VersionManager

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

requirements = [line.strip() for line in open('requirements.txt')]
scripts = [str(f) for f in Path('./bin').glob('*.py')]

setuptools.setup(
    name="dora",
    version=VersionManager().get_file_version(),
    author="Peio Ziarsolo",
    author_email="pziarsolo@gmail.com",
    description="Small utilities to deal with NGS Seq mapping",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pziarsolo/dora",
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    scripts=scripts,
    license='MIT',
    packages=find_packages(exclude=("dora.tests",)),
    # package_dir={"": "dora", "dora": 'mapping'},
    # packages=setuptools.find_packages(where="."),
    python_requires=">=3.6",
)
