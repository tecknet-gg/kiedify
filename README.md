WIP Music TTS thing

Will take any text input and convert it to speech using an artist's music!

Progress:
- [x] Music Downloader
- [x] Vocal Isolator
- [x] Lyric Sourcing
- [x] Word Level Syncing
- [x] Phoneme Level Syncing
- [x] Fuzzy Matching
- [x] Greedy Maxmial Matching Algorithm for Words
- [x] Phoneme Level Matching Algorithm
- [x] Audio Stitching
- [x] Semantic Matching
- [x] Graph Decoder (Viterbi) - abandoned
- [x] Polish Phoneme - abandoned
- [x] Clean Composition Methods
- [x] PiperTTS Dataset Preparation
- [x] PiperTTS Model Training
- [x] PiperTTS Inference
- [ ] RVC Model Training
- [ ] RVC Inference
- [ ] Reverse Transcription Checks (Using Cloud Models)
- [ ] API Routing
- [ ] Pipeline Polishing
- [ ] Backend Deployment
- [ ] Frontend

Currently working on improving the phoneme level syncing and cleaning up the dataset by running the processed data through a transcription model for quality assurance.

## Main pipeline functions:

### downloading and preprocessing
passed, failed = downloader.artistToInstalled(artists, qty=15, nthreads=25)

processor.generateQueue(passed, failed, nthreads=25)

processor.processMultithreaded(nthreads=2)

manager.cleanIsolatedDir()

manager.flattenProcessedDir()


### lyrics

lyrics.ammendMetadata()

lyrics.injectDuration()

lyrics.generateQueue()

lyrics.gatherMulithreaded()

lyrics.cleanLyricless()

### phoneme

#pass the class the path to MFA

phoneme.prepareMFA(artist) #run for all artists -> generates .lab filse

phoneme.processMFA(artist) #run for all artists -> runs .lab files through MFA

## Searching and stitching
#add phoneme toggling to basicMatch

stitchList = searcher.semanticMatch(query, artist) 
stitchList = searcher.basicMatch(query, artist, mode) #mode = "fuzzy" otherwise falls back to strict matching

stitchList is a universal format, and is fed directly into the audio stitcher:
stitcher.generateMP3(stitchList) #add toggles for normalisation, etc.



