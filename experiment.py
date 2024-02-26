"""
Adaption of "Cognitive Illusions of Authorship Reveal Hierarchical Error Detection in Skilled Typists" (https://doi.org/10.1126/science.1190483), adding EEG-recording to the experimental setup.
"""

"""
TODO
- amount of trials, length of trials
- feedback delivery -> sound signal for error?
- semantic and syntactic violations/surprises may pollute EEG trace 
- expected characters typed in 10 mins: ~3000 chars (~40 secs to type 200 chars)
- 5018 chars typed in 15m 43s
"""

from psychopy import core, event, visual, monitors
import os
import sys
import random
import datetime
import pathlib
import textwrap
import itertools
from texts import stories
try:
    from triggers import setParallelData
    ENABLE_EEG_MARKERS = True
    print("[SUCCESS]", "Connected to EEG parallel port")
except TypeError:
    ENABLE_EEG_MARKERS = False
    print("[ERROR]", "No parallel port driver found")

# EEG encodings
EEG_ENCODINGS = {
    "trial"               : 1,
    "feedback"            : 2,
    "correct"             : 11,
    "incorrect"           : 12,
    "error inserted"      : 13,
    "error rectified"     : 14,
}

PRODUCTION_MODE = "debug" not in sys.argv

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

# setting paths
LOGFILE_PATH = pathlib.Path(__file__).parent.absolute().joinpath("results.csv")
os.chdir(pathlib.Path(__file__).resolve().parent)

# constants for user input
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
ADMISSIBLE_KEYS = list(ALPHABET.lower()) + ["space", "escape"]

# datetime format for debugging info
DEBUG_DATETIME_FORMAT = "%d %b %Y %H:%M:%S"

