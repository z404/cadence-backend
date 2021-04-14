# Hiding linting error in importing BaseModel
# pylint: disable=no-name-in-module
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel


# Creating a class for the received data
class req(BaseModel):
    prompt: str
    songlist: str = None


# FastAPI Object
app = FastAPI()

# Defining method and path with a decorator
@app.post("/")
async def create_item(item: req):
    # Testing provided data
    new = dict(item)
    new["prompt"] = "hello " + new["prompt"]
    return new


# Run the server with the command 'uvicorn FastAPITest:app --reload'
# As this is a post method, it can be run by going to 'localhost:8000/docs' and pressing 'try it out'
