from pyinfra.operations import apt
from pyinfra.api import deploy


@deploy("Compressors")
def compressors():
    apt.packages(
        name="Install compression tools",
        packages=["xz-utils", "lzop", "lz4", "bzip2", "bzip3"],
        no_recommends=True,
        _sudo=True,
    )


@deploy("Stressors")
def stressors():
        apt.packages(
        name="Install stressor tools",
        packages=["stress-ng"],
        no_recommends=True,
        _sudo=True,
    )

