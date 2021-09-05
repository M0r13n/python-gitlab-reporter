"""
Handle uncaught Exceptions

Refer to:
    - sys.excepthook        :    https://docs.python.org/3/library/sys.html#sys.excepthook
    - threading.excepthook :    https://docs.python.org/3/library/threading.html#threading.excepthook
"""
import datetime
import functools
import logging
import sys
import threading
import traceback
from typing import Any, Optional, Type

from gitlab import Gitlab
from gitlab.v4.objects import ProjectIssue, Project

if sys.version_info <= (3, 8, 0):
    PY_37 = True
else:
    PY_37 = False

_original_sys_excepthook = sys.excepthook

if not PY_37:
    _original_threading_excepthook = threading.excepthook  # type: ignore

logger = logging.getLogger('python-gitlab-reporter')


def _description(exc_type: Type[BaseException], exc_value: Any, exc_traceback: Any) -> str:
    """
    Transform a set of exception attributes into a human readable description.

    :param exc_type:            Exception type.
    :param exc_value:           Exception value.
    :param exc_traceback:       Exception traceback.

    :return: Multiline string.
    """
    description = f"# Uncaught exception '{exc_type.__name__}: {str(exc_value)}'\n\n"
    description += "```py\n"
    description += "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    description += "```\n"
    description += f"The error lastly occurred at: **{datetime.datetime.now().isoformat()}**\n"
    description += "\n\n\n(*This issue was automatically opened by python-gitlab-reporter*)"
    return description


def _title(exc_type: Type[BaseException], exc_value: Any, exc_traceback: Any) -> str:
    """
    Get a title that is always the same for the same exception but differs for exceptions with different tracebacks.

    :param exc_type:            Exception type.
    :param exc_value:           Exception value.
    :param exc_traceback:       Exception traceback.

    :return: a single line string.
    """
    return f"{exc_type.__name__}: {str(exc_value)}"


def _create_issue(project: Project, title: str, description: str, assignee_id: Optional[int] = None) -> ProjectIssue:
    """
    Creates a new issue for a given project.

    :param project:         gitlab.Project instance to create the issue for
    :param title:           title of the new issue (str)
    :param description:     description of the new issue (str)
    :param assignee_id:     Optional assignee
    :return:                The instance of the newly created issue
    """
    issue = project.issues.create(
        {
            "title": title,
            "description": description,
            "assignee_id": assignee_id
        }
    )
    return issue


def _reopen_issue(issue: ProjectIssue, description: str) -> None:
    """
    Repopen and/or update the timestamp of an issue.

    :param issue:           The issue to reopen and/or update
    :param description:     The new updated descpriotn (e.g. new timestamp)

    :return:                None
    """
    issue.state = "open"
    issue.description = description
    issue.save()


def catch_all(f):
    """
    Catch all errors and write them to logging.exception.
    """

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            f(*args, **kwargs)
        except Exception as err:
            logger.exception(err)

    return wrapper


class Reporter:
    gitlab: Optional[Gitlab] = None
    project_id: Optional[int] = None
    assignee_id: Optional[int] = None

    @classmethod
    def _handle_sys_exception(cls, exc_type: Type[BaseException], exc_value: BaseException, exc_traceback: Any) -> None:
        """
        Handle uncaught exceptions.

        :param exc_type:            Exception type.
        :param exc_value:           Exception value.
        :param exc_traceback:       Exception traceback, can be manipulated with the traceback module.

        :return:Calls the original sys.excepthook
        """
        if cls.initialized():
            cls._create_or_reopen_issue(exc_type, exc_value, exc_traceback)
        else:
            logger.info('python-gitlab-reporter not configured. Nothing to do.')

        return _original_sys_excepthook(exc_type, exc_value, exc_traceback)

    @classmethod
    def _handle_threading_exception(cls, args):
        """
        Handle uncaught exceptions raised by `Thread.run()`.

        :param exc_type:            Exception type.
        :param exc_value:           Exception value, can be None.
        :param exc_traceback:       Exception traceback, can be None.
        :param thread:              Thread which raised the exception, can be None.

        :return: Calls the original threading.excepthook
        """
        if cls.initialized():
            cls._create_or_reopen_issue(args.exc_type, args.exc_value, args.exc_traceback)
        else:
            logger.info('python-gitlab-reporter not configured. Nothing to do.')

        return _original_threading_excepthook(args)

    @classmethod
    @catch_all
    def _create_or_reopen_issue(cls, exc_type: Type[BaseException], exc_value: BaseException,
                                exc_traceback: Any) -> None:
        """
        Create a new issue on Gitlab for the given error

        :param exc_type:            Exception type.
        :param exc_value:           Exception value, can be None.
        :param exc_traceback:       Exception traceback, can be None.

        :return: None
        """
        if not cls.initialized():
            raise ValueError("Reporter not initialized. Call Reporter.init() first.")

        # Does an issue with the same title already exists?
        title = _title(exc_type, exc_value, exc_traceback)
        description = _description(exc_type, exc_value, exc_traceback)
        project = cls.gitlab.projects.get(cls.project_id)  # type:ignore

        for issue in project.issues.list(as_list=False):
            if issue.title == title:
                # Found existing issue
                # Reopen it and/or update it's description
                _reopen_issue(issue, description)
                return

        # There is no existing issue -> the error is new
        _create_issue(project, title, description, assignee_id=cls.assignee_id)

    @classmethod
    def init(cls, host: str, private_token: str, project_id: int, assignee_id: Optional[int] = None) -> None:
        """
        Initialize the Reporter class. All unhandled exceptions will then be logged to Gitlab.

        :param host:                URL of the Gitlab instance (e.g. https://gitlab.com)
        :param private_token:       A private API token with API access for the gitlab instance
        :param project_id:          The ID of the project where the issue should be created
        :param assignee_id:         An optional ID of an Gitlab user that will be assigned to the issue

        :return: None
        """
        cls.gitlab = Gitlab(host, private_token=private_token)
        cls.project_id = project_id
        cls.assignee_id = assignee_id

        sys.excepthook = Reporter._handle_sys_exception

        if not PY_37:
            threading.excepthook = Reporter._handle_threading_exception  # type:ignore

    @classmethod
    def initialized(cls) -> bool:
        """
        Check whether the Reporter was initialized or not.
        """
        if cls.gitlab is None or cls.project_id is None:
            return False
        return True
