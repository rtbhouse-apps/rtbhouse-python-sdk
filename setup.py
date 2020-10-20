from setuptools import setup, find_packages
from rtbhouse_sdk import __version__ as version


def readfile(path):
    with open(path) as fp:
        return fp.read()


setup(
    name='rtbhouse_sdk',
    version=version,
    description='RTB House SDK',
    long_description=readfile('README.rst'),
    url='https://github.com/rtbhouse-apps/rtbhouse-python-sdk',
    author='RTB House Apps Team',
    author_email='apps@rtbhouse.com',
    packages=find_packages(),
    install_requires=[
        'requests>=2.18.4'
    ],
    extras_require={
        'dev': [
            'pytest==4.6.5',
            'pytest-cov==2.7.1',
            'twine==1.13.0',
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ]
)
