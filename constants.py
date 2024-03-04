import pathlib

PRODUCTION_MODE = True # whether or not to run in fullscreen
DEBUG_DATETIME_FORMAT = "%d %b %Y %H:%M:%S" # datetime format for debugging info
LOGFILE_PATH = pathlib.Path(__file__).parent.joinpath("data").joinpath("behavioural").joinpath("results.csv").resolve() # path to logfile

# EEG encodings
EEG_EVENT_ENCODINGS = {
    "keypress"              : 1,
    "trial/correct"         : 11,
    "trial/incorrect"       : 12,
    "trial/error inserted"  : 13,
    "trial/error rectified" : 14,
}

# display properties
WINDOW_EXTENT = 1 if PRODUCTION_MODE else 0.7
DISPLAY_SCALING = 1.75
DISPLAY_RESOLUTION = dict(
    width = 3000,
    height = 2000,
)
UNTYPED_CHAR_CONTRAST = 0

# text sizing
FONT_FAMILY = "Consolas"
PARAPGRAPH_WINDOW_WIDTH = 21
TEXT_CHAR_HEIGHT = 0.48
TEXT_CHAR_WIDTH = 1.15 * TEXT_CHAR_HEIGHT # widths of Consolas monospace characters are 115% of their height
MAX_PARAGRAPH_LENGTH = 250

# colors
class COLORS:
    background = "#050505" # deep black
    waiting_screen = "#B1B1B1" # clean grey
    positive_feedback = "#1ED760" # Spotify green
    negative_feedback = "#FF0000" # YouTube red

# experimental parameters
FALSE_ERROR_ODDS = 100 # rate of inserting errors despite being correct, in odds
RECTIFY_ERROR_ODDS = 10 # rate of rectifying errors despite pressing the wrong key, in odds

# user input
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
ADMISSIBLE_KEYS = list(ALPHABET.lower()) + ["space", "escape"]

