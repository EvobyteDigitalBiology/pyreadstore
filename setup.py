from setuptools import setup, find_packages

# Get version without importing the package
with open("pyreadstore/__version__.py") as version_file:
    version = version_file.read().split('__version__ = ')[-1].strip().strip("'")
    

setup(
    name="pyreadstore",
    version=version,
    author="Jonathan Alles",
    author_email="Jonathan.Alles@evo-byte.com",
    description="PyReadStore is the Python client (SDK) for the ReadStore API",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/EvobyteDigitalBiology/pyreadstore",
    packages=find_packages() + [],
    license="Apache-2.0 license",
    license_files = ('LICENSE',),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: Unix",
    ],
    python_requires='>=3.10',
    install_requires=[
        'requests>=2.32.3',
        'pydantic>=2.9',
        'pandas>=2.2'
    ],
    exclude_package_data={
        "": ["*.pyc", "*.pyo", "*~"],
    },
    include_package_data=True
)