import os
import hashlib
import pathlib


def to_posix(filename: str) -> str:
    return pathlib.PurePath(r"{}".format(filename)).as_posix()


def to_uri(filename: str) -> str:
    if filename in ["", ".", "..", "c:", "C:"]:
        return ""
    if not os.path.isabs(filename):
        uri = pathlib.Path(filename).resolve().as_uri()
        uri = uri[len(pathlib.Path(".").resolve().as_uri()) + 1 :]
    else:
        uri = pathlib.Path(filename).resolve().as_uri()
    return uri


def get_hash(filename: str) -> str:
    """
    Calculate the MD5 hash of a file path.
    On Windows system, prior to hash calculation, filename path is converted to posix style
    (i.e using '/' separator) to ensure hash is system independent.
    """
    return hashlib.md5(
        to_posix(filename).encode("utf-8"), usedforsecurity=False
    ).hexdigest()


def get_extension(filename: str) -> str:
    return pathlib.Path(filename).suffix[1:]
