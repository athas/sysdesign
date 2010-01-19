import os
import time
import sys
import getopt
from datetime import datetime, timedelta
from time import mktime
from locking import *

FILENAME_LOCKED   = 'lock'   # filename used when a file is locked
FILENAME_UNLOCKED = 'unlock' # filename used when a file is unlocked
RENAME_TIMEOUT    = 2        # time to wait between each retry to lock file
FILE_SUFFIX       = ';0'     # suffix for a file's revision-directory
DIR_SUFFIX        = ';*'     # suffix for a directory's revision-directory

class Cleaner:

    def __init__(self, dir, landmark_time, landmark_limit):
       self.landmark_time = float(landmark_time)
       self.landmark_limit = float(landmark_limit)
       self.rootdir = dir
       self.cleaner()

    # Creates a list of all the files and directories.
    def list_dir (self):
        files = list()
        dirs = list()
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

        for rev in os.listdir(file):
            if rev not in [FILENAME_LOCKED, FILENAME_UNLOCKED]:
                fullpath = file + '/' + rev
                time = os.path.getctime(fullpath) # should be good enough, as files should never be changed after a newer revision is available
                revisions.append([fullpath,time])

        return sorted(revisions)

    def clean_file (self, file):
        revisions = self.list_revisions(file)
        last_timestamp = 0
        last_filename = ''
        
        # The time it moves from KeepAll- to Landmark-retention
        landmark_limit = mktime((datetime.now()-timedelta(days=self.landmark_limit)).timetuple())

        for rev,time in revisions:
            if time > landmark_limit:
                # If the revision is newer than one month, let the rest be.
                break;
            else:
                if time - self.landmark_time < last_timestamp:
                    # Remove old revision
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
            Cleaner(dir + '/', self.landmark_time, self.landmark_limit)

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "", ['landmarktime=', 'landmarklimit=', 'dir='])
    except getopt.GetoptError, err:
        print str(err)
        sys.exit(2)
    root = ""
    landmark_time = 0
    landmark_limit = 0
    for o, a in opts:
        if o == "--dir":
            root = a
        elif o == "--landmarktime":
            landmark_time = a
        elif o == "--landmarklimit":
            landmark_limit = a
        else:
            sys.exit(2)
    if root != "" and landmark_time > 0 and landmark_limit > 0:
        Cleaner(root, landmark_time, landmark_limit)
    else:
        print('usage: cleaner.py --dir=<filesystem dir> --landmarktime=<landmark time> --landmarklimit=<landmark_limit>')
        sys.exit(2)

if __name__ == "__main__":
    main()
