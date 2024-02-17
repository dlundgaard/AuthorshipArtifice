from psychopy import core, event, visual, monitors
import os, random, datetime, pathlib, textwrap, itertools

os.chdir(pathlib.Path(__file__).resolve().parent)

# display properties
USE_FULLSCREEN_MODE = False
DISPLAY_SCALING = 1.75
DISPLAY_RESOLUTION = dict(
    width = 3000, 
    height = 2000
)
WINDOW_EXTENT = 0.7
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
TRIALS = 3 # amount of trials within each block
FALSE_ERROR_RATE = 0.005 # rate of inserting errors despite participant being correct
# RECTIFY_ERROR_RATE = 0.2 # rate of rectifying errors despite participant typing the wrong key

# locating resources
with open("countries.txt", "r") as file:
    WORDBANK = file.read().splitlines()
LOGFILE_PATH = pathlib.Path(__file__).parent.absolute().joinpath("results.csv")
ADMISSIBLE_KEYS = list("abcdefghijklmnopqrstuvwxyz") + ["space", "quit"]

### TODO
# capital letters?
# amount trials, length of trials
# feedback delivery
# smoothen out typing experience
# should interventions be exclusively either 1) inserted errors or 2) corrected errors 
# should tasks be stenographic? i.e. press a combination of keys simulataneously
# adapt to use metric units for display sizing
# request EEG equipment monitor resolution, dimensions

