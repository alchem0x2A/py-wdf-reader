import os
import sys

from setuptools import find_packages, setup

NAME = "renishawWiRE"
VERSION = "0.1.16"
DESCRIPTION = open("README.md", encoding="utf-8").read()


def verify_version():
    tag = os.getenv("GIT_TAG")
    if tag != VERSION:
        info = "Git tag: {0} does not match the version of this app: {1}".format(
            tag, VERSION
        )
        sys.exit(info)



if os.getenv("CI_VERIFY") is not None:
    verify_version()

setup(
    name=NAME,
    version=VERSION,
    packages=find_packages(exclude=["tests"]),
    url="https://github.com/alchem0x2A/py-wdf-reader",
    license="MIT",
    author="alchem0x2A",
    author_email="alchem0x2a@gmail.com",
    description="Reading wdf Raman spectroscopy file from Renishaw WiRE",
    long_description=DESCRIPTION,
    long_description_content_type="text/markdown",
    install_requires=["numpy>=1.12.0"],
    extras_require={
        "image": ["Pillow>=3.4.0"],
        "plot": ["Pillow>=3.4.0", "matplotlib>=2.1.0"],
    },
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    entry_points={
        "console_scripts": ["wdf-export=renishawWiRE.export:main"],
    },
    python_requires=">=3.6",
)
