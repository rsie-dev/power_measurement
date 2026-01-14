from fstab_entry import ExtEntry


def test_read_string_short():
    entry = ExtEntry()
    line = "tmpfs /var/log tmpfs size=50M,noatime,lazytime,nodev,nosuid"

    actual_entry = entry.read_string(line)

    assert actual_entry.valid
    assert actual_entry.type == "tmpfs"
    assert actual_entry.device == "tmpfs"
    assert actual_entry.dir == "/var/log"
    assert actual_entry.options == "size=50M,noatime,lazytime,nodev,nosuid"
    assert actual_entry.dump is None
    assert actual_entry.fsck is None


def test_read_string_long():
    entry = ExtEntry()
    line = "/dev/mapper/root  /       ext4    defaults    0 1"

    actual_entry = entry.read_string(line)

    assert actual_entry.valid
    assert actual_entry.type == "ext4"
    assert actual_entry.device == "/dev/mapper/root"
    assert actual_entry.dir == "/"
    assert actual_entry.options == "defaults"
    assert actual_entry.dump == 0
    assert actual_entry.fsck == 1


def test_read_string_swap():
    entry = ExtEntry()
    line = "/dev/swap     none        swap    sw"

    actual_entry = entry.read_string(line)

    assert actual_entry.valid
    assert actual_entry.type == "swap"
    assert actual_entry.device == "/dev/swap"
    assert actual_entry.dir == "none"
    assert actual_entry.options == "sw"
    assert actual_entry.dump is None
    assert actual_entry.fsck is None


def test_read_string_tag():
    entry = ExtEntry()
    line = "PARTUUID=ff3aa3cd-02 / ext4 defaults 0 1"

    actual_entry = entry.read_string(line)

    assert actual_entry.valid
    assert actual_entry.type == "ext4"
    assert actual_entry.device == "PARTUUID=ff3aa3cd-02"
    assert actual_entry.dir == "/"
    assert actual_entry.options == "defaults"
    assert actual_entry.dump == 0
    assert actual_entry.fsck == 1


def test_read_string_comment():
    entry = ExtEntry()
    line = "# some comment"

    actual_entry = entry.read_string(line)

    assert not actual_entry.valid
    assert actual_entry.comment == "# some comment"
    assert actual_entry.type is None
    assert actual_entry.device is None
    assert actual_entry.dir is None
    assert actual_entry.options is None
    assert actual_entry.dump is None
    assert actual_entry.fsck is None


def test_write_string_short():
    entry = ExtEntry(
        _device="tmpfs",
        _dir="/var/log",
        _type="tmpfs",
        _options="size=50M,noatime,lazytime,nodev,nosuid",
    )

    actual_line = entry.write_string()

    assert actual_line == "tmpfs /var/log tmpfs size=50M,noatime,lazytime,nodev,nosuid"


def test_write_string_long():
    entry = ExtEntry(
        _device="/dev/mapper/root",
        _dir="/",
        _type="ext4",
        _options="defaults",
        _dump=0,
        _fsck=1,
    )

    actual_line = entry.write_string()

    assert actual_line == "/dev/mapper/root / ext4 defaults 0 1"


def test_write_string_tag():
    entry = ExtEntry(
        _device="PARTUUID=ff3aa3cd-02",
        _dir="/",
        _type="ext4",
        _options="defaults",
        _dump=0,
        _fsck=1,
    )

    actual_line = entry.write_string()

    assert actual_line == "PARTUUID=ff3aa3cd-02 / ext4 defaults 0 1"


def test_write_string_comment():
    entry = ExtEntry(
        _comment="# some comment"
    )

    actual_line = entry.write_string()

    assert actual_line == "# some comment"
