import json
import os
from g2p_en import G2p
import nltk


class PhonemeExtractor:
    def __init__(self, musicDir="/Users/jeevan/Documents/Python/MusicTTS/Music", target=10):
        self.musicDir = musicDir
        self.target = target
        self.g2p = G2p()
        #nltk.download('averaged_perceptron_tagger_eng')

        self.validPhonemes = {
            'AA', 'AE', 'AH', 'AO', 'AW', 'AY', 'B', 'CH', 'D', 'DH', 'EH', 'ER', 'EY',
            'F', 'G', 'HH', 'IH', 'IY', 'JH', 'K', 'L', 'M', 'N', 'NG', 'OW', 'OY', 'P',
            'R', 'S', 'SH', 'T', 'TH', 'UH', 'UW', 'V', 'W', 'Y', 'Z', 'ZH'
        }

        self.phonemeWeights = {
            'AA': 2.5, 'AE': 2.5, 'AH': 2.0, 'AO': 2.5, 'AW': 3.0, 'AY': 3.0,
            'EH': 2.0, 'ER': 2.0, 'EY': 2.5, 'IH': 1.8, 'IY': 2.2, 'OW': 2.5,
            'OY': 3.0, 'UH': 1.8, 'UW': 2.2,

            'L': 1.2, 'M': 1.2, 'N': 1.2, 'NG': 1.4, 'R': 1.2, 'W': 1.0, 'Y': 1.0,

            'CH': 0.8, 'DH': 0.6, 'F': 0.8, 'HH': 0.7, 'JH': 0.8, 'S': 1.2,
            'SH': 1.2, 'TH': 0.7, 'Z': 1.2, 'ZH': 1.2,

            'B': 0.5, 'D': 0.5, 'G': 0.5, 'K': 0.5, 'P': 0.4, 'T': 0.4
        }

    def processArtist(self, artistName):
        processedDir = os.path.join(self.musicDir, "Processed2", artistName)
        manifestPath = os.path.join(processedDir, f"{artistName}Synced copy.json")
        outputPath = os.path.join(processedDir, f"{artistName}Phonemes.json")

        if not os.path.exists(manifestPath):
            print(f"Synced manifest database missing for: {artistName}")
            return

        with open(manifestPath, "r") as f:
            tracks = json.load(f)

        phonemeBank = {phoneme: [] for phoneme in self.validPhonemes}

        print(f"Slicing corpus for {artistName}")

        for track in tracks:
            audioPath = track.get("audioPath")
            wordList = track.get("words", [])

            if not os.path.exists(audioPath):
                continue

            for word in wordList:
                if self.quotasFilled(phonemeBank):
                    print(f"Reached quota for {artistName}")
                    break

                wordText = word.get("word", "").strip()
                wordStart = float(word.get("start", 0.0))
                wordEnd = float(word.get("end", 0.0))
                wordDuration = wordEnd - wordStart

                if not wordText or wordDuration <= 0:
                    continue

                rawPhonemes = self.g2p(wordText)

                cleanPhonemes = []
                for phoneme in rawPhonemes:
                    cleanPhoneme = "".join([i for i in phoneme if i.isalpha()]).upper()
                    if cleanPhoneme in self.validPhonemes:
                        cleanPhonemes.append(cleanPhoneme)

                if not cleanPhonemes:
                    continue

                currentTime = wordStart

                totalWeight = sum(self.phonemeWeights.get(phoneme, 1.0) for phoneme in cleanPhonemes)
                for phoneme in cleanPhonemes:
                    phonemeWeight = self.phonemeWeights.get(phoneme, 1.0)
                    sliceDuration = (phonemeWeight / totalWeight) * wordDuration #weighted interpolation

                    phonemeStart = currentTime
                    phonemeEnd = phonemeStart + sliceDuration

                    currentTime = phonemeEnd

                    if len(phonemeBank[phoneme]) < self.target:
                        phonemeBank[phoneme].append({
                            "text": wordText,
                            "audioPath": audioPath,
                            "start": round(phonemeStart,2),
                            "end": round(phonemeEnd,2),
                            "duration": round(sliceDuration,2)
                        })

            if self.quotasFilled(phonemeBank):
                break

        try:
            with open(outputPath, "w") as f:
                json.dump(phonemeBank, f, indent=4)
            print(f"Phoneme bank saved to: {outputPath}")
        except Exception as e:
            print(f"Failed to save phoneme bank for {artistName}: {e}")

    def quotasFilled(self, phonemeBank):
        return all(len(clips) >= self.target for clips in phonemeBank.values()) #returns true if all phonemes reach quota

if __name__ == "__main__":
    extractor = PhonemeExtractor()
    extractor.processArtist("Weezer")