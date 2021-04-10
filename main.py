"""
main.py
Main program to act as the server backend for the application
Pre-requisites:
 - Pre-trained model pickle file

Flow of the main program:
 -> Listen to incoming messages from firebase
 -> Once a message is recieved, validate the information received
 -> After validation, perform NLP on the received string to derive intent of the string
 -> If playlist link is received, process the link to obtain all songs and thier properties
 -> If song list is received, process each song to obtain song properties
 -> Load pre-trained model and predict tags for each received song
 -> Extract all songs that have the same tag as the derived intent above
 -> Select one random song out of the choices, and return the chosen song ID to firebase in given format
"""

import os
import pickle
import shutil

import numpy as np
import pandas as pd
import spotipy
import spotipy.oauth2 as oauth2
import yaml
from snips_nlu import SnipsNLUEngine
from snips_nlu.dataset import dataset
from snips_nlu.default_configs import CONFIG_EN
from snips_nlu.exceptions import PersistingError


# Function to create NLP model
def create_nlp_model() -> SnipsNLUEngine:
    """
    This function trains a new ML model from the given dataset. It then saves the model in the root directory of the project with the file name: nlpumodel
    This function will only be called once, at the start of the program, if nlumodel file is not detected in the current directory
    Parameters required: None
    Return data: Trained SnipsNLUEngine object
    """
    # Creating a barebones engine
    engine = SnipsNLUEngine(config=CONFIG_EN)

    # Creating dataset from yaml files present in nlputrain directory
    data = dataset.Dataset.from_yaml_files(
        "en", ["./nlputrain/" + i for i in os.listdir("./nlputrain/") if ".yaml" in i]
    )

    # Training the engine with given dataset
    engine.fit(data)

    # Persisting the engine so it can be used easily later
    # Persisting engine is saved in nlumodel folder
    try:
        engine.persist("nlumodel")
    except PersistingError:
        print("Old NLP file still exists. Deleting..")
        # Removing old model files using shutil
        shutil.rmtree("nlumodel")
        engine.persist("nlumodel")

    print("NLP model has been created and saved in directory: nlumodel")
    # Returning trained engine
    return engine


# Function to detect intent of string
def detect_intent(nlumodel: SnipsNLUEngine, string: str) -> dict:
    """
    This function detects the intent and the slots a string contains, if it is provided with a trained model and a string
    Parameters required: SnipsNLUEngine object, string
    Return data: Dictionary with keys ['intent','slotflag','slots']

    If slots are not detected, slotflag will be returned as False and vice versa
    """
    # Parsing the given string using the pretrained model
    output = nlumodel.parse(string)
    # Obtaining intent from parsed string
    intent = output["intent"]["intentName"]
    # Checking for slots
    slotflag = True if output["slots"] != [] else False
    # Obtaining slots from parsed string
    slots = output["slots"]
    # Returning obtained information
    return {"intent": intent, "slotflag": slotflag, "slots": slots}


# Function to get new Spotify Object
def newSpotifyObject() -> spotipy.client.Spotify:
    """
    This function creates a new spotify object using the creds.yaml file in the root folder to authenticate the object
    Parameters required: None
    Return data: Authenticated Spotify Object (spotipy.client.Spotify)
    """
    # Initializing Spotify Credentials
    with open("creds.yaml") as file:
        creds = yaml.full_load(file)

    cli_id = creds["spotify client id"]
    cli_sec = creds["spotify client secret"]

    # Creating spotify auth object to authenticate spotify object
    auth = oauth2.SpotifyClientCredentials(client_id=cli_id, client_secret=cli_sec)
    # Get access token from spotify
    token = auth.get_access_token(as_dict=False)
    # Create spotify object
    spotify = spotipy.Spotify(auth=token)
    # Returning Spotify Object
    return spotify


