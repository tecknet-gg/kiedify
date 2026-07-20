import os
import asyncio
import edge_tts
import subprocess
import sys


class RVC:
    def __init__(self, dir="/Users/jeevan/Documents/Python/MusicTTS/Music"):
        self.musicDir = dir
        self.rootDir = os.path.dirname(self.musicDir)
        self.modelsDir = os.path.join(self.musicDir, "models")

        self.applioCore = os.path.join(self.rootDir, "Applio", "Applio", "core.py")
        self.applioPython = os.path.join(self.rootDir, "Applio", ".venv", "bin", "python")

        self.index = {}
        self.indexModels()

    def indexModels(self):
        if not os.path.exists(self.modelsDir):
            os.makedirs(self.modelsDir)
            print(f"Missing models dir: {self.modelsDir}")
            return False

        self.index = {}
        for artistFolder in os.listdir(self.modelsDir):
            artistPath = os.path.join(self.modelsDir, artistFolder)

            if not os.path.isdir(artistPath):
                continue

            modelKey = artistFolder.lower()

            pthFile = None
            indexFile = None

            for filename in os.listdir(artistPath):
                filePath = os.path.join(artistPath, filename)
                filename = filename.lower()
                if filename.endswith(".pth"):
                    pthFile = filePath
                elif filename.endswith(".index"):
                    indexFile = filePath

            if pthFile or indexFile:
                self.index[modelKey] = {
                    "artistName": artistFolder,
                    "pth": pthFile,
                    "index": indexFile,
                }

            print(f"Indexed {modelKey}: {pthFile}")

        print(f"Indexed {len(self.index)} models")
        return True


    async def synthesise(self, text, artist, gender, filename="output.mp3", path=None): #change path to None
        modelKey = artist.lower()
        if modelKey not in self.index:
            print(f"No model for {modelKey}")
            return False

        tempTTS = os.path.join(self.musicDir, "Stitched", "Temp")
        os.makedirs(tempTTS, exist_ok=True)

        tempPath = os.path.join(tempTTS, f"{modelKey}.mp3")
        print(f"Generating {tempPath}")

        if gender == "male":
            voice = "en-US-AndrewNeural"
            pitch = 0
        elif gender == "female":
            voice = "en-US-JennyNeural"
            pitch = 0
        else:
            print(f"gender must be 'male' or 'female'")
            return False

        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(tempPath)
        print(f"Base audio file saved at {tempPath}")

        if path is None:
            outputPath = os.path.join(self.musicDir, "Stitched", "Fallback")
        else:
            outputPath = os.path.join(self.musicDir, "Stitched")

        os.makedirs(outputPath, exist_ok=True)
        finalPath = os.path.join(outputPath, filename)

        modelIndex = self.index[modelKey]["index"]
        modelPth = self.index[modelKey]["pth"]

        print(f"Generating {finalPath}")

        applioWorkingDir = os.path.dirname(self.applioCore)
        applioParentDir = os.path.dirname(applioWorkingDir)

        env = os.environ.copy()
        env["PYTHONPATH"] = f"{applioWorkingDir}{os.pathsep}{applioParentDir}{os.pathsep}{env.get('PYTHONPATH', '')}"

        env["OMP_NUM_THREADS"] = "1"
        env["MKL_NUM_THREADS"] = "1"
        env["VECLIB_MAXIMUM_THREADS"] = "1"
        env["NUMEXPR_NUM_THREADS"] = "1"


        cmd = [
            self.applioPython, self.applioCore, "infer",
            "--input_path", tempPath,
            "--output_path", finalPath,
            "--pth_path", modelPth,
            "--pitch", str(pitch),
            "--f0_method", "rmvpe",
        ]

        if modelIndex:
            cmd.extend(["--index_path", modelIndex, "--index_rate", "0.75"])

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=applioWorkingDir,
                env=env
            )

            stdout, stderr = await process.communicate()
            logs = stdout.decode()
            errors = stderr.decode()

            if logs:
                print(logs)

            if errors:
                print(errors)

            if process.returncode == 0 and os.path.exists(finalPath):
                print(f"Successfully generated {finalPath}")
                return finalPath
            else:
                print(f"Failed to generate {finalPath}, {process.returncode}, {stderr.decode().strip()}")
                return False

        except Exception as e:
            print(f"Failed to generate {finalPath}: {e}")


if __name__ == "__main__":
    rvc = RVC()
    rvc.indexModels()
    print(rvc.index)
    text = "testing hello"
    asyncio.run(rvc.synthesise(text, "Weezer", "male"))