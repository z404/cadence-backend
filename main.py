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

import spotipy
import spotipy.oauth2 as oauth2
import yaml
from snips_nlu import SnipsNLUEngine
from snips_nlu.dataset import dataset
from snips_nlu.default_configs import CONFIG_EN
from snips_nlu.exceptions import PersistingError


# Function to create NLP model
def create_nlp_model():
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
def detect_intent(nlumodel: SnipsNLUEngine, string: str):
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
def newSpotifyObject(cli_id: str, cli_sec: str):
    """
    This function takes input of a spotify account's Client ID and Client Secret, and creates a new spotify object
    Parameters required: Client ID and Client Secret for Spotify (strings)
    Return data: Authenticated Spotify Object (spotipy.client.Spotify)
    """
    # Creating spotify auth object to authenticate spotify object
    auth = oauth2.SpotifyClientCredentials(client_id=cli_id, client_secret=cli_sec)
    # Get access token from spotify
    token = auth.get_access_token(as_dict=False)
    # Create spotify object
    spotify = spotipy.Spotify(auth=token)
    # Returning Spotify Object
    return spotify

def get_playlist_tracks(spotify: spotipy.client.Spotify, playlist_id: str):
    """
    This function takes an authenticated Spotify client, and a playlist ID, and returns a list of song IDs of every song in the playlist
    Parameters required: Authenticated Spotify Client, and playlist ID or URL
    Return Data: List of song IDs in the playlist
    """
    #Get first 100 or lesser songs' details
    results = spotify.playlist_items(playlist_id)
    #Check if there are more songs for which details need to be obtained
    tracks = results["items"]
    while results["next"]:
        #Get next 100 songs' details, and append to the list of results already obtained
        results = spotify.next(results)
        tracks.extend(results["items"])
    #Create new list to hold track IDs
    track_id = []
    #Extract each track ID from the extracted information, and append to track_id list
    for i in tracks:
        if i["track"]["id"] != None:
            track_id.append("spotify:track:" + i["track"]["id"])
    #Return all track IDs
    return track_id

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

    # Initializing Spotify Credentials
    with open("creds.yaml") as file:
        creds = yaml.full_load(file)

    cli_id = creds["spotify client id"]
    cli_sec = creds["spotify client secret"]

    # In main flow, start firebase listener here

    # Testing detect_intent()
    # string = input()
    # output_intent = detect_intent(nluengine, string)
    # print(output_intent)
    # return 0

    # Testing newSpotifyObject()
    playlist_song_ids = get_playlist_tracks(newSpotifyObject(cli_id, cli_sec),"https://open.spotify.com/playlist/3It5BuAucg59mpLzILUS70?si=8MrxgpaWQhmvzLl1sBA_2A")
    print(playlist_song_ids)


# Start main function
main()
