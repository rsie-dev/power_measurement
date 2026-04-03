from pyinfra.operations import apt
from pyinfra.api import deploy


@deploy("Compressors")
def compressors():
    compressor_tools = ["gzip", "pigz",
                        "bzip2", "pbzip2", "lbzip2",
                        "bzip3",
                        "xz-utils",
                        "lzip", "plzip",
                        "lzop", "lz4",  "zstd",
                        "brotli", "zopfli",
                        ]
    apt.packages(
        name="Install compression tools",
        packages=compressor_tools,
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

