import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="alertbook",
    version="0.0.1",
    author="Kyle Kneitinger",
    author_email="kyle@kneit.in",
    description=("An Ansible-inspired Prometheus alert rules compiler"),
    license="BSD",
    keywords="prometheus",
    url="http://packages.python.org/alertbook",
    scripts=['bin/alertbook'],
    long_description=read('README.md'),
    install_requires=read('requirements.txt').splitlines(),
    classifiers=[
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
)
