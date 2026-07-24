import os
import uuid
import asyncio
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor

import subprocess
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field, ConfigDict
from starlette.middleware.cors import CORSMiddleware

from router import Router
import uvicorn


cloudflaredProcess = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global cloudflaredProcess

    cloudflaredProcess = subprocess.Popen([
        "cloudflared",
        "--config",
        "/Users/jeevan/.cloudflared/config-api.yml", #point to your cloudflared tunnel config
        "tunnel",
        "run"
    ])
    print("Starting cloudflare tunnel")
    yield

app = FastAPI(
    title="Kiedify API",
    description = "Music TTS",
    version = "1.0.1",
    lifespan=lifespan,
)

taskDb: Dict[str, Dict[str, Any]] = {}
taskQueue: List[str] = []

app.add_middleware( #for cloudflared
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://kiedify.tecknet.dev",
        "https://kiedify.tecknet.dev",
    ],

    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

musicDir = os.path.abspath(os.path.join(os.getcwd(),"..", "Music"))
stitchedDir = os.path.join(musicDir, "Stitched")
os.makedirs(stitchedDir, exist_ok=True)

artistsData = [
    ("Red Hot Chili Peppers", "male"),
    ("Weezer", "male"),
    ("The Pretenders", "female"),
    ("Fleetwood Mac", "female"),
]

router = Router(dir=musicDir, artists=artistsData)
router.rvc.indexModels()


executor = ThreadPoolExecutor(max_workers=2) #two tr

class GenerationRequest(BaseModel):

    model_config = ConfigDict(alias_generator=None)

    artist: str = Field(..., title="Red Hot Chili Peppers") #required input
    text: str = Field(..., title="Double double toil and trouble, fire burn and cauldron bubble") #required input
    mode: str = Field("basic", description="Generation mode: 'basic', 'semantic' or 'rvc'")

    patching: bool = Field(True, description="Enable RVC fallback for missing words")
    fuzzy: bool = Field(True, description="Enable fuzzy matching instead of exact word matching.")


class TaskResponse(BaseModel):
    taskId: str #define outputs
    status: str
    message: str

def processAudioJob(taskId: str, request: GenerationRequest):
    try:
        taskDb[taskId]["status"] = "processing"
        outputFile = f"{str(taskId)[:8]}"
        matchedArtist = None
        for name, gender in artistsData:
            if name.lower() == request.artist.lower():
                matchedArtist = name
                break

        if not matchedArtist:
            raise ValueError(f"t '{request.artist}' is not supported")


        if request.mode == "basic":
            generatedFile = router.basicMatch(text=request.text, artist=matchedArtist, fuzzy=request.fuzzy, patching=request.patching, filename=outputFile)

        elif request.mode == "semantic":
            generatedFile = router.semanticMatch(text=request.text, artist=matchedArtist, file=outputFile, fuzzy=request.patching)

        elif request.mode == "rvc":
            generatedFile = router.rvcSynth(text=request.text, artist=matchedArtist, fileName=outputFile)
            if not generatedFile:
                generatedFile = os.path.join(musicDir, "stitched", outputFile)

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
        if taskId in taskQueue:
            taskQueue.remove(taskId)

async def queueWorker(taskId: str, request: GenerationRequest):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, processAudioJob, taskId, request)

@app.get("/artists", tags=["Metadata"])
async def getArists():
    return {"artists": [{"name": name, "gender": gender} for name, gender in artistsData]}

@app.post("/generate", response_model=TaskResponse, tags=["Generation"])
async def generateAudio(request: GenerationRequest, backgroundTasks: BackgroundTasks):
    validArtist = any(name.lower() == request.artist.lower() for name, _ in artistsData)
    if not validArtist:
        raise HTTPException(status_code=400, detail="Artist not found. Check GET /artists for available artists.")

    taskId = str(uuid.uuid4())

    taskDb[taskId] = {
        "status": "queued",
        "filePath": None,
        "error": None,
    }
    taskQueue.append(taskId)
    backgroundTasks.add_task(queueWorker, taskId, request)

    return TaskResponse(taskId=taskId, status="queued", message=f"Task {taskId} queued succesfully. Track status using /status/{taskId}")

@app.get("/status/{taskId}", tags=["Task Management"])
async def getStatus(taskId: str):
    if taskId not in taskDb:
        raise HTTPException(status_code=404, detail="Task not found")

    task = taskDb[taskId]
    response = {
        "taskId": taskId,
        "status": task["status"],
        "error": task.get("error")
    }

    if task["status"] == "queued":
        try:
            position = taskQueue.index(taskId) + 1
            response["queuePosition"] = position
            response["estimatedWait"] = position * 15
        except ValueError:
            response["queuePosition"] = 1

    return response

@app.get("/download/{taskId}", tags=["Task Management"])
async def downloadTask(taskId: str):
    if taskId not in taskDb:
        raise HTTPException(status_code=404, detail="Task not found")

    task = taskDb[taskId]

    if task["status"] == "processing" or task["status"] == "queued":
        raise HTTPException(status_code=400, detail="Task is still processing.")

    if task["status"] == "failed":
        raise HTTPException(status_code=500, detail="Task has failed.")

    filePath = task.get("filePath")
    if not filePath or not os.path.exists(filePath):
        raise HTTPException(status_code=404, detail="Generated audio file could not be found.")

    return FileResponse(path=filePath, media_type="audio/mpeg", filename=f"kiedify-{taskId}.mp3")

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)