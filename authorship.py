from psychopy import core, event, visual, monitors
import random, datetime, pathlib

# display properties
USE_FULLSCREEN_MODE = False
DISPLAY_SCALING = 1.75
DISPLAY_RESOLUTION = dict(
    width = 3000, 
    height = 2000
)
WINDOW_EXTENT = 0.7
WINDOW_SIZE = (
    WINDOW_EXTENT * DISPLAY_RESOLUTION["width"] / DISPLAY_SCALING, 
    WINDOW_EXTENT * DISPLAY_RESOLUTION["height"] / DISPLAY_SCALING
)
FONT_FAMILY = "Consolas"
WRAP_LINEWIDTH = 4000
print(f"[DISPLAY] Running with {WINDOW_SIZE[0]:.0f}x{WINDOW_SIZE[1]:.0f}px")
class COLORS:
    background = "#050505" # deep black
    waiting_screen = "#B1B1B1" # clean grey

# experimental parameters
TRIALS = 20 # amount of trials within each block
FALSELY_ALLEGE_ERROR_RATE = 0.05
RECTIFY_ERROR_RATE = 0.2

# locating resources
with open("countries.txt", "r") as file:
    WORDBANK = file.read().splitlines()
LOGFILE_PATH = pathlib.Path(__file__).parent.absolute().joinpath("results.csv")

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
        self.window = visual.Window(
            title = "EEG Experiment",
            color = COLORS.background, 
            fullscr = USE_FULLSCREEN_MODE, 
            monitor = monitors.Monitor("displayMonitor", width=30, distance=60),
            units = "pix",
            size = WINDOW_SIZE,
        )

        self.background = visual.rect.Rect(self.window, size=WINDOW_SIZE)
        self.background.draw()
        self.set_background_color(COLORS.background)

        self.instructions = visual.TextStim(self.window, "", font = FONT_FAMILY, height = 36, wrapWidth = 950)
        text_stim_settings = dict(font = FONT_FAMILY, height = 42, anchorHoriz = "left", alignText = "left", wrapWidth = WRAP_LINEWIDTH)
        self.stimulus = visual.TextStim(
            self.window, 
            "", 
            opacity = 0.6,
            **text_stim_settings
        )
        self.stimulus_completed = visual.TextStim(
            self.window, 
            "", 
            **text_stim_settings
        )

        self.window.flip()

    def landing_page(self):
        self.set_background_color(COLORS.background)
        visual.TextStim(self.window, "EEG Typing Experiment", font = FONT_FAMILY, height = 48, wrapWidth = WRAP_LINEWIDTH).draw()
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

    def set_stimulus_text(self, text, completed = 0):
        self.stimulus.text = text
        self.stimulus.draw()
        self.stimulus_completed.text = text[:completed].ljust(len(text))
        self.stimulus_completed.draw()

    def present_trial(self, trial, word, queue):
        cursor_position = 0
        while cursor_position < len(word):
            self.set_stimulus_text(word + " " + " ".join(queue), cursor_position)
            self.window.flip()
            self.stopwatch.reset()
            pressed_key = event.waitKeys()[0]
            response_time = self.stopwatch.getTime()
            print(f"[KEYPRESS] {pressed_key.ljust(8)} {response_time:.2f}s")
            self.log_result(datum = dict(
                timestamp = datetime.datetime.now(),
                trial = trial, 
                response_time = response_time,
                word = word,
                cursor_position = cursor_position,
                target_response = word[cursor_position],
                response = pressed_key,
                # feedback = None,
            ))
            if pressed_key == word[cursor_position]:
                cursor_position += 1
            elif pressed_key == "quit":
                core.quit()

    def run_blocks(self):
        targets = self.rand.sample(WORDBANK, TRIALS)
        for trial, word in enumerate(targets, start=1):
            self.present_trial(
                trial = trial,
                word = word,
                queue = targets[trial:]
            )

    def show_credits(self):
        self.set_background_color(COLORS.waiting_screen)
        self.set_instruction_text("This concludes the experiment.")
        self.window.flip()
        core.wait(2)

    def setup_logfile(self):
        self.LOGFILE_COLUMNS = ["timestamp", "trial", "response_time", "word", "cursor_position","target_response", "response"]
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