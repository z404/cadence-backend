"""
This script is to create a dataset that is required to predict the type of a given song
The different classes of songs are
 - Travel              242+273 Songs
 - Study/Exam          300+161 Songs
 - Gym/Workout         152+140 Songs
 - Yoga                203+103 Songs
 - Meetings/Reminders  370 Songs
 - Sleep               208+107 Songs
"""

import time

import pandas as pd
import spotipy
import spotipy.oauth2 as oauth2
import yaml

# Creating dict of playlist urls
playlist_dict = {
    # "Travel": [
    #     "https://open.spotify.com/playlist/0yXe2Ok6uWm15lzStDZIyN?si=4q7fe4A3QHGX-gXVCLHuwg",
    #     "https://open.spotify.com/playlist/4du84WTLemvL4Pp2DAvlby?si=xuE2b2bXQRijycPi9kLlzw",
    # ],
    "Study": [
        "https://open.spotify.com/playlist/0vvXsWCC9xrXsKd4FyS8kM?si=aEAuimj4R8-7encKbkv8lg"
    ],
    "Gym": [
        "https://open.spotify.com/playlist/0L33OqcgnqcdtUDhUAyfPW?si=vSKSLbnZQpig_rnjXmdLAg",
        "https://open.spotify.com/playlist/0sPiindbOuUlsUevklWtEO?si=D9699hIAR8CejSVGeKO1Cg",
    ],
    "Yoga": [
        "https://open.spotify.com/playlist/37i9dQZF1DX9uKNf5jGX6m?si=W65q_28zT0mkIwuodAQxMQ",
        "https://open.spotify.com/playlist/59Mv9oVmx1wIQAaOoLWceY?si=Euwj3oZjQs2bugNCH67I1A",
    ],
    # "Meetings": [
    #     "https://open.spotify.com/playlist/4LJ5hkgqt04IKw454SUJqV?si=_BdJz3YlS6-biDd4Kv8Fpw"
    # ],
    "Sleep": [
        "https://open.spotify.com/playlist/21wbvqMl5HNxhfi2cNqsdZ?si=oalBs9Q1TyqoV1InDYeaYA",
        "https://open.spotify.com/playlist/37i9dQZF1DWYcDQ1hSjOpY?si=cddd6iLKQVei4H4Ko-VAcg",
    ],
}

# Opening credential file
with open("creds.yaml") as file:
    creds = yaml.full_load(file)


# Creating authenticated spotify object
auth = oauth2.SpotifyClientCredentials(
    client_id=creds["spotify client id"], client_secret=creds["spotify client secret"]
)

token = auth.get_access_token()
spotify = spotipy.Spotify(auth=token)

# Function to get all songs of the playlist, not just 100 songs
def get_playlist_tracks(playlist_id):
    results = spotify.playlist_items(playlist_id)
    tracks = results["items"]
    while results["next"]:
        results = spotify.next(results)
        tracks.extend(results["items"])

    track_id = {}
    for i in tracks:
        try:
            if i["track"]["id"] != None:
                track_id.update(
                    {
                        "spotify:track:"
                        + i["track"]["id"]: {
                            "artist": i["track"]["artists"][0]["name"],
                            "popularity": i["track"]["popularity"],
                            "name": i["track"]["name"],
                        }
                    }
                )
        except TypeError:
            continue
    print(type(track_id))
    return track_id


# Function to get features of given song id list
def get_audio_features(track_ids):
    featurelst = []
    count = 0
    while count <= len(track_ids):
        featurelst.extend(spotify.audio_features(track_ids[count : count + 100]))
        count = count + 100
    return featurelst


# Creating new DataFrame to store new dataset
dataset = pd.DataFrame()

# Iterating through each link to download song information
for tag, urls in playlist_dict.items():
    songs = {}
    for url in urls:
        songs.update(get_playlist_tracks(url))
    features = get_audio_features(list(songs.keys()))
    count = 0
    while count < len(features):
        if features[count] == None:
            del features[count]
        else:
            count += 1
    new_df = pd.DataFrame(features)
    # Adding custom columns
    new_df["Tag"] = tag
    new_df["Artist"] = [j["artist"] for i, j in songs.items()][: len(new_df)]
    new_df["Name"] = [j["name"] for i, j in songs.items()][: len(new_df)]
    new_df["Popularity"] = [j["popularity"] for i, j in songs.items()][: len(new_df)]
    # Adding to main dataset
    dataset = dataset.append(new_df, ignore_index=True)

# Removing duplicate songs
print(dataset.shape)
dataset = dataset.drop_duplicates(subset=["Name", "Artist"], keep="first")
print(dataset.shape)
dataset.to_csv("dataset.csv")
