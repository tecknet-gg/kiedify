from gtts import gTTS
import os

class TTS:
    def __init__(self, dir="/Users/jeevan/Documents/Python/MusicTTS/Music"):
        self.musicDir = dir

    def ttsSynth(self, text, filename="output.mp3"):
        dir = os.path.join(self.musicDir, "Stitched", "Fallback")
        outputPath = os.path.join(dir, filename)

        try:
            tts = gTTS(text=text, lang="en", slow=False)
            tts.save(outputPath)
            print(f"Successfully generated {outputPath}")
            return outputPath
        except Exception as e:
            print(f"Failed to generate {outputPath}, {e}")
            return None