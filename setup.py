from pathlib import Path

import setuptools
from setuptools import find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()
exec(open('dora/__version__.py').read())

with open('dora/__version__.py') as fh:
    version = fh.readline().strip()

requirements = [line.strip() for line in open('requirements.txt')]
scripts = [str(f) for f in Path('./bin').glob('*.py')]

setuptools.setup(
    name="dora",
    version=version,
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
