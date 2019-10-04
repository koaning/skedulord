import os
from setuptools import setup, find_packages

from skedulord import version


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


base_packages = ["Click==7.0"]

dev_packages = ["pip", "pytest-cov", "pytest", "flake8", "mkdocs"]

module_name = "skedulord"

setup(
    name=module_name,
    version=version,
    packages=find_packages(),
    long_description=read('readme.md'),
    install_requires=base_packages,
    entry_points={
        'console_scripts': [
            f'skedulord = skedulord.cli:main'
        ],
    },
    extras_require={
        "dev": dev_packages
    }
)
