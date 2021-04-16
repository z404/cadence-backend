# Hiding linting error in importing BaseModel
# pylint: disable=no-name-in-module
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel

import main


# Creating a class for the received data
class req(BaseModel):
    prompt: str
    songlist: str = None


# FastAPI Object
app = FastAPI()


# Starting main program
# Returning NLUEngine and MLModel is wrong, will change in next commit
NLUEngine, MLModel = main.startup()


# Defining method and path with a decorator
@app.post("/playlist")
async def get_song(data: req):
    # Predicting song with provided data
    retdata = dict(data)
    intent = main.detect_intent(NLUEngine, retdata["prompt"])["intent"]
    url = retdata["songlist"]
    prepared = main.prep_songs(
        main.get_playlist_tracks(main.newSpotifyObject(), url)["IDs"],
        main.newSpotifyObject(),
    )
    ret = main.predict_tag(prepared, MLModel)
    # Returning song
    return {"song": main.get_best_match(intent, ret), "intent": intent}


# Get method to check if backend is online
@app.get("/")
async def check_status():
    return {"status": "online"}