# Function to get playlist tracks
def get_playlist_tracks(spotify: spotipy.client.Spotify, playlist_id: str) -> list:
    """
    This function takes an authenticated Spotify client, and a playlist ID, and returns a list of song details of every song in the playlist
    Parameters required: Authenticated Spotify Client, and playlist ID or URL
    Return Data: List of song details in the playlist
    """
    # Get first 100 or lesser songs' details
    results = spotify.playlist_items(playlist_id)
    # Check if there are more songs for which details need to be obtained
    tracks = results["items"]
    while results["next"]:
        # Get next 100 songs' details, and append to the list of results already obtained
        results = spotify.next(results)
        tracks.extend(results["items"])
    # Create new list to hold track IDs
    track_id = {}
    # Extract each track detail from the extracted information, and append to track_id list
    track_id["IDs"] = []
    track_id["Name"] = []
    track_id["Artist"] = []
    track_id["Popularity"] = []
    for i in tracks:  # Looping through all tracks
        if i["track"]["id"] != None:
            track_id["IDs"].append(
                "spotify:track:" + i["track"]["id"]
            )  # Get ID of song
            track_id["Name"].append(i["track"]["name"])  # Get Name of song
            track_id["Artist"].append(
                i["track"]["artists"][0]["name"]
            )  # Get main Artist of song
            track_id["Popularity"].append(
                i["track"]["popularity"]
            )  # Get popularity of songs
    # Return all track IDs
    return track_id


# Function to get all features of a given list of song ids
def get_audio_features(spotify: spotipy.client.Spotify, track_ids: list) -> list:
    """
    This function gets the following features of a spotify song, hundred songs at a time:
    ["acousticness", "danceability", "durationms", "energy", "instrumentalness", "key", "liveness", "loudness", "mode", "speechiness"\
        , "tempo", "timesignature", "valence"]
    Getting more than 100 songs will result in a bad request error
    Parameters Required: Authenticated Spotify Client, and list of song IDs
    Return Data: List of dictionary containing song features
    """
    # Getting features
    featurelst = []
    count = 0
    while count <= len(track_ids):
        # Get 100 songs' features at a time. Getting any more will result in bad result error
        featurelst.extend(spotify.audio_features(track_ids[count : count + 100]))
        count = count + 100
    return featurelst


# Function to create dataset with certain songs
def create_dataset() -> None:
    """
    This function creates a csv file based on urls given below for specific tags. The csv will later be used to create the ML model,
    which will be used to classify songs into the below tags
    Tags: ['Study', 'Gym','Yoga','Sleep']
    Parameters Required: None
    Return Data: None
    """
    # Record of all urls that contribute to a tag
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
    dataset = pd.DataFrame()

    # Iterating through each link to download song information
    for tag, urls in playlist_dict.items():
        for url in urls:
            # Getting all songs' details in a playlist
            songs = get_playlist_tracks(newSpotifyObject(), url)
            # Getting song paramenters
            song_features = get_audio_features(newSpotifyObject(), songs["IDs"])
            finalsongs = []

            # Combining aquired information into one dictionary
            for i in range(len(song_features)):
                # Creating a temporary song dictionary to save info
                song = {}
                try:
                    song.update(song_features[i])
                    song.update(
                        {
                            "Name": songs["Name"][i],
                            "Artist": songs["Artist"][i],
                            "Popularity": songs["Popularity"][i],
                        }
                    )
                    song.update({"Tag": tag})
                    finalsongs.append(song)
                except:
                    pass
            print(len(finalsongs))
            # Appending dictionary to final dataset
            dataset = dataset.append(finalsongs, ignore_index=True)

    # Dropping duplicates of the dataset
    dataset = dataset.drop_duplicates(subset=["Name", "Artist"], keep="first")
    # Saving dataset to csv so it is accessable later
    dataset.to_csv("dataset.csv")


def main():
    """
    This is the main function, which starts the main flow of the servers
    """
    # Initializing NLPU
    if os.path.isdir("nlumodel"):
        # If trained model exists, load it
        nluengine = SnipsNLUEngine.from_path("nlumodel")
        print("Loaded local nlumodel save found in directory")
    else:
        # If model doesnt exist, then create a new one
        nluengine = create_nlp_model()
        print("Trained and loaded new model")

    # Checking for training dataset
    if not os.path.isfile("dataset.csv"):
        # If dataset doesnt exist, create it
        create_dataset()
        print("Dataset Created and saved")
    else:
        # If dataset exists, proceed
        print("Dataset Found")

    # TODO
    # Check if ML model for song classification exists, and add to program
    # Start firebase listener here

    # Testing detect_intent()
    # string = input()
    # output_intent = detect_intent(nluengine, string)
    # print(output_intent)
    # return 0

    # Testing newSpotifyObject(), playlist_song_ids(), and get_audio_features()
    # playlist_song_ids = get_playlist_tracks(
    #     newSpotifyObject(),
    #    "https://open.spotify.com/playlist/3It5BuAucg59mpLzILUS70?si=8MrxgpaWQhmvzLl1sBA_2A",
    # )
    # print(playlist_song_ids)
    # print(get_audio_features(newSpotifyObject(), playlist_song_ids))


# Start main function
main()
