WIP Music TTS thing

Will take any text input and convert it to speech using an artist's music!

Progress:
- [x] Music Downloader
- [x] Vocal Isolator
- [x] Lyric Sourcing
- [x] Word Level Syncing
- [ ] Phoneme Level Syncing
- [x] Fuzzy Matching
- [x] Greedy Maxmial Matching Algorithm for Words
- [ ] Phoneme Level Matching Algorithm
- [x] Audio Stitching
- [ ] Looped LLM (for better inputs)
- [ ] Graph Decoder (for basic semantic preservation only)
- [ ] Pipeline Polishing
- [ ] API Wrapping
- [ ] Backend Deployment
- [ ] Neutered LLM Chatbot
- [ ] Frontend

## Main pipeline functions:

passed, failed = downloader.artistToInstalled(artists, qty=15, nthreads=25)

processor.generateQueue(passed, failed, nthreads=25)
processor.processMultithreaded(nthreads=2)

manager.cleanIsolatedDir()
manager.flattenProcessedDir()


lyrics.ammendMetadata()
lyrics.injectDuration()
lyrics.generateQueue()
lyrics.gatherMulithreaded()
lyrics.cleanLyricless()


#pass the class the path to MFA
phoneme.prepareMFA(artist) #run for all artists -> generates .lab filse
phoneme.processMFA(artist) #run for all artists -> runs .lab files through MFA

## Searching and stitching
#add phoneme toggling to basicMatch

stitchList = searcher.semanticMatch(query, artist) 
stitchList = searcher.basicMatch(query, artist, mode) #mode = "fuzzy" otherwise falls back to strict matching

stitchList is a universal format, and is fed directly into the audio stitcher:
stitcher.generateMP3(stitchList) #add toggles for normalisation, etc.



