from contextlib import contextmanager
import io
import os
from tempfile import NamedTemporaryFile
from tempfile import _TemporaryFileWrapper
from types import MethodType

__all__ = ['save_file', 'CustomNamedTemporaryFile']


@contextmanager
def CustomNamedTemporaryFile(delete=True, *args, **kwargs) -> _TemporaryFileWrapper:
    """A custom ``tempfile.NamedTemporaryFile`` to enable the following points

    - Save without closing the file
    - Close the file without it being deleted
    - Still have it be automatically delete on end of with statement or error along as ``delete`` is set to True

    Examples:
        Use as a normal ``tempfile.NamedTemporaryFile`` but save in between:

            >>> with CustomNamedTemporaryFile() as some_file:
            >>>     some_file.write('foo bar')
            >>>     some_file.save()
            >>>     other_function(some_file)

        Use as a normal ``tempfile.NamedTemporaryFile`` but close in between:
        This is useful eg. on windows. When the file is open on windows, other programs may not be permitted to access
        the file. In this case we want to close the file, without deleting it. Normally in this case we can set
        ``delete=False`` in the parameters. But then we would need to manually close it after the with statement.
        Even though this is useful it isn't without it's own risks. When you closed your file, but it is still open in
        somewhere else, the file can't be deleted on windows. You will get an "PermissionError: [WinError 32]" error.
        So make sure the file is closed.

            >>> with CustomNamedTemporaryFile() as some_file:
            >>>     some_file.write('foo bar')
            >>>     some_file.close()
            >>>     other_function(some_file.name)

        If you still want the file not being deleted automatically after the with statement, you can still set
        ``delete=False``.

            >>> with CustomNamedTemporaryFile(delete=False) as some_file:
            >>>     ...
            >>> print(some_file.closed)
            >>> # False

    Args:
        Args are defiend in `tempfile.NamedTemporaryFile`
    Returns:
        :obj:`tempfile._TemporaryFileWrapper`:
    """
    file = NamedTemporaryFile(*args, **kwargs, delete=False)

    def delete_close():
        if delete:
            if not file.closed:
                file.close()
            if os.path.isfile(file.name):
                os.unlink(file.name)

    file.__del__ = delete_close
    file.save = MethodType(save_file, file)

    try:
        yield file
    finally:
        delete_close()


def save_file(file: io.BufferedWriter):
    """Save file without closing it

    Args:
        file (:obj:`io.BufferedWriter`): A file-like object
    """
    file.flush()
    os.fsync(file.fileno())
    file.seek(0)
