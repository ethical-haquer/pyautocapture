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

# TODO: Use logging
# TODO: Add implementations for Wayland

import os
import re
import shlex
import subprocess
import threading
import time
import tkinter as tk
from tkinter import scrolledtext

import cv2
import mss
import numpy as np
import PIL
import pyautogui
import pywinctl
from fastgrab import screenshot as fastgrab_screenshot
from PIL import Image

# TODO: Add support for pyscreenshot and mss.
# import pyscreenshot

file_name = "file2.txt"

open_apps = []


# Read the text file and display its content in the text widget.
def display_text_file():
    text_area.delete("1.0", tk.END)
    with open(file_name, "r") as file:
        for line in file:
            text_area.insert(tk.END, line)


# Save the text widget content to the text file.
def save_text_file():
    print("Saving text file...")
    text_content = text_area.get("1.0", "end-1c")
    with open(file_name, "w") as file:
        file.write(text_content)


# Read the text file and execute commands.
def read_text_file_and_execute(text_file):
    save_text_file()
    display_text_file()
    sleep(0.2)
    execute_commands(text_file, function_mapping)


def execute_commands(file_name, function_mapping):
    with open(file_name, "r") as file:
        for line_num, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue
            if line.startswith("#"):
                continue
            try:
                exec(line, function_mapping)

            except Exception as e:
                print(f"Error executing command on line {line_num}: {e}")


def sleep(secs):
    # print(f"SLEEPING for {secs} seconds")
    time.sleep(float(secs))


# TODO: Fix this
class Recorder:
    def __init__(self):
        self.is_recording = False
        self.video = None

    def start(self, file_extension="avi"):
        global screen_width, screen_height
        monitor = {"top": 0, "left": 0, "width": screen_width, "height": screen_height}
        area = screen_width, screen_height
        frame_rate = 60
        file_name = "Screen_Recording." + file_extension

        if file_extension == "mp4":
            codec = cv2.VideoWriter_fourcc(*"mp4v")
        else:
            codec = cv2.VideoWriter_fourcc(*"XVID")

        self.video = cv2.VideoWriter(file_name, codec, frame_rate, area)

        self.is_recording = True

        with mss.mss() as sct:
            while self.is_recording:
                try:
                    # screen_shot = pyautogui.screenshot()
                    recframe = np.array(sct.grab(monitor))
                    recframe = cv2.cvtColor(recframe, cv2.COLOR_BGR2RGB)
                    recframe = cv2.resize(recframe, area)

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


# Create a backdrop for detecting where an app is.
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


def get_window_data():
    x, y, w, h, window_id = get_window_data_pywinctl()
    x = int(x)
    y = int(y)
    w = int(w)
    h = int(h)

    return x, y, w, h, window_id


def convert_to_bbox(x, y, w, h):
    left = x
    top = y
    right = x + w
    bottom = y + h
    return (left, top, right, bottom)


def convert_to_cartesian(x, y):
    global screen_width, screen_height
    cartesian_x = x - screen_width // 2
    cartesian_y = screen_height // 2 - y
    return cartesian_x, cartesian_y


def get_window_data_pywinctl():
    active_window = pywinctl.getActiveWindow()
    print(active_window)

    win_id = active_window.getHandle()
    win_id = hex(int(win_id))

    xwininfo_process = subprocess.Popen(
        ["xwininfo", "-id", win_id], stdout=subprocess.PIPE
    )
    output, _ = xwininfo_process.communicate()
    xwininfo_text = output.decode()

    absolute_x_pattern = r"Absolute upper-left X:  (\d+)"
    absolute_y_pattern = r"Absolute upper-left Y:  (\d+)"
    width_pattern = r"Width: (\d+)"
    height_pattern = r"Height: (\d+)"

    absolute_x_match = re.search(absolute_x_pattern, xwininfo_text)
    absolute_y_match = re.search(absolute_y_pattern, xwininfo_text)
    width_match = re.search(width_pattern, xwininfo_text)
    height_match = re.search(height_pattern, xwininfo_text)

    x = int(absolute_x_match.group(1))
    y = int(absolute_y_match.group(1))
    width = int(width_match.group(1))
    height = int(height_match.group(1))

    xprop_process = subprocess.Popen(["xprop", "-id", win_id], stdout=subprocess.PIPE)
    output, _ = xprop_process.communicate()
    xprop_text = output.decode()

    frame_extents_pattern = (
        r"_GTK_FRAME_EXTENTS\(CARDINAL\) = (\d+), (\d+), (\d+), (\d+)"
    )
    frame_extents_match = re.search(frame_extents_pattern, xprop_text)

    if frame_extents_match:
        left, right, top, bottom = map(int, frame_extents_match.groups())
        width -= left + right
        height -= top + bottom
        x += left
        y += top

    return x, y, width, height, win_id


# Given a window's x, y, w, and h, return the top bar position.
def top_bar_position(x, y, w, h):
    try:
        # x = x + (w / 2)
        x += 25
        y += 30
        # print(f"top_bar_pos is: ", x, y)
        return x, y
    except Exception as e:
        print(e)


def get_screen_size():
    width, height = pyautogui.size()
    return width, height


