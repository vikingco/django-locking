class Error(Exception):
    pass


class LockError(Error):
    '''
    Base class for errors arising from attempts to acquire the lock.

    >>> try:
    ...   raise LockError
    ... except Error:
    ...   pass
    '''
    pass


class LockFailed(LockError):
    '''
    Lock creation failed for some unknown reason.

    >>> try:
    ...   raise LockFailed
    ... except LockError:
    ...   pass
    '''
    pass


class AlreadyLocked(LockFailed):
    '''
    Some other process is locking the object.

    >>> try:
    ...   raise AlreadyLocked
    ... except LockFailed:
    ...   pass
    '''
    pass


class UnlockError(Error):
    '''
    Base class for errors arising from attempts to release the lock.

    >>> try:
    ...   raise UnlockError
    ... except Error:
    ...   pass
    '''
    pass


class NotLocked(UnlockError):
    '''
    Raised when an attempt is made to unlock an unlocked file.

    >>> try:
    ...   raise NotLocked
    ... except UnlockError:
    ...   pass
    '''
    pass


class RenewalError(Error):
    '''
    Base class for errors arising from attempts to renew the lock.

    >>> try:
    ...   raise RenewalError
    ... except Error:
    ...   pass
    '''
    pass


class NonexistentLock(RenewalError):
    '''
    Raised when an attempt is made to renew a nonexistent lock.

    >>> try:
    ...   raise NonexistentLock
    ... except RenewalError:
    ...   pass
    '''
    pass


class Expired(RenewalError):
    '''
    Raised when an attempt is made to renew an expired lock.

    >>> try:
    ...   raise Expired
    ... except RenewalError:
    ...   pass
    '''
    pass