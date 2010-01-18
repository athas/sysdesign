import os
import time

FILENAME_LOCKED   = 'lock'   # filename used when a file is locked
FILENAME_UNLOCKED = 'unlock' # filename used when a file is unlocked
RENAME_TIMEOUT    = 2        # time to wait between each retry to lock file

def lock_file (file):
    # Change dir to file-revision-dir
    for t in range(1,4):
        try: 
            os.rename(file + '/' + FILENAME_UNLOCKED, file + '/' + FILENAME_LOCKED)
            return True
        except:
            print 'Locking file failed ' + str(t) + ' times'
            time.sleep(RENAME_TIMEOUT)
    return False

def unlock_file (file):
    try:
        os.rename(file + '/' + FILENAME_LOCKED, file + '/' + FILENAME_UNLOCKED)
    except:
        print 'Failed in unlocking file'
