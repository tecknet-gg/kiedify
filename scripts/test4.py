from router import Router
import time

artists = ["Weezer", "Red Hot Chili Peppers", "The Dismemberment Plan", "The Pretenders", "Fleetwood Mac", "Paramore"]
genders = ["male", "male", "male", "female", "female", "female"]
artists = tuple(zip(artists, genders))

router = Router(artists=artists)
#router.secondPass()

router.basicMatch(text="Hey guys how are we doing today", artist="Red Hot Chili Peppers")

