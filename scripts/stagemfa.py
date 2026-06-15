import os
import json

def prepareMFA(artist, musicDir="/Users/jeevan/Documents/Python/MusicTTS/Music"):
    processedDir = os.path.join(musicDir, "Processed3", artist)
    manifestPath = os.path.join(processedDir, f"{artist}Synced.json")

    if not os.path.exists(manifestPath):
        print(f"Synced manifest database missing for: {artist}")
        return

    with open(manifestPath, "r") as f:
        tracks = json.load(f)

    staged = 0
    print("Staging .lab files for MFA")

    for track in tracks:
        audioPath = track.get("audioPath")
        wordList = track.get("words", [])

        if not audioPath or not os.path.exists(audioPath):
            continue

        fullText = " ".join([word["word"] for word in wordList]).strip()

        if not fullText:
            continue

        audioName = os.path.basename(audioPath)
        songName, _ = os.path.splitext(audioName)
        labPath = os.path.join(processedDir, f"{songName}.lab")


        with open(labPath, "w") as f:
            f.write(fullText)
        staged += 1

    print(f"Staged {staged} pairs of .lab files for {artist}")
    return True

if __name__ == "__main__":
    prepareMFA("Weezer")