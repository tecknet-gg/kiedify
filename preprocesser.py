import os
from demucs.api import Separator



class Preprocessor:
    def __init__(self):
        pass

if __name__ == "__main__":
    outputDir = "/Users/jeevan/Documents/Python/MusicTTS/Music/Isolated"
    separator = Separator(model-"htdemucs", two_stems="vocals")
    origin, separated = separator.separate_audio_file("/Users/jeevan/Documents/Python/MusicTTS/Music/Weezer/Weezer (Blue Album)/Say It Ain't So (Original Mix).mp3")
    os.makedirs("/Users/jeevan/Documents/Python/MusicTTS/Music/Isolated", exist_ok=True)
    outputPath = os.path.join(outputDir, f"{stem}.wav")
    separator.save_audio(waveform, outputPath, saplerate=seprator.samplerate)
    print("Done")
