from pyinfra.operations import apt
from pyinfra.api import deploy


@deploy("Develop")
def develop():
    apt.packages(
        name="Install SCM tools",
        packages=["git"],
        no_recommends=True,
        _sudo=True,
    )
    apt.packages(
        name="Install python",
        packages=["python3", "python3-venv", "python3-pip"],
        no_recommends=True,
        _sudo=True,
    )
