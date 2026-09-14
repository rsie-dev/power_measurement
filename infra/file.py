import os

from pyinfra.api import operation
from pyinfra.facts.files import File
from pyinfra import host
from pyinfra.api import OperationError, QuoteString, StringCommand
from pyinfra.facts.files import Directory, FileContents, Sha256File
from pyinfra.operations.files import _remote_file_equal
from pyinfra.operations import files


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


@operation()
def copy_to(src: str, dest: str, overwrite=False):
    """
    Copy remote file/directory/link into remote directory

    + src: remote file/directory to copy
    + dest: remote file/directory to copy `src` into
    + overwrite: whether to overwrite dest, if present
    """
    src_is_dir = host.get_fact(Directory, src)
    if not host.get_fact(File, src) and not src_is_dir:
        raise OperationError(f"src {src} does not exist")

    dest_file_path = os.path.join(dest, os.path.basename(src))
    dest_file_exists = host.get_fact(File, dest_file_path)
    if dest_file_exists and not overwrite:
        if _remote_file_equal(src, dest_file_path):
            host.noop(f"{dest_file_path} already exists")
            return
        else:
            raise OperationError(f"{dest_file_path} already exists and is different than src")

    cp_cmd = ["cp -r"]

    if overwrite:
        cp_cmd.append("-f")

    yield StringCommand(*cp_cmd, QuoteString(src), QuoteString(dest))


@operation()
def pristine_block(
    path,
    content=None,
    checksum_path=None,
    present=True,
    line=None,
    before=False,
    after=False,
    marker=None,
    begin=None,
    end=None,
    backup=False,
    try_prevent_shell_expansion=False,
):
    checksum_path = checksum_path or f"{path}.pyinfra-sha256"

    checksum_info = host.get_fact(File, path=checksum_path)
    if checksum_info is False:
        raise OperationError(
            f"Checksum path exists but is not a file: {checksum_path}"
        )

    checksum_exists = checksum_info is not None
    if checksum_exists:
        checksum_lines = host.get_fact(
            FileContents,
            path=checksum_path,
        )
        saved_checksum = checksum_lines[0].strip() if checksum_lines else ""
    else:
        saved_checksum = None

    current_checksum = host.get_fact(Sha256File, path=path)

    # When a checksum exists, update only if the whole file still matches.
    if checksum_exists and saved_checksum != current_checksum:
        return

    yield from files.block._inner(
        path=path,
        content=content,
        present=present,
        line=line,
        before=before,
        after=after,
        marker=marker,
        begin=begin,
        end=end,
        backup=backup,
        try_prevent_shell_expansion=try_prevent_shell_expansion,
    )

    # Record the whole-file checksum after updating the block.
    yield StringCommand(
        "sha256sum",
        QuoteString(path),
        "| awk '{print $1}' >",
        QuoteString(checksum_path),
    )
