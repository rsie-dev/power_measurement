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
    assert actual_entry.dump == 0
    assert actual_entry.fsck == 0


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
    assert actual_entry.dump == 0
    assert actual_entry.fsck == 0


def test_write_string_short():
    entry = ExtEntry()
    entry.valid = True
    entry.type = "tmpfs"
    entry.device = "tmpfs"
    entry.dir = "/var/log"
    entry.options = "size=50M,noatime,lazytime,nodev,nosuid"
    entry.dump = 0
    entry.fsck = 0

    actual_line = entry.write_string()

    assert actual_line == "tmpfs /var/log tmpfs size=50M,noatime,lazytime,nodev,nosuid 0 0"


def test_write_string_long():
    entry = ExtEntry()
    entry.valid = True
    entry.type = "ext4"
    entry.device = "/dev/mapper/root"
    entry.dir = "/"
    entry.options = "defaults"
    entry.dump = 0
    entry.fsck = 1

    actual_line = entry.write_string()

    assert actual_line == "/dev/mapper/root / ext4 defaults 0 1"

