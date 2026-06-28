import os
import json
import re
import random
from rapidfuzz import fuzz

from g2p_en import G2p
import pydub
from pydub import AudioSegment
from rapidfuzz.distance.DamerauLevenshtein import similarity

class Searcher:
    def __init__(self, dir="/Users/jeevan/Documents/Python/MusicTTS/Music"):
        self.dir = dir
        self.processedDir = os.path.join(self.dir, "Processed")

    def normaliseWord(self, word):
        return re.sub(r'[^\w\s]', "", word).lower().strip() #cleans non alphabet stuff
        # expand on normalisation

    def semanticNormalise(self, text):
        rawSentence = " ".join(text)
        clean = re.sub(r'[^\w\s\']', "", rawSentence).lower().strip()
        return clean

    def semanticMatch(self, query, artist, minmumLength=3, similarityThreshold=0.70):
        print("Performing semantic matching search")

        queryTokens = query.strip().split()
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

        if not hasattr(self, 'nlp'): #checks to see if self.nlp has been loaded previously
            import spacy
            print("Loading spacy model")
            self.nlp = spacy.load("en_core_web_md") #lazy loading

        stitchInstructions = []
        cursor = 0

        print(f"Query length: {len(queryTokens)}")

        while cursor < len(queryTokens):
            remaining = queryTokens[cursor:]
            currentWord = remaining[0]
            print(f"Current word: {currentWord}")

            matchCount = 0
            matchData = None
            highestSimilarity = 0.0

            maxWindow = len(remaining)
            phraseFound = False

            for currentLength in range(maxWindow, minmumLength-1, -1):
                querySlice = remaining[:currentLength]
                normalisedQuery = self.semanticNormalise(querySlice)
                queryDoc = self.nlp(normalisedQuery)

                if not queryDoc.vector_norm: #rejects it if it doesn't have a normal to it (broken or whatever)
                    continue

                print(f"Current window length: {currentLength}")

                for track in tracks:
                    song = track.get("words", [])
                    if len(song) < currentLength:
                        continue

                    for i in range(len(song) - currentLength + 1):
                        songWindow = [song[j]["word"] for j in range(i, i+currentLength)]
                        normalisedSong = self.semanticNormalise(songWindow)
                        songDoc = self.nlp(normalisedSong)

                        if not songDoc.vector_norm:
                            continue

                        similarity = queryDoc.similarity(songDoc)

                        if similarity >= similarityThreshold:
                            if similarity > highestSimilarity:
                                highestSimilarity = similarity
                                matchCount = currentLength

                                matchData = {
                                    "title": track.get("title"),
                                    "audioPath": track.get("audioPath"),
                                    "startTime": song[i].get("start"),
                                    "endTime": song[i+currentLength-1].get("end")
                                }
                                phraseFound = True

                if phraseFound:
                    break

            if matchCount > 0 and matchData is not None:
                stitchInstructions.append({
                    "text": " ". join(remaining[:matchCount]),
                    "title": matchData.get("title"),
                    "audioPath": matchData.get("audioPath"),
                    "startTime": matchData.get("startTime"),
                    "endTime": matchData.get("endTime"),
                    "status": "matched",
                    "mode": "semantic"
                })
                cursor += matchCount
            else:
                stitchInstructions.append({
                    "text": " ". join(remaining[:matchCount]),
                    "title": matchData.get("title"),
                    "audioPath": matchData.get("audioPath"),
                    "startTime": matchData.get("startTime"),
                    "endTime": matchData.get("endTime"),
                    "status": "unmatched",
                    "mode": None
                })
                cursor += 1
        return stitchInstructions

    def fuzzyMatchWords(self, word1, word2, threshold=85):
        return fuzz.ratio(word1, word2) >= threshold

    def findFuzzyLCS(self, query, tracks, threshold=85):
        maxMatch = 0
        matchData = None
        bestMatches = []

        queryWords = [self.normaliseWord(word) for word in query]
        if not queryWords:
            return 0, None

        for track in tracks:
            song = track.get("words", [])
            songWords = [self.normaliseWord(word["word"]) for word in song]

            songIndex = 0
            while songIndex < len(songWords):
                if self.fuzzyMatchWords(songWords[songIndex], queryWords[0], threshold):
                    matchCount = 0
                    currentSong = songIndex
                    currentQuery = 0

                    while (currentSong < len(songWords) and currentQuery < len(queryWords) and self.fuzzyMatchWords(songWords[currentSong], queryWords[currentQuery], threshold)):
                        matchCount += 1
                        currentSong += 1
                        currentQuery += 1

                    if matchCount > 0:
                        matchData = {
                            "title": track.get("title"),
                            "audioPath": track.get("audioPath"),
                            "startTime": song[songIndex].get("start"),
                            "endTime": song[currentSong-1].get("end"),
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

    def basicMatch(self, query, artist, mode="fuzzy", patching=True, rtc=True):
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

            matchCount = 0
            matchData = None


            if mode == "exact":
                matchCount, matchData = self.findLCS(remaining, tracks, threshold)
            elif mode == "fuzzy":
                for threshold in [90, 75]:
                    matchCount, matchData = self.findFuzzyLCS(remaining, tracks, threshold)
                    if matchCount > 0:
                        break

            if matchCount > 0:
                stitchInstructions.append({
                    "text": " ". join(remaining[:matchCount]),
                    "title": matchData.get("title"),
                    "audioPath": matchData.get("audioPath"),
                    "startTime": matchData.get("startTime"),
                    "endTime": matchData.get("endTime"),
                    "mode": "basic"
                })

                cursor += matchCount
            else:
                print("Couldn't find word")
                #marked for phoneme stitching
                stitchInstructions.append({
                    "text": query[cursor],
                    "title": None,
                    "audioPath": None,
                    "startTime": None,
                    "endTime": None,
                    "mode": "phoneme"
                })
                cursor += 1
        return stitchInstructions


if __name__ == "__main__":
    searcher = Searcher()
    #results = searcher.getStitchMap("you only live once", "Weezer")
    #print(results)
    phonemePath = os.path.join(searcher.dir, "Processed3", "Weezer", "WeezerPhonemes.json")
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

