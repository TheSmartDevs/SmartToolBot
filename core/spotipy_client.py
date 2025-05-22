#Copyright @ISmartDevs
#Channel t.me/TheSmartDev
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
from utils import LOGGER

# Initialize Spotipy client
LOGGER.info("Creating Spotify Client From SPOTIFY_DEV!")
try:
    spotify = Spotify(
        auth_manager=SpotifyClientCredentials(
            client_id=SPOTIFY_CLIENT_ID, 
            client_secret=SPOTIFY_CLIENT_SECRET
        )
    )
    LOGGER.info("Spotify Client Successfully Created!")
except Exception as e:
    LOGGER.error(f"Failed to initialize Spotipy Client: {e}")
    raise
