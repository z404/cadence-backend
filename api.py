# Hiding linting error in importing BaseModel
# pylint: disable=no-name-in-module
from typing import Optional

import main
from fastapi import FastAPI
from pydantic import BaseModel



# Creating a class for the received data
class req(BaseModel):
    prompt: str
    songlist: str


class req_playlist(BaseModel):
    prompt: str
    playlist: str


# FastAPI Object
app = FastAPI()

# Function to run backend on a playlist url
@app.post("/playlist")
async def get_song_playlist(data: req_playlist):
    """
    This function is triggered when a POST request is received at '/playlist'
    The POST data required is in the form:
        {
            prompt: "example prompt",
            playlist: "playlist url"
        }
    """
    # Converting received data to dict to make it accessable
    retdata = dict(data)
    return main.apicall_playlist(retdata["prompt"], retdata["playlist"])


# Function to run backend on a list of song IDs seperated with a semicolon
@app.post("/")
async def get_song(data: req):
    """
    This function is triggered when a POST request is received at '/playlist'
    The POST data required is in the form:
        {
            prompt: "example prompt",
            playlist: "playlist url"
        }
    """
    # Converting received data to dict to make it accessable
    retdata = dict(data)
    return main.apicall_songlist(retdata["prompt"], retdata["songlist"])


# Get method to check if backend is online
@app.get("/")
async def check_status():
    return {"status": "online"}
