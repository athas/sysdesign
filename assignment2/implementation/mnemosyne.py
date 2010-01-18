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

def getName(path):
    """
    Returns the last part of a path
    """
    m = re.match('(.*/)([^/]+)',path);
    if m:
        return (m.group(1), m.group(2))
    else:
        return ('/','')


class Mnemosyne(Fuse):

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
                res = os.path.join(res, readlink(res+'/'+p))
        
        return res

    def real_path (self, path):
        if self.root[-1] == '/':
            res = self.root[0:-1]
        else:
            res = self.root
        return res + path

    def add_version(self, path, mode=-1, dev=-1):
        print '****** add_version', path, oct(mode), dev
        
        # check if symlink to newest version exists
        nolink = True
        if os.path.exists(self.real_path(path)):
            nolink = False

        # version step size
        if nolink:
            # skip a version to indicate deleted file
            i = 2
        else:
            i = 1

        # check if dir with file versions exist
        v = 0        
        (p,n) = getName(path)
        d = self.real_path(p)+n+';0'
        if not os.path.exists(d):
            # it didnt, create it
            os.mkdir(d)
        else:
            # find the next version number
            vname = ''
            stat = False
            for file in listdir(d):
                try:
                    if int(file) >= v:
                        v = int(file)+i
                        vname = d+'/'+file
                        stat = os.stat(vname)
                except ValueError:
                    pass

        # create the new version only if:
        #   - its a completely new version, v == 0
        #   - the file hasent been deleted and thus should be skipped, i > 1
        # copy old version if:
        #   - the newest version isent empty, st_size > 0
        # else dont add a new version, use the newest one since its empty
        if v == 0 or i > 1:
            os.mknod(d+'/'+str(v), mode, dev)
        elif stat != False and stat.st_size > 0:
            os.mknod(d+'/'+str(v), stat.st_mode, stat.st_dev)
            fd = open(self.convert_path(path), O_WRONLY)
            try:
                os.write(fd, self.read(path, stat.st_size, 0))
            finally:
                close(fd)
        else:
            return None

        # make the new symlink
        if not nolink:
            os.unlink(self.real_path(path))
        return os.symlink(n+';0/'+str(v),self.real_path(path))

    def getattr(self, path):
        print '*** getattr', path
        return lstat (self.convert_path (path))

    def opendir(self, path):
        print '*** opendir', path
        return 0

    def readdir(self, path, info):
        print '*** readdir', path
        if re.match('.*;([0-9]+|\*)$', path):
            res = []
            p = self.convert_path (path)
            for f in listdir (self.convert_path (path)):
                m = re.match('(.*);(0|\*)$', f)
                if m:
                    if m.group(2) == '*':
                        res.append(Direntry (m.group(1)))
                    elif m.group(2) == '0':
                        for r in listdir(p + '/' + f):
                            res.append(Direntry (m.group(1) + ';' + r))
            return res
        else:
            return [Direntry (f) for f in listdir (self.convert_path (path))
                    if not re.match('.*;(0|\*)$', f)]

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
        (p,n) = getName(path)
        d = self.real_path(p)+n+';*'
        if not os.path.exists(d):
            os.mkdir(d, mode)
        return os.symlink(n+';*',self.real_path(path))

    def mknod ( self, path, mode, dev ):
        print '*** mknod', path, oct(mode), dev
        return self.add_version(path, mode, dev)

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
        """
        check if newPath;0 / newPath;* exist (depending on it being a file or adir)
        yes, errno.EEXIST (??) custom error would be nice here
        no, do rename on both symlink and containing folder
        """
        
        # check if the target file/directory already exist
        (pold,nold) = getName(oldPath)
        (pnew,nnew) = getName(newPath)
        if os.path.isdir(self.real_path(oldPath)):
            if os.path.exists(self.real_path(newPath)+';*'):
                return errno.EEXIST
            else:
                # rename the dir
                os.rename(self.real_path(pold)+nold+';*',self.real_path(pnew)+nnew+';*')
                # unlink symlink
                unlink(self.real_path(oldPath))
                # create new symlink
                os.symlink(nnew+';*', self.real_path(newPath))
        else:
            if os.path.exists(self.real_path(newPath)+';0'):
                return errno.EEXIST
            else:
                # get the most reson version number
                (p,n) = getName( self.convert_path(oldPath) )
                # rename the file dir
                os.rename(self.real_path(pold)+nold+';0',self.real_path(pnew)+nnew+';0')
                # unlink symlink
                print self.real_path(oldPath)
                unlink(self.real_path(oldPath))
                # create new symlink
                print self.real_path(newPath), nnew+';0/'+n
                os.symlink(nnew+';0/'+n, self.real_path(newPath))
        return None

    def rmdir ( self, path ):
        print '*** rmdir', path
        return os.unlink(self.real_path(path))

    def statfs ( self ):
        print '*** statfs'
        return -errno.ENOSYS

    def symlink ( self, targetPath, linkPath ):
        print '*** symlink', targetPath, linkPath
        return -errno.ENOSYS

    def truncate ( self, path, size ):
        print '*** truncate', path, size

        # add a version if needed
        self.add_version(path)

        fd = open(self.convert_path(path), O_WRONLY)
        try:
            os.ftruncate(fd, size)
        finally:
            close (fd)
        return None

    def unlink ( self, path ):
        print '*** unlink', path
        return os.unlink(self.real_path(path))

    def utime ( self, path, times ):
        print '*** utime', path, times
        return os.utime(self.real_path(path), times)

    def write ( self, path, buf, offset ):
        print '*** write', path, buf, offset
        
        # add a version if needed
        self.add_version(path)

        fd = open(self.convert_path(path), O_WRONLY)
        try:
            os.lseek(fd, offset, SEEK_SET)
            return os.write(fd, buf)
        finally:
            close (fd)


if __name__ == "__main__":
    fuse.fuse_python_api = (0,2)
    fs = Mnemosyne()
    fs.parser.add_option(mountopt="root", metavar="PATH", default='/',
                         help="directory for physical storage [default: %default]")
    fs.flags = 0
    fs.multithreaded = 0
    fs.parse(values=fs)
    fs.main()
