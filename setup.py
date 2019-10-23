import os
from setuptools import setup, find_packages

from skedulord import version


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


base_packages = ["Click>=7.0", "prettytable>=0.7.2", "Flask>=1.0.3",
                 "Flask-Cors>=3.0.8", "waitress>=1.3.0", "PyYAML>=5.1.1"]

dev_packages = ["pytest", "pytest-cov"]


setup(
    name="skedulord",
    version=version,
    packages=find_packages(),
    long_description=read('readme.md'),
    long_description_content_type='text/markdown',
    url="https://koaning.github.io/skedulord/",
    author='Vincent D. Warmerdam',
    install_requires=base_packages,
    entry_points={
        'console_scripts': [
            f'lord = skedulord.cli:main'
        ],
    },
    extras_require={
        "dev": dev_packages
    },
    classifiers=['Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3.6',
                 'Programming Language :: Python :: 3.7',
                 'License :: OSI Approved :: MIT License',]
)