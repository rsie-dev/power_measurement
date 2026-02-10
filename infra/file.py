from pyinfra.api import operation
from pyinfra.facts.files import File
from pyinfra import host
from pyinfra.api import OperationError, QuoteString, StringCommand


@operation()
def rename(src: str, dest: str, overwrite=False):
    """
    Rename remote file/directory/link into remote directory

    + src: remote file/directory to move
    + dest: remote new remote name
    + overwrite: whether to overwrite dest, if present
    """

    if host.get_fact(File, src) is None:
        raise OperationError("src {0} does not exist".format(src))

    if host.get_fact(File, dest) is not None:
        if overwrite:
            yield StringCommand("rm", "-rf", QuoteString(dest))
        else:
            raise OperationError(
                "dest {0} already exists and `overwrite` is unset".format(dest)
            )

    yield StringCommand("mv", QuoteString(src), QuoteString(dest))
