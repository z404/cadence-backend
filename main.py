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
import random
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
from xgboost import XGBClassifier


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
def detect_intent(string: str) -> dict:
    """
    This function detects the intent and the slots a string contains, if it is provided with a trained model and a string
    Parameters required: SnipsNLUEngine object, string
    Return data: Dictionary with keys ['intent','slotflag','slots']

    If slots are not detected, slotflag will be returned as False and vice versa
    """
    global NLUModel
    # Parsing the given string using the pretrained model
    output = NLUModel.parse(string)
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
            # Appending dictionary to final dataset
            dataset = dataset.append(finalsongs, ignore_index=True)

    # Dropping duplicates of the dataset
    dataset = dataset.drop_duplicates(subset=["Name", "Artist"], keep="first")
    # Saving dataset to csv so it is accessable later
    dataset.to_csv("dataset.csv")


# Function to create ML Model pickle file
def create_ML_model() -> XGBClassifier:
    """
    This function creates an XGBoost Classifier and trains it with 'dataset.csv' in the root directory.
    It saves the model for future use, and also returns to model to function call
    Parameters Required: None
    Return Data: Trained XGBClassifier Object (xgboost.sklearn.XGBClassifier)
    """
    # Creating new Model
    model = XGBClassifier()
    # Opening and preprocessing dataset
    dataset = pd.read_csv("dataset.csv")
    columns_to_be_dropped = [
        "Unnamed: 0",
        "type",
        "id",
        "uri",
        "track_href",
        "analysis_url",
        "Artist",
        "Name",
        "Popularity",
        "duration_ms",
    ]
    # Dropping columns
    for i in columns_to_be_dropped:
        if i in dataset.columns:
            dataset = dataset.drop(i, axis=1)
    # Setting 'Tag' Column as prediction column
    Y = dataset["Tag"]
    # Removing 'Tag' Column for X values
    X = dataset.drop(["Tag"], axis=1)
    # Fitting classifier with X and Y
    model.fit(X, Y)
    # Saving classifier using pickle to root directory
    with open("MLModel.pickle", "wb") as handle:
        pickle.dump(model, handle, protocol=pickle.HIGHEST_PROTOCOL)
    # Returning model
    return model


# Function to give a dictionary of song properties
def prep_songs(song_ids: list, spotify: spotipy.client.Spotify) -> pd.DataFrame:
    """
    Songs passed with IDs cannot directly be used in the model. This function preps the song for the ML model
    Parameters Required: List of song ids (from client), authenticated spotify client
    Return Data: Pandas DataFrame of song details, for which classes can now be predicted
    """
    prep_set = []
    curr_number = 0
    tracks = []
    # Get all details of every song passed
    # Can only do 50 at a time, else throws an error of too many ids passed
    while curr_number <= len(song_ids):
        tracks.extend(
            spotify.tracks(song_ids[curr_number : curr_number + 50])["tracks"]
        )
        curr_number += 50
    # Getting audio features of all songs passed
    features = get_audio_features(spotify, song_ids)
    # Combining obtained data into single dictionary
    for i in range(len(features)):
        temp_song = features[i]
        temp_song["Popularity"] = tracks[i]["popularity"]
        temp_song["Name"] = tracks[i]["name"]
        temp_song["Artist"] = tracks[i]["artists"][0]["name"]
        # Adding dictionary to list containing all processed songs
        prep_set.append(temp_song)
    # Converting list of dictionaries to a pandas dataframe
    pred_data = pd.DataFrame(prep_set)
    # Returning Dataframe
    return pred_data


# Function to predict tags for given songs
def predict_tag(pred_data: pd.DataFrame) -> tuple:
    """
    This function predicts a tag given a model and the data for which it needs to predict
    Parameters Required: Prepared data of client song ids, ML model that is pretrained
    Returned data: Tuple of multiple data
        Tuple index 0: Predicted probabilites of each song belonging to one class
        Tuple index 1: List of song ids (in order)
        Tuple index 2: List of song names (in order)
        Tuple index 3: List of classes (in order for predicted probabilities)
    """
    global MLModel
    # Saving names and ids for return
    names = pred_data["Name"]
    ids = pred_data["id"]
    # Preprocessing client input data, dropping unwanted columns
    columns_to_be_dropped = [
        "Unnamed: 0",
        "type",
        "id",
        "uri",
        "track_href",
        "analysis_url",
        "Artist",
        "Name",
        "Popularity",
        "duration_ms",
    ]
    for i in columns_to_be_dropped:
        if i in pred_data.columns:
            pred_data = pred_data.drop(i, axis=1)
    # Predicting the probability of each song belonging to each class
    # The highest probability defines its class
    pred = MLModel.predict_proba(pred_data)
    # predclass = model.predict(pred_data)
    return pred, ids, names, MLModel.classes_