class Experiment:
    def __init__(self):
        # setup
        self.rand = random.Random()
        self.stopwatch = core.Clock()
        self.setup_window()
        self.setup_logfile()

        # scenes
        self.landing_page()
        self.get_ready()
        self.run_blocks()
        self.show_credits()

    def setup_window(self):
        self.window_size = (
            WINDOW_EXTENT * DISPLAY_RESOLUTION["width"] / DISPLAY_SCALING, 
            WINDOW_EXTENT * DISPLAY_RESOLUTION["height"] / DISPLAY_SCALING
        )
        self.window = visual.Window(
            title = "EEG Experiment",
            color = COLORS.background, 
            fullscr = USE_FULLSCREEN_MODE, 
            monitor = monitors.Monitor("displayMonitor", width=30, distance=60),
            units = "pix",
            size = self.window_size,
        )
        print(f"[DISPLAY] {self.window_size[0]:.0f} x {self.window_size[1]:.0f} px")

        self.background = visual.rect.Rect(self.window, size=self.window_size)
        self.background.draw()
        self.set_background_color(COLORS.background)

        self.instructions = visual.TextStim(self.window, "", font = FONT_FAMILY, height = 28, wrapWidth = 0.9 * self.window_size[0])
        text_stim_settings = dict(
            font = FONT_FAMILY, 
            pos = (0, 0),
            size = (0.65 * 2, 0.4 * 2),
            letterHeight = 0.08, 
            units = "norm",
            alignment = "top left",
        )
        self.stimulus = visual.TextBox2(self.window, "", contrast = UNTYPED_CHAR_CONTRAST, borderWidth = 1, borderColor = "#FFFFFF", **text_stim_settings)
        self.stimulus_completed = visual.TextBox2(self.window, "", **text_stim_settings)

        self.feedback_indicator = visual.rect.Rect(self.window, pos = (0, -0.5), size=(0.65 * 2, 0.05 * 2), units = "norm", fillColor = COLORS.background)

        self.window.flip()

    def landing_page(self):
        self.set_background_color(COLORS.background)
        visual.TextStim(self.window, "EEG Typing Experiment", font = FONT_FAMILY, height = 52, wrapWidth = self.window_size[0]).draw()
        self.window.flip()
        core.wait(1)

        self.set_instruction_text("For each trial, type out the word displayed as quickly as possible.\n\nFollowing each keypress, you will get feedback indicating whether you hit the right key.\n\n\nPress SPACE to proceed")
        self.window.flip()
        pressed_key = event.waitKeys(keyList = ["space", "quit"]) # await for user to actively proceed to trials
        if pressed_key == "quit":
            core.quit()

        self.set_instruction_text()
        self.window.flip()

    def get_ready(self):
        self.set_background_color(COLORS.waiting_screen)
        self.set_instruction_text("Get ready...")
        self.window.flip()
        core.wait(1)

    def set_background_color(self, color):
        self.background.color = color
        self.background.draw()

    def set_instruction_text(self, text = ""):
        self.instructions.text = text
        self.instructions.draw()


    def set_stimulus_text(self, text, completed):
        wrapped_paragraph = textwrap.wrap(text, TEXT_WRAP_CHAR_COLUMNS, drop_whitespace = False)
        end_lines_cursor_positions = itertools.accumulate(wrapped_paragraph, lambda acc, line: acc + len(line), initial = 0)
        newlines_before_cursor = sum([1 for val in end_lines_cursor_positions if val < completed and val > 0])
        completed_paragraph = ":".join(wrapped_paragraph)[:completed + newlines_before_cursor].split(":")

        self.stimulus.text = "\n".join(wrapped_paragraph).replace(" ", "_")
        self.stimulus.draw()
        self.stimulus_completed.text = "\n".join(completed_paragraph).replace(" ", "_")
        self.stimulus_completed.draw()

    def provide_feedback(self, negative):
        if negative:
            self.feedback_indicator.setFillColor(COLORS.negative_feedback)
        else:
            self.feedback_indicator.setFillColor(COLORS.background)
        self.feedback_indicator.draw()

    def present_trial(self, trial, text):
        cursor_position = 0
        while cursor_position < len(text):
            self.set_stimulus_text(text, cursor_position)
            self.window.flip()
            self.stopwatch.reset()
            pressed_key = event.waitKeys(keyList = ADMISSIBLE_KEYS)[0]
            response_time = self.stopwatch.getTime()
            print(f"[KEYPRESS] {pressed_key.ljust(8)} {1000 * response_time:4.0f}ms", pressed_key)
            target_response = "space" if text[cursor_position] == " " else text[cursor_position]
            if pressed_key == target_response:
                if self.rand.random() < FALSE_ERROR_RATE: # sham subject by falsely reporting that wrong key was pressed
                    negative_feedback = True
                else: # accept correct keypress and advance cursor
                    negative_feedback = False
                    cursor_position += 1
            elif pressed_key == "quit":
                core.quit()
            else: # fairly provide negative feedback by indicating a wrong keypress 
                negative_feedback = True
            self.provide_feedback(negative = negative_feedback)

            self.log_result(datum = dict(
                timestamp = datetime.datetime.now(),
                trial = trial,
                cursor_position = cursor_position - 1,
                response_time = response_time,
                target_response = target_response,
                response = pressed_key,
                feedback = "negative" if negative_feedback else "positive",
            ))

    def run_blocks(self):
        for trial in range(TRIALS):
            self.present_trial(
                trial = trial,
                text = " ".join(self.rand.sample(WORDBANK, 15)),
            )

    def show_credits(self):
        self.set_background_color(COLORS.waiting_screen)
        self.set_instruction_text("This concludes the experiment.")
        self.window.flip()
        core.wait(2)

    def setup_logfile(self):
        self.LOGFILE_COLUMNS = ["timestamp", "trial", "cursor_position", "response_time", "target_response", "response", "feedback"]
        if not LOGFILE_PATH.is_file():
            with open(LOGFILE_PATH, "w") as file:
                file.write(",".join(self.LOGFILE_COLUMNS))

    def log_result(self, datum):
        with open(LOGFILE_PATH, "a") as file:
            file.write("\n" + ",".join(map(str, datum.values())))

if __name__ == "__main__":
    print(f"[INITIATED] {datetime.datetime.now()}")
    Experiment()
    print(f"[CONCLUDED] {datetime.datetime.now()}")