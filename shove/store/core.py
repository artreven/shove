# -*- coding: utf-8 -*-

from copy import deepcopy
from urllib import url2pathname
from threading import Condition

from shove._compat import anydbm, synchronized
from shove.core import BaseStore, FileBase, SimpleBase

__all__ = ['SimpleStore', 'MemoryStore', 'FileStore', 'DbmStore']


class SimpleStore(SimpleBase, BaseStore):

    '''
    Single-process in-memory store.

    The shove psuedo-URL for a simple store is:

    simple://
    '''

    def __init__(self, engine, **kw):
        super(SimpleStore, self).__init__(engine, **kw)


class ClientStore(SimpleStore):

    '''
    Base for stores where updates have to be committed.
    '''

    def __init__(self, engine, **kw):
        super(ClientStore, self).__init__(engine, **kw)
        if engine.startswith(self.init):
            self._engine = url2pathname(engine.split('://')[1])

    def __getitem__(self, key):
        return self.loads(super(ClientStore, self).__getitem__(key))

    def __setitem__(self, key, value):
        super(ClientStore, self).__setitem__(key, self.dumps(value))


class SyncStore(ClientStore):

    '''Base for stores where updates have to be committed.'''

    def __getitem__(self, key):
        return self.loads(super(SyncStore, self).__getitem__(key))

    def __setitem__(self, key, value):
        super(SyncStore, self).__setitem__(key, value)
        try:
            self.sync()
        except AttributeError:
            pass

    def __delitem__(self, key):
        super(SyncStore, self).__delitem__(key)
        try:
            self.sync()
        except AttributeError:
            pass


class MemoryStore(SimpleStore):

    '''
    Thread-safe in-memory store.

    The shove psuedo-URL for a memory store is:

    memory://
    '''

    def __init__(self, engine, **kw):
        super(MemoryStore, self).__init__(engine, **kw)
        self._lock = Condition()

    @synchronized
    def __getitem__(self, key):
        return deepcopy(super(MemoryStore, self).__getitem__(key))

    __setitem__ = synchronized(SimpleStore.__setitem__)
    __delitem__ = synchronized(SimpleStore.__delitem__)


class FileStore(FileBase, BaseStore):

    '''
    Filesystem-based object store

    shove's psuedo-URL for filesystem-based stores follows the form:

    file://<path>

    Where the path is a URL path to a directory on a local filesystem.
    Alternatively, a native pathname to the directory can be passed as the
    'engine' argument.
    '''


class DbmStore(SyncStore):

    '''
    DBM Database Store.

    shove's psuedo-URL for DBM stores follows the form:

    dbm://<path>

    Where <path> is a URL path to a DBM database. Alternatively, the native
    pathname to a DBM database can be passed as the 'engine' parameter.
    '''

    init = 'dbm://'

    def __init__(self, engine, **kw):
        super(DbmStore, self).__init__(engine, **kw)
        self._store = anydbm.open(self._engine, 'c')
        try:
            self.sync = self._store.sync
        except AttributeError:
            pass
