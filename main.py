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
    Return data: None
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
