# Copyright (c) 2005, the Lawrence Journal-World
# Copyright (c) 2006 L. C. Rees
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    1. Redistributions of source code must retain the above copyright notice, 
#       this list of conditions and the following disclaimer.
#    
#    2. Redistributions in binary form must reproduce the above copyright 
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
#    3. Neither the name of Django nor the names of its contributors may be used
#       to endorse or promote products derived from this software without
#       specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

'''Berkeley Source Database based cache.'''

import bsddb
import time
try:
    from cStringIO import StringIO
except ImportError:
    from cStringIO import StringIO
from shove import synchronized
from shove.cache.memory import MemoryCache

__all__ = ['BsdCache']


class BsdCache(MemoryCache):

    '''Class for caching with a Berkeley Source Database.'''    

    def __init__(self, engine, **kw):
        super(BsdCache, self).__init__(engine, **kw)
        if engine.startswith('bsd://'): engine = engine.split('://')[1]
        self._cache = bsddb.hashopen(engine)
        
    @synchronized
    def __getitem__(self, key):
        local = StringIO(self._cache[key])
        exp = self.loads(local.readlines().rstrip())
        # Remove item if expired
        if exp < time.time():
            del self[key]
            raise KeyError('Key not in cache.')
        return self.loads(local.readlines())
                
    @synchronized
    def __setitem__(self, key, value):
        if len(self._cache) > self._max_entries: self._cull()
        local = StringIO()
        local.write(self.dumps(time.time() + self.timeout) + '\n')
        local.write(self.dumps(value))
        self._cache[key] = local.getvalue()