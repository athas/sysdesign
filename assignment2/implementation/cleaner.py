import os
import time
from datetime import datetime, timedelta
from time import mktime
from locking import *

FILENAME_LOCKED   = 'lock'   # filename used when a file is locked
FILENAME_UNLOCKED = 'unlock' # filename used when a file is unlocked
RENAME_TIMEOUT    = 2        # time to wait between each retry to lock file
FILE_SUFFIX       = ';0'     # suffix for a file's revision-directory
DIR_SUFFIX        = ';*'     # suffix for a directory's revision-directory
TEST              = False    # Enables testmode
TEST_DATA = {
    'file1.txt;0' :
        [['file1.txt;1', 1213270794.0],
         ['file1.txt;2', 1213271798.0],
         ['file1.txt;3', mktime((datetime.now()+timedelta(days=-31)).timetuple())],
         ['file1.txt;4', mktime((datetime.now()+timedelta(days=-29)).timetuple())],
         ['file1.txt;5', mktime((datetime.now()+timedelta(days=-1)).timetuple())]],
    'file2.txt;0' :
        [['file2.txt;1', 1213270794.0],
         ['file2.txt;2', 1213271798.0],
         ['file2.txt;3', 1213271898.0],
         ['file2.txt;4', 1213271998.0],
         ['file2.txt;5', mktime((datetime.now()+timedelta(days=-1)).timetuple())]]
    }


class Cleaner:

    def __init__(self, dir, landmark_time, landmark_limit):
       self.landmark_time = landmark_time
       self.landmark_limit = landmark_limit
       self.rootdir = dir
       self.cleaner()

    # Creates a list of all the files and directories.
    def list_dir (self):
        files = list()
        dirs = list()
        entries = list()
        if TEST:
            entries = TEST_DATA.keys()
        else:
            entries = os.listdir(self.rootdir)

        for entry in entries:
            if entry.endswith(FILE_SUFFIX):
                files.append(self.rootdir + entry)
            elif entry.endswith(DIR_SUFFIX):
                dirs.append(self.rootdir + entry)
        return files,dirs

    # Creates a list containing all file-revisions and their timestamp.
    def list_revisions (self, file):
        revisions = list()
        if TEST:
            return TEST_DATA[file]

        for rev in os.listdir(file):
            if rev not in [FILENAME_LOCKED, FILENAME_UNLOCKED]:
                time = os.path.getctime(file) # should be good enough, as files should never be changed after a newer revision is available
                revisions.append([self.rootdir + file + rev,time])

        return sorted(revisions)

    def clean_file (self, file):
        revisions = self.list_revisions(file)
        last_timestamp = 0
        last_filename = ''
        
        # The time it moves from KeepAll- to Landmark-retention
        landmark_limit = mktime((datetime.now()+timedelta(days=-30)).timetuple())

        for rev,time in revisions:
            if time > landmark_limit:
                # If the revision is never than one month, let the rest be.
                break;
            else:
                if time - self.landmark_time < last_timestamp:
                    # Remove old revision
                    if TEST:
                        print 'Removing ' + last_filename
                    else:
                        os.remove(last_filename)
            last_filename = rev
            last_timestamp = time

    def cleaner (self):
        files, dirs = self.list_dir()
        for file in files:
            if lock_file(file):
                self.clean_file(file)
                unlock_file(file)
        for dir in dirs:
            Cleaner(rootdir+dir, self.landmark_time, self.landmark_limit)

cleaner = Cleaner('/home/troels/test/', 3600, 31)
