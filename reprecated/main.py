from router import Router

router = Router()
artists = ["Weezer", "Red Hot Chili Peppers", "The Dismemberment Plan", "The Pretenders", "Fleetwood Mac", "Paramore"]
router.generateDatasets(artists=artists)
router.pruneDataset(artists=artists, target=5)
