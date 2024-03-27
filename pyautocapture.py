"""
pyautocapture - Automate taking multiple screenshots and videos
Copyright (C) 2024 ethical_haquer

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

# TODO: Use classes

import shlex
import subprocess
import threading
import time
import tkinter as tk
from tkinter import scrolledtext

import cv2
import numpy as np
import PIL
import pyautogui

# TODO: Add support for pyscreenshot and mss
# import pyscreenshot
# import mss

file_name = "file.txt"
save_delay = 1
save_pending = False

open_apps = []


# Read the text file and display its content in the text widget
def display_text_file():
    text_area.delete("1.0", tk.END)
    with open(file_name, "r") as file:
        for line in file:
            text_area.insert(tk.END, line)


# Save the text widget content to the text file after a delay
def save_text_file_delayed(event):
    global save_pending
    if not save_pending:
        save_pending = True
        print("Saving text file soon")
        root.after(save_delay * 2000, save_text_file)


# Save the text widget content to the text file
def save_text_file():
    global save_pending
    save_pending = False
    print("Saving text file...")
    text_content = text_area.get("1.0", "end-1c")
    with open(file_name, "w") as file:
        file.write(text_content)


# Read the text file and execute commands
def read_text_file_and_execute(text_file):
    save_text_file()
    display_text_file()
    execute_commands(text_file, function_mapping)


def execute_commands(file_name, function_mapping):
    with open(file_name, "r") as file:
        for line_num, line in enumerate(file, start=1):
            line = line.strip()

            if not line or line.startswith("#"):
                print(f"Skipping empty line or comment on line {line_num}")
                continue

            try:
                exec(line, function_mapping)
            except Exception as e:
                print(f"Error executing command on line {line_num}: {e}")


def sleep(secs):
    print(f"SLEEPING for {secs} seconds")
    time.sleep(float(secs))


# WIP
class Recorder:
    def __init__(self):
        self.is_recording = False
        self.video = None

    def start(self, file_extension="avi"):
        size = pyautogui.size()
        frame_rate = 30
        file_name = "Screen_Recording." + file_extension

        if file_extension == "mp4":
            codec = cv2.VideoWriter_fourcc(*"mp4v")
        else:
            codec = cv2.VideoWriter_fourcc(*"XVID")

        self.video = cv2.VideoWriter(file_name, codec, frame_rate, size)

        self.is_recording = True

        while self.is_recording:
            try:
                screen_shot = pyautogui.screenshot()
                recframe = np.array(screen_shot)
                recframe = cv2.cvtColor(recframe, cv2.COLOR_BGR2RGB)
                recframe = cv2.resize(recframe, size)

                if self.video is not None:
                    self.video.write(recframe)

                if cv2.waitKey(1) == ord("e"):
                    self.stop()
                    break
            except Exception as e:
                print("An error occurred:", e)
                self.stop()
                break

    def stop(self):
        self.is_recording = False
        cv2.destroyAllWindows()
        if self.video is not None:
            self.video.release()


def record(file_extension="mp4"):
    if file_extension not in ["avi", "mp4"]:
        raise ValueError(
            "Invalid file_extension for record(). Valid values are 'avi' or 'mp4'."
        )

    global recorder
    recorder = Recorder()

    def record_thread():
        recorder.start(file_extension)

    threading.Thread(target=record_thread).start()


def stop_record():
    global recorder
    recorder.stop()


def click(image=None, x=None, y=None, times=1):
    sleep(0.1)
    print("CLICKING...")
    if image != None:
        location = pyautogui.locateOnScreen(image)
        x, y = pyautogui.center(location)
    else:
        x = int(x)
        y = int(y)

    pyautogui.moveTo(x, y)
    for _ in range(times):
        pyautogui.click()


# Create a backdrop for detecting where an app is
class Backdrop:
    def __init__(self, color, app_name=None, fullscreen=True):
        self.backdrop = tk.Toplevel(root)
        if app_name == None:
            self.title = "Backdrop"
        else:
            self.title = app_name + " Backdrop"
        self.backdrop.attributes("-fullscreen", True)
        self.backdrop.configure(bg=color)
        self.backdrop.title(self.title)
        self.backdrop.bind("<Escape>", self.exit_fullscreen)
        self.backdrop.update_idletasks()

    def exit_fullscreen(self, event=None):
        self.backdrop.attributes("-fullscreen", False)

    def destroy(self):
        sleep(0.1)
        self.backdrop.destroy()


# TODO: Figure out why changing the fading values and then hitting "Start" again doesn't change the screenshot (it does change the returned result)
# TODO: Removing fading can be automated, we know what color the backdrop was
def get_location(
    old_image_path,
    new_image_path,
    threshold,
    use_threshold=True,
    fading=None,
    left_fading=None,
    right_fading=None,
    top_fading=None,
    bottom_fading=None,
):
    old_image = cv2.imread(old_image_path)
    new_image = cv2.imread(new_image_path)

    diff = cv2.absdiff(old_image, new_image)
    gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)

    if use_threshold:
        print("Using a threshold")
        # Apply a threshold to ignore pixels that are only a little different
        _, thresh = cv2.threshold(gray_diff, threshold, 255, cv2.THRESH_BINARY)
    else:
        thresh = gray_diff

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if len(contours) > 0:
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)

        # TODO: Allow passing the fading argument as a list
        print(x, y, w, h)
        if fading:
            print("Fading is")
            if left_fading:
                print(f"left_fading: {left_fading}")
                x += left_fading
                w -= left_fading
            if right_fading:
                print(f"right_fading: {right_fading}")
                w -= right_fading
            if top_fading:
                print(f"top_fading: {top_fading}")
                y += top_fading
                h -= top_fading
            if bottom_fading:
                print(f"bottom_fading: {bottom_fading}")
                # y = y - bottom_fading
                h -= bottom_fading
            print(x, y, w, h)

        """
        cv2.imshow("Grayscale Difference Image", gray_diff)
        cv2.waitKey(0)

        result = new_image.copy()
        cv2.rectangle(result, (x, y), (x + w, y + h), (36, 255, 12), 2)
        cv2.imshow("Result", result)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        """

        return x, y, (x + w), (y + h)

    else:
        print("No contours found. New app window not detected.")
        return None


def start(
    command,
    name,
    threshold=50,
    backdrop=True,
    color="red",
    wait=1,
    use_threshold=False,
    fading=None,
    left_fading=None,
    right_fading=None,
    top_fading=None,
    bottom_fading=None,
):
    try:
        if backdrop == True:
            backdrop = Backdrop(color, name)
            sleep(0.2)
        pyautogui.screenshot("old.png")
        subprocess.Popen(shlex.split(command))
        sleep(wait)

        def destroy():
            backdrop.destroy()

        pyautogui.screenshot("new.png")
        print(f"RUNNING: '{command}'")
        location = get_location(
            "old.png",
            "new.png",
            threshold,
            use_threshold,
            fading,
            left_fading,
            right_fading,
            top_fading,
            bottom_fading,
        )
        # TODO: Just wait till get_location() is done
        sleep(0.5)
        t = threading.Timer(0.2, destroy)
        t.start()
        open_apps.append({"app": name, "location": location})
        # print(open_apps)
        # Allow time for the backdrop to delete itself
        sleep(0.1)

    except Exception as e:
        print(f"Error executing 'start' command: {e}")


# TODO: Move and resize an opened app
def move(app, x=0, y=0):
    pass


# Once we have the app location, we won't have to use a backdrop again, we'll just keep track of where the app is
def get_app_location(app_name, app_list):
    for app_dict in app_list:
        if app_dict["app"] == app_name:
            return app_dict["location"]
    return None


# Take a screenshot
def shoot(file_name, app=None):
    try:
        if app == None:
            print("SHOOTING the desktop...")
            pyautogui.screenshot(file_name)
        else:
            print(f"SHOOTING {app}...")
            loc = get_app_location(app, open_apps)
            # print(loc)
            screenshot = PIL.ImageGrab.grab(bbox=loc, xdisplay=None)
            screenshot.save(f"{app}.png")
    except Exception as e:
        print(f"Error executing 'shoot' command: {e}")


function_mapping = {
    "start": start,
    "sleep": sleep,
    "shoot": shoot,
    "click": click,
    "record": record,
    "stop_record": stop_record,
}


# Create the root window
root = tk.Tk(className="pyautocapture")

# Scrolled text widget
text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=50, height=20)
text_area.pack()

display_text_file()

# Start button to read the text file and execute commands
start_button = tk.Button(
    root, text="Start", command=lambda: read_text_file_and_execute(file_name)
)
start_button.pack()

# Bind the text widget to save the file after a delay when modified
text_area.bind("<KeyRelease>", save_text_file_delayed)

root.mainloop()
