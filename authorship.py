"""
Adaption of "Cognitive Illusions of Authorship Reveal Hierarchical Error Detection in Skilled Typists" (https://doi.org/10.1126/science.1190483) to experimental setup which incorporates EEG. 
"""

"""TODO
- amount of trials, length of trials
- feedback delivery -> sound signal for error
- display sizing (physical units) -> request EEG equipment monitor resolution, dimensions
"""

# expected characters typed in 10 mins: ~3000 chars (~40 secs to type 200 chars)

PRODUCTION_MODE = True

from psychopy import core, event, visual, monitors
import os
import ctypes
import random
import datetime
import pathlib
import textwrap
import itertools
from texts import stories
# from triggers import setParallelData

# EEG encodings
class EEG_ENCODING:
    trial               = 0
    keypress            = 0
    feedback_negative   = 0
    feedback_positive   = 0
    error_rectified     = 0
    error_inserted      = 0

# display properties
WINDOW_EXTENT = 1 if PRODUCTION_MODE else 0.7
windows_instance = ctypes.windll.user32 
windows_instance.SetProcessDPIAware()
DISPLAY_RESOLUTION = dict(
    width = windows_instance.GetSystemMetrics(0),
    height = windows_instance.GetSystemMetrics(1)
)
MAX_PARAGRAPH_LENGTH = 250
TEXT_WRAP_CHAR_COLUMNS = 38
FONT_FAMILY = "Consolas"

# color specification
UNTYPED_CHAR_CONTRAST = 0
class COLORS:
    background = "#050505" # deep black
    waiting_screen = "#B1B1B1" # clean grey
    positive_feedback = "#1ED760" # Spotify green
    negative_feedback = "#FF0000" # YouTube red

# experimental parameters
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
ADMISSIBLE_KEYS = list(ALPHABET.lower()) + ["space", "escape"]
FALSE_ERROR_ODDS = 100 # rate of inserting errors despite being correct, in odds
RECTIFY_ERROR_ODDS = 10 # rate of rectifying errors despite pressing the wrong key, in odds

# setting paths
LOGFILE_PATH = pathlib.Path(__file__).parent.absolute().joinpath("results.csv")
os.chdir(pathlib.Path(__file__).resolve().parent)

class Experiment:
    def __init__(self):
        # setting up
        self.setup_logfile()
        self.rand = random.Random()
        self.stopwatch = core.Clock()
        self.setup_window()

        # running through scenes
        self.landing_page()
        self.run_blocks()
        self.show_credits()
        self.write_logs()

    def setup_window(self):
        self.window_size = (
            WINDOW_EXTENT * DISPLAY_RESOLUTION["width"],
            WINDOW_EXTENT * DISPLAY_RESOLUTION["height"],
        )
        self.window = visual.Window(
            color = COLORS.background, 
            fullscr = PRODUCTION_MODE, 
            monitor = monitors.Monitor("displayMonitor", width=30, distance=60),
            pos = (0, 50),
            size = self.window_size,
            units = "pix",
            useRetina = True,
            allowGUI = True,
        )
        print(f"[DISPLAY] {self.window_size[0]:.0f} x {self.window_size[1]:.0f} px")

        self.background = visual.rect.Rect(self.window, size=self.window_size, units = "pix")
        self.background.draw()
        self.set_background_color(COLORS.background)

        self.instructions = visual.TextStim(
            self.window, "", 
            font = FONT_FAMILY, 
            height = 0.07, 
            units = "norm",
            wrapWidth = 2 * 0.8
        )
        text_stim_settings = dict(
            font = FONT_FAMILY, 
            pos = (0, 0),
            size = (0.65 * 2, 0.4 * 2),
            alignment = "top left",
            letterHeight = 0.08,
            lineSpacing = 1.2,
            units = "norm",
        )
        self.stimulus = visual.TextBox2(self.window, "", contrast = UNTYPED_CHAR_CONTRAST, borderWidth = 1, borderColor = "#FFFFFF", **text_stim_settings)
        self.stimulus_completed = visual.TextBox2(self.window, "", **text_stim_settings)

        self.feedback_indicator = visual.rect.Rect(self.window, pos = (0, -0.65), size=(0.65 * 2, 0.2 * 2), units = "norm", fillColor = COLORS.background)

        self.window.flip()

    def landing_page(self):
        self.set_background_color(COLORS.background)
        visual.TextStim(self.window, "EEG Typing Experiment", font = FONT_FAMILY, height = 0.14, units = "norm", wrapWidth = self.window_size[0]).draw()
        self.window.flip()
        core.wait(1)

        self.set_instruction_text("\n\n".join([
            "For each trial, type out the paragraph of text displayed as quickly as possible.", "Spaces are displayed as underscores (_)\nWhen you get to an underscore, you need to press SPACE.",
            "Following each keypress, you will get feedback indicating whether you hit the right key.",
            "Press SPACE to proceed",
        ]))
        self.window.flip()
        pressed_key = event.waitKeys(keyList = ["space", "escape"]) # await for user to actively proceed to trials
        if pressed_key == "escape":
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
        wrapped_paragraph = textwrap.wrap(text, TEXT_WRAP_CHAR_COLUMNS, drop_whitespace = False)
        end_lines_cursor_positions = itertools.accumulate(wrapped_paragraph, lambda acc, line: acc + len(line), initial = 0)
        newlines_before_cursor = sum([1 for val in end_lines_cursor_positions if val < completed and val > 0])
        completed_paragraph = ":".join(wrapped_paragraph)[:completed + newlines_before_cursor].split(":")

        self.stimulus.text = "\n".join(wrapped_paragraph).replace(" ", "_")
        self.stimulus.draw()
        self.stimulus_completed.text = "\n".join(completed_paragraph).replace(" ", "_")
        self.stimulus_completed.draw()
        self.window.flip()

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
        assert all([len(story) <= MAX_PARAGRAPH_LENGTH for story in stories])
        for block, story in enumerate(stories, start = 1):
            self.intermission()
            story_text = "".join([char for char in story.lower() if char in list(ALPHABET.lower()) + [" "]])
            logs = self.run_trials(
                block = block,
                paragraph = story_text,
            )
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
    print(f"[INITIATED] {datetime.datetime.now()}")
    Experiment()
    print(f"[CONCLUDED] {datetime.datetime.now()}")