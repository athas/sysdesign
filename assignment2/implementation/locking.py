import os

FILENAME_LOCKED   = 'lock'   # filename used when a file is locked
FILENAME_UNLOCKED = 'unlock' # filename used when a file is unlocked
RENAME_TIMEOUT    = 2        # time to wait between each retry to lock file

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