class Experiment:
    def __init__(self):
        print(f"[INITIATED] {datetime.datetime.now().strftime(DEBUG_DATETIME_FORMAT)}")

        # setting up
        assert all([len(story) <= MAX_PARAGRAPH_LENGTH for story in stories])
        self.setup_logfile()
        self.rand = random.Random()
        self.stopwatch = core.Clock()
        self.setup_window()

        # running through scenes
        self.landing_page()
        self.run_blocks()
        self.show_credits()

        print(f"[COMPLETED] {datetime.datetime.now().strftime(DEBUG_DATETIME_FORMAT)}")

    def setup_window(self):
        self.window_resolution = (
            WINDOW_EXTENT * DISPLAY_RESOLUTION["width"] / DISPLAY_SCALING,
            WINDOW_EXTENT * DISPLAY_RESOLUTION["height"] / DISPLAY_SCALING,
        )
        monitor = monitors.Monitor(
                "displayMonitor", 
                width=30, 
                distance=60
        )
        monitor.setSizePix(DISPLAY_RESOLUTION.values())

        self.window = visual.Window(
            color = COLORS.background, 
            fullscr = PRODUCTION_MODE, 
            monitor = monitor,
            useRetina = True,
            size = self.window_resolution,
            units = "cm",
            allowGUI = True,
            pos = (0, 50),
        )
        print(f"[DISPLAY] {self.window_resolution[0]:.0f} x {self.window_resolution[1]:.0f} px")

        self.background = visual.rect.Rect(self.window, size=(2, 2), units = "norm")
        self.background.draw()
        self.set_background_color(COLORS.background)

        self.instructions = visual.TextStim(
            self.window, "", 
            font = FONT_FAMILY, 
            height = 0.4, 
            units = "cm",
            wrapWidth = 21 / 2,
        )
        text_stim_height_offset = 0.85 # offset of text box from vertical center
        text_stim_settings = dict(
            font = FONT_FAMILY, 
            pos = (0, text_stim_height_offset),
            size = (PARAPGRAPH_WINDOW_WIDTH / 2, 4.8),
            alignment = "top left",
            letterHeight = 0.45,
            lineSpacing = 1.2,
            units = "cm",
        )
        self.stimulus = visual.TextBox2(self.window, "", contrast = UNTYPED_CHAR_CONTRAST, borderWidth = 1, borderColor = "#FFFFFF", **text_stim_settings)
        self.stimulus_completed = visual.TextBox2(self.window, "", **text_stim_settings)

        feedback_indicator_height = 2 # height of feedback indicator in cm
        feedback_indicator_margin = 0.2 # margin/distance in cm from textbox to feedback indicator
        self.feedback_indicator = visual.rect.Rect(
            self.window, 
            pos = (0, text_stim_height_offset - (text_stim_settings["size"][1] / 2 + feedback_indicator_height / 2 + feedback_indicator_margin)), 
            size=(PARAPGRAPH_WINDOW_WIDTH / 2, 2), 
            units = "cm", 
            fillColor = COLORS.background
        )

        self.window.flip()

    def landing_page(self):
        self.set_background_color(COLORS.background)
        visual.TextStim(
            self.window, 
            "EEG Typing Experiment\n",
            font = FONT_FAMILY, 
            height = 0.9, 
            units = "cm", 
        ).draw()
        self.window.flip()
        core.wait(1)

        instructions = "\n\n".join([
            "Your task is to type out a series of paragraphs as quickly as possible.", "Spaces are displayed as underscores (_).\nWhen you get to an underscore, press SPACE.",
            "Following each keypress, you will get feedback indicating whether you typed that character correctly."
        ])
        self.set_instruction_text(instructions + "\n\n\n" + "")
        self.window.flip()

        if PRODUCTION_MODE:
            core.wait(10) # force user to wait and read text and wait before proceeding

        self.set_instruction_text(instructions + "\n\n\n" + "Press SPACE to proceed")
        self.window.flip()
        # await user to actively proceed to trials, allow exiting before engaging
        if event.waitKeys(keyList = ["space", "escape"])[0] == "escape": 
            core.quit()

        self.set_instruction_text()
        self.window.flip()

    def intermission(self):
        self.set_background_color(COLORS.waiting_screen)
        self.set_instruction_text("A story is being prepared.\n\nGet ready...")
        self.window.flip()
        core.wait(3)

    def show_credits(self):
        self.set_background_color(COLORS.waiting_screen)
        self.set_instruction_text("This concludes the experiment.")
        self.window.flip()
        core.wait(2)

    def set_background_color(self, color):
        self.background.color = color
        self.background.draw()

    def set_instruction_text(self, text = ""):
        self.instructions.text = text
        self.instructions.draw()

    def update_stimulus(self, text, completed):
        wrapped_paragraph = textwrap.wrap(text, int(PARAPGRAPH_WINDOW_WIDTH / TEXT_CHAR_WIDTH), drop_whitespace = False)
        end_lines_cursor_positions = itertools.accumulate(wrapped_paragraph, lambda acc, line: acc + len(line), initial = 0)
        newlines_before_cursor = sum([1 for val in end_lines_cursor_positions if val < completed and val > 0])
        completed_paragraph = ":".join(wrapped_paragraph)[:completed + newlines_before_cursor].split(":")

        self.stimulus.text = "\n".join(wrapped_paragraph).replace(" ", "_")
        self.stimulus.draw()
        self.stimulus_completed.text = "\n".join(completed_paragraph).replace(" ", "_")
        self.stimulus_completed.draw()

    def provide_feedback(self, feedback):
        assert feedback in ("positive", "negative")
        self.feedback_indicator.setFillColor(dict(
            positive = COLORS.background,
            negative = COLORS.negative_feedback,
        )[feedback])
        self.feedback_indicator.draw()

    def run_trials(self, block, paragraph):
        trial = 1
        cursor_position = 0
        logs = []
        while cursor_position < len(paragraph):
            self.update_stimulus(paragraph, cursor_position)
            self.window.flip()
            if ENABLE_EEG_MARKERS:
                self.window.callOnFlip(setParallelData, 0)
            self.stopwatch.reset()

            # take keyboard input
            pressed_key = event.waitKeys(keyList = ADMISSIBLE_KEYS)[0]
            response_time = self.stopwatch.getTime()

            # decide on feedback
            target_response = "space" if paragraph[cursor_position] == " " else paragraph[cursor_position]
            if pressed_key == "escape":
                core.quit()
            elif pressed_key == target_response:
                if self.rand.random() < (1 / FALSE_ERROR_ODDS): # sham subject by falsely reporting that wrong key was pressed
                    feedback = "negative"
                    condition = "error inserted"
                else: # provide positive feedback for correct keypress
                    feedback = "positive"
                    condition = "control"
            else:
                if self.rand.random() < (1 / RECTIFY_ERROR_ODDS): # provide positive feedback despite incorrect keypress
                    feedback = "positive"
                    condition = "error rectified"
                else: # fairly provide negative feedback by indicating a wrong keypress
                    feedback = "negative"
                    condition = "control"
            
            # decide feedback based on condition
            self.provide_feedback(feedback)

            if ENABLE_EEG_MARKERS:
                if condition == "control":
                    coded_value = EEG_ENCODINGS["correct"] if pressed_key == target_response else EEG_ENCODINGS["incorrect"]
                else:
                    coded_value = EEG_ENCODINGS[condition]
                if not PRODUCTION_MODE:
                    print(f"[EEG] {coded_value} ({bin(coded_value)})")
                self.window.callOnFlip(setParallelData, coded_value)

            # store datapoint to be written to logfile
            logs.append(dict(
                session = self.session,
                block = block,
                trial = trial,
                cursor_position = cursor_position,
                timestamp = datetime.datetime.now(),
                response_time = response_time,
                target_response = target_response,
                response = pressed_key,
                feedback = feedback,
                condition = condition
            ))

            if not PRODUCTION_MODE:
                print(f"[KEYPRESS] {pressed_key.ljust(8)} {1000 * response_time:4.0f}ms {feedback} feedback", pressed_key)

            # count each keypress as trial ("used attempt")
            trial += 1
            # if correct key was pressed, and this was not a sham feedback instance, advance cursor position
            if feedback == "positive":
                cursor_position += 1

        return logs

    def run_blocks(self):
        for block, story in enumerate(stories, start = 1):
            self.intermission()
            story_text = "".join([char for char in story.lower() if char in list(ALPHABET.lower()) + [" "]])
            logs = self.run_trials(block = block, paragraph = story_text)
            self.write_logs(logs) # flush/write logs collected up to this point

    def setup_logfile(self):
        self.LOGFILE_COLUMNS = ["session", "block", "trial", "cursor_position", "timestamp", "response_time", "target_response", "response", "feedback", "condition"]
        if not LOGFILE_PATH.is_file():
            with open(LOGFILE_PATH, "w") as file:
                file.write(",".join(self.LOGFILE_COLUMNS))
            self.session = 1
        else:
            with open(LOGFILE_PATH, "r") as file:
                lines = file.read().splitlines()
                assert lines[0] == ",".join(self.LOGFILE_COLUMNS)
                if len(lines) > 1:
                    last_datapoint = lines[-1]
                    self.session = int(last_datapoint.split(",")[0]) + 1
                else:
                    self.session = 1
        self.data_log = []

    def write_logs(self, logs):
        with open(LOGFILE_PATH, "a") as file:
            for datapoint in logs:
                assert list(datapoint.keys()) == self.LOGFILE_COLUMNS
                file.write("\n" + ",".join(map(str, datapoint.values())))

if __name__ == "__main__":
    Experiment()