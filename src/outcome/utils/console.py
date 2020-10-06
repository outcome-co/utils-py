"""Helpers to print to the console."""

import sys
import traceback
from contextlib import contextmanager
from typing import IO, Generator, List, Optional, Union

import colored
from colored import stylize

# Weights
_dim = 'dim'
_bold = 'bold'

# Colors
_green = 'green'
_red = 'red'


# Messages
_failure = 'Failure'
_success = 'Success'
_skipped = 'Skipped'
_error = 'Error'
_task_failed = 'Task Failed'


# Default
_bullet = '•'

_raise = 'raise'
_print = 'print'
_exit = 'exit'
_print_and_exit = 'print_and_exit'


def bold_red(message: str) -> str:
    return stylize(message, colored.fg(_red) + colored.attr(_bold))


def bold_green(message: str) -> str:
    return stylize(message, colored.fg(_green) + colored.attr(_bold))


def dim(message: str) -> str:
    return stylize(message, colored.attr(_dim))


def bold(message: str) -> str:
    return stylize(message, colored.attr(_bold))


class Status:
    """A lightweight object to represent the status of a task."""

    def __init__(self) -> None:
        self.completed = False

    def failure(self, message: Optional[str] = None, detail: Optional[str] = None) -> None:
        """Indicate that the task failed.

        Args:
            message (str, optional): The optional error message to display.
            detail (str, optional): Optional detail to appear under the task status.
        """
        self._mark_as_completed()
        failure(_failure)

        if detail:
            quiet(detail)

        if message:
            error(message)

    def success(self, detail: Optional[str] = None) -> None:
        """Indicate that the task succeeded.

        Args:
            detail (str, optional): Optional detail to appear under the task status.
        """
        self._mark_as_completed()
        success(_success)

        if detail:
            quiet(detail)

    def skipped(self, detail: Optional[str] = None) -> None:
        """Indicate that the task was skipped.

        Args:
            detail (str, optional): Optional detail to appear under the task status. Defaults to None.
        """
        self._mark_as_completed()
        skipped(_skipped)

        if detail:
            quiet(detail)

    def _mark_as_completed(self) -> None:
        """Mark the task as completed.

        Raises:
            Exception: If the status of the task has already been indicated.
        """
        if self.completed:
            raise Exception('Status already completed!')

        self.completed = True


@contextmanager
def critical_task(label: str, max_width: int = 80) -> Generator[Status, None, None]:  # pragma: no cover
    with task(label, max_width, exc='print_and_exit') as status:
        yield status


def completed_task(
    label: str, result: Union[bool, Exception], max_width: int = 80, exc: str = _raise, detail: Optional[str] = None,
):
    with task(label, max_width=max_width, exc=exc) as status:
        if isinstance(result, Exception):
            raise result
        elif result:
            status.success(detail=detail)
        else:
            status.failure(detail=detail)


@contextmanager
def task(label: str, max_width: int = 80, exc: str = _raise) -> Generator[Status, None, None]:  # noqa: WPS231,WPS213
    """Print a task's name, followed by its outcome.

    The outcome of the task is provided by called the `success` or `failure`
    methods on the provided `status` object.

    Exceptions thrown in the yield block can be handled in mulitple ways via the `exc` argument:
    - 'raise', the exception is raised, nothing is printed (default)
    - 'print', the exception is printed, execution continues
    - 'exit', the process exits, nothing is printed
    - 'print_and_exit', the exception is printer, the process exits

    Args:
        label (str): The name of the task.
        max_width (int): The max width of the printed message.
        exc (str): The exception strategy.

    Yields:
        Status: The status object.

    Raises:
        Exception: Passes through the exception raised in the yield block.

    Examples:
        ```
        with console.status('My Task') as status:
            did_succeed = run_task()

            if did_succeed:
                status.success()
            else:
                status.failure()
        ```
    """
    assert exc in {_raise, _print, _exit, _print_and_exit}  # noqa: S101

    dim_dots = stylize('.' * (max_width - len(label)), colored.attr(_dim))
    bold_label = stylize(label, colored.attr(_bold))

    write(f'{bold_label}{dim_dots}', with_newline=False)

    work_status = Status()

    try:
        yield work_status
    except Exception as ex:
        if not work_status.completed:
            work_status.failure()

        if exc == _raise:
            raise ex
        elif exc == _print:
            error(_task_failed)
        elif exc == _exit:
            fail()
        else:
            fail(_task_failed)

    if not work_status.completed:
        work_status.success()


