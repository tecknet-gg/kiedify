import os
import queue
from fastapi import FastAPI, HTTPException, BackgroundTasks
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

