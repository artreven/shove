# -*- coding: utf-8 -*-
'''
FTP-accessed stores

shove's URL for FTP accessed stores follows the standard form for FTP URLs
defined in RFC-1738:

ftp://<user>:<password>@<host>:<port>/<url-path>
'''

from ftplib import FTP, error_perm

from shove.core import BaseStore
from shove._compat import StringIO, urlsplit

__all__ = ['FTPStore']


class FTPStore(BaseStore):

    def __init__(self, engine, **kw):
        super(FTPStore, self).__init__(engine, **kw)
        user = kw.get('user', 'anonymous')
        password = kw.get('password', '')
        spliturl = urlsplit(engine)
        # Set URL, path, and strip 'ftp://' off
        base, path = spliturl[1], spliturl[2] + '/'
        if '@' in base:
            auth, base = base.split('@')
            user, password = auth.split(':')
        self._store = FTP(base, user, password)
        # Change to remote path if it exits
        try:
            self._store.cwd(path)
        except error_perm:
            self._makedir(path)
        self._base, self._user, self._password = base, user, password
        self._updated, self ._keys = True, None

    def __getitem__(self, key):
        try:
            local = StringIO()
            # Download item
            self._store.retrbinary('RETR %s' % key, local.write)
            self._updated = False
            return self.loads(local.getvalue())
        except:
            raise KeyError(key)

    def __setitem__(self, key, value):
        local = StringIO(self.dumps(value))
        self._store.storbinary('STOR %s' % key, local)
        self._updated = True

    def __delitem__(self, key):
        try:
            self._store.delete(key)
            self._updated = True
        except:
            raise KeyError(key)

    def _makedir(self, path):
        # makes remote paths on an FTP server
        paths = list(reversed([i for i in path.split('/') if i != '']))
        store = self._store
        while paths:
            tpath = paths.pop()
            store.mkd(tpath)
            store.cwd(tpath)

    def keys(self):
        '''Returns a list of keys in a store.'''
        if self._updated or self._keys is None:
            rlist, nlist = list(), list()
            nappend = nlist.append
            # remote directory listing
            self._store.retrlines('LIST -a', rlist.append)
            for rlisting in rlist:
                # split remote file based on whitespace
                rfile = rlisting.split()
                # append tuple of remote item type & name
                if rfile[-1] not in ('.', '..') and rfile[0].startswith('-'):
                    nappend(rfile[-1])
            self._keys = nlist
        return self._keys
