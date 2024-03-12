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

import shlex
import subprocess
import threading
import time
import tkinter as tk

import cv2 as cv
import numpy as np
import pyautogui

# TODO - Add support for pyscreenshot
# import pyscreenshot


def sleep(secs):
    print(f"Sleeping for {secs} seconds")
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
            codec = cv.VideoWriter_fourcc(*"mp4v")
        else:
            codec = cv.VideoWriter_fourcc(*"XVID")

        self.video = cv.VideoWriter(file_name, codec, frame_rate, size)

        self.is_recording = True

        while self.is_recording:
            try:
                screen_shot = pyautogui.screenshot()
                recframe = np.array(screen_shot)
                recframe = cv.cvtColor(recframe, cv.COLOR_BGR2RGB)
                recframe = cv.resize(recframe, size)

                if self.video is not None:
                    self.video.write(recframe)

                if cv.waitKey(1) == ord("e"):
                    self.stop()
                    break
            except Exception as e:
                print("An error occurred:", e)
                self.stop()
                break

    def stop(self):
        self.is_recording = False
        cv.destroyAllWindows()
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
    print("Clicking...")
    if image != None:
        location = pyautogui.locateOnScreen(image)
        x, y = pyautogui.center(location)
    else:
        x = int(x)
        y = int(y)

    pyautogui.moveTo(x, y)
    for _ in range(times):
        pyautogui.click()


def start(command, delay=0.5):
    try:
        print(f"Running '{command}'")
        subprocess.Popen(shlex.split(command))
        sleep(delay)
    except Exception as e:
        print(f"Error executing 'start' command: {e}")


def shoot(file_name):
    try:
        print("Shooting...")
        pyautogui.screenshot(file_name)
    except Exception as e:
        print(f"Error executing 'shoot' command: {e}")


root = tk.Tk(className="pyautocapture")

function_mapping = {
    "start": start,
    "sleep": sleep,
    "shoot": shoot,
    "click": click,
    "record": record,
    "stop_record": stop_record,
}

with open("file.txt", "r") as file:
    for line_num, line in enumerate(file, start=1):
        line = line.strip()
        parts = shlex.split(line)

        command = parts[0]
        args = []
        kwargs = {}
        i = 1
        while i < len(parts):
            if parts[i].startswith("-"):
                arg_name = parts[i][1:]
                i += 1
                if i < len(parts):
                    value = parts[i]
                    if value.isdigit():
                        value = int(value)
                    kwargs[arg_name] = value
            else:
                value = parts[i]
                if value.isdigit():
                    value = int(value)
                args.append(value)
            i += 1

        if command in function_mapping:
            try:
                function = function_mapping[command]
                function(*args, **kwargs)
            except TypeError as e:
                print(f"Error executing '{command}' command on line {line_num}: {e}")
        elif command.startswith("#"):
            pass
        else:
            print(f"Invalid command on line {line_num}: {command}")

root.mainloop()
