from setuptools import setup, find_packages
from rtbhouse_sdk import __version__ as version


setup(
    name='rtbhouse_sdk',
    version=version,
    description='RTB House SDK',
    url='git@github.com:rtbhouse-apps/rtb-apps-sdk.git',
    author='RTB House Apps Team',
    author_email='apps@rtbhouse.com',
    packages=find_packages(),
    install_requires=[
        'requests>=2.18.4'
    ],
    classifiers=(
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    )
)
