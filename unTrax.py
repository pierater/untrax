import os
import json
from acoustid import fingerprint_file, lookup, parse_lookup_result
from pprint import pprint
import sys
import unicodedata
import pygn
import eyed3

API_KEY = '1wAvr7OY' # acoustid unique key
ID = '657923086-31EF11ADF7865240B0F637D95890D548'
userID = '26553326526347855-467F6C10EA149D6F779D5368A6188C11'

'''
TODO:
    GUI
'''

def undo():
    '''
    Will read through the backup file and revert all names to old name
    Does not fix directory tree
    '''
    for line in reversed(list(open("backup.txt"))):
        if 'NEW BACKUP' in line:
            break
        line = line.rstrip()
        oldDir, newDir, directory = line.split('|')
        print "Reverting %sI back to %sII" % (directory + oldDir, newDir)
        os.rename(newDir, directory + oldDir)
    os.remove("backup.txt")


def backup(oldDir, newDir, directory):
    '''
    Will write old directory and names to file in order to revert back to in the future
    '''

    back = open("backup.txt", 'a+')
    back.write(oldDir + '|' + newDir + '|' + directory + '\n')
    back.close()

def log(flag, artist = '', title = '', oldDir = '', newDir = ''):

    '''
    Does its best to log any successes or failures
    Opens or creates log.txt
    TODO: Make less messy
    '''

    logFile = open('log.txt', 'a+')
    logFile.write(flag + "<" + artist + ">   <" + title + ">  < " + oldDir + ">   <" + newDir + ">\n")
    logFile.close()


def setTags(artist, album, title, track_num, path):
    '''
    uses eyed3 to change the id3 tags of a given song
    '''
    song = eyed3.load(path)
    track_num = track_num.split(' ')[0]
    if(track_num != ''):
        song.tag.track_num = (unicode(str(track_num), 'utf-8'), None)
    song.tag.artist = unicode(artist, 'utf-8')
    song.tag.album = unicode(album, 'utf-8')
    song.tag.album_artist = unicode(album, 'utf-8')
    song.tag.title = unicode(title, 'utf-8')
    song.tag.save()



def getTrackNum(artist, title, album):
    '''
    Uses pygn to get track number for each song
    '''
    data = pygn.search(ID, userID, artist, album, title)
    try:
        return data['track_number']
    except:
        log('ERRR===>', artist, title, 'Tried to get track_number')
        return 'Failed'
        

def getAlbum(artist, title):
    '''
    Uses pygn to get some missing metadata from another database
    '''
    data = pygn.search(ID, userID, artist, '', title)
    try:
        return data['album_title']
    except:
        log('ERRR===>', artist, title, 'Tried to get album')
        return 'Failed'

def fixStrings(string):
    '''
    Attempts to eliminate any name issues with strings
    if a new one is found, then it can be added here
    '''
    string = string.replace('/', '-')
    string = string.strip()
    string = unicodedata.normalize('NFKD', string).encode('ascii', 'ignore')
    return string


def renameFiles(data, db, subdir, rootDir, file, t):
    '''
    This parses through the data from acoustid
    It will also attempt to rename each file accordingly
    if it cannot rename, it will lof error
    '''
    title = '' # initialize to empty string to prevent nonetype issues
    artist = '' # but they still sometimes get by
    ren = ''
    album = ''
    track_num = ''
    if(db):
        ren = 'RENAMED' # Checks for the db flag and sets this to be appended to all file names
    for i in data: # data is a list of tuples, so must iterate through them
        title = i[2]
        artist = i[3]
        '''
    if(title == None):
        return
    if(artist == None):
        return
        '''
    artist = artist.split(';')[0]
    album = getAlbum(artist, title)
    if(t):
        track_num = getTrackNum(artist, title, album)
        track_num += ' - '
    try: # try to strip all whitespace and make sure encoding is of proper type
        artist = fixStrings(artist)
        title = fixStrings(title)
    except:
        log('ERROR===>', 'Nonetype', 'err', subdir + '/' + str(file))
        return
    print album
    print title
    if not os.path.exists(rootDir + '/' + artist + '/' +  album + '/'): # check if artists path exists, then make it
        os.makedirs(rootDir + '/' + artist + '/' + album + '/')
        log("SUCCESS", "Created directory", rootDir + artist + album)

    try:
        print subdir + '/' + file # just a thing to look at while running the code, should move to progessbar eventually
        os.rename(subdir + '/' + file, rootDir + '/' +  artist + '/' + album + '/' + track_num + title + ren + ".mp3")
        backup(file, rootDir + '/' + artist + '/' + album + '/' + track_num + title + ren + '.mp3', rootDir + '/' + artist + '/' + album + '/')
        log("SUCCESS", artist, title)
    except:
        log("ERROR===>", artist, title, subdir + '/' + str(file), rootDir + artist + '/' + album + '/' + track_num + '-' +  title)

    try:
        setTags(artist, album, title, track_num, rootDir + '/' + artist + '/' + album + '/' + track_num + title + ren + '.mp3')
    except:
        log("FAILED", "Permission denied", title)

def findSongs(rootDir, db = False, rm = False, t = False):
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
                renameFiles(data, db, subdir, rootDir, file, t) # attempts to rename files before moving on to next file
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
    t = False

    if '-h' in sys.argv:
        print "USAGE:\n     untrax [Music Dir] -[flags]"
        print
        print
        print "-h: print options"
        print
        print "-db: Will rename all files with appeneded 'RENAMED'"
        print
        print "-t: Will append a track number to each song"
        print
        print "-rm: Will remove any non .mp3 files and directories"
        print
        print "-rev: Will revert all file names to their previous name"
        print "NOTE-- This will only change back the NAME, not rework the directory structure"
        exit()
    
    if '-rev' in sys.argv:
        undo()
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
    if '-t' in sys.argv:
        t = True

    # This is so that the backup knows where to start
    back = open("backup.txt", 'a+')
    back.write("NEW BACKUP\n")
    back.close()
    findSongs(rootDir, db, rm, t)

