import requests

class Downloader:
    def __init__(self):
        self.baseURL = "https://api.deezer.com"
        print("Initialised")

    def getArtist(self, artist):
        url = f"{self.baseURL}/search/artist"
        res = requests.get(url, params={"q": artist}).json()

        return res["data"][0]

    def getTopAlbums(self, artist):
        artist = self.getArtist(artist)
        artist_id = artist["id"]

        url = f"{self.baseURL}/artist/{artist_id}/albums"
        res = requests.get(url, params={"limit": 100}).json()

        albums = []

        for a in res["data"]:
            albums.append({"id": a["id"], "title": a["title"], "rank": a.get("fans", 0)})

        albums.sort(key=self.sortByRank, reverse=True)

        return albums

    def sortByRank(self, item):
        return item["rank"]

    def prettyPrint(self, albums):
        print("TOP ALBUMS")
        for i, a in enumerate(albums, 1):
            print(f"{i:02d}. {a['title']}")

    def cleanDiscography(self, albums):
        targets = ["version", "deluxe", "live", "compilation", "best", "hits", "commercial", "remix", "acoustic", "international", "practice", "session", "anniversary"]
        clean = []
        for a in albums:
            title = a["title"].lower()
            if not(any(elem in title for elem in targets)):
                clean.append(a)

        return clean

    def getDiscog(self, artist, qty=10):
        albums = self.getTopAlbums(artist)
        albums = self.cleanDiscography(albums)

        finalAlbums = []
        length = len(albums) if len(albums) < qty else qty

        for i in range(0, length):
            finalAlbums.append(albums[i])

        return finalAlbums


if __name__ == "__main__":
    downloader = Downloader()
    albums = downloader.getDiscog("The Dismemberment Plan")
    downloader.prettyPrint(albums)
    print(albums[0]["id"])