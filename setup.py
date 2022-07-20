import os.path as osp
import re
from setuptools import setup, find_packages


def find_version():
    with open(osp.join('foamgraph', '__init__.py')) as fp:
        for line in fp:
            m = re.search(r'^__version__ = "(\d+\.\d+\.\d[a-z]*\d*)"', line, re.M)
            if m is None:
                # could be a hotfix
                m = re.search(r'^__version__ = "(\d.){3}\d"', line, re.M)
            if m is not None:
                return m.group(1)
        raise RuntimeError("Unable to find version string.")


setup(
    name='foamgraph',
    version=find_version(),
    author='Jun Zhu',
    author_email='zhujun981661@gmail.com',
    description='',
    long_description='',
    url='',
    packages=find_packages(),
    tests_require=['pytest'],
    install_requires=[
        'PyQt5==5.15.2',
    ],
    extras_require={
        'test': [
            'pytest',
            'pytest-cov',
        ],
    },
    python_requires='>=3.7',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Scientific/Engineering :: Visualization',
    ]
)