# TODO: Needs work
def start(
    command,
    name,
    backdrop=True,
    color="red",
    wait=1,
):
    try:
        global screen_width, screen_height
        screen_width, screen_height = get_screen_size()
        if backdrop == True:
            backdrop = Backdrop(color, name)
            sleep(0.2)

            def destroy():
                print("DESTROYING backdrop...")
                backdrop.destroy()

        else:

            def destroy():
                pass

        print(f"RUNNING: '{command}'")
        subprocess.Popen(shlex.split(command))
        sleep(wait)

        x, y, w, h, window_id = get_window_data()

        # TODO: Just wait till get_window_data() is done
        sleep(0.5)
        t = threading.Timer(0.2, destroy)
        t.start()

        open_apps.append({"app": name, "location": (x, y, w, h), "id": window_id})
        print(open_apps)

        # Allow time for the backdrop to delete itself
        sleep(0.1)

    except Exception as e:
        print(f"Error executing 'start' command: {e}")


# TODO: Move and resize an opened app
def move_app(app, x=0, y=0):
    pass


# Move the mouse
def move_mouse(x=None, y=None, image=None, cartesian=True):
    sleep(0.1)
    if image != None:
        location = pyautogui.locateOnScreen(image)
        x, y = pyautogui.center(location)
        print(f"MOVING to: {x}, {y}")
        pyautogui.moveTo(x, y)
    else:
        if cartesian:
            x, y = convert_to_cartesian(x, y)
            print(f"MOVING to cartesian: {x}, {y}")
            pyautogui.moveTo(x, y)
        else:
            print(f"MOVING to: {x}, {y}")
            pyautogui.moveTo(x, y)


# Click the mouse
def click(times=1):
    sleep(0.1)
    print("CLICKING...")
    for _ in range(times):
        pyautogui.click()


# Once we have the app location, we won't have to use a backdrop again,
# we'll just keep track of where the app is.
def get_app_location(app_name, app_list):
    try:
        for app_dict in app_list:
            if app_dict["app"] == app_name:
                x, y, w, h = app_dict["location"]
                left, top, right, bottom = convert_to_bbox(x, y, w, h)
                return x, y, w, h, left, top, right, bottom
        return None
    except Exception as e:
        print(f"An exception occured in get_app_location:\n{e}")


def get_window_id(app_name, app_list):
    try:
        for app_dict in app_list:
            if app_dict["app"] == app_name:
                window_id = app_dict["id"]
                return window_id
        return None
    except Exception as e:
        print(f"An exception occured in get_window_id:\n{e}")


# Does the actual screenshooting
def shoot(file_name, app=None, tool="import", x_offset=0, y_offset=0):
    try:
        if app:
            # TODO: Add error handling
            print(f"SHOOTING {app} with {tool}...")
            app_location = get_app_location(app, open_apps)
            window_id = get_window_id(app, open_apps)
            # window = window
            # raiseWindow
            if app_location:
                x, y, w, h, left, top, right, bottom = app_location
        else:
            print("SHOOTING the desktop...")
        if tool == "fastgrab":
            if app == None:
                img = fastgrab_screenshot.Screenshot().capture()
                im = Image.fromarray(img)
                im.save(f"{file_name}")
            else:
                pass

        elif tool == "pyautogui":
            if app == None:
                pyautogui.screenshot(file_name)
            else:
                screenshot = PIL.ImageGrab.grab(
                    bbox=(left, top, right, bottom), xdisplay=None
                )
                screenshot.save(f"{file_name}")

        elif tool == "import":
            if app == None:
                os.system(f"import -window root {file_name}")
            else:
                os.system(f"import -window {window_id} {file_name}")

        elif tool == "gnome-screenshot":
            if app == None:
                os.system(f"gnome-screenshot --file {file_name}")
            else:
                # TODO: This grabs the current window,
                # we can use pyautogui to click the correct window before-hand
                os.system(f"gnome-screenshot --window {window_id} --file {file_name}")

        elif tool == "mss":
            if app == None:
                with mss.mss() as sct:
                    sct.shot(output=f"{file_name}")
            else:
                with mss.mss() as sct:
                    area = {"top": top, "left": left, "width": w, "height": h}
                    # Grab the data
                    sct_img = sct.grab(area)

                    # Save to the picture file
                    mss.tools.to_png(sct_img.rgb, sct_img.size, output=f"{file_name}")

                pass
    except Exception as e:
        print(f"Error executing 'shoot' command: {e}")


function_mapping = {
    "start": start,
    "sleep": sleep,
    "shoot": shoot,
    "move_mouse": move_mouse,
    "click": click,
    # "record": record,
    # "stop_record": stop_record,
}

# Create the root window.
root = tk.Tk(className="pyautocapture")
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

# Create the scrolled text widget.
text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=50, height=20)
text_area.grid(row=0, column=0, sticky="nesw")

display_text_file()

# Start button to read the text file and execute commands.
start_button = tk.Button(
    root, text="Start", command=lambda: read_text_file_and_execute(file_name)
)

start_button.grid(row=1, column=0, sticky="we")

root.protocol("WM_DELETE_WINDOW", save_text_file())

root.mainloop()
