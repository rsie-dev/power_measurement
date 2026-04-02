from pathlib import Path

from pyinfra.operations import files


def install_ssh_keys(user: str):
    ssh_keys = _collect_ssh_keys()
    authorized_keys = Path(f"/home/{user}/.ssh/authorized_keys")

    # Ensure .ssh directory exists
    files.directory(
        name="Ensure .ssh directory exists",
        path=str(authorized_keys.parent),
        user=user,
        group=user,
        mode="700",
        _sudo=True,
    )

    # Ensure authorized_keys exists
    files.file(
        name="Ensure authorized_keys file exists",
        path=str(authorized_keys),
        user=user,
        group=user,
        mode="600",
        touch=True,
        _sudo=True,
    )

    # Add each key
    for key in ssh_keys:
        files.line(
            name=f"Ensure SSH key is present: {key[:30]}...",
            path=authorized_keys,
            line=key,
            present=True,
            _sudo=True,
        )


def _collect_ssh_keys():
    key_folder = Path.cwd() / "ssh_keys"
    ssh_keys = []
    for path in sorted(key_folder.glob("*.pub")):
        if path.is_file():
            key = path.read_text().strip()
            ssh_keys.append(key)
    return ssh_keys