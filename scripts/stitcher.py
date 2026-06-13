import pydub
import os
import subprocess
import tempfile

from pydub import AudioSegment
from pydub.scipy_effects import high_pass_filter
from pydub.effects import normalize


class Stitcher:
    def __init__(self, dir="/Users/jeevan/Documents/Python/MusicTTS/Music"):
        self.dir = dir
        self.savePath = os.path.join(self.dir, "Stitched")

        if not os.path.exists(self.savePath):
            os.makedirs(self.savePath)

    def generateMP3(self, stitchInstructions, filename="output.mp3", wordGap=200 ): #word gap in ms
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
                    source = AudioSegment.from_mp3(audioPath).set_frame_rate(44100).set_channels(1) #standardising the sampling rate
                    source = high_pass_filter(source, 130)
                    audioCache[audioPath] = source
                except:
                    print(f"Failed to load audio from {audioPath}")
                    continue
            source = audioCache[audioPath]

            start = int(startTime * 1000) #convert times to ms
            end = int(endTime * 1000)

            wordClip = source[start:end]
            wordClip = normalize(wordClip, headroom=1.0)
            wordClip = self.stretchClip(wordClip, 350)

            if len(wordClip) > 40:
                wordClip = wordClip.fade_in(20).fade_out(20)

            if index == 0:
                finalTrack = wordClip
            else:
                finalTrack = finalTrack.append(wordClip,crossfade=100)

            print(f"Stitched {text} from {startTime} to {endTime}")

        finalDestination = os.path.join(self.savePath, filename)

        try:
            print(f"Saving to {finalDestination}")
            finalTrack.export(finalDestination, format="mp3", bitrate="320k") #higher bitrate for better quality
            return finalDestination
        except Exception as e:
            print(f"Failed to save to {finalDestination}: {e}")
            return None

    def stretchClip(self, audioSegment, targetLength):
        currentLength = len(audioSegment)
        if currentLength > targetLength:
            return audioSegment

        playBackRate = currentLength / targetLength
        if playBackRate > 0.5:
            return self.timeStretch(audioSegment, playBackRate)
        else:
            stretched = self.timeStretch(audioSegment, 0.5)
            remaining = targetLength - len(stretched)

            if remaining > 0:
                stretched += AudioSegment.silent(duration=remaining)
            return stretched

    def timeStretch(self, audioSegment, rate):
        if rate < 0.5 or rate > 2:
            return audioSegment

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tempIn, tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tempOut:

            tempInName = tempIn.name
            tempOutName = tempOut.name

            try:
                audioSegment.export(tempInName, format="wav")
                cmd = [
                    "ffmpeg","-y", "-i", tempInName, "-filter:a", f"atempo={rate}", tempOutName
                ]

                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                return AudioSegment.from_wav(tempOutName)
            except Exception as e:
                print(f"Failed to time stretch: {e}")
                return audioSegment
            finally:
                os.remove(tempInName)
                os.remove(tempOutName)






