import json


class Downloader:
    def __init__(self, musicDir = "/Users/jeevan/Documents/Python/MusicTTS/Music/Raw"):
        self.baseURL = "https://api.deezer.com"
        self.musicDir = musicDir
        self.config = {}
        self.installQueue = Queue()

        self.passed = 0
        self.failed = 0

        try:
            with open("config.json", "r") as configFile:
                self.config = json.load(configFile)
        except FileNotFoundError:
            print("Configuration file not found.")
        except json.decoder.JSONDecodeError:
            print("Configuration file is not valid JSON.")

        self.config = self.config.get("opt",{})

        print("Initialised")



