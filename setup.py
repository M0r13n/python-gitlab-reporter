import setuptools  # type:ignore

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="python-gitlab-reporter",
    version="0.0.1",
    author="Leon Morten Richter",
    author_email="leon.morten@gmail.com",
    description="Handle uncaught exceptions and log them to GitLab as issues.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/M0r13n/python-gitlab-reporter",
    license="MIT",
    packages=setuptools.find_packages(),
    package_data={
        "pyais": ["py.typed"]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Communications",
        "Typing :: Typed",
    ],
    keywords=["GitLab", "Exceptions", "Logging"],
    python_requires='>=3.7',
    install_requires=[
        "python-gitlab"
    ],
)
