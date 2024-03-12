"""Setup file for lucullus_rest package."""

from setuptools import setup

setup(
    name='lucullus_rest',
    version='0.0.1',
    description=(
        'A Python package to access information via the REST-API'
        'of the Lucullus Process and Information Management System'
        '(PIMS) of Securecell.'
    ),
    url="https://github.com/StefanHauer/lucullus_rest",
    author='Stefan F. Hauer',
    author_email='hatr@zhaw.ch',
    license='MIT',
    packages=['lucullus_rest'],
    install_requires=[
        "numpy", "pandas", "requests", "json", "ipaddress"
    ],
    zip_safe=False
)
