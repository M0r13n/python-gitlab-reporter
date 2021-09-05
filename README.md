# Python gitlab reporter

[![PyPI](https://img.shields.io/pypi/v/python_gitlab_reporter)](https://pypi.org/project/python_gitlab_reporter/)
[![license](https://img.shields.io/pypi/l/python_gitlab_reporter)](https://github.com/M0r13n/python-gitlab-reporter/blob/master/LICENSE)
[![downloads](https://img.shields.io/pypi/dm/python_gitlab_reporter)](https://pypi.org/project/python_gitlab_reporter/)

A custom exception handler that can be used to (re)open issues on Gitlab for projects written in Python.

The aim was to build a very small module that is easy to use and that works with a local Gitlab instance.
This module is useful for those who want to aggregate runtime errors in a central location without
using third-party software (e.g. sentry.io, etc).

Duplicate errors will be tracked in a single issue and will not be duplicated to avoid *error-spamming*.

The script is thread-safe and handles errors from ``Thread.run()``.

## Installation

The module is available on Pypi:

````bash
pip install python-gitlab-reporter
````

In your Python project call:

```python
from reporter.core import Reporter

Reporter.init("https://gitlab.com", private_token="12345657678890", project_id=123456)
```


## How does it work?

The script adds custom hooks to [sys.excepthook](https://docs.python.org/3/library/sys.html#sys.excepthook) and
[threading.excepthook](https://docs.python.org/3/library/threading.html#threading.excepthook).
These wrap around the original hooks and send issues to Gitlab. Any error that is caused by `python-gitlab-reporter`
itself is ignored. The original `sys.excepthook` and `threading.excepthook` will **always** be called, so that
the exceptions still terminate the program, etc.