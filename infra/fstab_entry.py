import re

from pyfstab import Entry, InvalidFstabLine, InvalidEntry


class ExtEntry(Entry):
    def __init__(
        self,
        _device=None,
        _dir=None,
        _type=None,
        _options=None,
        _dump=None,
        _fsck=None,
        _comment=None,
    ):
        """
        :param _device:
            Fstab device (1st parameter in the fstab entry).
            Tuple/list in form of (type, value) is also accepted
            (e.g. ("UUID", "1234567890"))
        :type _device: Union[str, tuple, list]

        :param _dir: Fstab device (2nd parameter in the fstab entry)
        :type _dir: str

        :param _type: Fstab device (3rd parameter in the fstab entry)
        :type _type: str

        :param _options: Fstab device (4th parameter in the fstab entry)
        :type _options: str

        :param _dump: Fstab device (5th parameter in the fstab entry)
        :type _dump: int

        :param _fsck: Fstab device (6th parameter in the fstab entry)
        :type _fsck: int
        """
        # Use setters and getters for these
        self._device = None
        self._device_tag_type = None
        self._device_tag_value = None

        self.device = _device
        self.dir = _dir
        self.type = _type
        self.options = _options
        self.dump = _dump
        self.fsck = _fsck
        self._comment = _comment

        self.valid = True
        self.valid &= self._device is not None
        self.valid &= isinstance(self._device, (str, tuple, list))
        self.valid &= self.dir is not None
        self.valid &= self.type is not None
        self.valid &= self.options is not None

        self.valid &= (self.dump is None) == (self.fsck is None)

    @property
    def comment(self):
        return self._comment

    def read_string(self, line):
        """
        Parses an entry from a string

        :param line: Fstab entry line.
        :type line: str

        :return: self
        :rtype: Entry

        :raises InvalidEntry: If the data in the string cannot be parsed.
        """
        self.valid = False
        self.device = None
        self.dir = None
        self.type = None
        self.options = None
        self.dump = None
        self.fsck = None

        line = line.strip()
        if line:
            if line[0] == "#":
                self._comment = line
                return self
            return self._parse_entry(line)

        raise InvalidEntry("Entry cannot be parsed")

    def _parse_entry(self, line):
        parts = re.split(r"\s+", line)

        if len(parts) == 6:
            [_device, _dir, _type, _options, _dump, _fsck] = parts

            _dump = int(_dump)
            _fsck = int(_fsck)

            self.device = _device
            self.dir = _dir
            self.type = _type
            self.options = _options
            self.dump = _dump
            self.fsck = _fsck

            self.valid = True
            return self
        elif len(parts) == 4 and parts[2] in ["tmpfs", "swap"]:
            # tmpfs /var/log tmpfs size=50M,noatime,lazytime,nodev,nosuid
            # /var/swap none swap sw

            [_device, _dir, _type, _options] = parts

            self.device = _device
            self.dir = _dir
            self.type = _type
            self.options = _options
            self.dump = None
            self.fsck = None

            self.valid = True
            return self

        raise InvalidFstabLine(line)

    def write_string(self):
        """
        Formats the Entry into fstab entry line.

        :return: Fstab entry line.
        :rtype: str

        :raises InvalidEntry:
            A string cannot be generated because the entry is invalid.
        """
        if not self:
            if self._comment:
                return "{}".format(
                    self._comment,
                )
            raise InvalidEntry("Entry cannot be formatted")

        if self.dump is not None:
            return "{} {} {} {} {} {}".format(
                self.device,
                self.dir,
                self.type,
                self.options,
                self.dump,
                self.fsck,
            )

        return "{} {} {} {}".format(
            self.device,
            self.dir,
            self.type,
            self.options,
        )
