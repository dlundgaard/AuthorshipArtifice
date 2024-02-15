from psychopy import core, event, visual, monitors
import random, datetime, pathlib

FALSELY_ALLEGE_ERROR_RATE = 0.05
RECTIFY_ERROR_RATE = 0.2
with open("fruits.txt", "r") as file:
    WORDBANK = file.read().splitlines()
TRIALS = 10 # amount of trials within each block
LOGFILE_PATH = pathlib.Path(__file__).parent.absolute().joinpath("results.csv")

class Experiment:
    def __init__(self):
        self.rand = random.Random()
        self.stopwatch = core.Clock()
        self.setup_window()

        # scenes
        self.menu_page()
        self.get_ready()
        self.run_blocks()
        self.show_credits()

    def setup_window(self):
        self.window = visual.Window(color = "#050505", fullscr = False, size=(1080, 720), monitor = "MainMonitor")

        self.background = visual.rect.Rect(self.window, size=3)
        self.background.draw()
        self.set_background_color("#050505")

        self.instructions = visual.TextStim(self.window, "", font = "Consolas")
        self.stimulus = visual.TextStim(self.window, "", font = "Consolas", opacity = 0.6)
        self.stimulus_completed = visual.TextStim(self.window, "", font = "Consolas")

        self.window.flip()

    def setup_monitor(self):
        monitors.Monitor("MainMonitor").save()

    def menu_page(self):
        self.set_background_color("#050505")
        self.set_instruction_text("EEG Typing Experiment")
        self.window.flip()

        core.wait(1.5)

    def get_ready(self):
        self.set_instruction_text("For each trial, type out the word displayed as quickly as possible.\n\nFor each letter, you will get feedback to indicate if you make a mistake.\n\nPress SPACE to proceed")
        self.window.flip()

        event.waitKeys(keyList = ["space"]) # await for user to actively proceed to trials

        self.set_instruction_text()
        self.window.flip()

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

    def present_trial(self, trial, word):
        cursor_position = 0
        while cursor_position < len(word):
            self.set_stimulus_text(word, cursor_position)
            self.window.flip()
            self.stopwatch.reset()
            pressed_key = event.waitKeys()[0]
            response_time = self.stopwatch.getTime()
            print(f"[KEYPRESS] {pressed_key.ljust(8)} {response_time:.2f}s")
            if pressed_key == word[cursor_position]:
                cursor_position += 1
        # self.log_result(
        #     trial = trial, 
        #     response_time = response_time,
        #     target_response = word,
        #     response = response,
        # )

    def run_blocks(self):
        for trial, word in enumerate(self.rand.sample(WORDBANK, TRIALS), start=1):
            self.present_trial(
                trial = trial,
                word = word,
            )

    def show_credits(self):
        self.set_background_color("grey")
        self.set_instruction_text("This concludes the experiment.")
        self.window.flip()
        core.wait(2)

    def log_result(self, block, trial, response_time, target_response, response):
        if not LOGFILE_PATH.is_file():
            with open(LOGFILE_PATH, "w") as file:
                file.write("timestamp,block,trial,response_time,target_response,response")
        with open(LOGFILE_PATH, "a") as file:
            file.write(f"\n{datetime.datetime.now()},{block},{trial},{response_time},{target_response},{response}")

if __name__ == "__main__":
    print(f"[INITIATED] {datetime.datetime.now()}")
    Experiment()
    print(f"[CONCLUDED] {datetime.datetime.now()}")