# Function to get top 10 of each tag
def get_best_match(intent: str, preds: tuple) -> str:
    """
    This funtion takes in predicted intent, and predicted probabilities, and returns the best match for both of them
    It picks a single song from a range of top 10 best matches
    Parameters Required: Intent of given prompt, and predicted tuple from predict_tag function
    Return Data: Single string of song ID
    """
    # Get index of required intent to process specific probability
    if intent not in ["gym", "sleep", "study", "yoga"]:
        if intent == "reminder":
            intent = "yoga"
        elif intent == "travel":
            intent = "gym"
        else:
            intent = "gym"
    index = list(preds[3]).index(intent.capitalize())
    combinedlist = []
    # Combine name, probability and id lists into one list (for easy sorting)
    for i in range(len(preds[0])):
        combinedlist.append([preds[0][i], preds[1][i], preds[2][i]])

    # Sort key function to return specific song
    def sortlst(element):
        return element[0][index]

    # Sort combined list
    combinedlist.sort(key=sortlst, reverse=True)
    # Choose top 10 songs to randomize from
    listofchosensongs = [i[1] for i in combinedlist[:10]]

    # Names of chosen songs, uncomment to access
    # nameofsongs = [i[2] for i in combinedlist[:10]]

    final_choice = random.choice(listofchosensongs)
    return "spotify:track:" + final_choice


# Function to verify all major files are present
def startup() -> tuple:
    """
    This function returns the NLU model and the ML model after verifying its presence in the root directory
    It also creates a trainable dataset if it isnt present in the root directory
    Parameters Required: None
    Return data: tuple
        index 1: NLU Model
        index 2: ML Model
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

    if not os.path.isfile("MLModel.pickle"):
        mlmodel = create_ML_model()
    else:
        # Model exists, load into program
        with open("MLModel.pickle", "rb") as handle:
            mlmodel = pickle.load(handle)
    return nluengine, mlmodel


# Function that is called only when the file is directly run
def main():
    """
    This function is used for testing purposes, and is run only when the main file is run
    """
    global NLUModel, MLModel
    NLUModel, MLModel = startup()

    # Testing all functions
    phrase = input("Enter a prompt: ")
    playlist_link = input("Enter a playlist url: ")
    intent = detect_intent(phrase)["intent"]
    prepared = prep_songs(
        get_playlist_tracks(newSpotifyObject(), playlist_link)["IDs"],
        newSpotifyObject(),
    )
    ret = predict_tag(prepared)
    print(get_best_match(intent, ret))


# Function called by api to compute best match from playlist
def apicall_playlist(prompt: str, songlist: str) -> dict:
    """
    This function is called when a request with a playlist link is received
    It runs calls all nesessary functions to finally return the best song choice for the given prompt
    Parameters required: (sent from received request) given prompt and playlist link
    Return Data: Dictionary containing best match and detected intent
    """
    # Obtain intent
    intent = detect_intent(prompt)["intent"]
    # Obtain dataframe of prepared data
    prepared = prep_songs(
        get_playlist_tracks(newSpotifyObject(), songlist)["IDs"],
        newSpotifyObject(),
    )
    # Get predicted tags
    ret = predict_tag(prepared)
    # Get best match from predicted data and return
    return {"song": get_best_match(intent, ret), "intent": intent}


# Function called by an api to compute best match from list of song IDs
def apicall_songlist(prompt: str, songlist: str) -> dict:
    """
    This function is called when a request with a list of songs is received
    It runs calls all nesessary functions to finally return the best song choice for the given prompt
    Parameters required: (sent from received request) given prompt and a list of songs
    Return Data: Dictionary containing best match and detected intent
    """
    # Obtain intent
    intent = detect_intent(prompt)["intent"]
    # Create list of songs from a string
    songs = songlist.split(";")[:-1]
    # Obtain dataframe of prepared data
    prepared = prep_songs(
        songs,
        newSpotifyObject(),
    )
    # Get predicted tags
    ret = predict_tag(prepared)
    # Get best match from predicted data and return
    return {"song": get_best_match(intent, ret), "intent": intent}


# Start main function
if __name__ == "__main__":
    # This is only for running tests
    main()
else:
    # Creating Global variables to hold NLU and ML models, as they can be accessed from anywhere
    global NLUModel, MLModel
    NLUModel, MLModel = startup()
