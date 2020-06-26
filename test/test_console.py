from unittest import mock

import pytest
from colors import strip_color
from outcome.utils import console


def nl(message: str = '') -> str:
    return f'{message}\n'


@pytest.fixture
def write():
    with mock.patch.object(console, 'write') as write:
        yield write


@pytest.fixture(scope='session')
def message():
    return 'message'


@pytest.fixture(scope='session')
def task():
    return 'task'


class TestBasics:
    def test_write_standard(self, capfd, message):
        console.write(message)
        captured = capfd.readouterr()

        assert captured.out == nl(message)

    def test_write_no_new_line(self, capfd, message):
        console.write(message, with_newline=False)
        captured = capfd.readouterr()

        assert captured.out == message

    def test_success(self, write, message):
        console.success(message)
        write.assert_called_once_with(console.bold_green(message))

    def test_failure(self, write, message):
        console.failure(message)
        write.assert_called_once_with(console.bold_red(message))

    def test_quiet(self, write, message):
        console.quiet(message)
        write.assert_called_once_with(console.dim(message))

    def test_loud(self, write, message):
        console.loud(message)
        write.assert_called_once_with(console.bold(message))

    def test_nl(self, capfd):
        console.newline()
        captured = capfd.readouterr()
        assert captured.out == nl()

    def test_padding(self, capfd, message):
        with console.padding():
            console.write(message)

        captured = capfd.readouterr()
        lines = captured.out.split('\n')

        assert len(lines) == 4  # There are 3 newline chars
        assert lines[1] == message
        assert len(lines[0]) == len(lines[2])
        assert len(lines[0]) == 0

    def test_list(self, capfd, message):
        items = ['item_1', 'item_2', 'item_3']

        console.write_list(message, items)

        captured = capfd.readouterr()
        lines = strip_color(captured.out).split('\n')

        for idx in range(-1, 1):
            assert lines[idx] == ''

        assert lines[2] == message

        for item_idx, item in enumerate(items):
            assert lines[item_idx + 4].startswith(f' {console._bullet}')
            assert lines[item_idx + 4].endswith(item)


class TestTasks:
    def test_basic_success(self, capfd, task):
        with mock.patch.object(console, 'success', wraps=console.success) as success:
            with console.task(task):
                1 + 1

            success.assert_called_once()

        captured = capfd.readouterr()
        basic = strip_color(captured.out)

        assert basic.startswith(task)
        assert basic.endswith(nl(console._success))

    def test_controlled_success(self, capfd, task):
        with mock.patch.object(console, 'success', wraps=console.success) as success:
            with console.task(task) as status:
                1 + 1
                status.success()

            success.assert_called_once()

        captured = capfd.readouterr()
        basic = strip_color(captured.out)

        assert basic.startswith(task)
        assert basic.endswith(nl(console._success))

    def test_double_status(self, task):
        with pytest.raises(Exception):
            with console.task(task) as status:
                status.success()
                status.success()

    def test_basic_failure(self, capfd, task):
        with mock.patch.object(console, 'failure', wraps=console.failure) as failure:
            with pytest.raises(Exception):
                with console.task(task):
                    raise Exception

            failure.assert_called_once()

        captured = capfd.readouterr()
        basic = strip_color(captured.out)

        assert basic.startswith(task)
        assert basic.endswith(nl(console._failure))

    def test_basic_failure_print(self, capfd, task):
        with console.task(task, exc='print'):
            raise Exception

        captured = capfd.readouterr()
        basic_lines = strip_color(captured.out).split('\n')
        basic_err = strip_color(captured.err).split('\n')

        assert basic_lines[0].startswith(task)
        assert basic_lines[0].endswith(console._failure)

        assert basic_err[0].startswith(console._error)
        assert basic_err[0].endswith(console._task_failed)
        assert basic_err[1].startswith('Traceback')

    def test_basic_failure_exit(self, capfd, task):
        with mock.patch('outcome.utils.console.sys.exit', auto_spec=True) as sys_exit:
            with console.task(task, exc='exit'):
                raise Exception

            sys_exit.assert_called_once()

        captured = capfd.readouterr()
        basic_lines = strip_color(captured.out).split('\n')

        assert basic_lines[0].startswith(task)
        assert basic_lines[0].endswith(console._failure)

        assert captured.err == ''

    def test_basic_failure_print_exit(self, capfd, task):
        with mock.patch('outcome.utils.console.sys.exit', auto_spec=True) as sys_exit:
            with console.task(task, exc='print_and_exit'):
                raise Exception

            sys_exit.assert_called_once()

        captured = capfd.readouterr()
        basic_lines = strip_color(captured.out).split('\n')
        basic_err = strip_color(captured.err).split('\n')

        assert basic_lines[0].startswith(task)
        assert basic_lines[0].endswith(console._failure)

        assert basic_err[0].startswith(console._error)
        assert basic_err[0].endswith(console._task_failed)
        assert basic_err[1].startswith('Traceback')

    def test_controlled_failure(self, capfd, task):
        with mock.patch.object(console, 'failure', wraps=console.failure) as failure:
            with console.task(task) as status:
                status.failure()

            failure.assert_called_once()

        captured = capfd.readouterr()
        basic_lines = strip_color(captured.out).split('\n')

        assert basic_lines[0].startswith(task)
        assert basic_lines[0].endswith(console._failure)

        assert captured.err == ''

    def test_controlled_failure_with_message(self, capfd, task, message):
        with mock.patch.object(console, 'failure', wraps=console.failure) as failure:
            with console.task(task) as status:
                status.failure(message)

            failure.assert_called_once()

        captured = capfd.readouterr()
        basic_lines = strip_color(captured.out).split('\n')
        basic_err = strip_color(captured.err).split('\n')

        assert basic_lines[0].startswith(task)
        assert basic_lines[0].endswith(console._failure)

        assert basic_err[0].startswith(console._error)
        assert basic_err[0].endswith(message)

    def test_width(self, capfd, task):
        for i in range(1, 3):
            with console.task(task * i) as status:
                status.success()

        captured = capfd.readouterr()
        basic_lines = strip_color(captured.out).split('\n')

        line_len = len(basic_lines[0])

        for line in basic_lines:
            if line != '':
                assert len(line) == line_len
