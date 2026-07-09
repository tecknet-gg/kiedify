from router import Router

artists = ["Weezer", "Red Hot Chili Peppers", "The Dismemberment Plan", "The Pretenders", "Fleetwood Mac", "Paramore"]
genders = ["male", "male", "male", "female", "female", "female"]
artists = tuple(zip(artists, genders))

router = Router(artists=artists)

router.basicMatch("hello guys, how are we doing today?", "Weezer", fuzzy=True)