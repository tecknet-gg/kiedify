import os
import json
import re
import random

from g2p_en import G2p
import pydub
from pydub import AudioSegment


#add fuzzy search
#add phoneme stitching for missing words


class Searcher:
    def __init__(self, dir="/Users/jeevan/Documents/Python/MusicTTS/Music"):
        self.dir = dir
        self.processedDir = os.path.join(self.dir, "Processed2")

    def normaliseWord(self, word):
        return re.sub(r'[^\w\s]', "", word).lower().strip() #cleans non alphabet stuff
        # change normalisation


    def findLCS(self, query, tracks):

        maxMatch = 0
        matchData = None
        bestMatches = []

        queryWords = [self.normaliseWord(word) for word in query] #normalise words in query

        for track in tracks:
            song = track.get("words", [])

            songWords = [self.normaliseWord(word["word"]) for word in song]
            songIndex = 0


            while songIndex < len(songWords):
                if songWords[songIndex] == queryWords[0]:
                    matchCount = 0
                    currentSong = songIndex
                    currentQuery = 0

                    while (currentSong < len(songWords) and currentQuery < len(queryWords) and songWords[currentSong] == queryWords[currentQuery]):
                        matchCount += 1
                        currentSong += 1
                        currentQuery += 1

                    if matchCount > 0:
                        matchData = {
                            "title": track.get("title"),
                            "audioPath": track.get("audioPath"),
                            "startTime": song[songIndex].get("start"),
                            "endTime": song[currentSong-1].get("end")
                        }

                        if matchCount > maxMatch:
                            maxMatch = matchCount
                            bestMatches = [matchData]

                        elif matchCount == maxMatch:
                            bestMatches.append(matchData)

                    songIndex = currentSong if matchCount > 1 else songIndex + 1

                else:
                    songIndex += 1

        if maxMatch == 0:
            return 0, None

        chosenMatch = random.choice(bestMatches)
        return maxMatch, chosenMatch

    def getTimestamps(self, query, artist):
        queryWords = query.strip().split()

        artistPath = os.path.join(self.processedDir, artist)
        manifestPath = os.path.join(artistPath, f"{artist}Synced.json")

        if not os.path.exists(manifestPath):
            print(f"Missing {artist}Synced.json ")
            return []

        try:
            with open(manifestPath, "r") as f:
                tracks = json.load(f)
        except Exception as e:
            print(f"Error loading {artist}Synced.json: {e}")
            return []

        results = []

        for track in tracks:
            songWords = track.get("words", [])
            if not songWords:
                continue

            matchCount, matchData = self.findLCS(queryWords, [track])
            if matchCount > 0:
                results.append({
                    "title": track.get("title"),
                    "artist": artist,
                    "audioPath": track.get("audioPath"),
                    "startTime": matchData.get("startTime"),
                    "endTime": matchData.get("endTime")
                })

        return results

    def getStitchMap(self, query, artist):

        query = query.strip().split()

        artistPath = os.path.join(self.processedDir, artist)
        manifestPath = os.path.join(artistPath, f"{artist}Synced.json")

        if not os.path.exists(manifestPath):
            print(f"Missing {artist}Synced.json ")
            return []

        try:
            with open(manifestPath, "r") as f:
                tracks = json.load(f)
        except Exception as e:
            print(f"Error loading {artist}Synced.json: {e}")
            return []

        stitchInstructions = []
        cursor = 0 #state tracker
        totalWords = len(query)

        while cursor < totalWords:
            remaining = query[cursor:]

            matchCount, matchData = self.findLCS(remaining, tracks)
            if matchCount > 0:
                stitchInstructions.append({
                    "text": " ". join(remaining[:matchCount]),
                    "title": matchData.get("title"),
                    "audioPath": matchData.get("audioPath"),
                    "startTime": matchData.get("startTime"),
                    "endTime": matchData.get("endTime")
                })

                cursor += matchCount
            else:
                print("Couldn't find word")
                stitchInstructions.append({
                    "text": query[cursor],
                    "title": None,
                    "audioPath": None,
                    "startTime": None,
                    "endTime": None
                })
                cursor += 1
        return stitchInstructions


if __name__ == "__main__":
    searcher = Searcher()
    #results = searcher.getStitchMap("you only live once", "Weezer")
    #print(results)
    phonemePath = os.path.join(searcher.dir, "Processed2", "Weezer", "WeezerPhonemes.json")
    targetWord = "cumulonimbus"
    output = os.path.join(searcher.dir,"Stitched", f"{targetWord}.mp3")

    with open(phonemePath, "r") as f:
        phonemeBank = json.load(f)

    g2p = G2p()
    rawPhonemes = g2p(targetWord)

    targetPhonemes = ["".join([char for char in phoneme if char.isalpha()]).upper() for phoneme in rawPhonemes]

    audioStitch = []
    missingPhonemes = False

    for phoneme in targetPhonemes:
        availableClips = phonemeBank.get(phoneme, [])

        if not availableClips:
            missingPhonemes = True
            continue

        selectedClip = availableClips[0]
        audioStitch.append(selectedClip)

        if missingPhonemes:
            print(f"Missing phonemes for {targetWord}")
        else:
            combinedAudio = AudioSegment.empty()
            for index, step in enumerate(audioStitch):
                sourcePath = step["audioPath"]

                if not os.path.exists(sourcePath):
                    print(f"Missing audio file: {sourcePath}")
                    continue

                start = int(step["start"]*1000)
                end = int(step["end"]*1000)

                trackAudio = AudioSegment.from_file(sourcePath)
                phonemeSlice = trackAudio[start:end]

                combinedAudio += phonemeSlice

            combinedAudio.export(output, format="mp3")

