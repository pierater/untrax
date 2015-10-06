import os
import json
from acoustid import fingerprint_file, lookup, parse_lookup_result
from pprint import pprint
import sys

API_KEY = '1wAvr7OY' # acoustid unique key

def log(flag, artist = '', title = '', oldDir = '', newDir = ''):

    '''
    Does its best to log any successes or failures
    Opens or creates log.txt
    TODO: Make less messy
    '''

    logFile = open('log.txt', 'a+')
    logFile.write(flag + "<" + artist + ">   <" + title + ">  < " + oldDir + ">   <" + newDir + ">\n")
    logFile.close()

def fixStrings(string):
    '''
    Attempts to eliminate any name issues with strings
    if a new one is found, then it can be added here
    '''
    string = string.replace('/', '-')
    return string


def renameFiles(data, db, subdir, rootDir, file):
    '''
    This parses through the data from acoustid
    It will also attempt to rename each file accordingly
    if it cannot rename, it will lof error
    '''
    title = '' # initialize to empty string to prevent nonetype issues
    artist = '' # but they still sometimes get by
    ren = ''
    if(db):
        ren = 'RENAMED' # Checks for the db flag and sets this to be appended to all file names
    for i in data: # data is a list of tuples, so must iterate through them
        title = i[2]
        artist = i[3]
    try: # try to strip all whitespace and make sure encoding is of proper type
        title = title.strip() # to prevent linux ascii issues
        artist = artist.strip()
        title = title.encode('utf-8')
        artist = artist.encode('utf-8')
        artist = fixStrings(artist)
        title = fixStrings(title)
    except:
        log('ERROR===>', 'Nonetype', 'err', subdir + '/' + str(file))
        return


    if not os.path.exists(rootDir + artist): # check if artists path exists, then make it
        os.mkdir(rootDir + artist)
        log("SUCCESS", "Created directory", rootDir + artist)

    try:
        print subdir + '/' + file # just a thing to look at while running the code, should move to progessbar eventually
        os.rename(subdir + '/' + file, rootDir + artist + '/' + title + ren + ".mp3")
        log("SUCCESS", artist, title)
    except:
        log("ERROR===>", artist, title, subdir + '/' + str(file), rootDir + artist + '/' + title)


def findSongs(rootDir, db = False, rm = False):
    '''
    Will go through every directory and file in rootDir
    For each file, it will be fingerprinted and changed
    if flags are set, then they will do other things such
    as deleting non mp3 and empty dirs
    Also has a debug option
    '''
    for subdir, dirs, files in os.walk(rootDir): # for every file and folder in rootDir
        for file in files:
            if(file.endswith('.mp3')): # Only checks files that are mp3a
                duration, fingerprint = fingerprint_file(os.path.join(subdir, file)) # runs acoustid fingerprint algorithm
                obj = lookup(API_KEY, fingerprint, duration) # gets json obj info from acoustid
                data = parse_lookup_result(obj)
                renameFiles(data, db, subdir, rootDir, file) # attempts to rename files before moving on to next file
            else: # If it is not a mp3
                if(rm): # checks rm flag
                    try:
                        os.remove(subdir + '/' + file)
                        log("SUCCESS", "Removed", subdir + '/' + file)
                    except:
                        log("ERROR===>", "tried to remove ->", file, subdir + '/' + file)
                    try:
                        os.rmdir(subdir)
                        log("SUCCESS", "Removed", subdir)
                    except:
                        log("ERROR===>", "Tried to remove folder")
                    continue
        for dirs in subdir: # checks all actual directories that are EMTPY
            if(rm):
                try:
                    os.rmdir(subdir)
                    log("SUCCESS", "Removed", subdir)
                except:
                    log("ERROR===>", "Tried to remove folder", subdir)



if __name__ == "__main__":
    '''
    checks argument flags and runs findSongs
    '''
    db = False
    rm = False

    if '-h' in sys.argv:
        print "USAGE:\n     untrax [Music Dir] -[flags]"
        print
        print "-h: print options"
        print "-db: Will rename all files with appeneded 'RENAMED'"
        print "-rm: Will remove any non .mp3 files"
        exit()

    if len(sys.argv) == 1:
        print "You must include a music path!"
        print "Usage: 'untrax ~/Music/'"
        print "use -h for a list of options"
        exit()
    else:
        rootDir = sys.argv[1]
    if '-db' in sys.argv:
        db = True
    if '-rm' in sys.argv:
        rm = True
    findSongs(rootDir, db, rm)

