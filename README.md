# Kiedify

A silly little [site](https://kiedify.tecknet.dev) to find strings of text within an artist's discography! Back-end written in Python, with a React frontend. Search using simple longest common substring, semantic searching, or running an RVC model.

>[!NOTE]
> If the website is down, please check again in a few hours, due to the cost of compute for RVC and Semantic searches, I have to self host this. I try to maintain good uptime, but occasionally, my device might be on a network that doesn't permit cloudflare tunnels.  

# How it works

The back-end is the bread and butter of this project. The pipeline indexes any artists' discography using Deezer's [API](https://developers.deezer.com/login?redirect=/api) and uses [yt-dlp](https://github.com/yt-dlp/yt-dlp)'s built in search feature to source and download the track from YouTube. The vocals are then isolated using [demucs](https://github.com/facebookresearch/demucs). A manifest of all tracks that pass this initial pipeline is produced and their lyrics, synced to the line, are pulled from [LRCLIB](https://lrclib.net/). 

[WhisperX](https://github.com/m-bain/whisperx) is then used to do the actual syncing, force aligning each word to the audio snippet, and a word level manifest is produced for each artist, providing the start and end timestamps of each word. A second pass is done blind to the results of the first. It transcribes the audio, to get the actual test, and that is used as the ground-truth, providing more accurate timestamps and reducing drift. 

Obviously an artist won't have said every word in the English dictionary, so a fallback was needed. My first approach was using Phoneme Extraction using [MFA](https://github.com/MontrealCorpusTools/Montreal-Forced-Aligner), and then using Graph Traversal to produce audio for new words, using Viterbi's Algorithm. Ended up not being viable. The second approach was using a TTS model I trained using ![PiperTTS](https://github.com/rhasspy/piper). The resultant model ended up being pretty bad, so I pivoted to RVC, which promises to preserve the artists timbre more accurately. Initially used a pure programmatic approach using a [library](https://pypi.org/project/rvc-python/). Ended up not working at all, so I switched to a web-ui called [Applio](https://applio.org/). Worked nearly immediately, and after 50 epochs of training on a ~1hr dataset, I got pretty decent results. Inference is cheap, and that is the final fallback approach implemented.

# Why I made this project

I do not know actually. I vaguely remembering watching a video of someone using Red Hot Chili Peppers as a voice for Alexa or something. As hard as I try I cannot attribute a source to that. I thought it'd be funny to recreate it as a simple weekend project. One of those turned out true. Quite funny, took me 80 hours to build though! tldr; I thought it was a cool idea, and wanted to implement it myself!



# Examples

<img width="1255" height="697" alt="image" src="https://github.com/user-attachments/assets/1d05d7bc-52eb-48db-96e1-16f91b6df72a" />

## Audio:
- [Sometimes I feel... - Weezer](https://user-cdn.hackclub-assets.com/019fa8e9-1c7c-741b-9566-8f139ea1e3a5/sometimes%20i%20feel%20like.mp3)
- [What is the meaning of life - Red Hot Chili Peppers](https://user-cdn.hackclub-assets.com/019fa8ea-07a4-7e77-897e-1e9933fc1729/meaning%20of%20life.mp3)
- [Hey guys... - Red Hot Chili Peppers](https://user-cdn.hackclub-assets.com/019fa8ea-9556-774e-83c2-f370104ec13d/hey%20guys2.mp3)


# How to use

If you only care about using it, and don't mind the current artist selection (Red Hot Chili Peppers, Weezer, The Pretenders, Fleetwood Mac), visit: [kiedify.tecknet.dev](https://kiedify.tecknet.dev). 

>[!WARNING]
> The semantic search method does work, but the compute required for longer inputs is very high. To test out the semantic search, use phrases that are shorter than 8 words. Inputs will be sliced to a maximum length of 8 for semantic, and 50 for other methods. 


The API is public at [api.tecknet.dev](https://api.tecknet.dev), and the auto-generated swagger [documentation](https://api.tecknet.dev/docs) for the same. A short summary:

| Method                 | Notes                                                          |
| ---------------------- | -------------------------------------------------------------- |
| GET /artists           | Returns a list of available artists and their genders          |
| POST /generate         | Queue an audio generation task with parameters. Returns a UUID |
| GET /status/{taskID}   | Gets the status of a generation task. Input the UUID           |
| GET /download/{taskID} | Download the audio file for a UUID                             |

## How to use locally

If you'd like to deploy this locally and produce datasets for your own artist here you are.

### Prerequisites:

- [Python](https://www.python.org/) 3.10.x
- [Node.js](https://nodejs.org/en) v18+
- [ffmpeg](https://www.ffmpeg.org/)

### Instructions:

```
# Clone repo and install dependecies

git clone https://github.com/tecknet-gg/kiedify 
cd kiedify

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

cd kiedify-ui
npm install
```

In your project you also want to clone Applio if you're planning on training an RVC model:

```
git clone https://github.com/iahispano/Applio
```

All the main pipeline features are wrapped into ```router.py```. The names are pretty self explanatory as to what they do. Here's how you would generate a basic dataset

```
from router import Router

artists = ["artist1", "artist2"]
genders = ["male", "female"]
artistsMeta = tuple(zip(artists, genders))
router = Router(artists=artistsMeta)

router.downloadArtists(artists, qty=10) # Download 10 albums from each artists
router.precprocessAll(nthreads=2) # Run vocal isolation on 2 threads

router.amendMetadata() # Amend manifest metadata and source lyrics
router.sourceLyrics()

router.postClean() # Clean up all songs missing lyrics

router.syncAll() # First sync run

router.secondPass() # Second pass syncing
```

And with that pipeline you should have your basic dataset generated! You can run basic matches without RVC fallback using  ```router.basicMatch() with patching=False```

To generate the RVC models needed:

```
from rvctrainer import RVCTrainer
from router.py import Router

router = Router(artists=artistsMeta)
trainer = RVCTrainer()


router.downloadRVCBases()
trainer.makeDataset(artist)
```

```
cd Applio
./run-install.sh # One time to install dependencies
./run-applio.sh
```

That will produce the dataset for an artist, then open up the Applio web-ui. Run through the training steps sequentially. For the live version I'm running, I ran it on 1 hour of data, for 50 epochs with batch sizes of 8. 
After training, export the model_info.json, the *.pth file (rename to just the Artist's name), and the .index file that was generated. Move those to ```~/Music/models/{artist}```. The RVC inference script will pick up new models. 

And with that, you should have a fully capable local setup! If you want to host your own API, change the tunnel config in ```api.py```, I'm using cloudflare tunnels since my ISP uses CGNAT. To run the API and the frontend:

```
python scripts/api.py # Run with .venv active
```

```
cd kiedify-ui
npm run dev
```

And with that you should be up and running!






