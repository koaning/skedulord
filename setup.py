import os
from setuptools import setup, find_packages

from skedulord import __version__


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


base_packages = ["PyYAML>=5.1.1", "rich>=9.10.0", "clumper>=0.2.8"]

dev_packages = ["pytest", "pytest-cov"]


setup(
    name="skedulord",
    version=__version__,
    packages=find_packages(),
    long_description=read('readme.md'),
    long_description_content_type='text/markdown',
    url="https://koaning.github.io/skedulord/",
    author='Vincent D. Warmerdam',
    install_requires=base_packages,
    entry_points={
        'console_scripts': [
            'lord = skedulord.__main__:main'
        ],
    },
    extras_require={
        "dev": dev_packages
    },
    classifiers=['Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3.6',
                 'Programming Language :: Python :: 3.7',
                 'License :: OSI Approved :: MIT License']
)
