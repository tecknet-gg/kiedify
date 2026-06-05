import subprocess


class Preprocessor:
    def __init__(self):
        pass

    def separateTrack(self, inputPath, outputDir):
        subprocess.run([
            "python", "-m", "demucs",
            "-o", outputDir,
            inputPath
        ], check=True)



if __name__ == "__main__":
    inputPath = "/Users/jeevan/Documents/Python/MusicTTS/Music/Weezer/Weezer (Blue Album)/Say It Ain't So (Original Mix).mp3"
    outputDir = "/Users/jeevan/Documents/Python/MusicTTS/Music/Isolated"
    preprocessor = Preprocessor()
    preprocessor.separateTrack(inputPath, outputDir)