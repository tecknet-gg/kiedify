import json
import os
import subprocess

from g2p_en import G2p
import nltk
import os
import json
import re
import inflect


class PhonemeExtractor:

    def __init__(self, musicDir="/Users/jeevan/Documents/Python/MusicTTS/Music", mfaPath="/Users/jeevan/miniconda3/envs/mfa/bin/mfa", target=10):
        self.musicDir = musicDir
        self.mfaPath = mfaPath
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

    def interpolateArtist(self, artistName):
        processedDir = os.path.join(self.musicDir, "Processed2", artistName)
        manifestPath = os.path.join(processedDir, f"{artistName}Synced copy.json")
        outputPath = os.path.join(processedDir, f"{artistName}Interpolated.json")

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

    def quotasFilled(self, phonemeBank): #for the basic interpolator
        return all(len(clips) >= self.target for clips in phonemeBank.values()) #returns true if all phonemes reach quota

    def getEnv(self):
        env = os.environ.copy()
        env["PATH"] = f"{os.path.dirname(self.mfaPath)}:{env.get('PATH', '')}"
        return env

    def processMFA(self, artistName):
        processedDir = os.path.join(self.musicDir, "Processed3", artistName)
        mfaOutputDir = os.path.join(processedDir, "MFA")
        outputPath = os.path.join(processedDir, f"{artistName}Phonemes.json")

        if not os.path.exists(mfaOutputDir):
            pass

    def runMFA(self, artistName):
        processedDir = os.path.join(self.musicDir, "Processed3", artistName)
        mfaOutputDir = os.path.join(processedDir, "MFA")

        if not os.path.exists(mfaOutputDir):
            os.makedirs(mfaOutputDir)

        myEnv = self.getEnv()


        try:
            subprocess.run([self.mfaPath, "model", "download", "dictionary", "english_us_arpa"], check=True, env=myEnv)
            subprocess.run([self.mfaPath, "model", "download", "acoustic", "english_us_arpa"], check=True, env=myEnv)
            print("Downloaded MFA models")
        except subprocess.CalledProcessError as e:
            print(f"Failed to download MFA models: {e}")

        print(f"Starting MFA alignment for {artistName}")

        cmd = [
            f"{self.mfaPath}", "align", processedDir, "english_us_arpa", "english_us_arpa", mfaOutputDir, "--clean"
        ]

        try:
            result = subprocess.run(cmd, check=True, capture_output=False, text=True, env=myEnv)
            print(f"MFA alignment completed for {artistName}")
            print(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            print(f"MFA alignment failed for {artistName}: {e}")
            print(e.stdout)
            print(e.stderr)
            return False

    def cleanLyrics(self, lyrics):
        text = re.sub(r'\d+', self.replaceNum, lyrics)

        text = text.lower()
        text = re.sub(r'[()\[\]{}.,!?;\"]', '', text)
        text = text.replace('-', ' ')

        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def replaceNum(self, match):
        p = inflect.engine()
        return p.number_to_words(match.group(0)).replace("-", " ").strip()

    def prepareMFA(self, artist):
        processedDir = os.path.join(self.musicDir, "Processed3", artist)
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

            if not audioPath:
                continue

            audioName = os.path.basename(audioPath)
            localAudioPath = os.path.join(processedDir, audioName)

            if not os.path.exists(localAudioPath):
                continue

            fullText = " ".join([word["word"] for word in wordList]).strip()
            fullText = self.cleanLyrics(fullText)

            if not fullText:
                continue

            songName, _ = os.path.splitext(audioName)
            labPath = os.path.join(processedDir, f"{songName}.lab")

            with open(labPath, "w") as f:
                f.write(fullText)
            staged += 1

        print(f"Staged {staged} pairs of .lab files for {artist}")
        return True

class PhonemeNode:
    def __init__(self, nodeId, phoneme, start, end, wordContext="", songName=""):
        self.id = nodeId
        self.phoneme = phoneme
        self.start = start
        self.end = end
        self.wordContext = wordContext
        self.songName = songName
        self.edges = []

    def addEdge(self, edge):
        self.edges.append(edge)

class PhonemeGraph:
    def __init__(self):
        self.nodes = {}
        self.startNodes = []
        self.endNodes = []

    def addNode(self, node):
        self.nodes[node.id] = node

    def buildGraph(self, intervals, weights):
        sortedIntervals = sorted(intervals, key=lambda x:x["start"])
        self.nodes = {}
        self.startNodes = []
        self.endNodes = []

        for i, interval in enumerate(sortedIntervals):
            node = PhonemeNode(
                nodeId=f"node_{i}",
                phoneme=interval["phoneme"],
                start = interval["start"],
                end = interval["end"],
                wordContext=interval.get("word", "")
            )
            self.addNode(node)

        nodeList = list(self.nodes.values())

        if not nodeList:
            return

        firstStart = nodeList[0].start

        for i, currentNode in enumerate(nodeList):
            if currentNode.start <= firstStart + 1.5:
                self.startNodes.append(currentNode)

            outgoing = False

            lookahead = min(i+30, len(nodeList))
            for j in range(i+1, lookahead):
                nextNode = nodeList[j]

                if nextNode.start >= currentNode.end - 0.02:
                    timeDelta = nextNode.start - currentNode.end

                    if timeDelta <= 2.0:
                        cleanKey = "".join([character for character in nextNode.phoneme if not character.isdigit()]) #remove numbers from phonemes
                        baseWeight = weights.get(cleanKey, 1.0)

                        penalty = 0.5 if timeDelta > 0.1 else 0.0
                        edgeWeight = max(0.1, baseWeight - penalty)

                        currentNode.addEdge((nextNode, edgeWeight))
                        outgoing = True
                    else:
                        continue

            if not outgoing:
                self.endNodes.append(currentNode)

    def decode(self):

        if not self.nodes:
            return [], 0.0

        maxWeights = {nodeId: float("-inf") for nodeId in self.nodes} #initialise with negative infinity as opposed to positive infinity in shorted dijkstras'
        backpointers = {nodeId: None for nodeId in self.nodes}

        for startNode in self.startNodes:
            maxWeights[startNode.id] = 0.0

        topologicalNodes = sorted(self.nodes.values(), key=lambda x:x.start) #sort by start time

        for currentNode in topologicalNodes:
            currentWeight = maxWeights[currentNode.id]
            if currentWeight == float("-inf"):
                continue

            for neighbour, edgeWeight in currentNode.edges:
                newWeight = currentWeight + edgeWeight
                if newWeight > maxWeights[neighbour.id]:
                    maxWeights[neighbour.id] = newWeight
                    backpointers[neighbour.id] = currentNode.id

        bestEndNode = None
        bestTotalWeight = float("-inf")
        for endNode in self.endNodes:
            if maxWeights[endNode.id] > bestTotalWeight:
                bestTotalWeight = maxWeights[endNode.id]
                bestEndNode = endNode

        if not bestEndNode:
            return [], 0.0 #return in case of failure

        decodedPath = []
        currentId = bestEndNode.id
        while currentId is not None:
            decodedPath.append(self.nodes[currentId])
            currentId = backpointers[currentId]

        decodedPath.reverse()
        return decodedPath, bestTotalWeight

class PhonemeSynth:
    def __init__(self, musicDir,  globalNodes, weights=None):

        self.musicDir = musicDir

        self.globalNodes = globalNodes
        self.g2p = G2p()

        self.weights = weights

    def textToPhonemes(self, text):
        output = self.g2p(text)
        return [phoneme for phoneme in output if phoneme.isalnum()]


    def calculateTransition(self, nodeA, nodeB):

        if nodeA.songName != nodeB.songName:
            if abs(nodeA.start - nodeB.start) < 0.02:
                return 0.0
        return 1.5

    def calculateCost(self, node, targetPhoneme):
        cleanNode = "".join([character for character in node.phoneme if not character.isdigit()])
        cleanTarget = "".join([character for character in targetPhoneme if not character.isdigit()])

        if cleanNode != cleanTarget:
            return float("inf")

        basePriority = self.weights.get(cleanTarget, 1.0)
        return max(0.1, 2.0 - (basePriority * 0.5))

    def generateStitchMap(self, input):
        targetSequence = self.textToPhonemes(input)
        print(f"Generating stitch map for: {input}")
        matrix = []
        for targetPhoneme in targetSequence:
            cleanTarget = "".join([character for character in targetPhoneme if not character.isdigit()])
            candidates = [
                node for node in self.globalNodes if "".join([character for character in node.phoneme if not character.isdigit()]) == cleanTarget
            ]
            if not candidates:
                candidates = [node for node in self.globalNodes if node.phoneme.startswith(cleanTarget[0])]
            matrix.append(candidates)

        trellis = []
        backpointers = []

        firstStepCost = {id(node): self.calculateCost(node, targetSequence[0]) for node in matrix[0]}
        firstStepPointers = {id(node): None for node in matrix[0]}
        trellis.append(firstStepCost)
        backpointers.append(firstStepPointers)

        for t in range(1, len(targetSequence)):
            currentCost = {}
            currentPointers = {}

            prevNodeMap = {id(node): node for node in matrix[t-1]}

            for currentNode in matrix[t]:
                print(f"Current node: {currentNode.phoneme}")
                currentId = id(currentNode)
                bestCost = float("inf")
                bestPrevId = None

                tCost = self.calculateCost(currentNode, targetSequence[t])

                for prevId, prevAccumulatedCost in trellis[t-1].items():
                    prevNode = prevNodeMap[prevId]
                    if not prevNode:
                        continue

                    cost = self.calculateTransition(prevNode, currentNode)

                    totalCost = prevAccumulatedCost + cost + tCost
                    if totalCost < bestCost:
                        bestCost = totalCost
                        bestPrevId = prevId

                currentCost[currentId] = bestCost
                currentPointers[currentId] = bestPrevId

            trellis.append(currentCost)
            backpointers.append(currentPointers)

        lastLayer = trellis[-1]
        if not lastLayer:
            return []

        winningId = min(lastLayer, key=lastLayer.get)
        optimalNodes = []

        currentTraceId = winningId

        for t in reversed(range(len(targetSequence))):
            matchedNode = next(node for node in matrix[t] if id(node) == currentTraceId)
            optimalNodes.append(matchedNode)
            currentTraceId = backpointers[t][currentTraceId]

        optimalNodes.reverse()

        stitchMap = []
        cursor = 0.0

        for i, node in enumerate(optimalNodes):
            duration = node.end - node.start
            crossfade = False

            print(f"Node: {node.phoneme} - Duration: {duration}")

            if i > 0:
                prevNode = optimalNodes[i-1]
                if prevNode.songName != node.songName or abs(prevNode.end - node.start) >= 0.02:
                    crossfade = True

            title = os.path.splitext(os.path.basename(node.songName))[0] if node.songName else "Unknown"
            stitchInstructions = {
                "text": node.phoneme,
                "title": title,
                "audioPath": node.songName,
                "startTime": round(node.start, 4),
                "endTime": round(node.end, 4),
                "mode": "phoneme",
                "targetTime": round(cursor, 4),
                "crossfade": 0.015 if crossfade else 0.00
            }

            stitchMap.append(stitchInstructions)
            cursor += duration - (0.015 if crossfade else 0.00)
        print(f"Generated stitch map for {input}")
        return stitchMap

    def loadIntervals(self, path):
        intervals = []

        if not os.path.exists(path):
            return intervals

        with open(path, "r") as f:
            data = f.read()

            sections = data.split("item [")
            phonemeSections = None
            for section in sections:
                if '"phones"' in section or 'name = "phones"' in section:
                    phonemeSections = section
                    break

            if not phonemeSections:
                return intervals

            pattern = re.compile(
                r'intervals\s*\[\d+\]:\s*xmin\s*=\s*([\d.]+)\s*xmax\s*=\s*([\d.]+)\s*text\s*=\s*"([^"]*)"')
            matches = pattern.findall(phonemeSections)

            for match in matches:
                xmin, xmax, phoneme = float(match[0]), float(match[1]), match[2].strip().upper()

                if phoneme and phoneme not in ["", "sp", "sil", "spn"]:
                    intervals.append({
                        "start": xmin,
                        "end": xmax,
                        "phoneme": phoneme
                    })
            return intervals

    def loadCorpus(self, artistName):
        mfaDir = os.path.join(self.musicDir, "Processed3", artistName, "MFA")
        globalNodes = []

        if not os.path.exists(mfaDir):
            print(f"No MFA directory found for {artistName}")
            return globalNodes

        files = [file for file in os.listdir(mfaDir) if file.endswith(".TextGrid")]

        nodes = 0
        for file in files:
            fullPath = os.path.join(mfaDir, file)
            base, _ = os.path.splitext(file)

            audioPath = os.path.join(self.musicDir, "Processed3", artistName, f"{base}.mp3")

            intervals = self.loadIntervals(fullPath)

            for interval in intervals:
                node = PhonemeNode(
                    nodeId=f"{nodes}",
                    phoneme=interval["phoneme"],
                    start=interval["start"],
                    end=interval["end"],
                    wordContext=interval.get("word", ""),
                    songName=audioPath
                )
                globalNodes.append(node)
                nodes += 1
        print(f"Loaded {nodes} nodes for {artistName}")
        return globalNodes

    def runCorpus(self, text, artist):
        target = artist

        globalDatbase = self.loadCorpus(target)
        if not globalDatbase:
            print("No global database found")
            return

        self.globalNodes = globalDatbase
        stitchMap = self.generateStitchMap(text)
        return stitchMap