@contextmanager
def padding(**kwargs) -> Generator[None, None, None]:
    """Pad the output in newlines.

    Args:
        kwargs (Any): Options passed to `write`.

    Yields:
        None
    """
    newline(**kwargs)
    yield
    newline(**kwargs)


def success(message: str, **kwargs) -> None:
    """Write a bold green message.

    Args:
        message (str): The message.
        kwargs (Any): Options passed to `write`.
    """
    write(bold_green(message), **kwargs)


def failure(message: str, **kwargs) -> None:
    """Write a bold red message.

    Args:
        message (str): The message.
        kwargs (Any): Options passed to `write`.
    """
    write(bold_red(message), **kwargs)


def skipped(message: str, **kwargs) -> None:
    """Write a dimmed message.

    Args:
        message (str): The message.
        kwargs (Any): Options passed to `write`.
    """
    quiet(message, **kwargs)


def quiet(message: str, **kwargs) -> None:
    """Write a dimmed message.

    Args:
        message (str): The message.
        kwargs (Any): Options passed to `write`.
    """
    write(dim(message), **kwargs)


def loud(message: str, **kwargs) -> None:
    """Write a bold message.

    Args:
        message (str): The message.
        kwargs (Any): Options passed to `write`.
    """
    write(bold(message), **kwargs)


def header(message: str, **kwargs) -> None:
    """Write a bold message with padding.

    Args:
        message (str): The message.
        kwargs (Any): Options passed to `write`.
    """
    with padding(**kwargs):
        loud(message, **kwargs)


def newline(**kwargs) -> None:
    """Write a newline.

    Args:
        kwargs (Any): Options passed to `write`.
    """
    write('\n', with_newline=False, **kwargs)


def write(message: str, file: Optional[IO[str]] = None, with_newline: bool = True) -> None:
    """Write a message.

    Args:
        message (str): The message.
        file (IO): The file descriptor to which the message will be written.
        with_newline (bool): Whether to print a newline.
    """
    if not file:
        file = sys.stdout

    file.write(message)

    if with_newline:
        file.write('\n')

    file.flush()


def write_list(message: str, items: List, bullet: str = _bullet, **kwargs) -> None:
    """Prints a header and a list of items.

    Args:
        message (str): The header message.
        items (List): The list of items to print.
        bullet (str): The bullet character to use.
        kwargs (Any): Options passed to `write`.
    """
    with padding(**kwargs):
        header(message, **kwargs)

        for item in items:
            write(f' {bullet} {item}', **kwargs)


def fail(message: Optional[str] = None, **kwargs) -> None:
    """Prints an error message to stderr and exits the script with a non-zero exit code.

    Args:
        message (str): The message to print.
        kwargs (Any): Options passed to `write`.
    """
    if message:
        error(message, **kwargs)
    sys.exit(-1)


def error(message: str, **kwargs) -> None:
    """Prints an error message to stderr.

    Optionally print the stacktrace for the current exception.

    Args:
        message (str): The message to be displayed.
        kwargs (Any): Options passed to `write`.
    """
    error_prefix = bold_red(_error)
    message = bold(message)
    write(f'{error_prefix}: {message}', **{'file': sys.stderr, **kwargs})

    # If we're currently handling an exception, print the stacktrace
    _ex_type, ex, _trace = sys.exc_info()
    if ex:
        quiet(traceback.format_exc(), **{'file': sys.stderr, **kwargs})
