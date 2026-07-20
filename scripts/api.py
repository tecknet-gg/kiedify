import os
import uuid
import asyncio
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from router import Router

app = FastAPI(
    title="Kiedify API",
    description = "Music TTS",
    version = "1.0.0"
)

musicDir = os.path.abspath(os.path.join(os.getcwd(), "Music"))
stitchedDir = os.path.join(musicDir, "Stitched")
os.makedirs(stitchedDir, exist_ok=True)

artistsData = [
    ("Weezer", "male"),
    ("Red Hot Chili Peppers", "male"),
    ("The Dismemberment Plan", "male"),
    ("The Pretenders", "female"),
    ("Fleetwood Mac", "female"),
    ("Paramore", "female")
]

router = Router(dir=musicDir, artists=artistsData)
router.rvc.indexModels()

taskDb: [str, Dict[str, Any]] = {}
taskQueue: List[str] = []

executor = ThreadPoolExecutor(max_workers=2)

class GenerationRequest(BaseModel):
    artist: str = Field(..., title="Red Hot Chili Peppers")
    text: str = Field(..., title="Double double toil and trouble, fire burn and cauldron bubble")
    mode: str = Field("basic", example="basic")
    patching: bool = Field(True, description="Enable RVC fallback for missing words")

    class Config:
        aliasGenerator = None


class TaskResponse(BaseModel):
    taskId: str
    status: str
    message: str

def processAudioJob(taskId: str, request: GenerationRequest):
    try:
        taskDb[taskId]["status"] = "processing"
        outputFile = f"{taskId}.mp3"

        matchedArtist = None
        for name, gender in artistData:
            if name.lower() == requests.artist.lower()
                matchedArtist = name
                break

        if not matchedArist:
            raise ValueError(f"Arist '{request.artist}' is not supported")

        if request.mode == "basic":
            generatedFile = router.basicMatch(text=request.text, artist=matchedArtist, patching=request.patching)

        elif request.mode == "semantic":
            generatedFile = router.semanticMatch(text=request.text, artist=matchedArtist)

        elif request.mode == "rvc":
            generatedFile = router.rvcMatch(text=request.text, artist=matchedArtist, filename=outputFile)

        else:
            raise ValueError(f"Unknown mode '{request.mode}'")

        if not generatedFile or not os.path.exists(generatedFile):
            raise RuntimeError(f"File {generatedFile} does not exist")

        taskDb[taskId]["status"] = "completed"
        taskDb[taskId]["filePath"] = f"{generatedFile}"

    except Exception as e:
        print(f"Error processing {taskId}: {e}")
        taskDb[taskId]["status"] = "failed"
        taskDb[taskId]["error"] = str(e)

    finally:
        if taskId in taskDb:
            taskQueue.remove(taskId)
