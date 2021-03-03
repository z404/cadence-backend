'''
Standalone program to test the usage of spotipy
Spotipy package helps this program interact with spotify applications
Features:
 - Provided a track ID/Url, it can get all details of the track, including:
   - Song parameters (intensity, dancability, loudness etc.)
   - Title, Url, ID
   - Album name, Disc number, Artist name, Song number, song art cover url
   - 30 Second demo of the song (full song can be obtained if authenticated as user)
 - Given a playlist ID/Url, it can get all details of the playlist, including:
   - All songs in the playlist (uses pagination, and returns 100 songs at a time)
   - Playlist title, cover, playlist creator's name, url, id.
   - Private playlists work as long as the url is valid

This project requires both these features to work
A spotify developer account is needed to generate client id and secret
requirements: spotipy (https://github.com/plamere/spotipy)

'''
#Importing spotify packages
import spotipy
import spotipy.oauth2 as oauth2

#Opening credential file
with open('creds.txt') as file:
    creds = file.readlines()
    cli_id = creds[0].rstrip('\n')
    cli_sec = creds[1].rstrip('\n')

#Creating spotify auth object to authenticate spotify object
auth = oauth2.SpotifyClientCredentials(
    client_id=cli_id,
    client_secret=cli_sec
)
#Get access token from spotify
token = auth.get_access_token()
#Create spotify object
spotify = spotipy.Spotify(auth=token)

#Showing features of a song
#features = spotify.track('https://open.spotify.com/track/1tm4Bl2E5RwTevOiBs4gtH?si=X7KuHtN6TQ6lZ15ijB4v4A')
#print(features)

#Showing features of a playlist, including songs present in it (returns only 100 songs)
#response = spotify.playlist_items('https://open.spotify.com/playlist/2kUbABZX9A2m0b6fopyouM?si=7gk-1UcdTN-oJnRpwZlFwA')
#print(response)

#Getting audio features of a song from spotify
#print(spotify.audio_features(['https://open.spotify.com/track/1tm4Bl2E5RwTevOiBs4gtH?si=X7KuHtN6TQ6lZ15ijB4v4A']))

#Function to get all songs of the playlist, not just 100 songs
def get_playlist_tracks(playlist_id):
    results = spotify.playlist_items(playlist_id)
    tracks = results['items']
    while results['next']:
        results = spotify.next(results)
        tracks.extend(results['items'])
    return tracks

#Gets all details of all songs in thee playlist
track_list = get_playlist_tracks('https://open.spotify.com/playlist/3It5BuAucg59mpLzILUS70?si=kAj3vfBESyOHF8c-2d5qNw')
featurelst = []
#getting features
for i in track_list:
    if i['track']['id'] != None:
        #Need to optimise this api call, it takes way too long
        featurelst.append(spotify.audio_features(['spotify:track:'+i['track']['id']]))
    
        

