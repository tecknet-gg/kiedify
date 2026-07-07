import os
import uuid
import threading
from typing import Dict, Any, List
import queue
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from router import Router
app = FastAPI(title="Kiedify", version="0.1")
musicDir = os.getcwd().replace("scripts", "Music")
stitched = os.path.join(musicDir, "Stitched")

artists = ["Weezer", "Red Hot Chili Peppers", "The Dismemberment Plan", "The Pretenders", "Fleetwood Mac", "Paramore"] #load from .env maybe?
genders = ["male", "male", "male", "female", "female", "female"]

artists = tuple(zip(artists, genders))

os.makedirs(stitched, exist_ok=True)


router = Router(dir=musicDir, artists=artists)

tasks: Dict[str, str] = {}
executionQueue = queue.Queue()

class GenerationRequest(BaseModel):
    options: Dict[str, Any]

def processingWorker():
    while True:
        pass
    # parse the options and route everything to generate the resultant file

workerThread = threading.thread(target=processingWorker, daemon=True)
workerThread.start()


@app.get("/artists")
async def getArtists(): #give the frontend all the available artists
    artists = [
        {"name": name, "gender": gender}
        for name, gender in artists
    ]

@app.get("/queueGeneration")
async def getQueue(request:GenerationRequest):
    options = request.options

    if "artist" not in options or "text" not in options:
        raise HTTPException(
            status_code=400,
            detail="Missing required parameters, please provide 'artist' and 'text'",
        )
    taskId = str(uuid.uuid4())
    tasks[taskId] = "pending"

    executionQueue.put((taskId, options))
    return {
        "status": "queued",
        "uuid": taskId,
        "message": f"Task received and queued. Try /status/{taskId} to get generation status.",
    }

@app.get("/retrieveFile")
async def retrieveFile():
    #if exists, return file
    #else say file doesn't exist
    return

@app.get("/status/{taskId}")
async def getStatus(taskId: str):
    #return true if done
    #return queue position + time estimate otherwise
    return