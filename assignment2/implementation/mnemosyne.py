#!/usr/bin/python

from fuse import *
import fuse
from time import time

import stat    # for file properties
import os      # for filesystem modes (O_RDONLY, etc)
from os import *
import re
import errno   # for error number codes (ENOENT, etc)
               # - note: these must be returned as negatives

def dirFromList(list):
    """
    Return a properly formatted list of items suitable to a directory listing.
    [['a', 'b', 'c']] => [[('a', 0), ('b', 0), ('c', 0)]]
    """
    return [[(x, 0) for x in list]]

def getDepth(path):
    """
    Return the depth of a given path, zero-based from root ('/')
    """
    if path == '/':
        return 0
    else:
        return path.count('/')

def getParts(path):
    """
    Return the slash-separated parts of a given path as a list
    """
    if path == '/':
        return ['/']
    else:
        return path.split('/')

class Mnemosyne(Fuse):
    """
    """

    def __init__(self, *args, **kw):
        Fuse.__init__(self, *args, **kw)
        self.root = '/'
        print 'Init complete.'

    def convert_path (self, path):
        """
        Convert a path specified by the user into a path to the actual file path.
        """
        parts = getParts (path)
        res = self.root
        for p in parts[1:]:
            m = re.match('(.*);([0-9]+|\*)$', p)
            if m:
                if m.group(2) == '*':
                    if m.group(1) != '':
                        res = res + '/' + m.group(1) + ';*';
                else:
                    res = res + '/' + m.group(1) + ';0' + '/' + m.group(2);
            else:
                res = os.path.join(self.root, readlink(res+'/'+p))
        return res

    def getattr(self, path):
        print '*** getattr', path
        return lstat (self.convert_path (path))

    def opendir(self, path):
        print '*** opendir', path
        return 0

    def readdir(self, path, info):
        print '*** readdir', path
        versions = re.match('.*;([0-9]+|\*)$', path)
        return [Direntry (f) for f in listdir (self.convert_path (path))
                if (versions and bool(re.match('.*;([0-9]+|\*)$', f)))
                or (not (versions or bool(re.match('.*;([0-9]+|\*)$', f))))]

    def getdir(self, path):
        print '*** getdir', path
        return self.readdir (path)

    def mythread ( self ):
        print '*** mythread'
        return -errno.ENOSYS

    def chmod ( self, path, mode ):
        print '*** chmod', path, oct(mode)
        return -errno.ENOSYS

    def chown ( self, path, uid, gid ):
        print '*** chown', path, uid, gid
        return -errno.ENOSYS

    def fsync ( self, path, isFsyncFile ):
        print '*** fsync', path, isFsyncFile
        return -errno.ENOSYS

    def link ( self, targetPath, linkPath ):
        print '*** link', targetPath, linkPath
        return -errno.ENOSYS

    def mkdir ( self, path, mode ):
        print '*** mkdir', path, oct(mode)
        return -errno.ENOSYS

    def mknod ( self, path, mode, dev ):
        print '*** mknod', path, oct(mode), dev
        return -errno.ENOSYS

    def open ( self, path, flags ):
        print '*** open', path, flags
        return None

    def read ( self, path, length, offset ):
        print '*** read', path, length, offset
        fd = open(self.convert_path (path), O_RDONLY)
        try:
            lseek(fd, offset, SEEK_SET)
            return read(fd, length)
        finally:
            close (fd)

    def readlink ( self, path ):
        print '*** readlink', path
        return -errno.ENOSYS

    def release ( self, path, flags ):
        print '*** release', path, flags
        return None

    def rename ( self, oldPath, newPath ):
        print '*** rename', oldPath, newPath
        return -errno.ENOSYS

    def rmdir ( self, path ):
        print '*** rmdir', path
        return -errno.ENOSYS

    def statfs ( self ):
        print '*** statfs'
        return -errno.ENOSYS

    def symlink ( self, targetPath, linkPath ):
        print '*** symlink', targetPath, linkPath
        return -errno.ENOSYS

    def truncate ( self, path, size ):
        print '*** truncate', path, size
        return -errno.ENOSYS

    def unlink ( self, path ):
        print '*** unlink', path
        return -errno.ENOSYS

    def utime ( self, path, times ):
        print '*** utime', path, times
        return -errno.ENOSYS

    def write ( self, path, buf, offset ):
        print '*** write', path, buf, offset
        return -errno.ENOSYS

if __name__ == "__main__":
    fuse.fuse_python_api = (0,2)
    fs = Mnemosyne()
    fs.parser.add_option(mountopt="root", metavar="PATH", default='/',
                         help="directory for physical storage [default: %default]")
    fs.flags = 0
    fs.multithreaded = 0
    fs.parse(values=fs)
    fs.main()
