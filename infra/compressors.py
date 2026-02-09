from pyinfra.operations import apt
from pyinfra.api import deploy


@deploy("Compressors")
def compressors():
    apt.packages(
        name="Install compression tools",
        packages=["gzip", "xz-utils", "lzop", "lz4", "bzip2", "bzip3", "brotli", "zopfli", "zstd", "pigz", "pbzip2"],
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

