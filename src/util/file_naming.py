import hashlib
import pathlib

def to_posix(filename: str) -> str:
    return pathlib.PurePath(r"{}".format(filename)).as_posix()

def to_uri(filename: str) -> str:
    return pathlib.Path(filename).resolve().as_uri()[len(pathlib.Path('.').resolve().as_uri())+1:]

def get_hash(filename: str) -> str:
    """
    Calculate the MD5 hash of a file  path
    on Windows system, prio to hash calculation, filename path is convert to unix style (i.e using '/' separator) to ensure hash is system independent
    """
    return hashlib.md5(to_posix(filename).encode('utf-8')).hexdigest()

def get_extension(filename: str) -> str:
    return pathlib.Path(filename).suffix[1:]
