import subprocess
import sys
print(sys.executable)



class Preprocessor:
    def __init__(self):
        pass

    def separateTrack(self, inputPath, outputDir):
        subprocess.run([sys.executable, "-m", "demucs", "-o", outputDir, inputPath], check=True)



if __name__ == "__main__":
    inputPath = "/Users/jeevan/Documents/Python/MusicTTS/Music/Green Day/American Idiot/American Idiot.mp3"
    outputDir = "/Users/jeevan/Documents/Python/MusicTTS/Music/Isolated/Paramore"
    preprocessor = Preprocessor()
    preprocessor.separateTrack(inputPath, outputDir)
