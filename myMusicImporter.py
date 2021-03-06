import os
import sys
import spotipy
import spotipy.util as util
from rdioapi import Rdio
from urllib2 import HTTPError

def rdioCollectionForUser(rdio, user):
    """
    
    """
    try:
        # authenticate against the Rdio service
        url = rdio.begin_authentication('oob')
        print 'Go to: %s' % (url)
        verifier = raw_input("Then enter the code: ").strip()
        rdio.complete_authentication(verifier)

        # get tracks in collection
        tracks = rdio.call('getTracksInCollection')

    except HTTPError as e:
        # if we have a protocol error, print it
        print(e.read()) 
        return 1 #TODO: Return an error message?

    return tracks 


def getArtistForTrack(track):
    return track['artists'][0]['name']


def spotifyTrackIDForSong(sp, songName, artist):
    """
    Returns the Spotify track ID of the first song found matching the given
    song name and artist. 
    """
    query = "track:" + songName
    #query = "artist:" + artist + "+track:" + songName
    #TODO: What if search results are empty?
    matchingTracks = sp.search(query, type='track')['tracks']['items']
    matchingTracksWithArtist = [track for track in matchingTracks
                                if getArtistForTrack(track) == artist]
    
    bestMatch = max(matchingTracksWithArtist, key=lambda track:
                                                    track['popularity'])
    print ("%-30s" * 2) % (getArtistForTrack(bestMatch), bestMatch['name'])
    return matchingTracksWithArtist[0]['id'].encode('ascii', 'ignore')


def main(argv):
    if len(argv) != 3:
        print "Usage: python myMusicImporter.py <spotify-username> <rdio-username>"
        return 1
    
    spotifyUser = argv[1]
    rdioUser = argv[2]

    scope = 'user-library-modify'
    token = util.prompt_for_user_token(spotifyUser, scope)
    
    RDIO_CONSUMER_KEY = os.getenv('RDIO_CONSUMER_KEY')
    RDIO_CONSUMER_SECRET = os.getenv('RDIO_CONSUMER_SECRET')

    if RDIO_CONSUMER_KEY and RDIO_CONSUMER_SECRET:
        rdio = Rdio(RDIO_CONSUMER_KEY, RDIO_CONSUMER_SECRET, {})
        rdioCollection = rdioCollectionForUser(rdio, rdioUser)
    else:
        print "Both RDIO_CONSUMER_KEY and RDIO_CONSUMER_SECRET must be \
                set as environment variables."
        return 1 #TODO: return an error code?

    tids = [] # spotify track ids
    if token:
        sp = spotipy.Spotify(auth=token)
        for rdioTrack in rdioCollection:
            try:
                tids.append(spotifyTrackIDForSong(sp, rdioTrack['name'], rdioTrack['artist']))
            except ValueError:
                print "No Spotify track found for Rdio Track: %s Artist:%s \
                        Continuing..." % \
                        (rdioTrack['name'], rdioTrack['artist'])
        
       #TODO: fix this bug 
        print tids
        for tid in tids:
            tid_ls = [tid]
            try:
                sp.current_user_saved_tracks_add(tracks=tid_ls)
            except:
                print "Error for tid: %s" % (tid)
        #results = sp.current_user_saved_tracks_add(tracks=tids)
        #TODO: What to do with results? 
        sp.trace = False
    else:
        print "Can't get token for ", spotifyUser


if __name__ == '__main__':
    main(sys.argv)
