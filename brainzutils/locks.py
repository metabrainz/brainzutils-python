import contextlib
import fcntl


M_READ, M_WRITE, M_READWRITE = range(3)
_MODES = [
    # open for reading
    (fcntl.LOCK_SH, 'rb'),
    # create for writing
    (fcntl.LOCK_EX, 'wb'),
    # open for reading and writing
    (fcntl.LOCK_EX, 'r+b')
]


@contextlib.contextmanager
def locked_open(filename, mode=M_READ, blocking=True):
    flock_flags, open_mode = _MODES[mode]
    if not blocking:
        flock_flags = flock_flags | fcntl.LOCK_NB

    file = open(filename, open_mode)
    try:
        fcntl.flock(file, flock_flags)
        yield file
    finally:
        file.flush()
        fcntl.flock(file, fcntl.LOCK_UN)
