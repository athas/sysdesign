import os
import time
from datetime import datetime, timedelta
from time import mktime

FILENAME_LOCKED   = 'lock'   # filename used when a file is locked
FILENAME_UNLOCKED = 'unlock' # filename used when a file is unlocked
RENAME_TIMEOUT    = 2        # time to wait between each retry to lock file
FILE_SUFFIX       = ';0'     # suffix for a file's revision-directory
DIR_SUFFIX        = ';*'     # suffix for a directory's revision-directory
LANDMARK_TIME     = 3600     # If revisions are within this boundary, they should be merged
TEST              = True     # Enables testmode


# Creates a list of all the files and directories.
def list_dir (rootdir):
    files = list()
    dirs = list()
    entries = os.listdir(rootdir)
    for entry in entries:
        if entry.endswith(FILE_SUFFIX):
            files.append(entry)
        elif entry.endswith(DIR_SUFFIX):
            dirs.append(entry)
    os.chdir(rootdir)
    return files,dirs

# Creates a list containing all file-revisions and their timestamp.
def list_revisions (rootdir ,file):
    revisions = list()
    os.chdir(file)
    for file in os.listdir('.'):
           if file not in [FILENAME_LOCKED, FILENAME_UNLOCKED]:
               time = os.path.getctime(file) # should be good enough, as files should never be changed after a newer revision is available
               revisions.append([file,time])

    os.chdir(rootdir)
    return sorted(revisions)

# Locks a file
def lock_file (rootdir, file):
    # Change dir to file-revision-dir
    os.chdir(file)
    for t in range(1,4):
        try: 
            os.rename(FILENAME_UNLOCKED, FILENAME_LOCKED)
            break
        except:
            print 'Locking file failed ' + str(t) + ' times'
            time.sleep(RENAME_TIMEOUT)
    os.chdir(rootdir)

def unlock_file (rootdir, file):
    os.chdir(file)
    try:
        os.rename(FILENAME_LOCKED, FILENAME_UNLOCKED)
    except:
        print 'Failed in unlocking file'
    os.chdir(rootdir)

def clean_file (rootdir, file):
    revisions = list_revisions(rootdir, file)
    last_timestamp = 0
    last_filename = ''
    
    t = datetime.now()
    last_month = mktime((t+timedelta(days=-30)).timetuple())

    for rev,time in revisions:
        if time > last_month:
            # If the revision is never than one month, let the rest be.
            break;
        else:
            if time - LANDMARK_TIME < last_timestamp:
                # Remove old revision
                os.remove(last_filename)
        last_filename = rev
        last_timestamp = time
    
    print revisions

def cleaner (rootdir):
    os.chdir(rootdir)
    files, dirs = list_dir(rootdir)
    for file in files:
        clean_file(rootdir, file)
    for dir in dirs:
        cleaner(rootdir+dir)

cleaner('/home/troels/test/')
