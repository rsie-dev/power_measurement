from io import StringIO

from pyinfra import logger
from pyinfra.api import operation
from pyinfra.api import OperationError, OperationValueError
from pyinfra.api import FactBase
from pyinfra import host
from pyinfra.api import FileUploadCommand

import pyfstab.fstab as fstabpy
from fstab_entry import ExtEntry
fstabpy.Entry = ExtEntry

_FSTAB = "/etc/fstab"


class Fstab(FactBase):
    def command(self, fstab=None):
        if fstab is None:
            fstab = _FSTAB
        return 'cat %s' % fstab

    def process(self, output):
        fstab = fstabpy.Fstab().read_string("\n".join(output))
        return fstab


class FstabDirs(FactBase):
    def command(self, fstab=None):
        if fstab is None:
            fstab = _FSTAB
        return 'cat %s' % fstab

    def process(self, output):
        fstab = fstabpy.Fstab().read_string("\n".join(output))
        return fstab.entry_by_dir.keys()


@operation()
def fstab_option(mount_dir: str,
                 read_only=None,
                 read_write=None,
                 fstab=None,
                 ):
    logger.info("Update fstab entry for mount: {0}".format(mount_dir))

    if read_only and read_write:
        raise OperationValueError("only one option can be given: read_only or read_write")

    if fstab is None:
        fstab = _FSTAB

    fstab_content = host.get_fact(Fstab, fstab)
    if mount_dir not in fstab_content.entry_by_dir:
        raise OperationError("no fstab entry for {0}".format(mount_dir))
    entry = fstab_content.entry_by_dir[mount_dir]
    options = entry.options.split(",")

    new_options = []
    del_options = []
    if read_only is not None:
        if read_only == True:
            if "rw" in options:
                del_options.append("rw")
            if "ro" not in options:
                new_options.append("ro")
        else:
            pass
    if read_write is not None:
        if read_write == True:
            if "ro" in options:
                del_options.append("ro")
            if "rw" not in options:
                new_options.append("rw")
        else:
            pass

    if not new_options and not del_options:
        return ""
    options.extend(new_options)
    for o in del_options:
        options.remove(o)
    entry.options = ",".join(options)

    yield _write_fstab(fstab_content, fstab)


@operation()
def fstab_add_entry(device: str,
                    mount_dir: str,
                    fs_type: str,
                    options=None,
                    fstab=None,
                    ):
    logger.info("Update fstab entry for mount: {0}".format(mount_dir))

    if fstab is None:
        fstab = _FSTAB

    fstab_content = host.get_fact(Fstab, fstab)

    entry = ExtEntry(
        _device=device,
        _dir=mount_dir,
        _type=fs_type,
        _options=options if options else "defaults",
    )

    fstab_content.entries.append(entry)

    yield _write_fstab(fstab_content, fstab)


def _write_fstab(fstab_content, fstab):
    content = fstab_content.write_string() + "\n"
    return FileUploadCommand(
        StringIO(content),
        fstab,
        remote_temp_filename=host.get_temp_filename(fstab),
    )
