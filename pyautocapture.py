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
import time
import tkinter as tk

import cv2 as cv
import numpy as np
import pyautogui


def sleep(secs):
    print(f"Sleeping for {secs} seconds")
    time.sleep(float(secs))


# WIP
class Recorder:
    def _init_(self):
        pass

    def start(self):
        size = pyautogui.size()
        # Define the codec and frame rate
        codec = cv.VideoWriter_fourcc(*"XVID")
        frame_rate = 40  # Adjust the frame rate as needed

        # Create the VideoWriter object with user-specified codec and frame rate
        self.video = cv.VideoWriter("Screen_Recording.avi", codec, frame_rate, size)

        while True:
            try:
                screen_shot = pyautogui.screenshot()
                recframe = np.array(screen_shot)
                recframe = cv.cvtColor(recframe, cv.COLOR_BGR2RGB)

                # Resize the frame for optimization
                recframe = cv.resize(recframe, size)

                self.video.write(recframe)
                cv.imshow("Recording Preview (Minimize it)", recframe)

                if cv.waitKey(1) == ord("e"):
                    break
            except Exception as e:
                print("An error occurred:", e)
                break
        self.stop()

    def stop(self):
        cv.destroyAllWindows()
        self.video.release()


def record():
    recorder = Recorder()
    recorder.start()


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
                    # Convert value to integer if possible
                    if value.isdigit():
                        value = int(value)
                    kwargs[arg_name] = value
            else:
                value = parts[i]
                # Convert value to integer if possible
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
