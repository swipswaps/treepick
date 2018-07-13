import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ppick",
    version="0.0.1",
    author="Toby Slight",
    author_email="tobyslight@gmail.com",
    description="Curses based path picker",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tslight/ppick",
    packages=setuptools.find_packages(),
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD 3 Clause",
        "Operating System :: OS Independent",
    ),
)
