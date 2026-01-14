import re

from pyfstab import Entry, InvalidFstabLine, InvalidEntry


class ExtEntry(Entry):
    def read_string(self, line):
        """
        Parses an entry from a string

        :param line: Fstab entry line.
        :type line: str

        :return: self
        :rtype: Entry

        :raises InvalidEntry: If the data in the string cannot be parsed.
        """
        line = line.strip()
        if line and not line[0] == "#":
            return self._parse_entry(line)

        self.device = None
        self.dir = None
        self.type = None
        self.options = None
        self.dump = None
        self.fsck = None

        self.valid = False

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
            self.dump = 0
            self.fsck = 0

            self.valid = True
            return self

        raise InvalidFstabLine(line)
