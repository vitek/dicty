from setuptools import setup
import io

with io.open('README.rst', 'rt', encoding="utf-8") as readme_file:
    long_description = readme_file.read()

setup(
    name='dicty',
    version='0.1',
    author='Victor Makarov',
    author_email='vitja.makarov@gmail.com',
    description='A library for mapping dictionaries to Python objects',
    long_description=long_description,
    url='https://github.com/vitek/dicty',
    py_modules=['dicty'],
    install_requires=[''],
    tests_require=['py.test'],
    test_suite='test',
)
