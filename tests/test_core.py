import unittest
from threading import Thread
from unittest.mock import patch, MagicMock

from reporter.core import _description, _title, _create_issue, _reopen_issue, catch_all, Reporter


class TestCase(unittest.TestCase):

    def test_description(self):
        try:
            raise ValueError("Ooopsie")
        except ValueError as err:
            description = _description(err.__class__, err, err.__traceback__)

        description = description.splitlines()

        self.assertEqual(description[0], "# Uncaught exception 'ValueError: Ooopsie'")
        self.assertEqual(description[2], "```py")
        self.assertEqual(description[3], "Traceback (most recent call last):")
        self.assertEqual(description[6], "ValueError: Ooopsie")
        self.assertEqual(description[-1], "(*This issue was automatically opened by python-gitlab-reporter*)")

    def test_title(self):
        try:
            raise ValueError("Ooopsie")
        except ValueError as err:
            title = _title(err.__class__, err, err.__traceback__)
        self.assertEqual(title, "ValueError: Ooopsie")

        try:
            Thread(target=lambda: 1 / 0).run()
        except ZeroDivisionError as err:
            title = _title(err.__class__, err, err.__traceback__)

        self.assertEqual(title, "ZeroDivisionError: division by zero")

    def test_create_issue_no_assignee(self):
        project = MagicMock()
        issue = _create_issue(project, "FooBar", "Hello, World!")

        self.assertIsNotNone(issue)
        project.issues.create.assert_called_once()
        project.issues.create.assert_called_once_with(
            {
                'title': 'FooBar',
                'description': 'Hello, World!', 'assignee_id': None
            }
        )

    def test_create_issue_with_assignee(self):
        project = MagicMock()
        issue = _create_issue(project, "FooBar", "Hello, World!", 12345)

        self.assertIsNotNone(issue)
        project.issues.create.assert_called_once()
        project.issues.create.assert_called_once_with(
            {
                'title': 'FooBar',
                'description': 'Hello, World!',
                'assignee_id': 12345
            }
        )

    def test_reopen_issue(self):
        issue = MagicMock(state="closed", description="Old text")
        self.assertEqual(issue.state, "closed")
        self.assertEqual(issue.description, "Old text")

        _reopen_issue(issue, "New text")

        self.assertEqual(issue.state, "open")
        self.assertEqual(issue.description, "New text")
        issue.save.assert_called_once()

    def test_catch_all(self):
        @catch_all
        def val_error():
            raise ValueError("Broken")

        @catch_all
        def runtime_error():
            raise RuntimeError("Ops")

        @catch_all
        def overflow_error():
            raise OverflowError("Not good")

        self.assertIsNone(val_error())
        self.assertIsNone(runtime_error())
        self.assertIsNone(overflow_error())

    def test_reporter_init(self):
        self.assertFalse(Reporter.initialized())

        Reporter.init("https://gitlab", "12345", 56789, 9999)

        self.assertEqual(Reporter.gitlab.url, "https://gitlab")
        self.assertEqual(Reporter.gitlab.private_token, "12345")
        self.assertEqual(Reporter.project_id, 56789)
        self.assertEqual(Reporter.assignee_id, 9999)

        self.assertTrue(Reporter.initialized())

    @patch("reporter.core._original_sys_excepthook")
    def test_handle_normal_exception_uninitialized(self, orig_excepthook):
        err = ValueError("Oooosie")

        Reporter._handle_sys_exception(err.__class__, err, None)

        orig_excepthook.assert_called_once()
        orig_excepthook.assert_called_once_with(err.__class__, err, None)

    @patch("gitlab.Gitlab")
    @patch("reporter.core._original_sys_excepthook")
    def test_handle_normal_exception_uninitialized(self, orig_excepthook, mock_gitlab):
        Reporter.gitlab = mock_gitlab

        err = ValueError("Oooosie")

        Reporter._handle_sys_exception(err.__class__, err, None)

        orig_excepthook.assert_called_once()
        orig_excepthook.assert_called_once_with(err.__class__, err, None)
        mock_gitlab.projects.get(56789)
