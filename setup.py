import os
import sys

from setuptools import find_packages, setup
from setuptools.command.install import install

NAME = "renishawWiRE"
VERSION = "0.1.5"
DESCRIPTION = open("README.md", encoding="utf-8").read()


class VerifyVersionCommand(install):
    """Custom command to verify that the git tag matches our version"""

    description = "verify that the git tag matches our version"

    def run(self):
        tag = os.getenv("CIRCLE_TAG")

        if tag != VERSION:
            info = "Git tag: {0} does not match the version of this app: {1}".format(
                tag, VERSION)
            sys.exit(info)


setup(
    name=NAME,
    version=VERSION,
    packages=find_packages(exclude=["tests"]),
    url="https://github.com/alchem0x2A/py-wdf-reader",
    # project_urls={
        # "Changelog": ("https://github.com/pennlabs/github-project/blob/master/CHANGELOG.md")
    # },
    license="MIT",
    author="alchem0x2A",
    author_email="tian.tian@chem.ethz.ch",
    description="Reading wdf Raman spectroscopy file from Renishaw WiRE",
    long_description=DESCRIPTION,
    long_description_content_type="text/markdown",
    install_requires=["numpy>=1.12.0"],
    extras_require={
        "image": ["Pillow>=3.4.0"],
        "plot":  ["Pillow>=3.4.0",
                  "matplotlib>=2.1.0"],
    },
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    python_requires=">=3.6",
    cmdclass={"verify": VerifyVersionCommand},
)
