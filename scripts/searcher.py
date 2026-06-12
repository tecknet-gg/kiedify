import os
import json
import re



class Searcher:
    def __init__(self, dir="/Users/jeevan/Documents/Python/MusicTTS/Music"):
        self.dir = dir
        self.processedDir = os.path.join(self.dir, "Processed2")

    def normaliseWord(self, word):
        return re.sub(r'[^\w\s]', "", word).lower().strip() #cleans non alphabet stuff


    def findLCS(self, query, tracks):

        maxMatch = 0
        bestData = None

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

                    if matchCount > maxMatch:
                        maxMatch = matchCount
                        bestData = {
                            "title": track.get("title"),
                            "audioPath": track.get("audioPath"),
                            "startTime": song[songIndex].get("start"),
                            "endTime": song[currentSong-1].get("end")
                        }

                    songIndex = currentSong if matchCount > 1 else songIndex + 1

                else:
                    songIndex += 1

        if maxMatch == 0:
            return 0, None

        return maxMatch, bestData

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
    results = searcher.getStitchMap("you only live once", "Weezer")
    print(results)