from setuptools import setup, find_packages


setup(
    name='Executor',
    version='0.1',
    packages=find_packages(),
    requires=['jsonschema', 'six'],

    # Metadata
    author='Mikolaj Kowalik',
    author_email='mxk@illinois.edu',
    description='A wrapper allowing to run the tasks in arbitrary locations.',
    url='https://github.com/lsst-dm/Executor',
)
