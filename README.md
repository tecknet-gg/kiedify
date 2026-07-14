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
- [x] RVC Model Training
- [ ] RVC Inference
- [x] Reverse Transcription Checks (Using Cloud Models) (Scrapped)
- [ ] API Routing (Started)
- [x] Pipeline Polishing 
- [ ] Backend Deployment
- [ ] Frontend

Currently working on improving the phoneme level syncing and cleaning up the dataset by running the processed data through a transcription model for quality assurance.

# Router
router.py has most of the most accessed functions neatly wrapped into one class :]



