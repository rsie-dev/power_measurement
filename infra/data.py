
from pyinfra.api import deploy
from pyinfra.operations import files


@deploy("Data folder")
def setup_data_folder(sync: bool):
    files.directory(
        name="Create data folder",
        path="/data",
        mode="755",
        _sudo=True,
    )

    if sync:
        files.sync(
            name="Sync data folder",
            src="data/",
            dest="/data",
            _sudo=True,
        )
