import pydub
import os

from pydub import AudioSegment


class Stitcher:
    def __init__(self, dir="/Users/jeevan/Documents/Python/MusicTTS/Music"):
        self.dir = dir
        self.savePath = os.path.join(self.dir, "Stitched")

        if not os.path.exists(self.savePath):
            os.makedirs(self.savePath)

    def generateMP3(self, stitchInstructions, filename="output.mp3", wordGap=250 ): #word gap in ms
        finalTrack = AudioSegment.empty()
        audioCache = {}
        separator = AudioSegment.silent(duration=wordGap)

        for index, item in enumerate(stitchInstructions):
            text = item.get("text")
            audioPath = item.get("audioPath")
            startTime = item.get("startTime")
            endTime = item.get("endTime")

            if not audioPath or not os.path.exists(audioPath):
                print(f"Skipping {text} as audioPath is missing or audio file doesn't exist")
                continue

            if audioPath not in audioCache:
                try:
                    audioCache[audioPath] = AudioSegment.from_mp3(audioPath)
                except:
                    print(f"Failed to load audio from {audioPath}")
                    continue
            source = audioCache[audioPath]

            start = int(startTime * 1000) #convert times to ms
            end = int(endTime * 1000)

            wordlClip = source[start:end]

            if index > 0:
                finalTrack += separator
            finalTrack += wordlClip
            print(f"Stitched {text} from {startTime} to {endTime}")

        finalDestination = os.path.join(self.savePath, filename)

        try:
            print(f"Saving to {finalDestination}")
            finalTrack.export(finalDestination, format="mp3")
        except Exception as e:
            print(f"Failed to save to {finalDestination}: {e}")
            return None


