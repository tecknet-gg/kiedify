import os
import json
import re


class Searcher:
    def __init__(self, dir="/Users/jeevan/Documents/Python/MusicTTS/Music"):
        self.dir = dir
        self.processedDir = os.path.join(self.dir, "Processed2")

    def normaliseWord(self, word):
        return re.sub(r'[^\w\s]', "", word).lower().strip() #cleans non alphabet stuff


    def findLCS(self, query, song):

        maxMatch = 0
        bestStart = -1
        bestEnd = -1

        songWords = [self.normalise(word["word"]) for word in song] #normalise across song and query
        queryWords = [self.normalise(word["word"]) for word in query]

        songIndex = 0

        while songIndex < len(songWords):
            if songWords[songIndex] == queryWords[0]:
                matchCount = 0
                currentS = songIndex
                currentQ = 0

                while (currentS < len(songWords) and currentQ < len(queryWords) and songWords[currentS] == queryWords[currentQ]):
                    matchCount += 1
                    currentS += 1
                    currentQ += 1

                if matchCount > maxMatch:
                    maxMatch = matchCount
                    bestStart = songIndex
                    bestEnd = currentS - 1

                songIndex = currentS if matchCount > 1 else songIndex + 1

            else:
                songIndex += 1

        if maxMatch == 0:
            return 0, None, None

        startTime = songWords[bestStart].get("start")
        endTime = songWords[bestEnd].get("end")

        return maxMatch, startTime, endTime

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

            matchCount, startTime, endTime = self.findLCS(queryWords, songWords)
            if matchCount > 0:
                results.append({
                    "title": track.get("title"),
                    "artist": artist,
                    "audioPath": track.get("audioPath"),
                    "startTime": startTime,
                    "endTime": endTime
                })


