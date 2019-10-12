import os
from setuptools import setup, find_packages

from skedulord import version


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


base_packages = ["Click==7.0", "flask", "flask_cors", "waitress", "pyyaml"]

dev_packages = ["pip", "pytest-cov", "pytest", "flake8", "mkdocs", "mkdocs-material"]

setup(
    name="skedulord",
    version=version,
    packages=find_packages(),
    long_description=read('readme.md'),
    install_requires=base_packages,
    entry_points={
        'console_scripts': [
            f'skedulord = skedulord.cli:main',
            f'lord = skedulord.cli:main'
        ],
    },
    extras_require={
        "dev": dev_packages
    }
)
