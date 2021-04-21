# Hiding linting error in importing BaseModel
# pylint: disable=no-name-in-module
from typing import Optional

import main
import spotipy
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
app = FastAPI(
    title="Cadence API",
    description="This API is the backend for Cadence app",
    redocs_url="/api/v2/redocs",
)

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
    try:
        return main.apicall_playlist(retdata["prompt"], retdata["playlist"])
    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 404 or e.http_status == 400:
            return {"error": "Check validity of given playlist url", "errormessage": e}
        else:
            return {"error": "internal", "errormessage": e}
    except Exception as e:
        return {"error": "internal", "errormessage": e}


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
    try:
        return main.apicall_songlist(retdata["prompt"], retdata["songlist"])
    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 404 or e.http_status == 400:
            return {"error": "Check validity of given track IDs", "errormessage": e}
        else:
            return {"error": "internal", "errormessage": e}
    except TypeError as e:
        return {"error": "Check if all song IDs are valid", "errormessage": e}
    except IndexError as e:
        return {"error": "Check format of input", "errormessage": e}
    except Exception as e:
        return {"error": "internal", "errormessage": e}


# Get method to check if backend is online
@app.get("/")
async def check_status():
    return {"status": "online"}
