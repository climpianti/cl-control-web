"""Prepare this App's private data, then run the web service unprivileged.

Supervisor owns the configuration file. Its content is never read, copied,
logged or changed here. The dedicated service group receives read-only access.
No recursive ownership changes, public permissions, or HA configuration edits.
"""
from __future__ import annotations

import os
from pathlib import Path
import pwd
import stat
import sys

DATA_DIR = Path("/data")
OPTIONS_FILE = DATA_DIR / "options.json"


def prepare_private_data(directory: Path, uid: int, gid: int) -> None:
    """Only prepare the exact App data directory, never its children."""
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = directory.lstat()
    if not stat.S_ISDIR(info.st_mode):
        raise RuntimeError("Private App data directory is invalid")
    os.chown(directory, uid, gid, follow_symlinks=False)
    os.chmod(directory, 0o700, follow_symlinks=False)


def prepare_service_options(path: Path, gid: int) -> bool:
    """Grant the dedicated service group read access to one regular file.

    O_NOFOLLOW prevents following a substituted symlink. Work on the opened
    descriptor so a replaced pathname cannot redirect the permission change.
    An absent file is allowed for offline/development use.
    """
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    except FileNotFoundError:
        return False
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise RuntimeError("App configuration must be one regular file")
        os.fchown(fd, 0, gid)
        os.fchmod(fd, 0o640)
    finally:
        os.close(fd)
    return True


def main() -> None:
    if os.geteuid() != 0:
        raise RuntimeError("App startup requires container initialization privileges")
    service = pwd.getpwnam("clcontrol")
    if service.pw_uid == 0 or service.pw_gid == 0:
        raise RuntimeError("A non-root service account is required")
    prepare_private_data(DATA_DIR, service.pw_uid, service.pw_gid)
    present = prepare_service_options(OPTIONS_FILE, service.pw_gid)
    print("CL Control: private configuration access prepared" if present
          else "CL Control: no App options file; offline defaults remain active", flush=True)
    os.execvp("gosu", ["gosu", "clcontrol", sys.executable, "app/server.py"])


if __name__ == "__main__":
    main()
