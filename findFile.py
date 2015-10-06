

import os
import json
from acoustid import fingerprint_file, lookup, parse_lookup_result
from pprint import pprint
import sys

API_KEY = '1wAvr7OY'

def log(artist, title, oldDir, newDir):

    logFile = open('log.txt', 'w')
    logFile.write("artist   title   oldDir   newDir\n")
    logFile.write("================================\n")
    logFile.write(artist + "   " + title + "   " + oldDir + "   " + newDir + "\n")
    logFile.close()


if __name__ == "__main__":

    if len(sys.argv) == 1:
        print "You must include a music path!"
        print "Usage: 'untrax ~/Music/'"
        exit()
    else:
        rootDir = sys.argv[1]

    for subdir, dirs, files in os.walk(rootDir):
        for file in files:
            if(file.endswith('.mp3')):
                
                diration, fingerprint = fingerprint_file(os.path.join(subdir,file))
                obj = lookup(API_KEY, fingerprint, diration)
                data = parse_lookup_result(obj)
                for i in data:
                    title = i[2]
                    artist = i[3]
                title = title.strip()
                artist = artist.strip()
                title = title.encode('utf-8')
                artist = artist.encode('utf-8')
                print "title: %s" % ( title)
                print "artist: %s" % (artist)

                if not os.path.exists(rootDir + artist):
                    print rootDir + artist
                    os.mkdir(rootDir + artist)
                print subdir + file
                print rootDir + artist + '/' + title + "RENAMED.mp3"
                try:
                    os.rename(subdir + '/' + file, rootDir + artist + '/' + title + "RENAMED.mp3")
                except:
                    log(artist, title, subdir + '/' + file, rootDir + artist + '/' + title)

            else:
                continue

